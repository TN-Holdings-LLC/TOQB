#!/bin/bash
# Readable depth on rings placed around the defect list (prereg/drafts-2026-10-31/clean_depth_note.md): the mirror echo
# of 30 October's rule-only rerun (hz 0 0.1 0.3; one-way L 12 25 50; h 0.6; 500 shots) at n = 20 40 72, all built on the
# day's fetch masked by the list (toqb.defect_list mask). One job. CPU only; nothing is submitted here.
#   FETCH=DAY/fetch OUT=DAY/depth [LIST=...] bash TOQB/gpu/clean_depth.sh
set -u
W=$(pwd); TQ=${TOQB_DIR:-$W/TOQB}; VA=${VENV_ACT:-$W/venv/bin/activate}
FETCH=${FETCH:?set FETCH}; OUT=${OUT:?set OUT}
LIST=${LIST:-$TQ/results/coverage-days-2026-10-31-day1/list_after.json}
NOTE=${NOTE:-prereg/drafts-2026-10-31/clean_depth_note.md}; DEVICE=${DEVICE:-ibm_kingston}
NOW=${NOW:-$(TZ=Europe/Zurich date '+%Y-%m-%dT%H:%M:%S')}
NS="20 40 72"; HZS="0 0.1 0.3"; LS="12 25 50"; H=0.6; ARM=fold:rule; SHOTS=500; MAX=60
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
python -m pytest -q tests/test_kising_echo.py tests/test_defect_list.py > "$OUT/check_tests.log" 2>&1
tail -1 "$OUT/check_tests.log" | grep -q " passed" && ! tail -1 "$OUT/check_tests.log" | grep -q "failed" || { echo "STOP: tests (see check_tests.log)"; exit 1; }
{ echo "toqb $(git log --oneline -1 | cut -c1-60)"; echo "note $(sha256sum $NOTE)"; echo "list $(sha256sum $LIST)";
  echo "fetch $(python -c "import json,sys; f=json.load(open(sys.argv[1])); print(f['backend'], f['calibration_time'], f['target_sha256'])" "$FETCH/fetch.json")";
  echo "n $NS; hz $HZS; one-way L $LS; h $H; shots $SHOTS; arm $ARM; list date $NOW";
  echo "start $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')"; } | tee "$OUT/times.txt"
python -m toqb.defect_list status "$LIST" --now "$NOW" | grep "^$DEVICE " | tee "$OUT/list_status.txt"
python -m toqb.defect_list mask "$FETCH" "$LIST" "$OUT/fetch_masked" --now "$NOW" | tee "$OUT/mask.txt"
[ -f "$OUT/fetch_masked/target.pkl" ] || { echo "STOP: mask failed"; exit 1; }
for n in $NS; do
  for hz in $HZS; do
    for L in $LS; do
      python -m toqb.kising_echo build "$OUT/fetch_masked" "$OUT/runs" --arm "$ARM" --n "$n" --L "$L" --hz "$hz" --h "$H" --shots "$SHOTS" 2>&1 \
        | grep -v Warn | tail -1 | sed "s/^/[n $n hz $hz L $L] /" | tee -a "$OUT/build.txt"
    done
  done
done
N=$(ls "$OUT"/runs/*.json 2>/dev/null | wc -l)
[ "$N" = 27 ] || { echo "STOP: $N records, not 27 (see build.txt)"; exit 1; }
# rings, and whether they hold a listed path (reported; the mask should leave none)
python - "$OUT/runs" "$OUT/list_status.txt" <<'PY' | tee -a "$OUT/build.txt"
import glob, json, re, sys
paths = [tuple(int(x) for x in m.group(1).split(", ")) for m in
         (re.search(r"centre \[([0-9, ]+)\]: LISTED", l) for l in open(sys.argv[2])) if m]
from toqb.defect_list import contains_path
rings = {}
for f in sorted(glob.glob(sys.argv[1] + "/*.json")):
    r = json.load(open(f)); n = r["task"]["n"]; mq = r["echo"]["measured_qubits"]
    rings.setdefault(n, set()).add(tuple(int(mq[str(j)]) for j in range(n)))
for n, s in sorted(rings.items()):
    ring = next(iter(s))
    hit = [p for p in paths if contains_path(ring, p)]
    print(f"n {n}: {len(s)} ring(s); listed paths on it: {hit or 'none'}; ring {list(ring)}")
PY
( cd "$OUT/runs" && sha256sum *.qpy ) > "$OUT/qpy_sha256.txt"
python -m toqb.kising_echo rehearse "$OUT/runs" | tee "$OUT/rehearse.txt"
python -m toqb.s2rc_device assemble --fetch "$OUT/fetch_masked" --runs "$OUT/runs" --out "$OUT/job" --max-seconds "$MAX" | tee "$OUT/assemble.txt"
[ -f "$OUT/job/manifest.json" ] || { echo "STOP: no job (see assemble.txt)"; exit 1; }
echo "end $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')" | tee -a "$OUT/times.txt"
echo "== DONE: $OUT/job"
# after the result:
#   python -m toqb.kising_echo score $OUT/job $OUT/runs        (echo_score.json: L* per n and hz under "walls")
