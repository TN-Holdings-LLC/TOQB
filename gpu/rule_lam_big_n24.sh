#!/bin/bash
# Flow J, n = 24 with the noiseless reference on the GPU (prereg/drafts-2026-10-27/rule_lam_big_amend2.md). Two
# declared checks first, then gpu/rule_lam_big.sh with NS=24. Run from the folder that holds TOQB, psf and venv:
#   TARGET=/workspace/target.pkl REF=/workspace/rule_lam_big_2026-10-27/n20.jsonl \
#     OUT=/workspace/rule_lam_big_n24_2026-10-27 bash TOQB/gpu/rule_lam_big_n24.sh 2>&1 | tee rb24.txt
set -u
W=$(pwd)
TQ=${TOQB_DIR:-$W/TOQB}
VA=${VENV_ACT:-$W/venv/bin/activate}
OUT=${OUT:?set OUT}
TARGET=${TARGET:?set TARGET}
REF=${REF:?set REF (flow J n = 20 rows)}
CHK=${OUT}_check
[ -e "$OUT" ] || [ -e "$CHK" ] && { echo "STOP: $OUT or $CHK exists"; exit 1; }
. "$VA"
mkdir -p "$CHK"
stamp() { echo "$1 $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')" | tee -a "$CHK/times.txt"; }
stamp "check start (toqb $(git -C "$TQ" log --oneline -1 | cut -c1-7))"
# Check 1: the direct statevector equals Qiskit's, on numpy and on cupy.
( cd "$TQ" && PYTHONPATH="$TQ" TOQB_XP=cupy python -m toqb.noiseless_xp check 3 5 8 12 13 ) > "$CHK/check1.txt" 2>&1
tail -1 "$CHK/check1.txt" | tee -a "$CHK/times.txt"
tail -1 "$CHK/check1.txt" | grep -q PASS || { stamp "STOP check 1 failed"; exit 1; }
# Check 2: flow J's n = 20, model 0, again with the reference on the GPU: lam, delta and corr equal to REF's row.
# (run from $CHK so that its zip is written there, never over /workspace/rule_lam_big_n20.zip)
( cd "$CHK" && TOQB_DIR="$TQ" PSF_DIR=${PSF_DIR:-$W/psf} VENV_ACT="$VA" TOQB_NOISELESS=cupy OUT="$CHK/run" NS=20 \
  NOTE=prereg/drafts-2026-10-27/rule_lam_big_amend2.md TARGET="$TARGET" bash "$TQ/gpu/rule_lam_big.sh" ) > "$CHK/check2.log" 2>&1 &
pid=$!
until [ "$(wc -l < "$CHK/run/n20.jsonl" 2>/dev/null || echo 0)" -ge 1 ]; do sleep 20; kill -0 $pid 2>/dev/null || break; done
pkill -P $pid -f "rule_lam_big[.]sh" 2>/dev/null; kill $pid 2>/dev/null; pkill -f "toqb[.]fold_lam $CHK"; sleep 2
python - "$CHK/run/n20.jsonl" "$REF" <<'PY' | tee -a "$CHK/times.txt"
import json, sys
new = json.loads(open(sys.argv[1]).readline())
ref = [json.loads(l) for l in open(sys.argv[2]) if "mseed" not in json.loads(l)][0]
bad = [k for k in ("lam", "delta", "corr", "q2", "us") if new.get(k) != ref.get(k)]
print("check2", "FAIL " + " ".join(bad) if bad else "PASS (n = 20 model 0 equal with the reference on the GPU)")
PY
grep -q "check2 PASS" "$CHK/times.txt" || { stamp "STOP check 2 failed"; exit 1; }
stamp "checks passed"
TOQB_NOISELESS=cupy NS=24 NOTE=prereg/drafts-2026-10-27/rule_lam_big_amend2.md OUT="$OUT" TARGET="$TARGET" \
  bash "$TQ/gpu/rule_lam_big.sh"
