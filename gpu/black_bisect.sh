#!/bin/bash
# Black bisection, one round (prereg/drafts-2026-10-31/black_bisect_note.md): where on kingston's n = 40 ring is the
# error that the global frame flip cancels? Off and two local flips (arms A, B: even ring positions of two halves of
# the current span; virtual Z keeps the ideal circuit) on the rule's standard n = 40 ring, hz 0, h 0.6, 1000 shots,
# L 6 and 12. 6 records, 48 circuits. CPU only; nothing is submitted here.
#   FETCH=DAY/fetch OUT=DAY/bK ARM_A=0,2,...,18 ARM_B=20,...,38 bash TOQB/gpu/black_bisect.sh
set -u
W=$(pwd); TQ=${TOQB_DIR:-$W/TOQB}; VA=${VENV_ACT:-$W/venv/bin/activate}
FETCH=${FETCH:?set FETCH}; OUT=${OUT:?set OUT}; ARM_A=${ARM_A:?set ARM_A}; ARM_B=${ARM_B:?set ARM_B}
NOTE=${NOTE:-prereg/drafts-2026-10-31/black_bisect_note.md}; DEVICE=${DEVICE:-ibm_kingston}
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
  echo "arm A positions $ARM_A"; echo "arm B positions $ARM_B";
  echo "start $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')"; } | tee "$OUT/times.txt"
b() { python -m toqb.kising_echo build "$FETCH" "$OUT/runs" --arm fold:rule --n 40 --L "$1" --hz 0 --h $H --shots $SHOTS $2 2>&1 \
        | grep -v Warn | tail -1 | sed "s/^/[L $1 ${2:-off}] /" | tee -a "$OUT/build.txt"; }
for L in 6 12; do b $L ""; b $L "--flip-sites $ARM_A --flip-tag A"; b $L "--flip-sites $ARM_B --flip-tag B"; done
C=$(ls "$OUT"/runs/*.json 2>/dev/null | wc -l)
[ "$C" = 6 ] || { echo "STOP: $C records, not 6 (see build.txt)"; exit 1; }
S40=$(sha256sum "$OUT/runs/kecho_n40_D24_hz0_h0.6-fold_rule.qpy" | cut -d' ' -f1)
{ [ "$S40" = "$REF40" ] && echo "n40 D24 off: byte-identical to 30 October ($S40)" || echo "n40 D24 off: DIFFERS from 30 October ($S40)"; } | tee -a "$OUT/build.txt"
python - "$OUT/runs" "$ARM_A" "$ARM_B" <<'PY' | tee -a "$OUT/build.txt"
import glob, json, sys
rings = set()
for f in sorted(glob.glob(sys.argv[1] + "/*.json")):
    r = json.load(open(f)); mq = r["echo"]["measured_qubits"]
    rings.add(tuple(int(mq[str(j)]) for j in range(r["task"]["n"])))
ring = list(next(iter(rings)))
for tag, arg in (("A", sys.argv[2]), ("B", sys.argv[3])):
    pos = [int(x) for x in arg.split(",")]
    cpl = sorted({(p - 1) % 40 for p in pos} | set(pos))
    print(f"arm {tag}: flipped qubits {[ring[p] for p in pos]}; couplers covered "
          f"{[(ring[c], ring[(c + 1) % 40]) for c in cpl]}")
print(f"{len(rings)} ring(s): {ring}")
sys.exit(0 if len(rings) == 1 else 1)
PY
[ "${PIPESTATUS[0]}" = 0 ] || { echo "STOP: rings differ"; exit 1; }
( cd "$OUT/runs" && sha256sum *.qpy ) > "$OUT/qpy_sha256.txt"
python -m toqb.s2rc_device assemble --fetch "$FETCH" --runs "$OUT/runs" --out "$OUT/job" --max-seconds "$MAX" | tee "$OUT/assemble.txt"
[ -f "$OUT/job/manifest.json" ] || { echo "STOP: no job (see assemble.txt)"; exit 1; }
echo "end $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')" | tee -a "$OUT/times.txt"
echo "== DONE: $OUT/job"
# after the result:
#   python -m toqb.ff_score $OUT/job $OUT/runs --block 38,49,50,51,52,53,54,55,59 \
#     --segment 3,4,5,6,7,17,27,28,29,38,49,50,51,52,53,54,55,59 --control-n 0 --out $OUT/ff_score.json
