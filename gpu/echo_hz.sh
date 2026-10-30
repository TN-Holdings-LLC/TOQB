#!/bin/bash
# Test 2 (prereg/drafts-2026-10-30/echo_hz_note.md), the build step for the device: the mirror circuits of
# toqb.kising_echo for every arm x n x hz x one-way L, assembled into jobs of at most MAX seconds by the time model.
# n is an argument: NS (default "20 36"); for the next stage set NS="40 72" and nothing else changes (each n must place
# on the day's map; a refused placement or a failed two-qubit acceptance is recorded in build.txt, never replaced).
# Map-free arms only (failed elements); no twin, no quality number read. CPU is enough. From /workspace, with the
# day's fetch folder from home:
#   FETCH=/root/echo_fetch OUT=/workspace/echo NS="20 36" DEVICE=ibm_marrakesh nohup bash TOQB/gpu/echo_hz.sh > echo.txt 2>&1 &
set -u
W=$(pwd); TQ=${TOQB_DIR:-$W/TOQB}; VA=${VENV_ACT:-$W/venv/bin/activate}
FETCH=${FETCH:?set FETCH}; OUT=${OUT:?set OUT}
NS=${NS:-"20 36"}; HZS=${HZS:-"0 0.1 0.3"}; LS=${LS:-"12 25 50"}; H=${H:-0.6}
ARMS=${ARMS:-"fold:rule fold:zipcyc qiskit:2:blind:template"}
SHOTS=${SHOTS:-500}; MAX=${MAX:-120}
NOTE=${NOTE:-prereg/drafts-2026-10-30/echo_hz_note.md}
DEVICE=${DEVICE:-}  # optional: the backend the fetch must be of (e.g. ibm_marrakesh); checked against fetch.json
[ -d "$TQ" ] && [ -f "$FETCH/target.pkl" ] && [ -f "$FETCH/fetch.json" ] || { echo "STOP: needs TOQB and a fetch"; exit 1; }
[ -e "$OUT" ] && { echo "STOP: $OUT exists"; exit 1; }
[ -f "$TQ/$NOTE" ] || { echo "STOP: no declaration $NOTE"; exit 1; }
if [ -n "$DEVICE" ]; then
  FB=$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['backend'])" "$FETCH/fetch.json")
  [ "$FB" = "$DEVICE" ] || { echo "STOP: the fetch is of $FB, not $DEVICE"; exit 1; }
fi
[ -f "$VA" ] && . "$VA"
mkdir -p "$OUT"
export PYTHONPATH="$TQ" PYTHONWARNINGS=ignore OMP_NUM_THREADS=4
cd "$TQ" || exit 1
python -m pytest -q tests/test_kising_echo.py tests/test_fold.py tests/test_fold_bands.py > "$OUT/check_tests.log" 2>&1
tail -1 "$OUT/check_tests.log" | grep -q " passed" && ! tail -1 "$OUT/check_tests.log" | grep -q "failed" || { echo "STOP: tests (see check_tests.log)"; exit 1; }
{ echo "toqb $(git log --oneline -1 | cut -c1-60)"; echo "note $(sha256sum $NOTE)"; echo "tests $(tail -1 "$OUT/check_tests.log")";
  echo "fetch $(python -c "import json,sys; f=json.load(open(sys.argv[1])); print(f['backend'], f['calibration_time'], f['target_sha256'])" "$FETCH/fetch.json")";
  echo "n $NS; hz $HZS; one-way L $LS; h $H; shots $SHOTS; arms $ARMS"; echo "device ${DEVICE:-(from the fetch)}";
  echo "start $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')"; } | tee "$OUT/times.txt"
for n in $NS; do
  for arm in $ARMS; do
    for hz in $HZS; do
      for L in $LS; do
        python -m toqb.kising_echo build "$FETCH" "$OUT/runs" --arm "$arm" --n "$n" --L "$L" --hz "$hz" --h "$H" --shots "$SHOTS" 2>&1 \
          | grep -v Warn | tail -1 | sed "s/^/[n $n $arm hz $hz L $L] /" | tee -a "$OUT/build.txt"
      done
    done
  done
done
# a refused placement leaves no record; a failed acceptance leaves an invalid record that assemble still lists but score skips
python -m toqb.kising_echo rehearse "$OUT/runs" | tee "$OUT/rehearse.txt"
python -m toqb.s2rc_device assemble --fetch "$FETCH" --runs "$OUT/runs" --out "$OUT/job" --max-seconds "$MAX" | tee "$OUT/assemble.txt"
[ -f "$OUT/job/manifest.json" ] || { echo "STOP: no job (see assemble.txt; above MAX seconds, split NS or lower SHOTS)"; exit 1; }
echo "end $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')" | tee -a "$OUT/times.txt"
cd "$W" && python -m zipfile -c "$W/echo_jobs.zip" "$OUT" && echo "== DONE: $W/echo_jobs.zip"
# home, after the owner's go: s2rc_device submit / result for the job, then
#   python -m toqb.kising_echo score $OUT/job $OUT/runs
