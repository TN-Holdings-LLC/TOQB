#!/bin/bash
# Fix repeat (prereg/drafts-2026-11-01/fix_repeat_note.md): does the two-qubit frame flip at 27, 29 (ring positions 6, 8
# of the rule's standard n = 40 ring on ibm_kingston) still fix the dead run a day later? Off, the global flip and the
# flip at 27, 29 (tag B3, as on 31 October); hz 0, h 0.6, 1000 shots, L 6 and 12. 6 records, 48 circuits.
# CPU only; nothing is submitted here.
#   FETCH=DAY/fetch OUT=DAY/fix bash TOQB/gpu/fix_repeat.sh
set -u
W=$(pwd); TQ=${TOQB_DIR:-$W/TOQB}; VA=${VENV_ACT:-$W/venv/bin/activate}
FETCH=${FETCH:?set FETCH}; OUT=${OUT:?set OUT}; B3=6,8
NOTE=${NOTE:-prereg/drafts-2026-11-01/fix_repeat_note.md}; DEVICE=${DEVICE:-ibm_kingston}
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
  echo "arms B3 $B3 (27, 29), global";
  echo "start $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')"; } | tee "$OUT/times.txt"
b() { python -m toqb.kising_echo build "$FETCH" "$OUT/runs" --arm fold:rule --n 40 --L "$1" --hz 0 --h $H --shots $SHOTS $2 2>&1 \
        | grep -v Warn | tail -1 | sed "s/^/[L $1 ${2:-off}] /" | tee -a "$OUT/build.txt"; }
for L in 6 12; do b $L ""; b $L --frame-flip; b $L "--flip-sites $B3 --flip-tag B3"; done
C=$(ls "$OUT"/runs/*.json 2>/dev/null | wc -l)
[ "$C" = 6 ] || { echo "STOP: $C records, not 6 (see build.txt)"; exit 1; }
S40=$(sha256sum "$OUT/runs/kecho_n40_D24_hz0_h0.6-fold_rule.qpy" | cut -d' ' -f1)
{ [ "$S40" = "$REF40" ] && echo "n40 D24 off: byte-identical to 30 October ($S40)" || echo "n40 D24 off: DIFFERS from 30 October ($S40)"; } | tee -a "$OUT/build.txt"
python - "$OUT/runs" "$B3" <<'PY' | tee -a "$OUT/build.txt"
import glob, json, sys
rings = set()
for f in sorted(glob.glob(sys.argv[1] + "/*.json")):
    r = json.load(open(f)); mq = r["echo"]["measured_qubits"]
    rings.add(tuple(int(mq[str(j)]) for j in range(r["task"]["n"])))
ring = list(next(iter(rings)))
for tag, arg in (("B3", sys.argv[2]),):
    pos = [int(x) for x in arg.split(",")]
    cpl = sorted({(p - 1) % 40 for p in pos} | set(pos))
    print(f"arm {tag}: flipped qubits {[ring[p] for p in pos]}; couplers covered "
          f"{[(ring[c], ring[(c + 1) % 40]) for c in cpl]}")
print(f"{len(rings)} ring(s): {ring}")
ok = [ring[p] for p in (6, 8)] == [27, 29]
print("B3 qubits 27, 29 as declared" if ok else "B3 qubits NOT as declared")
sys.exit(0 if len(rings) == 1 and ok else 1)
PY
[ "${PIPESTATUS[0]}" = 0 ] || { echo "STOP: rings differ or B3 is not the declared qubits"; exit 1; }
( cd "$OUT/runs" && sha256sum *.qpy ) > "$OUT/qpy_sha256.txt"
python -m toqb.s2rc_device assemble --fetch "$FETCH" --runs "$OUT/runs" --out "$OUT/job" --max-seconds "$MAX" | tee "$OUT/assemble.txt"
[ -f "$OUT/job/manifest.json" ] || { echo "STOP: no job (see assemble.txt)"; exit 1; }
echo "end $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')" | tee -a "$OUT/times.txt"
echo "== DONE: $OUT/job"
# after the result:
#   python -m toqb.ff_score $OUT/job $OUT/runs --block 38,49,50,51,52,53,54,55,59 \
#     --segment 3,4,5,6,7,17,27,28,29,38,49,50,51,52,53,54,55,59 --control-n 0 --out $OUT/ff_score.json
