#!/bin/bash
# Gray zone, stage 1 (prereg/drafts-2026-10-31/gray_stage1_note.md): where does the signal of a weak (not dead) stretch
# go? The n = 72 ring the rule places around the defect list (the ring of 31 October's coverage job B and clean depth,
# whose stretch 35-19-15-14 read 0.10-0.18), read in Z at one-way L 1 2 3 4 6 8 10 12 and in X and Y at L 6 and 12;
# hz 0, h 0.6, 1000 shots; 12 records, 96 circuits. CPU only; nothing is submitted here.
#   FETCH=DAY/fetch OUT=DAY/gray [LIST=...] bash TOQB/gpu/gray_stage1.sh
set -u
W=$(pwd); TQ=${TOQB_DIR:-$W/TOQB}; VA=${VENV_ACT:-$W/venv/bin/activate}
FETCH=${FETCH:?set FETCH}; OUT=${OUT:?set OUT}
LIST=${LIST:-$TQ/results/coverage-days-2026-10-31-day1/list_after.json}
NOTE=${NOTE:-prereg/drafts-2026-10-31/gray_stage1_note.md}; DEVICE=${DEVICE:-ibm_kingston}
NOW=${NOW:-$(TZ=Europe/Zurich date '+%Y-%m-%dT%H:%M:%S')}
H=0.6; SHOTS=1000; MAX=45; N=72; BLOCK="35 19 15 14"
# the n = 72, D = 24, Z circuit of 31 October's coverage job B and clean depth (QPY SHA-256)
REF72=df8eda3c5118edf652c7f117dd0d494591166391ac16740bad4ee8e80cf4013c
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
python -m pytest -q tests/test_kising_echo.py tests/test_echo_tomo.py tests/test_defect_list.py > "$OUT/check_tests.log" 2>&1
tail -1 "$OUT/check_tests.log" | grep -q " passed" && ! tail -1 "$OUT/check_tests.log" | grep -q "failed" || { echo "STOP: tests (see check_tests.log)"; exit 1; }
{ echo "toqb $(git log --oneline -1 | cut -c1-60)"; echo "note $(sha256sum $NOTE)"; echo "list $(sha256sum $LIST)";
  echo "fetch $(python -c "import json,sys; f=json.load(open(sys.argv[1])); print(f['backend'], f['calibration_time'], f['target_sha256'])" "$FETCH/fetch.json")";
  echo "n $N; list date $NOW"; echo "start $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')"; } | tee "$OUT/times.txt"
python -m toqb.defect_list mask "$FETCH" "$LIST" "$OUT/fetch_masked" --now "$NOW" | tee "$OUT/mask.txt"
[ -f "$OUT/fetch_masked/target.pkl" ] || { echo "STOP: mask failed"; exit 1; }
b() { python -m toqb.echo_tomo build "$OUT/fetch_masked" "$OUT/runs" --n $N --L "$1" --basis "$2" --hz 0 --h $H --shots $SHOTS 2>&1 \
        | grep -v Warn | tail -1 | sed "s/^/[L $1 $2] /" | tee -a "$OUT/build.txt"; }
for L in 1 2 3 4 6 8 10 12; do b $L Z; done
for L in 6 12; do b $L X; b $L Y; done
C=$(ls "$OUT"/runs/*.json 2>/dev/null | wc -l)
[ "$C" = 12 ] || { echo "STOP: $C records, not 12 (see build.txt)"; exit 1; }
S72=$(sha256sum "$OUT/runs/kecho_n72_D24_hz0_h0.6-fold_rule.qpy" | cut -d' ' -f1)
{ [ "$S72" = "$REF72" ] && echo "n72 D24 Z: byte-identical to 31 October's coverage job B and clean depth ($S72)" \
  || echo "n72 D24 Z: DIFFERS from 31 October ($S72)"; } | tee -a "$OUT/build.txt"
python - "$OUT/runs" $BLOCK <<'PY' | tee -a "$OUT/build.txt"
import glob, json, sys
rings = set()
for f in sorted(glob.glob(sys.argv[1] + "/*.json")):
    r = json.load(open(f)); mq = r["echo"]["measured_qubits"]
    rings.add(tuple(int(mq[str(j)]) for j in range(r["task"]["n"])))
ring = next(iter(rings)); block = [int(x) for x in sys.argv[2:]]
print(f"{len(rings)} ring(s); block {block} on the ring: {all(q in ring for q in block)}; ring {list(ring)}")
sys.exit(0 if len(rings) == 1 and all(q in ring for q in block) else 1)
PY
[ "${PIPESTATUS[0]}" = 0 ] || { echo "STOP: rings differ or the block is not on the ring"; exit 1; }
( cd "$OUT/runs" && sha256sum *.qpy ) > "$OUT/qpy_sha256.txt"
python -m toqb.s2rc_device assemble --fetch "$OUT/fetch_masked" --runs "$OUT/runs" --out "$OUT/job" --max-seconds "$MAX" | tee "$OUT/assemble.txt"
[ -f "$OUT/job/manifest.json" ] || { echo "STOP: no job (see assemble.txt)"; exit 1; }
echo "end $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')" | tee -a "$OUT/times.txt"
echo "== DONE: $OUT/job"
# after the result:
#   python -m toqb.echo_tomo score $OUT/job $OUT/runs --n 72 --block 35,19,15,14 --other 33,34,13,12,11 \
#     --segment 33,34,35,19,15,14,13,12,11 --path 35,19,15,14 --weak-rel 0.5 --out $OUT/gray_score.json
