#!/bin/bash
# Avoid job (second job of a scan-then-avoid session; prereg/drafts-2026-11-01/two_devices_note.md): n = 40 and 72 on
# the rule's rings when the day's fetch is masked by the list made from the session's scan (LISTED paths of DEVICE).
# A size whose masked ring equals the scan's standard ring is dropped and reported. D = 24, hz 0, h 0.6, 1000 shots.
# CPU only; nothing is submitted here.
#   FETCH=DAY/fetch SCAN=DAY/scan OUT=DAY/avoid DEVICE=ibm_fez bash TOQB/gpu/avoid_job.sh
set -u
W=$(pwd); TQ=${TOQB_DIR:-$W/TOQB}; VA=${VENV_ACT:-$W/venv/bin/activate}
FETCH=${FETCH:?set FETCH}; SCAN=${SCAN:?set SCAN}; OUT=${OUT:?set OUT}; DEVICE=${DEVICE:?set DEVICE}
NOTE=${NOTE:-prereg/drafts-2026-11-01/two_devices_note.md}
NOW=${NOW:-$(TZ=Europe/Zurich date '+%Y-%m-%dT%H:%M:%S')}
FETCH=$(realpath "$FETCH"); SCAN=$(realpath "$SCAN"); OUT=$(realpath -m "$OUT"); LIST="$SCAN/list_after.json"
[ -d "$TQ" ] && [ -f "$FETCH/target.pkl" ] && [ -f "$FETCH/fetch.json" ] || { echo "STOP: needs TOQB and a fetch"; exit 1; }
[ -e "$OUT" ] && { echo "STOP: $OUT exists"; exit 1; }
[ -f "$TQ/$NOTE" ] && [ -f "$LIST" ] || { echo "STOP: no declaration, or the scan has not been scored (no list_after.json)"; exit 1; }
FB=$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['backend'])" "$FETCH/fetch.json")
[ "$FB" = "$DEVICE" ] || { echo "STOP: the fetch is of $FB, not $DEVICE"; exit 1; }
[ -f "$VA" ] && . "$VA"
mkdir -p "$OUT"
export PYTHONPATH="$TQ" PYTHONWARNINGS=ignore OMP_NUM_THREADS=4
cd "$TQ" || exit 1
{ echo "toqb $(git log --oneline -1 | cut -c1-60)"; echo "note $(sha256sum $NOTE)"; echo "list $(sha256sum $LIST)";
  echo "fetch $(python -c "import json,sys; f=json.load(open(sys.argv[1])); print(f['backend'], f['calibration_time'], f['target_sha256'])" "$FETCH/fetch.json")";
  echo "device $DEVICE; list date $NOW"; echo "start $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')"; } | tee "$OUT/times.txt"
python -m toqb.defect_list status "$LIST" --now "$NOW" | grep "^$DEVICE " | tee "$OUT/list_status.txt"
grep -q "LISTED" "$OUT/list_status.txt" || { echo "NOTHING LISTED for $DEVICE: no avoid job (reported by the note)" | tee "$OUT/nothing_listed.txt"; exit 0; }
python -m toqb.defect_list mask "$FETCH" "$LIST" "$OUT/fetch_masked" --now "$NOW" | tee "$OUT/mask.txt"
[ -f "$OUT/fetch_masked/target.pkl" ] || { echo "STOP: mask failed"; exit 1; }
for n in 40 72; do
  python -m toqb.kising_echo build "$OUT/fetch_masked" "$OUT/runs_B" --arm fold:rule --n $n --L 12 --hz 0 --h 0.6 --shots 1000 2>&1 \
    | grep -v Warn | tail -1 | sed "s/^/[B] /" | tee -a "$OUT/build.txt"
done
python - "$OUT" "$SCAN" <<'EOF' | tee -a "$OUT/build.txt"
import json, os, sys, shutil
out, scan = sys.argv[1], sys.argv[2]
for n in (40, 72):
    name = f"kecho_n{n}_D24_hz0_h0.6-fold_rule"
    a = json.load(open(os.path.join(scan, "runs_A", name + ".json")))["echo"]["measured_qubits"]
    pb = os.path.join(out, "runs_B", name + ".json")
    if os.path.exists(pb) and json.load(open(pb))["echo"]["measured_qubits"] == a:
        os.makedirs(os.path.join(out, "dropped_B"), exist_ok=True)
        for ext in (".json", ".qpy"):
            shutil.move(os.path.join(out, "runs_B", name + ext), os.path.join(out, "dropped_B", name + ext))
        print(f"[B] n {n}: the masked ring equals the standard ring; dropped")
EOF
if ls "$OUT"/runs_B/*.json >/dev/null 2>&1; then
  ( cd "$OUT/runs_B" && sha256sum *.qpy ) > "$OUT/qpy_sha256.txt"
  python -m toqb.s2rc_device assemble --fetch "$OUT/fetch_masked" --runs "$OUT/runs_B" --out "$OUT/job_B" --max-seconds 30 | tail -2 | tee "$OUT/assemble.txt"
else
  echo "every size dropped: no avoid job" | tee "$OUT/nothing_listed.txt"
fi
echo "end $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')" | tee -a "$OUT/times.txt"
echo "== DONE: $OUT"
# after the result:
#   python -m toqb.defect_list coverage $SCAN/job_A $SCAN/runs_A --b $OUT/job_B $OUT/runs_B --paths <listed> --out $OUT/coverage.json
