#!/bin/bash
# Flow G, test match 3 (prereg/drafts-2026-10-26/rule_match_k_note.md): the count rule against the zipper on the twin
# of ibm_kingston's 2026-10-24 calibration. Run from the folder that holds TOQB, psf and venv:
#   TARGET=/workspace/target.pkl OUT=/workspace/rule_match_k_2026-10-26 bash TOQB/gpu/rule_match_k.sh 2>&1 | tee rk.txt
set -u
W=$(pwd)
TQ=${TOQB_DIR:-$W/TOQB}
PSF=${PSF_DIR:-$W/psf}
VA=${VENV_ACT:-$W/venv/bin/activate}
OUT=${OUT:?set OUT}
TARGET=${TARGET:?set TARGET}
WANT=3b93913856d2f0b9bf97ac03f89c43457157735413b02d8722c82d31065b218d
[ -d "$TQ" ] && [ -f "$VA" ] && [ -d "$PSF" ] || { echo "STOP: needs TOQB, venv, psf"; exit 1; }
[ -e "$OUT" ] && { echo "STOP: $OUT exists; a run never overwrites another"; exit 1; }
[ "$(sha256sum "$TARGET" | cut -c1-64)" = "$WANT" ] || { echo "STOP: $TARGET is not the 2026-10-24 kingston Target"; exit 1; }
. "$VA"
mkdir -p "$OUT"
unset PSF_AI_FILE PSF_COMPILE_FILE PSF_RING_ZIP
export PYTHONPATH="$TQ" PSF_ZERO_REPO="$PSF" PYTHONWARNINGS=ignore TOQB_XP=${TOQB_XP:-cupy} TOQB_TRAJ_DTYPE=complex64 \
  TOQB_TRAJ_MEM_GB=${TOQB_TRAJ_MEM_GB:-16} OMP_NUM_THREADS=4
cd "$TQ" || exit 1
. "$TQ/gpu/rust_psf.sh"
{ nvidia-smi --query-gpu=name,memory.total --format=csv,noheader; echo "toqb $(git log --oneline -1)"; \
  echo "psf-zero $(git -C "$PSF" log --oneline -1)"; echo "note $(sha256sum prereg/drafts-2026-10-26/rule_match_k_note.md)"; \
  echo "target $(sha256sum "$TARGET" | cut -c1-64)"; \
  echo "start $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')"; } | tee "$OUT/times.txt"
python -m toqb.fold_lam "$OUT/main.jsonl" --n 13 14 15 16 17 18 --L 16 --P 24 --T 256 --models sim \
  --arms fold:rule psfai:template_zip --max-active 20 --models-seed 0 1 2 3 --device "file:$TARGET" > "$OUT/main.log" 2>&1
echo "main done $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')" | tee -a "$OUT/times.txt"
python -m zipfile -c "$W/rule_match_k.zip" "$OUT" && echo "== DONE: $W/rule_match_k.zip"
