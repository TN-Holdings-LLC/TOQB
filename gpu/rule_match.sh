#!/bin/bash
# Flow F, test match 2 (prereg/drafts-2026-10-26/rule_match_note.md): toqb.fold_lam, the count rule against the
# zipper over four models at L = 16, then the read-out node moved. Run from the folder that holds TOQB, psf and venv:
#   OUT=/workspace/rule_match_2026-10-26 bash TOQB/gpu/rule_match.sh 2>&1 | tee rm.txt
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
  echo "psf-zero $(git -C "$PSF" log --oneline -1)"; echo "note $(sha256sum prereg/drafts-2026-10-26/rule_match_note.md)"; \
  echo "start $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')"; } | tee "$OUT/times.txt"
A="--L 16 --P 24 --T 256 --models sim dev --max-active 20 --models-seed 0 1 2 3"
python -m toqb.fold_lam "$OUT/main.jsonl" --n 13 14 15 16 17 18 --arms fold:rule psfai:template_zip $A > "$OUT/main.log" 2>&1
echo "main done $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')" | tee -a "$OUT/times.txt"
python -m toqb.fold_lam "$OUT/rot.jsonl" --n 13 14 15 16 17 --arms fold:rulerot $A > "$OUT/rot.log" 2>&1
echo "rot done $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')" | tee -a "$OUT/times.txt"
python -m zipfile -c "$W/rule_match.zip" "$OUT" && echo "== DONE: $W/rule_match.zip"
