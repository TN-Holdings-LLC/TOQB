#!/bin/bash
# Coherent-error stage 1 (prereg/drafts-2026-10-31/coherent_stage1_DRAFT.md; a draft until the owner fixes it):
# where does the signal of kingston's dead run go? The rule's mirror echo, rule only, hz 0, h 0.6, 1000 shots, one job:
#   n = 40: Z at one-way L 1 2 3 4 6 8 10 12 (D 2 ... 24); X and Y at L 6 and 12 (D 12, 24)
#   n = 20 (control): Z at L 6 and 12; X and Y at L 12
# 16 records, 128 circuits. CPU only; nothing is submitted here.
#   FETCH=DAY/fetch OUT=DAY/stage1 bash TOQB/gpu/coherent_stage1.sh
set -u
W=$(pwd); TQ=${TOQB_DIR:-$W/TOQB}; VA=${VENV_ACT:-$W/venv/bin/activate}
FETCH=${FETCH:?set FETCH}; OUT=${OUT:?set OUT}
NOTE=${NOTE:-prereg/drafts-2026-10-31/coherent_stage1_DRAFT.md}; DEVICE=${DEVICE:-ibm_kingston}
H=0.6; SHOTS=1000; MAX=60
# the n = 40, D = 24, Z circuit of 30 October (rerun, test 3E, options test): QPY SHA-256
REF40=42376e3f9ca59862f98caa777c1b95b25a32d50ee31f1b8a1a1f679ac1998d38
[ -d "$TQ" ] && [ -f "$FETCH/target.pkl" ] && [ -f "$FETCH/fetch.json" ] || { echo "STOP: needs TOQB and a fetch"; exit 1; }
[ -e "$OUT" ] && { echo "STOP: $OUT exists"; exit 1; }
[ -f "$TQ/$NOTE" ] || { echo "STOP: no declaration $NOTE"; exit 1; }
FB=$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['backend'])" "$FETCH/fetch.json")
[ "$FB" = "$DEVICE" ] || { echo "STOP: the fetch is of $FB, not $DEVICE"; exit 1; }
[ -f "$VA" ] && . "$VA"
mkdir -p "$OUT"
export PYTHONPATH="$TQ" PYTHONWARNINGS=ignore OMP_NUM_THREADS=4
cd "$TQ" || exit 1
python -m pytest -q tests/test_kising_echo.py tests/test_echo_tomo.py > "$OUT/check_tests.log" 2>&1
tail -1 "$OUT/check_tests.log" | grep -q " passed" && ! tail -1 "$OUT/check_tests.log" | grep -q "failed" || { echo "STOP: tests (see check_tests.log)"; exit 1; }
{ echo "toqb $(git log --oneline -1 | cut -c1-60)"; echo "note $(sha256sum $NOTE)"; echo "tests $(tail -1 "$OUT/check_tests.log")";
  echo "fetch $(python -c "import json,sys; f=json.load(open(sys.argv[1])); print(f['backend'], f['calibration_time'], f['target_sha256'])" "$FETCH/fetch.json")";
  echo "start $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')"; } | tee "$OUT/times.txt"
b() { python -m toqb.echo_tomo build "$FETCH" "$OUT/runs" --n "$1" --L "$2" --basis "$3" --hz 0 --h $H --shots $SHOTS 2>&1 \
        | grep -v Warn | tail -1 | sed "s/^/[n $1 L $2 $3] /" | tee -a "$OUT/build.txt"; }
for L in 1 2 3 4 6 8 10 12; do b 40 $L Z; done
for L in 6 12; do b 40 $L X; b 40 $L Y; done
for L in 6 12; do b 20 $L Z; done
b 20 12 X; b 20 12 Y
N=$(ls "$OUT"/runs/*.json 2>/dev/null | wc -l)
[ "$N" = 16 ] || { echo "STOP: $N records, not 16 (see build.txt)"; exit 1; }
# the same ring and gates as 30 October? (reported; a different hash is not a stop, the ring is what the rule places today)
S40=$(sha256sum "$OUT/runs/kecho_n40_D24_hz0_h0.6-fold_rule.qpy" | cut -d' ' -f1)
{ [ "$S40" = "$REF40" ] && echo "n40 D24 Z: byte-identical to 30 October ($S40)" || echo "n40 D24 Z: DIFFERS from 30 October ($S40)"; } | tee -a "$OUT/build.txt"
python - "$OUT/runs" <<'EOF' | tee -a "$OUT/build.txt"
import json, glob, sys
rings = {}
for f in sorted(glob.glob(sys.argv[1] + "/*.json")):
    r = json.load(open(f)); n = r["task"]["n"]; mq = r["echo"]["measured_qubits"]
    rings.setdefault(n, set()).add(tuple(int(mq[str(j)]) for j in range(n)))
for n, s in sorted(rings.items()):
    print(f"n {n}: {'one ring for all records' if len(s) == 1 else 'STOP: %d rings' % len(s)}: {list(next(iter(s)))}")
    if len(s) != 1:
        sys.exit(1)
EOF
[ "${PIPESTATUS[0]}" = 0 ] || { echo "STOP: rings differ between records"; exit 1; }
( cd "$OUT/runs" && sha256sum *.qpy ) > "$OUT/qpy_sha256.txt"
python -m toqb.s2rc_device assemble --fetch "$FETCH" --runs "$OUT/runs" --out "$OUT/job" --max-seconds "$MAX" | tee "$OUT/assemble.txt"
[ -f "$OUT/job/manifest.json" ] || { echo "STOP: no job (see assemble.txt)"; exit 1; }
echo "end $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')" | tee -a "$OUT/times.txt"
echo "== DONE: $OUT/job"
# after the result:
#   python -m toqb.echo_tomo score $OUT/job $OUT/runs --block 38,49,50,51,52,53,54,55,59 \
#     --other 3,4,5,6,7,17,27,28,29 --segment 3,4,5,6,7,17,27,28,29,38,49,50,51,52,53,54,55,59 --out $OUT/stage1_score.json
