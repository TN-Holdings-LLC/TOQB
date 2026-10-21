#!/bin/bash
# GPU pod, short: W12's twin part (T2) on the fruit match's and the test match's records, keeping the twin's per-point
# training outputs (z_train) for the label-free undamping test (results/readout-2026-10-21). About 20 to 30 minutes.
#   OUT=... setsid nohup bash TOQB/gpu/w12_twin.sh > w12.txt 2>&1 < /dev/null &
set -u
W=$(pwd)
TQ=${TOQB_DIR:-$W/TOQB}
PSF=${PSF_DIR:-$W/psf}
VA=${VENV_ACT:-$W/venv/bin/activate}
OUT=${OUT:?set OUT}
DIRS=${DIRS:-"$W/fruit_match_1/runs $W/s2re4_match_1/runs"}
[ -e "$OUT" ] && { echo "STOP: $OUT exists"; exit 1; }
. "$VA"
export PYTHONPATH="$TQ" PSF_ZERO_REPO="$PSF" PYTHONWARNINGS=ignore TOQB_XP=cupy TOQB_TRAJ_DTYPE=complex64 \
  TOQB_TRAJ_MEM_GB=${TOQB_TRAJ_MEM_GB:-4} OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 RAYON_NUM_THREADS=1 \
  PSF_COMPILE_FILE="$PSF/patches/psf_compile_c61_2026-10-15/psf_compile.py" \
  PSF_AI_FILE="$PSF/patches/psf_ai_compile_a22_2026-10-15/psf_ai_compile.py"
cd "$TQ" || exit 1
echo "start $(TZ=Europe/Zurich date '+%H:%M:%S %Z') toqb $(git log --oneline -1 | cut -c1-8)"
python -m toqb.w12_check twin "$OUT" $DIRS && echo "== DONE: $OUT ($(wc -l < "$OUT") points) $(TZ=Europe/Zurich date '+%H:%M:%S %Z')"
