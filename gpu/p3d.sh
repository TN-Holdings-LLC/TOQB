#!/bin/bash
# P3D (prereg/drafts-2026-10-29/p3d_note.md): the check of the Paper 3 diagnosis. Noiseless, numpy only (CPU; no
# GPU, no device, no Qiskit run). 21 runs, longest first, PAR at a time (one thread each). From the TOQB root's parent:
#   OUT=/workspace/p3d PAR=8 nohup bash TOQB/gpu/p3d.sh > p3d.txt 2>&1 &
set -u
W=$(pwd); TQ=${TOQB_DIR:-$W/TOQB}; OUT=${OUT:?set OUT}; PAR=${PAR:-2}
NOTE=prereg/drafts-2026-10-29/p3d_note.md
[ -d "$TQ" ] || { echo "STOP: no TOQB"; exit 1; }
[ -e "$OUT" ] && { echo "STOP: $OUT exists"; exit 1; }
[ -f "$TQ/$NOTE" ] || { echo "STOP: no declaration $NOTE"; exit 1; }
[ -n "${VENV_ACT:-}" ] && . "$VENV_ACT"
mkdir -p "$OUT/runs"
export PYTHONPATH="$TQ" OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONWARNINGS=ignore
cd "$TQ" || exit 1
python -m pytest -q tests/test_p3d.py tests/test_exact_batch.py tests/test_s2re.py > "$OUT/check_tests.log" 2>&1
tail -1 "$OUT/check_tests.log" | grep -q " passed" && ! tail -1 "$OUT/check_tests.log" | grep -q "failed" || { echo "STOP: tests (see check_tests.log)"; exit 1; }
python -m toqb.p3d check > "$OUT/check_A0a.json" || { echo "STOP: A0a (fast simulator / adjoint)"; cat "$OUT/check_A0a.json"; exit 1; }
{ echo "toqb $(git log --oneline -1 | cut -c1-60)"; echo "note $(sha256sum $NOTE)"; echo "tests $(tail -1 "$OUT/check_tests.log")";
  echo "A0a $(cat "$OUT/check_A0a.json")"; echo "python $(python -c 'import sys, numpy, scipy; print(sys.version.split()[0], numpy.__version__, scipy.__version__)')";
  echo "PAR $PAR"; echo "start $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')"; } | tee "$OUT/times.txt"
# A0b (gate): theta = 0 on the device-day task must give home's recorded 0.934
python -m toqb.p3d run --part A --arm Z "$OUT/runs/A_Z.json" | tee -a "$OUT/times.txt"
[ -n "${P3D_SMOKE:-}" ] && echo "SMOKE: procedure rehearsal (tiny model); A0b skipped; nothing here is a result" | tee -a "$OUT/times.txt"
[ -n "${P3D_SMOKE:-}" ] || python - "$OUT/runs/A_Z.json" <<'PY' || { echo "STOP: A0b"; exit 1; }
import json, sys
a = json.load(open(sys.argv[1]))["test"]["acc"]
print("A0b theta = 0 accuracy", a, "recorded 0.934", "MATCH" if round(a, 3) == 0.934 else "NO MATCH")
sys.exit(0 if round(a, 3) == 0.934 else 1)
PY
J="$OUT/jobs.txt"; : > "$J"
for t in 17 18 19; do echo "--part C --arm G --teacher $t --ntrain 330 $OUT/runs/C_G_t${t}_N330.json" >> "$J"; done
for t in 17 18 19; do echo "--part C --arm G --teacher $t --ntrain 64 $OUT/runs/C_G_t${t}_N64.json" >> "$J"; done
echo "--part A --arm G $OUT/runs/A_G.json" >> "$J"
for t in 17 18 19; do echo "--part C --arm E --teacher $t --ntrain 330 $OUT/runs/C_E_t${t}_N330.json" >> "$J"; done
for s in 301 302 303; do echo "--part A --arm C --seed $s $OUT/runs/A_C_s${s}.json" >> "$J"; done
echo "--part A --arm E $OUT/runs/A_E.json" >> "$J"
for t in 17 18 19; do echo "--part C --arm E --teacher $t --ntrain 64 $OUT/runs/C_E_t${t}_N64.json" >> "$J"; done
for t in 17 18 19; do echo "--part C --arm Z --teacher $t --ntrain 64 $OUT/runs/C_Z_t${t}_N64.json" >> "$J"; done
xargs -P "$PAR" -L 1 sh -c 'python -m toqb.p3d run "$@" || echo "RUN FAILED: $*"' _ < "$J" 2>&1 | tee -a "$OUT/progress.txt"
echo "end $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')" | tee -a "$OUT/times.txt"
N=$(ls "$OUT/runs"/*.json | wc -l); echo "runs $N of 21 (A_Z + 20)" | tee -a "$OUT/times.txt"
python -m toqb.p3d score "$OUT/runs" > /dev/null && cp "$OUT/runs/p3d_score.md" "$OUT/"
cd "$W" && python -m zipfile -c "$W/p3d_results.zip" "$OUT" && echo "== DONE: $W/p3d_results.zip"
