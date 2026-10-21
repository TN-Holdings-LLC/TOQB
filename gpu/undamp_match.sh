#!/bin/bash
# GPU pod: the undamped-readout match (W14 draft, 2026-10-21). Design C's training (C0: toqb.s2rc_ckpt, seed 201, init 0,
# 2,000 loops) on both compiler arms (PSF and Qiskit level 2 with the Target), fresh teachers 13, 14, 15 x the W9
# ladder (angles 0.3, 1.0, 2.0) x L 8: 18 runs; then toqb.undamp_run on each (final parameters, 1,024 trajectories).
# Scoring at home: toqb.match_score_undamp RUNS UNDAMP OUT.md. Simulation only, no IBM.
# Order: the Qiskit runs first (about twice as long), then PSF, then the undamp step.
# RUST (default 1, gpu/rust_psf.sh): the PSF arm's template built in Rust and checked against the Python's, and bound in
# Rust (TOQB_FAST_PSF=1: records bit-identical to the Python path); RUST=0 for the Python path. Needs cargo.
#   DAY=... OUT=... setsid nohup bash TOQB/gpu/undamp_match.sh > undamp.txt 2>&1 < /dev/null &
set -u
W=$(pwd)
TQ=${TOQB_DIR:-$W/TOQB}
PSF=${PSF_DIR:-$W/psf}
VA=${VENV_ACT:-$W/venv/bin/activate}
DAY=${DAY:?set DAY}
OUT=${OUT:?set OUT}
PAR=${PAR:-6}
[ -d "$TQ" ] && [ -f "$VA" ] && [ -d "$PSF" ] || { echo "STOP: needs TOQB, the venv and psf (see the header)"; exit 1; }
[ -e "$OUT" ] && { echo "STOP: $OUT exists; a run never overwrites another"; exit 1; }
. "$VA"
mkdir -p "$OUT/logs" "$OUT/plans" "$OUT/runs" "$OUT/undamp" "$DAY"
{ nvidia-smi --query-gpu=name,memory.total --format=csv,noheader; echo "toqb $(git -C "$TQ" log --oneline -1)"; \
  echo "PAR=$PAR"; echo "start $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')"; } | tee "$OUT/times.txt"
export PYTHONPATH="$TQ" PSF_ZERO_REPO="$PSF" PYTHONWARNINGS=ignore TOQB_XP=cupy TOQB_TRAJ_DTYPE=complex64 \
  TOQB_TRAJ_MEM_GB=${TOQB_TRAJ_MEM_GB:-4} OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 RAYON_NUM_THREADS=1 \
  PSF_COMPILE_FILE="$PSF/patches/psf_compile_c61_2026-10-15/psf_compile.py" \
  PSF_AI_FILE="$PSF/patches/psf_ai_compile_a22_2026-10-15/psf_ai_compile.py"
cd "$TQ" || exit 1
. "$TQ/gpu/rust_psf.sh"
python - "$OUT/plans" <<'PY'
import json, sys
out = sys.argv[1]
for a in (0.3, 1.0, 2.0):
    for ts in (13, 14, 15):
        plan = {"name": f"undamp match C0 L8 angle{a} teacher{ts}", "device": "snapshot:marrakesh",
                "task": {"n": 10, "layers": 8, "enc": 1.5707963267948966, "teacher_seed": ts, "teacher_angle": a,
                         "teacher_gap": 0.2, "n_train": 64, "n_test": 500},
                "train": {"seed": 201, "init": 0.0, "pairs": 8, "sim_batch": 4, "sim_traj": 32, "h": 0.1, "lr": 0.4,
                          "loops": 2000, "curve_every": 200, "curve_points": 100, "curve_traj": 64},
                "predict": {"traj": 1024, "shots": 1000, "reps": 20000, "level": 0.99, "seed": 50000 + ts},
                "standin": {"t12": 0.3, "over": 0.01, "zz_hz": 10000.0, "seed": 20261017}}
        json.dump(plan, open(f"{out}/C0_L8_a{a}_t{ts}.json", "w"), indent=1)
PY
JOBS="$OUT/jobs.txt"
{ for f in "$OUT"/plans/*.json; do echo "$f qiskit:2:target:template"; done; \
  for f in "$OUT"/plans/*.json; do echo "$f psfai:template"; done; } > "$JOBS"
echo "$(wc -l < "$JOBS") runs" | tee -a "$OUT/times.txt"
export OUT
xargs -P "$PAR" -L 1 sh -c 'b=$(basename "$0" .json); a=$(echo "$1" | tr : _); \
  python -m toqb.s2rc_ckpt "$0" "$OUT/runs/$b-$a.json" "$1" > "$OUT/logs/$b-$a.log" 2>&1; \
  python -m toqb.undamp_run "$OUT/runs/$b-$a.json" "$OUT/undamp/$b-$a.json" --final-only > "$OUT/logs/$b-$a.undamp.log" 2>&1; \
  echo "$b $1 done $(TZ=Europe/Zurich date +%H:%M:%S) $(tail -n 1 "$OUT/logs/$b-$a.undamp.log" | cut -c1-200)"' < "$JOBS" \
  | tee "$OUT/progress.txt"
echo "end $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')" | tee -a "$OUT/times.txt"
python -m zipfile -c "$DAY/undamp_match.zip" "$OUT" && echo "== DONE: $DAY/undamp_match.zip"
