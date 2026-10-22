#!/bin/bash
# GPU pod, report only (declared in prereg/drafts-2026-10-22/zip_undamp_note.md): toqb.undamp_run --final-only on the
# four records of results/zip-compare-2026-10-22/runs (item 31 and zipper, L 8 and 16), then
# toqb.zip_undamp_summary. Run from /workspace (venv, TOQB, psf there):
#   OUT=/workspace/zu_2026-10-22 setsid nohup bash TOQB/gpu/zip_undamp.sh > zu.txt 2>&1 < /dev/null &
set -u
W=$(pwd)
TQ=${TOQB_DIR:-$W/TOQB}
PSF=${PSF_DIR:-$W/psf}
VA=${VENV_ACT:-$W/venv/bin/activate}
OUT=${OUT:?set OUT}
PAR=${PAR:-2}
[ -e "$OUT" ] && { echo "STOP: $OUT exists; a run never overwrites another"; exit 1; }
. "$VA"
mkdir -p "$OUT/logs" "$OUT/undamp"
export PYTHONPATH="$TQ" PSF_ZERO_REPO="$PSF" PYTHONWARNINGS=ignore TOQB_XP=${TOQB_XP:-cupy} TOQB_TRAJ_DTYPE=complex64 \
  TOQB_TRAJ_MEM_GB=${TOQB_TRAJ_MEM_GB:-4}  # 4, as the runs it reads (another value reshapes the trajectory batches and the redraw differs) OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 RAYON_NUM_THREADS=1 \
  PSF_COMPILE_FILE="$PSF/patches/psf_compile_c61_2026-10-15/psf_compile.py" \
  PSF_AI_FILE="$PSF/patches/psf_ai_compile_a22_2026-10-15/psf_ai_compile.py"
cd "$TQ" || exit 1
. "$TQ/gpu/rust_psf.sh"
RUNS="$TQ/results/zip-compare-2026-10-22/runs"
{ nvidia-smi --query-gpu=name,memory.total --format=csv,noheader; echo "toqb $(git log --oneline -1)"; \
  echo "start $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')"; } | tee "$OUT/times.txt"
export OUT
ls "$RUNS"/*.json | xargs -P "$PAR" -I{} sh -c 'b=$(basename "{}" .json); \
  python -m toqb.undamp_run "{}" "$OUT/undamp/$b.json" --final-only > "$OUT/logs/$b.log" 2>&1; \
  echo "$b done $(TZ=Europe/Zurich date +%H:%M:%S) $(tail -n 1 "$OUT/logs/$b.log" | cut -c1-220)"' | tee "$OUT/progress.txt"
python -m toqb.zip_undamp_summary "$RUNS" "$OUT/undamp" | tee "$OUT/summary.md"
echo "end $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')" | tee -a "$OUT/times.txt"
python -m zipfile -c "$W/zip_undamp.zip" "$OUT" && echo "== DONE: $W/zip_undamp.zip"
