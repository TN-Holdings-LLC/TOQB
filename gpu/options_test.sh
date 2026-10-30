#!/bin/bash
# Options test of 2026-10-30 evening (prereg/drafts-2026-10-30/options_test_note.md): the rule's mirror echo at
# n = 20 and 40, D = 24, hz = 0, 1000 shots, built once and assembled into three identical jobs that are submitted
# with different SamplerV2 options (off / dd XY4 / gate twirling). CPU only.
#   FETCH=DAY/fetch OUT=DAY/opt DEVICE=ibm_kingston bash TOQB/gpu/options_test.sh
set -u
W=$(pwd); TQ=${TOQB_DIR:-$W/TOQB}; VA=${VENV_ACT:-$W/venv/bin/activate}
FETCH=${FETCH:?set FETCH}; OUT=${OUT:?set OUT}; DEVICE=${DEVICE:-ibm_kingston}
NOTE=prereg/drafts-2026-10-30/options_test_note.md
[ -d "$TQ" ] && [ -f "$FETCH/target.pkl" ] && [ -f "$FETCH/fetch.json" ] || { echo "STOP: needs TOQB and a fetch"; exit 1; }
[ -e "$OUT" ] && { echo "STOP: $OUT exists"; exit 1; }
[ -f "$TQ/$NOTE" ] || { echo "STOP: no declaration $NOTE"; exit 1; }
FB=$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['backend'])" "$FETCH/fetch.json")
[ "$FB" = "$DEVICE" ] || { echo "STOP: the fetch is of $FB, not $DEVICE"; exit 1; }
[ -f "$VA" ] && . "$VA"
mkdir -p "$OUT"
export PYTHONPATH="$TQ" PYTHONWARNINGS=ignore OMP_NUM_THREADS=4
cd "$TQ" || exit 1
python -m pytest -q tests/test_kising_echo.py tests/test_echo_sites.py tests/test_submit_options.py > "$OUT/check_tests.log" 2>&1
tail -1 "$OUT/check_tests.log" | grep -q " passed" && ! tail -1 "$OUT/check_tests.log" | grep -q "failed" || { echo "STOP: tests (see check_tests.log)"; exit 1; }
{ echo "toqb $(git log --oneline -1 | cut -c1-60)"; echo "note $(sha256sum $NOTE)";
  echo "fetch $(python -c "import json,sys; f=json.load(open(sys.argv[1])); print(f['backend'], f['calibration_time'], f['target_sha256'])" "$FETCH/fetch.json")";
  echo "start $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')"; } | tee "$OUT/times.txt"
for n in 20 40; do
  python -m toqb.kising_echo build "$FETCH" "$OUT/runs" --arm fold:rule --n $n --L 12 --hz 0 --h 0.6 --shots 1000 2>&1 \
    | grep -v Warn | tail -1 | tee -a "$OUT/build.txt"
done
for o in off dd twirl; do
  python -m toqb.s2rc_device assemble --fetch "$FETCH" --runs "$OUT/runs" --out "$OUT/job_$o" --max-seconds 30 | tail -2 | tee -a "$OUT/assemble.txt"
  [ -f "$OUT/job_$o/manifest.json" ] || { echo "STOP: no job_$o"; exit 1; }
done
echo "end $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')" | tee -a "$OUT/times.txt"
echo "== DONE: $OUT/job_off job_dd job_twirl"
