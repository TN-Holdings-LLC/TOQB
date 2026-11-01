#!/bin/bash
# Score of a scan-then-avoid session (prereg/drafts-2026-11-01/two_devices_note.md): usable sites of the scan's
# standard rings against the avoid job's rings (toqb.defect_list coverage), and the list with the avoid job added.
#   SCAN=DAY/scan AVOID=DAY/avoid DEVICE=ibm_fez bash TOQB/gpu/avoid_score.sh
set -u
W=$(pwd); TQ=${TOQB_DIR:-$W/TOQB}; VA=${VENV_ACT:-$W/venv/bin/activate}
SCAN=$(realpath "${SCAN:?set SCAN}"); AVOID=$(realpath "${AVOID:?set AVOID}"); DEVICE=${DEVICE:?set DEVICE}
[ -f "$VA" ] && . "$VA"
export PYTHONPATH="$TQ" PYTHONWARNINGS=ignore
cd "$TQ" || exit 1
[ -e "$AVOID/coverage.json" ] && { echo "STOP: $AVOID/coverage.json exists"; exit 1; }
PATHS=$(python - "$AVOID/list_status.txt" <<'PY'
import re, sys
print(",".join("-".join(x.strip() for x in m.group(1).split(",")) for m in
               (re.search(r"centre \[([0-9, ]+)\]: LISTED", l) for l in open(sys.argv[1])) if m))
PY
)
B=()
ls "$AVOID"/job_B/raw_counts.json* >/dev/null 2>&1 && B=(--b "$AVOID/job_B" "$AVOID/runs_B")
python -m toqb.defect_list coverage "$SCAN/job_A" "$SCAN/runs_A" "${B[@]}" --paths "$PATHS" --out "$AVOID/coverage.json" | tee "$AVOID/coverage.txt"
if [ ${#B[@]} -gt 0 ]; then
  python -m toqb.defect_list ingest "$AVOID/list_after.json" --base "$SCAN/list_after.json" --obs "$DEVICE:$AVOID/job_B:$AVOID/runs_B:avoid" | tee "$AVOID/ingest.txt"
fi
echo "== DONE: $AVOID/coverage.txt"
