#!/bin/bash
# OS plan M3 (prereg/drafts-2026-11-01/qca_m3_note.md): a forward-only Clifford computation (n layers of H on every
# qubit then the CZ ring; the identity on the n-ring) on the rule's standard rings (job S: n = 20, 40) and on the n = 40
# ring placed around the defect list (job V). 1000 shots. CPU only; nothing is submitted here.
#   FETCH=DAY/fetch OUT=DAY/m3 [LIST=...] bash TOQB/gpu/qca_m3.sh
set -u
W=$(pwd); TQ=${TOQB_DIR:-$W/TOQB}; VA=${VENV_ACT:-$W/venv/bin/activate}
FETCH=${FETCH:?set FETCH}; OUT=${OUT:?set OUT}
LIST=${LIST:-$TQ/results/coverage-days-2026-11-01-day2/list_after.json}
NOTE=${NOTE:-prereg/drafts-2026-11-01/qca_m3_note.md}; DEVICE=${DEVICE:-ibm_kingston}
NOW=${NOW:-$(TZ=Europe/Zurich date '+%Y-%m-%dT%H:%M:%S')}
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
python -m pytest -q tests/test_qca.py tests/test_defect_list.py > "$OUT/check_tests.log" 2>&1
tail -1 "$OUT/check_tests.log" | grep -q " passed" && ! tail -1 "$OUT/check_tests.log" | grep -q "failed" || { echo "STOP: tests (see check_tests.log)"; exit 1; }
{ echo "toqb $(git log --oneline -1 | cut -c1-60)"; echo "note $(sha256sum $NOTE)"; echo "list $(sha256sum $LIST)";
  echo "fetch $(python -c "import json,sys; f=json.load(open(sys.argv[1])); print(f['backend'], f['calibration_time'], f['target_sha256'])" "$FETCH/fetch.json")";
  echo "list date $NOW"; echo "start $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')"; } | tee "$OUT/times.txt"
python -m toqb.defect_list status "$LIST" --now "$NOW" | grep "^$DEVICE " | tee "$OUT/list_status.txt"
python -m toqb.defect_list mask "$FETCH" "$LIST" "$OUT/fetch_masked" --now "$NOW" | tee "$OUT/mask.txt"
[ -f "$OUT/fetch_masked/target.pkl" ] || { echo "STOP: mask failed"; exit 1; }
for n in 20 40; do python -m toqb.qca_test build "$FETCH" "$OUT/runs_S" --arm fold:rule --n $n 2>&1 | grep -v Warn | tail -1 | sed "s/^/[S] /" | tee -a "$OUT/build.txt"; done
python -m toqb.qca_test build "$OUT/fetch_masked" "$OUT/runs_V" --arm fold:rule --n 40 2>&1 | grep -v Warn | tail -1 | sed "s/^/[V] /" | tee -a "$OUT/build.txt"
python - "$OUT" <<'PY' | tee -a "$OUT/build.txt"
import json, sys
from toqb.defect_list import contains_path
out = sys.argv[1]
ring = lambda f: (lambda r: [int(r["echo"]["measured_qubits"][str(j)]) for j in range(r["task"]["n"])])(json.load(open(f)))  # noqa: E731
s, v = ring(out + "/runs_S/kqca_n40_D40-fold_rule.json"), ring(out + "/runs_V/kqca_n40_D40-fold_rule.json")
print("n 40 standard ring", s); print("n 40 avoid ring   ", v)
print("the two rings differ" if s != v else "STOP: the avoid ring equals the standard ring")
print("standard ring holds [28, 29, 38, 49]:", contains_path(s, (28, 29, 38, 49)), "; avoid ring:", contains_path(v, (28, 29, 38, 49)))
sys.exit(0 if s != v else 1)
PY
[ "${PIPESTATUS[0]}" = 0 ] || { echo "STOP: no avoid ring"; exit 1; }
( cd "$OUT" && sha256sum runs_S/*.qpy runs_V/*.qpy ) > "$OUT/qpy_sha256.txt"
python -m toqb.s2rc_device assemble --fetch "$FETCH" --runs "$OUT/runs_S" --out "$OUT/job_S" --max-seconds 20 | tail -2 | tee "$OUT/assemble.txt"
python -m toqb.s2rc_device assemble --fetch "$OUT/fetch_masked" --runs "$OUT/runs_V" --out "$OUT/job_V" --max-seconds 20 | tail -2 | tee -a "$OUT/assemble.txt"
[ -f "$OUT/job_S/manifest.json" ] && [ -f "$OUT/job_V/manifest.json" ] || { echo "STOP: no jobs (see assemble.txt)"; exit 1; }
echo "end $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')" | tee -a "$OUT/times.txt"
echo "== DONE: $OUT/job_S $OUT/job_V"
# after the results:
#   python -m toqb.qca_test score $OUT/job_S $OUT/runs_S --out $OUT/score_S.json
#   python -m toqb.qca_test score $OUT/job_V $OUT/runs_V --out $OUT/score_V.json
