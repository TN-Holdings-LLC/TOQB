#!/bin/bash
# Flow L (prereg/drafts-2026-10-28/clifford_lam_note.md): Clifford eigenstate lam_C of the bare 20-ring at L = 8, 16, 50,
# 100 and the real-angle bridge at L = 8 (L = 16 from flow J after a check), on the twin of ibm_kingston's 2026-10-24
# calibration. Run from the folder that holds TOQB, psf and venv:
#   TARGET=/workspace/target.pkl OUT=/workspace/clifford_l_2026-10-28 bash TOQB/gpu/clifford_l.sh 2>&1 | tee cl.txt
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
  echo "psf-zero $(git -C "$PSF" log --oneline -1)"; echo "note $(sha256sum prereg/drafts-2026-10-28/clifford_lam_note.md)"; \
  echo "target $(sha256sum "$TARGET" | cut -c1-64)"; } | tee "$OUT/times.txt"
stamp start
DEV=(--device "file:$TARGET")
python -m toqb.fold_lam "$OUT/check.jsonl" --n 20 --L 16 --P 24 --T 256 --models sim --arms fold:rule --max-active 24 \
  --models-seed 0 "${DEV[@]}" > "$OUT/check.log" 2>&1
python - "$OUT/check.jsonl" results/flow-j-2026-10-27/n20.jsonl <<'PY' | tee -a "$OUT/times.txt"
import json, sys
new = [json.loads(l) for l in open(sys.argv[1])]
ref = [r for r in map(json.loads, open(sys.argv[2])) if "mseed" not in r][0]
bad = [k for k in ("lam", "q2", "us") if len(new) != 1 or new[0].get(k) != ref.get(k)]
print("check", "FAIL " + " ".join(bad) if bad else "PASS (n = 20, L = 16, model 0 equal to flow J)")
PY
grep -q "check PASS" "$OUT/times.txt" || { stamp "STOP check failed"; exit 1; }
stamp "real L8 start"
python -m toqb.fold_lam "$OUT/real_L8.jsonl" --n 20 --L 8 --P 24 --T 256 --models sim --arms fold:rule --max-active 24 \
  --models-seed 0 1 2 3 "${DEV[@]}" > "$OUT/real_L8.log" 2>&1
stamp "clifford start"
python -m toqb.clifford_lam "$OUT/clifford.jsonl" --n 20 --L 8 16 50 100 --P 24 --T 256 --seeds 0 1 2 3 \
  --arms fold:rule "${DEV[@]}" > "$OUT/clifford.log" 2>&1
stamp "all done"
python -m zipfile -c "$W/clifford_l.zip" "$OUT" && echo "== DONE: $W/clifford_l.zip"
