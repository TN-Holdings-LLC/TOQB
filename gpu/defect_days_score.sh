#!/bin/bash
# Coverage days, after the results (prereg/drafts-2026-10-31/coverage_days_note.md): usable sites of job A (standard
# rings) and job B (rings placed around the list), whether the listed paths are dead on job A's rings, and the list
# for the next day (this day's jobs added to the morning's list). CPU only, no network.
#   OUT=DAY/cover [DEVICE=ibm_kingston] [LABEL=day1] bash TOQB/gpu/defect_days_score.sh
set -u
W=$(pwd); TQ=${TOQB_DIR:-$W/TOQB}; VA=${VENV_ACT:-$W/venv/bin/activate}
OUT=$(realpath "${OUT:?set OUT}"); DEVICE=${DEVICE:-ibm_kingston}; LABEL=${LABEL:-$(basename "$(dirname "$OUT")")}
[ -f "$OUT/job_A/manifest.json" ] && [ -f "$OUT/list_before.json" ] || { echo "STOP: $OUT is not a coverage-day folder"; exit 1; }
ls "$OUT"/job_A/raw_counts.json* >/dev/null 2>&1 || { echo "STOP: no results for job A (run s2rc_device result first)"; exit 1; }
[ -e "$OUT/coverage.json" ] && { echo "STOP: $OUT/coverage.json exists"; exit 1; }
[ -f "$VA" ] && . "$VA"
export PYTHONPATH="$TQ" PYTHONWARNINGS=ignore
cd "$TQ" || exit 1
PATHS=$(python - "$OUT/list_status.txt" <<'EOF'
import re, sys
out = []
for line in open(sys.argv[1]):
    m = re.search(r"centre \[([0-9, ]+)\]: LISTED", line)
    if m:
        out.append("-".join(x.strip() for x in m.group(1).split(",")))
print(",".join(out))
EOF
)
B=()
if ls "$OUT"/job_B/raw_counts.json* >/dev/null 2>&1; then B=(--b "$OUT/job_B" "$OUT/runs_B"); fi
python -m toqb.defect_list coverage "$OUT/job_A" "$OUT/runs_A" "${B[@]}" --paths "$PATHS" --out "$OUT/coverage.json" \
  | tee "$OUT/coverage.txt"
OBS=("$DEVICE:$OUT/job_A:$OUT/runs_A:${LABEL}A")
[ ${#B[@]} -gt 0 ] && OBS+=("$DEVICE:$OUT/job_B:$OUT/runs_B:${LABEL}B")
python -m toqb.defect_list ingest "$OUT/list_after.json" --base "$OUT/list_before.json" --obs "${OBS[@]}" | tee "$OUT/ingest.txt"
python -m toqb.defect_list status "$OUT/list_after.json" --now "$(TZ=Europe/Zurich date '+%Y-%m-%dT%H:%M:%S')" \
  | grep "^$DEVICE " | tee "$OUT/list_after_status.txt"
echo "== DONE: $OUT/coverage.txt; next day: LIST=$OUT/list_after.json"
