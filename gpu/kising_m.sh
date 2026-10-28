#!/bin/bash
# Flow M (prereg/drafts-2026-10-28/kising_m_note.md): the kicked Ising ring at J = pi/4, h = 0.6, n = 20, fold:rule,
# L = 8, 16, 24, 50, 100, seeds 0-3, on the twin of ibm_kingston's 2026-10-24 calibration; exact noiseless reference.
# Run from the folder that holds TOQB, psf and venv:
#   TARGET=/workspace/target.pkl OUT=/workspace/kising_m_2026-10-28 nohup bash TOQB/gpu/kising_m.sh > km.txt 2>&1 &
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
unset PSF_AI_FILE PSF_COMPILE_FILE PSF_RING_ZIP TOQB_NOISELESS
export PYTHONPATH="$TQ" PSF_ZERO_REPO="$PSF" PYTHONWARNINGS=ignore TOQB_XP=${TOQB_XP:-cupy} TOQB_TRAJ_DTYPE=complex64 \
  TOQB_TRAJ_MEM_GB=${TOQB_TRAJ_MEM_GB:-16} OMP_NUM_THREADS=4
cd "$TQ" || exit 1
. "$TQ/gpu/rust_psf.sh"
stamp() { echo "$1 $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')" | tee -a "$OUT/times.txt"; }
{ nvidia-smi --query-gpu=name,memory.total --format=csv,noheader; echo "toqb $(git log --oneline -1)"; \
  echo "psf-zero $(git -C "$PSF" log --oneline -1)"; echo "note $(sha256sum prereg/drafts-2026-10-28/kising_m_note.md)"; \
  echo "target $(sha256sum "$TARGET" | cut -c1-64)"; } | tee "$OUT/times.txt"
stamp start
python -c "import pytest" 2>/dev/null || pip install -q pytest
python -m pytest -q tests/test_kising.py > "$OUT/check.log" 2>&1
if tail -1 "$OUT/check.log" | grep -q "6 passed"; then stamp "check PASS (tests/test_kising.py, 6 passed)"
else stamp "STOP check failed (see check.log)"; exit 1; fi
stamp "kising start"
python -m toqb.kising "$OUT/kising.jsonl" --n 20 --L 8 16 24 50 100 --h 0.6 --P 24 --T 256 --seeds 0 1 2 3 \
  --arms fold:rule --device "file:$TARGET" > "$OUT/kising.log" 2>&1
stamp "all done"
python -m zipfile -c "$W/kising_m.zip" "$OUT" && echo "== DONE: $W/kising_m.zip"
