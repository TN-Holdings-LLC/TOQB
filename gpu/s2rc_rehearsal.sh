#!/bin/bash
# GPU pod: design C rehearsal (simulation only; not scored). For each seed, compiler and depth: learn on the GPU twin
# for LOOPS loops, predict one device job (P test points x SHOTS shots, 99 % interval), then verify on the stand-in.
# The twin and the compilers use the stand-in's published calibration (device snapshot:marrakesh, owner decision of
# 2026-10-19): the stand-in differs from it only by its deliberate deviations (T1 / T2 scaled, over-rotation, ZZ).
# Needs the environment that gpu/s2rg_pilot.sh built (venv, psf next to TOQB). Run from the folder that holds TOQB:
#   DAY=... OUT=... LR=... setsid nohup bash TOQB/gpu/s2rc_rehearsal.sh > rehearsal.txt 2>&1 &
# LR is the learning rate chosen from the S2R2-B pilot. Seeds default to 201-203 (outside every earlier range).
set -u
W=$(pwd)
DAY=${DAY:?set DAY to the folder that receives the zip}
OUT=${OUT:?set OUT to a new folder for the results}
LR=${LR:?set LR, the learning rate chosen from the S2R2-B pilot}
LOOPS=${LOOPS:-2000}
SEEDS=${SEEDS:-201 202 203}
P=${P:-500}
SHOTS=${SHOTS:-1000}
PAR=${PAR:-6}
[ -d "$W/TOQB" ] && [ -d "$W/venv" ] && [ -d "$W/psf" ] || { echo "STOP: needs TOQB, venv and psf here"; exit 1; }
[ -e "$OUT" ] && { echo "STOP: $OUT exists; a run never overwrites another"; exit 1; }
. "$W/venv/bin/activate"
mkdir -p "$OUT/logs" "$OUT/plans" "$OUT/runs"
{ nvidia-smi --query-gpu=name,memory.total --format=csv,noheader; echo "cpus $(nproc)"; \
  echo "toqb $(git -C "$W/TOQB" log --oneline -1)"; echo "psf-zero $(git -C "$W/psf" log --oneline -1)"; \
  echo "LR=$LR LOOPS=$LOOPS SEEDS=$SEEDS P=$P SHOTS=$SHOTS PAR=$PAR"; \
  echo "start $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')"; } | tee "$OUT/times.txt"
export PYTHONPATH="$W/TOQB" PSF_ZERO_REPO="$W/psf" PYTHONWARNINGS=ignore TOQB_XP=cupy TOQB_TRAJ_DTYPE=complex64 \
  TOQB_TRAJ_MEM_GB=${TOQB_TRAJ_MEM_GB:-4} OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 RAYON_NUM_THREADS=1 \
  PSF_COMPILE_FILE="$W/psf/patches/psf_compile_c61_2026-10-15/psf_compile.py" \
  PSF_AI_FILE="$W/psf/patches/psf_ai_compile_a22_2026-10-15/psf_ai_compile.py"
cd "$W/TOQB" || exit 1
python - "$OUT/plans" "$LR" "$LOOPS" "$P" "$SHOTS" $SEEDS <<'PY'
import json, sys
out, lr, loops, P, shots, seeds = sys.argv[1], float(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]), sys.argv[6:]
for L in (8, 16):
    for s in seeds:
        s = int(s)
        plan = {"name": f"S2RC rehearsal L{L} s{s}", "device": "snapshot:marrakesh",
                "task": {"n": 10, "layers": L, "enc": 1.5707963267948966, "teacher_seed": 4, "teacher_angle": 0.3,
                         "teacher_gap": 0.2, "n_train": 64, "n_test": P},
                "train": {"seed": s, "init": 1.0, "pairs": 8, "sim_batch": 4, "sim_traj": 32, "h": 0.1, "lr": lr,
                          "loops": loops, "curve_every": 200, "curve_points": 100, "curve_traj": 64},
                "predict": {"traj": 1024, "shots": shots, "reps": 20000, "level": 0.99, "seed": 50000 + s},
                "standin": {"t12": 0.3, "over": 0.01, "zz_hz": 10000.0, "seed": 20261017}}
        json.dump(plan, open(f"{out}/L{L}_s{s}.json", "w"), indent=1)
PY
JOBS="$OUT/jobs.txt"
for f in "$OUT"/plans/L16_*.json "$OUT"/plans/L8_*.json; do for arm in qiskit:2:target:template psfai:template; do
  echo "$f $arm"; done; done > "$JOBS"
echo "$(wc -l < "$JOBS") runs" | tee -a "$OUT/times.txt"
export OUT
xargs -P "$PAR" -L 1 sh -c 'b=$(basename "$0" .json); a=$(echo "$1" | tr : _); \
  python -m toqb.s2rc "$0" "$OUT/runs/$b-$a.json" "$1" > "$OUT/logs/$b-$a.log" 2>&1; \
  echo "$b $1 done $(TZ=Europe/Zurich date +%H:%M:%S) $(tail -n 1 "$OUT/logs/$b-$a.log" | cut -c1-260)"' < "$JOBS" \
  | tee "$OUT/progress.txt"
echo "end $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')" | tee -a "$OUT/times.txt"
python - "$OUT" <<'PY' | tee "$OUT/summary.txt"
import glob, json, os, sys
print(f"{'run':44s} {'pred CE [99 %]':26s} {'stand-in CE':11s} in? {'pred acc':8s} {'acc':6s} p1 rmse  twin CE start->end")
for f in sorted(glob.glob(os.path.join(sys.argv[1], "runs", "*.json"))):
    r = json.load(open(f))
    name = os.path.basename(f)[:-5]
    if "rehearsal" not in r:
        print(f"{name:44s} no result ({r.get('error')})"); continue
    P, R, c = r["prediction"], r["rehearsal"], r["curve"]
    print(f"{name:44s} {P['ce_mean']:.4f} [{P['ce_interval'][0]:.4f}, {P['ce_interval'][1]:.4f}]  {R['ce']:.4f}      "
          f"{'yes' if R['ce_inside'] else 'NO ':3s} {P['acc_mean']:.3f}    {R['acc']:.3f}  {R['twin_vs_standin_p1_rmse']:.4f}  "
          f"{c[0]['twin_ce']:.4f}->{c[-1]['twin_ce']:.4f}")
PY
python -m zipfile -c "$DAY/s2rc_rehearsal.zip" "$OUT" && echo "== DONE: $DAY/s2rc_rehearsal.zip"
