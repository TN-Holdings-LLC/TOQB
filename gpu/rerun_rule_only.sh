#!/bin/bash
# Rule-only rerun of 2026-10-30 evening (prereg/drafts-2026-10-30/rerun_rule_only_note.md): the mirror echo of test 2 and
# test 3E with the rule as the only arm (n 20 36 40 72, hz 0 0.1 0.3, one-way L 12 25 50, 500 shots). One job. CPU only.
#   FETCH=DAY/fetch OUT=DAY/rerun DEVICE=ibm_kingston bash TOQB/gpu/rerun_rule_only.sh
set -u
W=$(pwd); TQ=${TOQB_DIR:-$W/TOQB}; VA=${VENV_ACT:-$W/venv/bin/activate}
FETCH=${FETCH:?set FETCH}; OUT=${OUT:?set OUT}
NS="20 36 40 72"; HZS="0 0.1 0.3"; LS="12 25 50"; H=0.6; ARM=fold:rule; SHOTS=500; MAX=120
NOTE=${NOTE:-prereg/drafts-2026-10-30/rerun_rule_only_note.md}
DEVICE=${DEVICE:-ibm_kingston}
[ -d "$TQ" ] && [ -f "$FETCH/target.pkl" ] && [ -f "$FETCH/fetch.json" ] || { echo "STOP: needs TOQB and a fetch"; exit 1; }
[ -e "$OUT" ] && { echo "STOP: $OUT exists"; exit 1; }
[ -f "$TQ/$NOTE" ] || { echo "STOP: no declaration $NOTE"; exit 1; }
FB=$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['backend'])" "$FETCH/fetch.json")
[ "$FB" = "$DEVICE" ] || { echo "STOP: the fetch is of $FB, not $DEVICE"; exit 1; }
[ -f "$VA" ] && . "$VA"
mkdir -p "$OUT"
export PYTHONPATH="$TQ" PYTHONWARNINGS=ignore OMP_NUM_THREADS=4
cd "$TQ" || exit 1
python -m pytest -q tests/test_kising_echo.py tests/test_fold.py tests/test_fold_bands.py > "$OUT/check_tests.log" 2>&1
tail -1 "$OUT/check_tests.log" | grep -q " passed" && ! tail -1 "$OUT/check_tests.log" | grep -q "failed" || { echo "STOP: tests (see check_tests.log)"; exit 1; }
{ echo "toqb $(git log --oneline -1 | cut -c1-60)"; echo "note $(sha256sum $NOTE)"; echo "tests $(tail -1 "$OUT/check_tests.log")";
  echo "fetch $(python -c "import json,sys; f=json.load(open(sys.argv[1])); print(f['backend'], f['calibration_time'], f['target_sha256'])" "$FETCH/fetch.json")";
  echo "n $NS; hz $HZS; one-way L $LS; h $H; shots $SHOTS; arm $ARM";
  echo "start $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')"; } | tee "$OUT/times.txt"
for n in $NS; do
  for hz in $HZS; do
    for L in $LS; do
      python -m toqb.kising_echo build "$FETCH" "$OUT/runs" --arm "$ARM" --n "$n" --L "$L" --hz "$hz" --h "$H" --shots "$SHOTS" 2>&1 \
        | grep -v Warn | tail -1 | sed "s/^/[n $n hz $hz L $L] /" | tee -a "$OUT/build.txt"
    done
  done
done
python -m toqb.kising_echo rehearse "$OUT/runs" | tee "$OUT/rehearse.txt"
python -m toqb.s2rc_device assemble --fetch "$FETCH" --runs "$OUT/runs" --out "$OUT/job" --max-seconds "$MAX" | tee "$OUT/assemble.txt"
[ -f "$OUT/job/manifest.json" ] || { echo "STOP: no job (see assemble.txt)"; exit 1; }
echo "end $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')" | tee -a "$OUT/times.txt"
echo "== DONE: $OUT/job"
# after the result:
#   python -m toqb.kising_echo score $OUT/job $OUT/runs
