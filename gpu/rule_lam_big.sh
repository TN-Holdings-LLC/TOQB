#!/bin/bash
# Flow J (prereg/drafts-2026-10-27/rule_lam_big_note.md): fold:rule's lam at n = 20,
# 22, 24 on the twin of ibm_kingston's 2026-10-24 calibration. Run from the folder that holds TOQB, psf and venv:
#   TARGET=/workspace/target.pkl OUT=/workspace/rule_lam_big NS="20 22" bash TOQB/gpu/rule_lam_big.sh 2>&1 | tee rb.txt
# A zip of everything so far is written after each n (rule_lam_big_n<n>.zip).
set -u
W=$(pwd)
TQ=${TOQB_DIR:-$W/TOQB}
PSF=${PSF_DIR:-$W/psf}
VA=${VENV_ACT:-$W/venv/bin/activate}
OUT=${OUT:?set OUT}
TARGET=${TARGET:?set TARGET}
NS=${NS:-"20 22"}
NOTE=${NOTE:-prereg/drafts-2026-10-27/rule_lam_big_note.md}
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
stamp() { echo "$1 $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')" | tee -a "$OUT/times.txt"; }
{ nvidia-smi --query-gpu=name,memory.total --format=csv,noheader; echo "toqb $(git log --oneline -1)"; \
  echo "psf-zero $(git -C "$PSF" log --oneline -1)"; echo "note $(sha256sum "$NOTE")"; \
  echo "target $(sha256sum "$TARGET" | cut -c1-64)"; echo "noiseless ${TOQB_NOISELESS:-qiskit}"; } | tee "$OUT/times.txt"
stamp start
for n in $NS; do
  stamp "n$n start"
  python -m toqb.fold_lam "$OUT/n$n.jsonl" --n "$n" --L 16 --P 24 --T 256 --models sim --arms fold:rule \
    --max-active 24 --models-seed 0 1 2 3 --device "file:$TARGET" > "$OUT/n$n.log" 2>&1
  stamp "n$n done"
  python -m zipfile -c "$W/rule_lam_big_n$n.zip" "$OUT" && echo "== zip: $W/rule_lam_big_n$n.zip"
done
stamp "all done"
