#!/bin/bash
# Flow H, amendment 1 (prereg/drafts-2026-10-26/holes_vs_zip_amend1.md): the n = 10 part on the pod.
#   OUT=/workspace/flow_h_n10 bash TOQB/gpu/holes_zip_n10.sh 2>&1 | tee fh.txt
set -u
W=$(pwd); TQ=${TOQB_DIR:-$W/TOQB}; PSF=${PSF_DIR:-$W/psf}; VA=${VENV_ACT:-$W/venv/bin/activate}; OUT=${OUT:?set OUT}
[ -d "$TQ" ] && [ -f "$VA" ] && [ -d "$PSF" ] || { echo "STOP: needs TOQB, venv, psf"; exit 1; }
[ -e "$OUT" ] && { echo "STOP: $OUT exists; a run never overwrites another"; exit 1; }
. "$VA"; mkdir -p "$OUT"
unset PSF_AI_FILE PSF_COMPILE_FILE PSF_RING_ZIP
export PYTHONPATH="$TQ" PSF_ZERO_REPO="$PSF" PYTHONWARNINGS=ignore TOQB_XP=${TOQB_XP:-cupy} TOQB_TRAJ_DTYPE=complex64 \
  TOQB_TRAJ_MEM_GB=${TOQB_TRAJ_MEM_GB:-16} OMP_NUM_THREADS=4
cd "$TQ" || exit 1
. "$TQ/gpu/rust_psf.sh"
{ echo "toqb $(git log --oneline -1)"; echo "psf-zero $(git -C "$PSF" log --oneline -1)"; \
  echo "note $(sha256sum prereg/drafts-2026-10-26/holes_vs_zip_note.md)"; echo "amend $(sha256sum prereg/drafts-2026-10-26/holes_vs_zip_amend1.md)"; \
  echo "start $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')"; } | tee "$OUT/times.txt"
python -m toqb.fold_lam "$OUT/n10.jsonl" --n 10 --L 16 --P 24 --T 256 --models sim dev \
  --arms fold:template psfai:template_zip --max-active 20 --models-seed 0 1 2 3 > "$OUT/n10.log" 2>&1
echo "done $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')" | tee -a "$OUT/times.txt"
python -m zipfile -c "$W/flow_h_n10.zip" "$OUT" && echo "== DONE: $W/flow_h_n10.zip"
