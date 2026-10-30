#!/bin/bash
# Test 3 part P (prereg/drafts-2026-10-30/test3_note.md): the size wall read by the ring's parity (toqb.kising_parity),
# n = 20 and 36 judged, 40 and 72 reported; arms fold:rule, fold:zipcyc, qiskit:2:blind:template (an arm that cannot be
# placed is recorded, not replaced); one job (288 circuits x 1000 shots, time model 91.1 s). CPU is enough. From the
# folder that holds TOQB, with the day's fetch from home:
#   FETCH=<fetch folder> OUT=<new folder> DEVICE=ibm_kingston bash TOQB/gpu/parity_size.sh > parity.txt 2>&1
set -u
W=$(pwd); TQ=${TOQB_DIR:-$W/TOQB}; [ -n "${VENV_ACT:-}" ] && . "$VENV_ACT"
FETCH=${FETCH:?set FETCH}; OUT=${OUT:?set OUT}; SHOTS=${SHOTS:-1000}; MAX=${MAX:-120}; H=${H:-0.6}
NOTE=${NOTE:-prereg/drafts-2026-10-30/test3_note.md}; DEVICE=${DEVICE:-}
VSTAR=${VSTAR:-}  # declared V* per arm for the rehearsal, e.g. fold:rule=171,fold:zipcyc=47.5
[ -d "$TQ" ] && [ -f "$FETCH/target.pkl" ] && [ -f "$FETCH/fetch.json" ] || { echo "STOP: needs TOQB and a fetch"; exit 1; }
[ -e "$OUT" ] && { echo "STOP: $OUT exists"; exit 1; }
[ -f "$TQ/$NOTE" ] || { echo "STOP: no declaration $NOTE"; exit 1; }
if [ -n "$DEVICE" ]; then
  FB=$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['backend'])" "$FETCH/fetch.json")
  [ "$FB" = "$DEVICE" ] || { echo "STOP: the fetch is of $FB, not $DEVICE"; exit 1; }
fi
mkdir -p "$OUT"
export PYTHONPATH="$TQ" PYTHONWARNINGS=ignore OMP_NUM_THREADS=4
cd "$TQ" || exit 1
python -m pytest -q tests/test_kising_parity.py > "$OUT/check_tests.log" 2>&1
tail -1 "$OUT/check_tests.log" | grep -q " passed" && ! tail -1 "$OUT/check_tests.log" | grep -q "failed" || { echo "STOP: tests (see check_tests.log)"; exit 1; }
{ echo "toqb $(git log --oneline -1 | cut -c1-60)"; echo "note $(sha256sum $NOTE)"; echo "tests $(tail -1 "$OUT/check_tests.log")";
  echo "fetch $(python -c "import json,sys; f=json.load(open(sys.argv[1])); print(f['backend'], f['calibration_time'], f['target_sha256'])" "$FETCH/fetch.json")";
  echo "start $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')"; } | tee "$OUT/times.txt"
for n in 20 36 40 72; do
  if [ "$n" = 20 ]; then LS="2 4 8"; else LS="1 2 4"; fi
  for arm in fold:rule fold:zipcyc qiskit:2:blind:template; do
    for L in $LS; do
      python -m toqb.kising_parity build "$FETCH" "$OUT/runs" --arm $arm --n $n --L $L --h $H --shots $SHOTS 2>&1 | grep -v Warn | tail -1 | tee -a "$OUT/build.txt"
    done
  done
done
[ -n "$VSTAR" ] && python -m toqb.kising_parity rehearse "$OUT/runs" --vstar "$VSTAR" | tee "$OUT/rehearse.txt"
python -m toqb.s2rc_device assemble --fetch "$FETCH" --runs "$OUT/runs" --out "$OUT/job" --max-seconds "$MAX" | tee "$OUT/assemble.txt"
[ -f "$OUT/job/manifest.json" ] || { echo "STOP: no job"; exit 1; }
echo "end $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')" | tee -a "$OUT/times.txt"
cd "$W" && python -m zipfile -c "$W/parity_job.zip" "$OUT" && echo "== DONE: $W/parity_job.zip"
# home, after submit and result (VPN OFF):
#   python -m toqb.kising_parity score $OUT/job $OUT/runs --vstar-pred fold:rule=<V>,fold:zipcyc=<V/3.6> --judged-n 20,36
