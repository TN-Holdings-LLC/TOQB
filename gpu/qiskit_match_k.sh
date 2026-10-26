#!/bin/bash
# Flow I, test match 4 (prereg/drafts-2026-10-26/qiskit_match_k_note.md): Qiskit against the count rule and the zipper
# on the twin of ibm_kingston's 2026-10-24 calibration. Run from the folder that holds TOQB, psf and venv:
#   TARGET=/workspace/target.pkl OUT=/workspace/qiskit_match_k_2026-10-26 bash TOQB/gpu/qiskit_match_k.sh 2>&1 | tee qk.txt
# Parts run in order 1-4; a zip of everything so far is written after each part (qiskit_match_k_partN.zip).
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
stamp() { echo "$1 $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')" | tee -a "$OUT/times.txt"; }
{ nvidia-smi --query-gpu=name,memory.total --format=csv,noheader; echo "toqb $(git log --oneline -1)"; \
  echo "psf-zero $(git -C "$PSF" log --oneline -1)"; echo "note $(sha256sum prereg/drafts-2026-10-26/qiskit_match_k_note.md)"; \
  echo "target $(sha256sum "$TARGET" | cut -c1-64)"; } | tee "$OUT/times.txt"
stamp start
COMMON=(--L 16 --P 24 --T 256 --models sim --max-active 24 --models-seed 0 1 2 3 --device "file:$TARGET")
ALL=(fold:rule psfai:template_zip qiskit:2:target:template)

# Check: fold:rule and the zipper at n = 13, model 0, must equal flow G's rows.
python -m toqb.fold_lam "$OUT/check.jsonl" --n 13 --L 16 --P 24 --T 256 --models sim --max-active 24 \
  --models-seed 0 --device "file:$TARGET" --arms fold:rule psfai:template_zip > "$OUT/check.log" 2>&1
python - "$OUT/check.jsonl" results/flow-g-2026-10-26/main.jsonl <<'EOF' | tee -a "$OUT/times.txt"
import json, sys
new = [json.loads(l) for l in open(sys.argv[1])]
old = {(r["n"], r["arm"]): r for r in map(json.loads, open(sys.argv[2])) if "mseed" not in r}
bad = [r["arm"] for r in new if any(r.get(k) != old[(r["n"], r["arm"])].get(k) for k in ("lam", "q2", "us"))]
print("check", "FAIL " + " ".join(bad) if bad or len(new) != 2 else "PASS (equal to flow G)")
EOF
grep -q "check PASS" "$OUT/times.txt" || { stamp "STOP check failed"; exit 1; }

part() {  # part number, then fold_lam arguments
  local k=$1; shift
  stamp "part$k start"
  python -m toqb.fold_lam "$OUT/part$k.jsonl" "$@" "${COMMON[@]}" > "$OUT/part$k.log" 2>&1
  stamp "part$k done"
  python -m zipfile -c "$W/qiskit_match_k_part$k.zip" "$OUT" && echo "== zip: $W/qiskit_match_k_part$k.zip"
}
part 1 --n 13 14 16 18 --arms qiskit:2:target:template
part 2 --n 15 17 --arms qiskit:2:target:template
part 3 --n 20 22 --arms "${ALL[@]}"
part 4 --n 24 --arms "${ALL[@]}"
stamp "all done"
echo "== DONE: $W/qiskit_match_k_part4.zip"
