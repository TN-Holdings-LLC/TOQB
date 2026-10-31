#!/bin/bash
# Black stage 2 (prereg/drafts-2026-10-31/black_stage2_note.md): the frame flip (toqb.kising_echo --frame-flip: X on the
# even ring qubits around the CZ ring of every even layer; the ideal circuit unchanged) against kingston's dead run.
# The rule's standard rings; hz 0, h 0.6, 1000 shots; n = 40 off / flip at L 6 and 12; n = 20 off / flip at L 12.
# 6 records, 48 circuits. CPU only; nothing is submitted here.
#   FETCH=DAY/fetch OUT=DAY/s2 bash TOQB/gpu/black_stage2.sh
set -u
W=$(pwd); TQ=${TOQB_DIR:-$W/TOQB}; VA=${VENV_ACT:-$W/venv/bin/activate}
FETCH=${FETCH:?set FETCH}; OUT=${OUT:?set OUT}
NOTE=${NOTE:-prereg/drafts-2026-10-31/black_stage2_note.md}; DEVICE=${DEVICE:-ibm_kingston}
H=0.6; SHOTS=1000; MAX=30
REF40=42376e3f9ca59862f98caa777c1b95b25a32d50ee31f1b8a1a1f679ac1998d38
FETCH=$(realpath "$FETCH"); OUT=$(realpath -m "$OUT")
[ -d "$TQ" ] && [ -f "$FETCH/target.pkl" ] && [ -f "$FETCH/fetch.json" ] || { echo "STOP: needs TOQB and a fetch"; exit 1; }
[ -e "$OUT" ] && { echo "STOP: $OUT exists"; exit 1; }
[ -f "$TQ/$NOTE" ] || { echo "STOP: no declaration $NOTE"; exit 1; }
FB=$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['backend'])" "$FETCH/fetch.json")
[ "$FB" = "$DEVICE" ] || { echo "STOP: the fetch is of $FB, not $DEVICE"; exit 1; }
[ -f "$VA" ] && . "$VA"
mkdir -p "$OUT"
export PYTHONPATH="$TQ" PYTHONWARNINGS=ignore OMP_NUM_THREADS=4
cd "$TQ" || exit 1
python -m pytest -q tests/test_kising_echo.py > "$OUT/check_tests.log" 2>&1
tail -1 "$OUT/check_tests.log" | grep -q " passed" && ! tail -1 "$OUT/check_tests.log" | grep -q "failed" || { echo "STOP: tests (see check_tests.log)"; exit 1; }
{ echo "toqb $(git log --oneline -1 | cut -c1-60)"; echo "note $(sha256sum $NOTE)"; echo "tests $(tail -1 "$OUT/check_tests.log")";
  echo "fetch $(python -c "import json,sys; f=json.load(open(sys.argv[1])); print(f['backend'], f['calibration_time'], f['target_sha256'])" "$FETCH/fetch.json")";
  echo "start $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')"; } | tee "$OUT/times.txt"
b() { python -m toqb.kising_echo build "$FETCH" "$OUT/runs" --arm fold:rule --n "$1" --L "$2" --hz 0 --h $H --shots $SHOTS $3 2>&1 \
        | grep -v Warn | tail -1 | sed "s/^/[n $1 L $2 ${3:-off}] /" | tee -a "$OUT/build.txt"; }
for L in 6 12; do b 40 $L ""; b 40 $L --frame-flip; done
b 20 12 ""; b 20 12 --frame-flip
C=$(ls "$OUT"/runs/*.json 2>/dev/null | wc -l)
[ "$C" = 6 ] || { echo "STOP: $C records, not 6 (see build.txt)"; exit 1; }
S40=$(sha256sum "$OUT/runs/kecho_n40_D24_hz0_h0.6-fold_rule.qpy" | cut -d' ' -f1)
{ [ "$S40" = "$REF40" ] && echo "n40 D24 off: byte-identical to 30 October ($S40)" || echo "n40 D24 off: DIFFERS from 30 October ($S40)"; } | tee -a "$OUT/build.txt"
python - "$OUT/runs" <<'PY' | tee -a "$OUT/build.txt"
import glob, json, sys
rings = {}
for f in sorted(glob.glob(sys.argv[1] + "/*.json")):
    r = json.load(open(f)); mq = r["echo"]["measured_qubits"]; n = r["task"]["n"]
    rings.setdefault(n, set()).add(tuple(int(mq[str(j)]) for j in range(n)))
for n, s in sorted(rings.items()):
    print(f"n {n}: {len(s)} ring(s) over off and flip: {list(next(iter(s)))}")
sys.exit(0 if all(len(s) == 1 for s in rings.values()) else 1)
PY
[ "${PIPESTATUS[0]}" = 0 ] || { echo "STOP: off and flip are on different rings"; exit 1; }
( cd "$OUT/runs" && sha256sum *.qpy ) > "$OUT/qpy_sha256.txt"
python -m toqb.s2rc_device assemble --fetch "$FETCH" --runs "$OUT/runs" --out "$OUT/job" --max-seconds "$MAX" | tee "$OUT/assemble.txt"
[ -f "$OUT/job/manifest.json" ] || { echo "STOP: no job (see assemble.txt)"; exit 1; }
echo "end $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')" | tee -a "$OUT/times.txt"
echo "== DONE: $OUT/job"
# after the result:
#   python -m toqb.ff_score $OUT/job $OUT/runs --block 38,49,50,51,52,53,54,55,59 \
#     --segment 3,4,5,6,7,17,27,28,29,38,49,50,51,52,53,54,55,59 --out $OUT/ff_score.json
