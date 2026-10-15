#!/bin/bash
# TOQB loop long run, n = 6, L = 8, seeds 3001-3005 x 100,000 iterations: Qiskit level 2's template against
# PSF-Zero's (a22 + c61), the pilot's SPSA, fast engine. Pre-registration: prereg/2026-10-15-loop-n6-long.md (pushed
# before this run). Home, WSL; no network. Ten processes (5 seeds x 2 arms). Checks every fixed hash; never overwrites.
# While it runs:  python -m toqb.score_loop_preg3 results/loop-n6-long-2026-10-15 --partial
set -u
TOQB=${TOQB:-~/toqb_push_2026-10-15}
PSF=${PSF:-~/psf_zero_fresh_test}
DAY=${DAY:?set DAY to the folder that receives the zip}
FIRST=${FIRST:-3001}
LAST=${LAST:-3005}
OUT=${OUT:-results/loop-n6-long-2026-10-15}
P=prereg/loop-n6-long-2026-10-15
cd "$TOQB" || { echo "STOP: no $TOQB"; exit 1; }
echo "f1266e2c22dfa64545b5b39c3a5d7c939f99f4270197f15781c7ca0b4cec12d0  prereg/2026-10-15-loop-n6-long.md" | sha256sum -c --quiet || { echo "STOP: pre-registration changed"; exit 1; }
echo "cae9f0e3b0667dd6183e3a72dfe1e3aca5cca104df8f1ec4d1cf66b951403e50  $P/SHA256SUMS" | sha256sum -c --quiet \
  || { echo "STOP: plan list changed"; exit 1; }
echo "6fad9ba8ddf8ea9eeeba97eca076efaad6b9ee34d4be301c1d4dd1b7994b1a81  $P/CODE_SHA256SUMS" | sha256sum -c --quiet \
  || { echo "STOP: code list changed"; exit 1; }
( cd "$P" && sha256sum -c --quiet SHA256SUMS ) || { echo "STOP: a plan changed"; exit 1; }
sha256sum -c --quiet "$P/CODE_SHA256SUMS" || { echo "STOP: TOQB code differs from the pre-registered"; exit 1; }
( cd "$PSF" && printf '%s\n' \
  "254cfabc5924118a5c54e159fa2284202d21b87894202f447333de07f06b3728  patches/psf_compile_c61_2026-10-15/psf_compile.py" \
  "625f9431344cd0fad6715ea44dc347044b0c64507c008f69202145d03b14a8ce  patches/psf_ai_compile_a22_2026-10-15/psf_ai_compile.py" \
  | sha256sum -c --quiet ) || { echo "STOP: PSF-Zero files differ from the pre-registered ones"; exit 1; }
python -c "import qiskit, qiskit_aer; assert (qiskit.__version__, qiskit_aer.__version__) == ('2.5.2', '0.17.2')" \
  || { echo "STOP: needs Qiskit 2.5.2 and Aer 0.17.2"; exit 1; }
[ -e "$OUT" ] && { echo "STOP: $OUT exists; a run never overwrites another"; exit 1; }
mkdir -p "$OUT/logs"
for s in $(seq "$FIRST" "$LAST"); do mkdir -p "$OUT/seed$s" && cp "$P/plan_s$s.json" "$OUT/seed$s/plan.json"; done
{ echo "toqb $(git log --oneline -1)"; echo "psf-zero $(git -C "$PSF" log --oneline -1)"; \
  echo "start $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')"; } | tee "$OUT/times.txt"
export PSF_ZERO_REPO="$PSF" PSF_COMPILE_FILE="$PSF/patches/psf_compile_c61_2026-10-15/psf_compile.py" \
  PSF_AI_FILE="$PSF/patches/psf_ai_compile_a22_2026-10-15/psf_ai_compile.py" PYTHONWARNINGS=ignore OUT P
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 RAYON_NUM_THREADS=1 QISKIT_NUM_PROCS=1 \
  NUMEXPR_NUM_THREADS=1 QISKIT_PARALLEL=FALSE
for s in $(seq "$FIRST" "$LAST"); do for a in psfai:template qiskit:2:target:template; do echo "$s $a"; done; done \
  | xargs -P 10 -L 1 sh -c 'python -m toqb.task_loop arm "$P/plan_s$0.json" "$OUT/seed$0" "$1" \
      > "$OUT/logs/seed$0-$(echo $1 | tr : _).log" 2>&1; echo "seed $0 $1 done $(TZ=Europe/Zurich date +%H:%M:%S)"'
for s in $(seq "$FIRST" "$LAST"); do python -m toqb.task_loop classical "$P/plan_s$s.json" "$OUT/seed$s" > /dev/null 2>&1; done
echo "end $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')" | tee -a "$OUT/times.txt"
python -m toqb.score_loop_preg3 "$OUT" --seeds "$FIRST-$LAST" > "$OUT/logs/score.log" 2>&1
sed -n '1,/^## Reported/p' "$OUT/score.md"; sed -n '/^## Trajectory/,$p' "$OUT/score.md"
python -m zipfile -c "$DAY/loop_n6_long_results.zip" "$OUT" && echo "== DONE: $DAY/loop_n6_long_results.zip"
