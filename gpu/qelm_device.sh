#!/bin/bash
# QELM task A on the device (prereg/drafts-2026-10-30/qelm_A_note.md and qelm_A_addendum1.md: ibm_kingston only):
# one job per arm (984 circuits x 250 shots, time model 104.8 s each) from the declared teacher task
# (results/qelm-A-2026-10-30/noiseless.json, SHA-256 32a6d656...b38d, checked here). CPU is enough. From the folder
# that holds TOQB, with the day's fetch:
#   FETCH=<fetch folder> OUT=<new folder> DEVICE=ibm_kingston bash TOQB/gpu/qelm_device.sh > qelm_dev.txt 2>&1
set -u
W=$(pwd); TQ=${TOQB_DIR:-$W/TOQB}; [ -n "${VENV_ACT:-}" ] && . "$VENV_ACT"
FETCH=${FETCH:?set FETCH}; OUT=${OUT:?set OUT}; DEVICE=${DEVICE:-ibm_kingston}; MAX=${MAX:-120}
TASK=$TQ/results/qelm-A-2026-10-30; TASK_SHA=32a6d65651abe1ea7ca58b592280d88a2a9af04ed4ee40a13acb545adf7bb38d
[ -d "$TQ" ] && [ -f "$FETCH/target.pkl" ] || { echo "STOP: needs TOQB and a fetch"; exit 1; }
[ -e "$OUT" ] && { echo "STOP: $OUT exists"; exit 1; }
[ "$(sha256sum "$TASK/noiseless.json" | cut -c1-64)" = "$TASK_SHA" ] || { echo "STOP: the teacher task differs from the declared one"; exit 1; }
FB=$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['backend'])" "$FETCH/fetch.json")
[ "$FB" = "$DEVICE" ] || { echo "STOP: the fetch is of $FB, not $DEVICE"; exit 1; }
mkdir -p "$OUT"; export PYTHONPATH="$TQ" PYTHONWARNINGS=ignore PYTHONUNBUFFERED=1
cd "$TQ" || exit 1
{ echo "toqb $(git log --oneline -1 | cut -c1-60)"; echo "note $(sha256sum prereg/drafts-2026-10-30/qelm_A_note.md)";
  echo "addendum $(sha256sum prereg/drafts-2026-10-30/qelm_A_addendum1.md)"; echo "task $TASK_SHA";
  echo "fetch $(python -c "import json,sys; f=json.load(open(sys.argv[1])); print(f['backend'], f['calibration_time'], f['target_sha256'])" "$FETCH/fetch.json")";
  echo "start $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')"; } | tee "$OUT/times.txt"
for arm in fold:rule fold:zipcyc qiskit:2:blind:template; do
  A=${arm//:/_}
  python -m toqb.qelm_device build "$FETCH" "$TASK" "$OUT/runs_$A" --arm $arm 2>&1 | grep -v Warn | tail -1 | tee -a "$OUT/build.txt" \
    || { echo "NOTE: $arm failed rule G: recorded, not replaced" | tee -a "$OUT/build.txt"; continue; }
  python -m toqb.s2rc_device assemble --fetch "$FETCH" --runs "$OUT/runs_$A" --out "$OUT/job_$A" --max-seconds "$MAX" | tee -a "$OUT/assemble.txt"
done
echo "end $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')" | tee -a "$OUT/times.txt"
cd "$W" && python -m zipfile -c "$W/qelm_jobs.zip" "$OUT" && echo "== DONE: $W/qelm_jobs.zip"
# home, after submit and result of each job (VPN OFF):
#   python -m toqb.qelm_device score TOQB/results/qelm-A-2026-10-30 <score dir> --job fold:rule=$OUT/job_fold_rule:$OUT/runs_fold_rule \
#     --job fold:zipcyc=... --job qiskit:2:blind:template=... --predict TOQB/results/qelm-A-2026-10-30/predict_kingston.json
