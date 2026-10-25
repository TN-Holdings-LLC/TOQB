#!/bin/bash
# Flow D, the pod step (prereg/drafts-2026-10-25/fold_lam_note.md): toqb.fold_lam at L = 8, then L = 16.
# Run from the folder that holds TOQB, psf and venv (after gpu/setup_and_bench.sh):
#   OUT=/workspace/fold_lam_2026-10-25 bash TOQB/gpu/fold_lam.sh 2>&1 | tee fl.txt
set -u
W=$(pwd)
TQ=${TOQB_DIR:-$W/TOQB}
PSF=${PSF_DIR:-$W/psf}
VA=${VENV_ACT:-$W/venv/bin/activate}
OUT=${OUT:?set OUT}
[ -d "$TQ" ] && [ -f "$VA" ] && [ -d "$PSF" ] || { echo "STOP: needs TOQB, venv, psf"; exit 1; }
[ -e "$OUT" ] && { echo "STOP: $OUT exists; a run never overwrites another"; exit 1; }
[ -d "$PSF/patches/psf_ai_compile_a25_2026-10-25" ] || { echo "STOP: psf-zero has no a25 (pull fab3602 or later)"; exit 1; }
. "$VA"
mkdir -p "$OUT"
unset PSF_AI_FILE PSF_COMPILE_FILE PSF_RING_ZIP
export PYTHONPATH="$TQ" PSF_ZERO_REPO="$PSF" PYTHONWARNINGS=ignore TOQB_XP=${TOQB_XP:-cupy} TOQB_TRAJ_DTYPE=complex64 \
  TOQB_TRAJ_MEM_GB=${TOQB_TRAJ_MEM_GB:-16} OMP_NUM_THREADS=4
cd "$TQ" || exit 1
. "$TQ/gpu/rust_psf.sh"
{ nvidia-smi --query-gpu=name,memory.total --format=csv,noheader; echo "toqb $(git log --oneline -1)"; \
  echo "psf-zero $(git -C "$PSF" log --oneline -1)"; echo "note $(sha256sum prereg/drafts-2026-10-25/fold_lam_note.md)"; \
  echo "start $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')"; } | tee "$OUT/times.txt"
for L in 8 16; do
  python -m toqb.fold_lam "$OUT/L$L.jsonl" --n 9 10 11 13 14 15 16 17 18 19 --L $L --P 24 --T 256 --models sim dev \
    --arms fold:template psfai:template_zip qiskit:2:target:template --max-active 24 > "$OUT/L$L.log" 2>&1
  echo "L $L done $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')" | tee -a "$OUT/times.txt"
done
python -m zipfile -c "$W/fold_lam.zip" "$OUT" && echo "== DONE: $W/fold_lam.zip"
