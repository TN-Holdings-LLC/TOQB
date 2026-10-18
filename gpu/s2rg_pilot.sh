#!/bin/bash
# GPU pod: S2R2-B pilot (tuning only, not scored; seeds 101 and 102 are outside every pre-registered seed range).
# Installs the environment if needed, checks the trajectory engine on the GPU, times it, probes CUDA-Q, measures how
# well the simulator knows the stand-in's gradient (toqb.gradcos: both compilers, L = 8 and 16), then runs
#   S2R2-B (toqb.s2r2 s2rg): lr in {0.05, 0.1, 0.2};  SPSA2: a in {0.2, 0.5, 1.0} (c = 0.2, A = 10);
#   both compilers, L = 8 and 16, n = 10, budget $100 of stand-in time each (about 500 loops of 2 circuits x 100 shots).
# Results go to OUT (outside the repo; must not exist) and a zip into DAY. Run from the folder that holds the TOQB clone:
#   DAY=... OUT=... PAR=6 setsid nohup bash TOQB/gpu/s2rg_pilot.sh > pilot.txt 2>&1 &
set -u
W=$(pwd)
DAY=${DAY:?set DAY to the folder that receives the zip}
OUT=${OUT:?set OUT to a new folder for the results}
PAR=${PAR:-6}
[ -d "$W/TOQB" ] || { echo "STOP: no TOQB clone here"; exit 1; }
[ -e "$OUT" ] && { echo "STOP: $OUT exists; a run never overwrites another"; exit 1; }
[ -d "$W/psf" ] || git clone -q https://github.com/TN-Holdings-LLC/psf-zero.git "$W/psf" || { echo "STOP: psf-zero clone"; exit 1; }
if [ ! -d "$W/venv" ]; then
  python3 -m venv "$W/venv" && . "$W/venv/bin/activate"
  pip install -q qiskit==2.5.2 qiskit-aer==0.17.2 qiskit-ibm-runtime==0.49.0 numpy scipy maturin cupy-cuda12x \
    || { echo "STOP: pip"; exit 1; }
  command -v cargo >/dev/null || { curl -sSf https://sh.rustup.rs | sh -s -- -y -q && . "$HOME/.cargo/env"; }
  ( cd "$W/psf" && pip install -q -e . && maturin develop --release -q ) || { echo "STOP: PSF-Zero core"; exit 1; }
fi
. "$W/venv/bin/activate"
python -c "import psf_zero_core as c; print('CORE_VERSION', c.CORE_VERSION)" || { echo "STOP: PSF-Zero core"; exit 1; }
mkdir -p "$OUT/logs" "$OUT/plans" "$OUT/runs"
{ nvidia-smi --query-gpu=name,memory.total --format=csv,noheader; echo "cpus $(nproc)"; \
  echo "toqb $(git -C "$W/TOQB" log --oneline -1)"; echo "psf-zero $(git -C "$W/psf" log --oneline -1)"; \
  echo "start $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')"; } | tee "$OUT/times.txt"
export PYTHONPATH="$W/TOQB" PSF_ZERO_REPO="$W/psf" PYTHONWARNINGS=ignore TOQB_XP=cupy TOQB_TRAJ_DTYPE=complex64 \
  TOQB_TRAJ_MEM_GB=${TOQB_TRAJ_MEM_GB:-4} OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 RAYON_NUM_THREADS=1 \
  PSF_COMPILE_FILE="$W/psf/patches/psf_compile_c61_2026-10-15/psf_compile.py" \
  PSF_AI_FILE="$W/psf/patches/psf_ai_compile_a22_2026-10-15/psf_ai_compile.py"
cd "$W/TOQB" || exit 1
echo "== check_traj2 on the GPU"; python -m toqb.check_traj2 2>&1 | tee "$OUT/check_traj2.txt" | tail -n 1
grep -q '^PASS' "$OUT/check_traj2.txt" || { echo "STOP: check_traj2 did not pass"; exit 1; }
echo "== bench_traj2"; python -m toqb.bench_traj2 10 8 16 2>&1 | tee "$OUT/bench_traj2.txt"
echo "== CUDA-Q probe (first contact; failures are reported, not fatal)"
( pip install -q cudaq && python -m toqb.cudaq_probe 8 16 ) > "$OUT/cudaq_probe.txt" 2>&1; tail -n 20 "$OUT/cudaq_probe.txt"
echo "== gradient agreement, simulator vs stand-in (24 directions, 8 points, T = 256; two student means each)"
for L in 8 16; do for a in psfai:template qiskit:2:target:template; do for sd in 5 6; do
  python -m toqb.gradcos "$a" $L 24 8 256 $sd 2>&1 | tail -n 1; done; done; done | tee "$OUT/gradcos.txt"
python - "$OUT/plans" <<'PY'
import json, sys
out = sys.argv[1]
base = {"device": "fake:FakeFez", "evaluation": {"test_traj": 64, "seed": 777, "every": 50},
        "standin": {"t12": 0.3, "over": 0.01, "zz_hz": 10000.0, "seed": 20261017},
        "qpu_cost": {"per_shot_s": 0.00027, "per_circuit_s": 0.036, "usd_per_s": 1.6}}
for L in (8, 16):
    for seed in (101, 102):
        for lr, a in ((0.05, 0.2), (0.1, 0.5), (0.2, 1.0)):
            p = dict(base, name=f"S2RG pilot L{L} s{seed} lr{lr} a{a}",
                     task={"n": 10, "layers": L, "enc": 1.5707963267948966, "teacher_seed": 4, "teacher_angle": 0.3,
                           "teacher_gap": 0.2, "n_train": 64, "n_test": 200},
                     s2rg={"seed": seed, "init": 1.0, "pairs": 8, "sim_batch": 4, "sim_traj": 32, "h": 0.1, "lr": lr,
                           "shots": 100, "budget_usd": 100.0, "max_loops": 100000},
                     spsa2={"seed": seed, "init": 1.0, "a": a, "c": 0.2, "A": 10, "max_iterations": 100000})
            json.dump(p, open(f"{out}/L{L}_s{seed}_lr{lr}_a{a}.json", "w"), indent=1)
PY
JOBS="$OUT/jobs.txt"
for L in 8 16; do for k in s2rg spsa2; do for f in "$OUT"/plans/L${L}_*.json; do for arm in psfai:template qiskit:2:target:template; do
  echo "$k $f $arm"; done; done; done; done > "$JOBS"
echo "$(wc -l < "$JOBS") runs, PAR=$PAR" | tee -a "$OUT/times.txt"
export OUT
xargs -P "$PAR" -L 1 sh -c 'b=$(basename "$1" .json); a=$(echo "$2" | tr : _); \
  python -m toqb.s2r2 "$0" "$1" "$OUT/runs/$0-$b-$a.json" "$2" > "$OUT/logs/$0-$b-$a.log" 2>&1; \
  echo "$0 $b $2 done $(TZ=Europe/Zurich date +%H:%M:%S) $(tail -n 1 "$OUT/logs/$0-$b-$a.log" | cut -c1-200)"' < "$JOBS" \
  | tee "$OUT/progress.txt"
echo "end $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')" | tee -a "$OUT/times.txt"
python - "$OUT" <<'PY' | tee "$OUT/summary.txt"
import glob, json, os, sys
rows = []
for f in sorted(glob.glob(os.path.join(sys.argv[1], "runs", "*.json"))):
    r = json.load(open(f))
    ev = r.get("evals") or [{}]
    rows.append((os.path.basename(f)[:-5], r.get("valid"), r.get("auc_ce"), ev[0].get("ce"), ev[-1].get("ce"),
                 r.get("loops") or r.get("iterations"), r.get("wall_s")))
for name, ok, auc, c0, c1, k, w in rows:
    print(f"{name:60s} valid {ok} auc {auc:.4f} ce {c0:.4f} -> {c1:.4f} loops {k} wall {w / 60:.1f} min"
          if auc is not None else f"{name:60s} valid {ok} (no evaluation)")
PY
python -m zipfile -c "$DAY/s2rg_pilot.zip" "$OUT" && echo "== DONE: $DAY/s2rg_pilot.zip"
