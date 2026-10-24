#!/bin/bash
# Flow B (prereg/drafts-2026-10-24/flow_b_note.md): PART=b1 (the a24 switch on the GPU), b2 (where the readout offset
# comes from), b3 (decaying against constant step; declared rule). A pod or the owner's PC (WSL, RTX 4070). Run from
# the folder that holds TOQB, psf and venv:
#   PART=b1 OUT=$PWD/fb_b1 bash TOQB/gpu/flow_b.sh 2>&1 | tee fb_b1.txt
#   PART=b2 OUT=$PWD/fb_b2 setsid nohup bash TOQB/gpu/flow_b.sh > fb_b2.txt 2>&1 < /dev/null &
#   PART=b3 OUT=$PWD/fb_b3 setsid nohup bash TOQB/gpu/flow_b.sh > fb_b3.txt 2>&1 < /dev/null &
# The front end is PSF-Zero a24 (TOQB's default from fb86f64; PSF_AI_FILE and PSF_COMPILE_FILE are left unset).
set -u
W=$(pwd)
TQ=${TOQB_DIR:-$W/TOQB}
PSF=${PSF_DIR:-$W/psf}
VA=${VENV_ACT:-$W/venv/bin/activate}
OUT=${OUT:?set OUT}
PART=${PART:?set PART to b1, b2 or b3}
PAR=${PAR:-3}
[ -d "$TQ" ] && [ -f "$VA" ] && [ -d "$PSF" ] || { echo "STOP: needs TOQB, the venv and psf"; exit 1; }
[ -e "$OUT" ] && { echo "STOP: $OUT exists; a run never overwrites another"; exit 1; }
. "$VA"
mkdir -p "$OUT/logs"
unset PSF_AI_FILE PSF_COMPILE_FILE PSF_RING_ZIP
export PYTHONPATH="$TQ" PSF_ZERO_REPO="$PSF" PYTHONWARNINGS=ignore TOQB_XP=${TOQB_XP:-cupy} TOQB_TRAJ_DTYPE=complex64 \
  TOQB_TRAJ_MEM_GB=${TOQB_TRAJ_MEM_GB:-3} OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 RAYON_NUM_THREADS=1
cd "$TQ" || exit 1
. "$TQ/gpu/rust_psf.sh"
{ nvidia-smi --query-gpu=name,memory.total --format=csv,noheader; echo "toqb $(git log --oneline -1)"; \
  echo "psf-zero $(git -C "$PSF" log --oneline -1)"; echo "PART=$PART PAR=$PAR TOQB_TRAJ_MEM_GB=$TOQB_TRAJ_MEM_GB"; \
  echo "start $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')"; } | tee "$OUT/times.txt"

case "$PART" in
b1)
  echo "== check_traj, complex64, a24"; python -m toqb.check_traj 4000 2>&1 | tee "$OUT/check.txt"
  grep -q "^PASS" "$OUT/check.txt" || { echo "STOP: check_traj did not pass"; exit 1; }
  python - "$OUT" "$PSF" <<'PY' || { echo "STOP: a22 and a24 differ"; exit 1; }
import json, math, os, subprocess, sys
out, psf = sys.argv[1], sys.argv[2]
plan = dict(name="flow B1: a22 against a24, 20 loops", device="snapshot:marrakesh", verify=True,
            task=dict(n=10, layers=16, enc=math.pi / 2, teacher_seed=17, teacher_angle=1.0, teacher_gap=0.2,
                      n_train=64, n_test=20),
            train=dict(seed=301, init=0.0, pairs=8, sim_batch=4, sim_traj=32, h=0.1, lr=0.4, loops=20,
                       curve_every=200, curve_points=10, curve_traj=16, progress_every=10),
            predict=dict(traj=64, shots=250, reps=200, level=0.99, seed=50301),
            standin=dict(t12=0.3, over=0.01, zz_hz=10000.0, seed=20261017))
pf = os.path.join(out, "b1_plan.json"); json.dump(plan, open(pf, "w"), indent=1)
a22 = dict(PSF_AI_FILE=os.path.join(psf, "patches/psf_ai_compile_a22_2026-10-15/psf_ai_compile.py"),
           PSF_COMPILE_FILE=os.path.join(psf, "patches/psf_compile_c61_2026-10-15/psf_compile.py"))
ok = True
for spec in ("psfai:template_zip", "psfai:template"):
    res = {}
    for fe, extra in (("a24", {}), ("a22", a22)):
        f = os.path.join(out, f"b1_{spec.replace(':', '_')}_{fe}.json")
        subprocess.run([sys.executable, "-m", "toqb.s2rc_ckpt", pf, f, spec], env=dict(os.environ, **extra),
                       check=True, stdout=open(f + ".log", "w"), stderr=subprocess.STDOUT)
        res[fe] = json.load(open(f))["final_mean"]
    d = max(abs(a - b) for a, b in zip(res["a24"], res["a22"]))
    print(f"{spec}: max |a24 - a22| of the final parameters after 20 loops = {d:.3e}")
    ok &= d == 0.0
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
PY
  ;;
b2)
  python -m toqb.offset_ablate "$TQ/results/far-teacher-2026-10-23/runs" "$OUT/offset_ablate.json" \
    > "$OUT/logs/offset_ablate.log" 2>&1 || { echo "STOP: offset_ablate"; tail -5 "$OUT/logs/offset_ablate.log"; exit 1; }
  ;;
b3)
  mkdir -p "$OUT/plans" "$OUT/runs"
  python - "$OUT/plans" <<'PY' || { echo "STOP: plans"; exit 1; }
import json, math, os, sys
out = sys.argv[1]
for t in (20, 21, 22):
    for sched, dec in (("const", None), ("decay", {"A": 1000, "alpha": 0.602})):
        train = dict(seed=301, init=0.0, pairs=8, sim_batch=4, sim_traj=32, h=0.1, lr=0.4, loops=4000,
                     curve_every=500, curve_points=100, curve_traj=64, progress_every=250,
                     checkpoints=[500, 1000, 2000])
        if dec:
            train["lr_decay"] = dec
        p = dict(name=f"flow B3: L16 t{t} angle 1.0 s301 {sched}", device="snapshot:marrakesh", verify=True,
                 task=dict(n=10, layers=16, enc=math.pi / 2, teacher_seed=t, teacher_angle=1.0, teacher_gap=0.2,
                           n_train=64, n_test=500),
                 train=train, predict=dict(traj=1024, shots=250, reps=20000, level=0.99, seed=50301),
                 standin=dict(t12=0.3, over=0.01, zz_hz=10000.0, seed=20261017))
        json.dump(p, open(os.path.join(out, f"L16_t{t}_a10_s301-{sched}.json"), "w"), indent=1)
        print(f"L16_t{t}_a10_s301-{sched}.json", flush=True)
PY
  export OUT
  ls "$OUT"/plans/*.json | xargs -P "$PAR" -I{} sh -c 'b=$(basename {} .json); \
    python -m toqb.s2rc_ckpt {} "$OUT/runs/$b.json" psfai:template_zip > "$OUT/logs/$b.log" 2>&1; \
    echo "$b done $(TZ=Europe/Zurich date +%H:%M:%S) $(tail -n 1 "$OUT/logs/$b.log" | cut -c1-160)"' | tee "$OUT/progress.txt"
  echo "trained $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')" | tee -a "$OUT/times.txt"
  python -m toqb.lrdecay_score "$OUT/runs" "$OUT/score.md" --json "$OUT/score.json"
  ;;
*) echo "STOP: PART must be b1, b2 or b3"; exit 1 ;;
esac
echo "end $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')" | tee -a "$OUT/times.txt"
python -m zipfile -c "$W/flow_${PART}.zip" "$OUT" && echo "== DONE: $W/flow_${PART}.zip"
