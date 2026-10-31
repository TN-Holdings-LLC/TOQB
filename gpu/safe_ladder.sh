#!/bin/bash
# Safe ladder, one round (prereg/drafts-2026-10-31/safe_ladder_note.md): from the verified ring at n = 40 up to n = 72,
# all placed by the rule on the day's fetch masked by the strict safe list (toqb.safe_loop mask); n = 20 the control.
# The echo at hz 0, one-way L 12 25 50 (D 24 50 100), h 0.6, 500 shots. One job. CPU only; nothing is submitted here.
#   FETCH=DAY/fetch OUT=DAY/roundK LIST=<safe list> bash TOQB/gpu/safe_ladder.sh
set -u
W=$(pwd); TQ=${TOQB_DIR:-$W/TOQB}; VA=${VENV_ACT:-$W/venv/bin/activate}
FETCH=${FETCH:?set FETCH}; OUT=${OUT:?set OUT}; LIST=${LIST:?set LIST}
NOTE=${NOTE:-prereg/drafts-2026-10-31/safe_ladder_note.md}; DEVICE=${DEVICE:-ibm_kingston}
NS="20 40 48 56 64 72"; HZ=0; LS="12 25 50"; H=0.6; ARM=fold:rule; SHOTS=500; MAX=45
FETCH=$(realpath "$FETCH"); OUT=$(realpath -m "$OUT"); LIST=$(realpath "$LIST")
[ -d "$TQ" ] && [ -f "$FETCH/target.pkl" ] && [ -f "$FETCH/fetch.json" ] || { echo "STOP: needs TOQB and a fetch"; exit 1; }
[ -e "$OUT" ] && { echo "STOP: $OUT exists"; exit 1; }
[ -f "$TQ/$NOTE" ] && [ -f "$LIST" ] || { echo "STOP: no declaration or no list"; exit 1; }
FB=$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['backend'])" "$FETCH/fetch.json")
[ "$FB" = "$DEVICE" ] || { echo "STOP: the fetch is of $FB, not $DEVICE"; exit 1; }
[ -f "$VA" ] && . "$VA"
mkdir -p "$OUT"
export PYTHONPATH="$TQ" PYTHONWARNINGS=ignore OMP_NUM_THREADS=4
cd "$TQ" || exit 1
python -m pytest -q tests/test_kising_echo.py tests/test_safe_loop.py tests/test_defect_list.py > "$OUT/check_tests.log" 2>&1
tail -1 "$OUT/check_tests.log" | grep -q " passed" && ! tail -1 "$OUT/check_tests.log" | grep -q "failed" || { echo "STOP: tests (see check_tests.log)"; exit 1; }
{ echo "toqb $(git log --oneline -1 | cut -c1-60)"; echo "note $(sha256sum $NOTE)"; echo "list $(sha256sum $LIST)";
  echo "fetch $(python -c "import json,sys; f=json.load(open(sys.argv[1])); print(f['backend'], f['calibration_time'], f['target_sha256'])" "$FETCH/fetch.json")";
  echo "n $NS; hz $HZ; one-way L $LS; h $H; shots $SHOTS; arm $ARM";
  echo "start $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')"; } | tee "$OUT/times.txt"
cp "$LIST" "$OUT/list_before.json"
python -m toqb.safe_loop mask "$FETCH" "$LIST" "$OUT/fetch_masked" | tee "$OUT/mask.txt"
[ -f "$OUT/fetch_masked/target.pkl" ] || { echo "STOP: mask failed"; exit 1; }
for n in $NS; do
  for L in $LS; do
    python -m toqb.kising_echo build "$OUT/fetch_masked" "$OUT/runs" --arm "$ARM" --n "$n" --L "$L" --hz "$HZ" --h "$H" --shots "$SHOTS" 2>&1 \
      | grep -v Warn | tail -1 | sed "s/^/[n $n L $L] /" | tee -a "$OUT/build.txt"
  done
done
python - "$OUT/runs" <<'PY' | tee -a "$OUT/build.txt"
import glob, json, sys
rings = {}
for f in sorted(glob.glob(sys.argv[1] + "/*.json")):
    r = json.load(open(f)); n = r["task"]["n"]; mq = r["echo"]["measured_qubits"]
    rings.setdefault(n, set()).add(tuple(int(mq[str(j)]) for j in range(n)))
for n, s in sorted(rings.items()):
    print(f"n {n}: {len(s)} ring(s): {list(next(iter(s)))}")
PY
( cd "$OUT/runs" && sha256sum *.qpy ) > "$OUT/qpy_sha256.txt"
python -m toqb.s2rc_device assemble --fetch "$OUT/fetch_masked" --runs "$OUT/runs" --out "$OUT/job" --max-seconds "$MAX" | tee "$OUT/assemble.txt"
[ -f "$OUT/job/manifest.json" ] || { echo "STOP: no job (see assemble.txt)"; exit 1; }
echo "end $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')" | tee -a "$OUT/times.txt"
echo "== DONE: $OUT/job"
# after the result:
#   python -m toqb.kising_echo score $OUT/job $OUT/runs
#   python -m toqb.safe_loop judge $OUT/job $OUT/runs --list $OUT/list_before.json --out $OUT/judge.json --next $OUT/list_after.json
