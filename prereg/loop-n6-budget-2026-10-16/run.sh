#!/bin/bash
# TOQB loop budget run, n = 6, L = 8, seeds 6001-7000, a hard 2-minute QPU budget ($192): Qiskit level 2's template
# against PSF-Zero's (a22 + c61), run 1's SPSA, fast engine. Pre-registration: prereg/2026-10-16-loop-n6-budget.md
# (pushed before this run). Home, WSL; no network. Ten processes. Checks every fixed hash; never overwrites.
set -u
TOQB=${TOQB:-~/toqb_push_2026-10-15}
PSF=${PSF:-~/psf_zero_fresh_test}
DAY=${DAY:?set DAY to the folder that receives the zip}
FIRST=${FIRST:-6001}
LAST=${LAST:-7000}
PAR=${PAR:-10}
OUT=${OUT:-results/loop-n6-budget-2026-10-16}
P=prereg/loop-n6-budget-2026-10-16
cd "$TOQB" || { echo "STOP: no $TOQB"; exit 1; }
echo "0e35edcf983da4887712716152e384e07170894c46da107528f36ac90b5130ea  prereg/2026-10-16-loop-n6-budget.md" | sha256sum -c --quiet || { echo "STOP: pre-registration changed"; exit 1; }
echo "71a7f6996324891feaba549a7d7c1700da4a47a4c43a0ba006469ee473d487a7  $P/SHA256SUMS" | sha256sum -c --quiet \
  || { echo "STOP: plan list changed"; exit 1; }
echo "dd3c443efade3aa37c1edd3b5e9f7d29975e0de8f890b753785fa2fc2b851470  $P/CODE_SHA256SUMS" | sha256sum -c --quiet \
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
  | xargs -P "$PAR" -L 1 sh -c 'python -m toqb.task_loop arm "$P/plan_s$0.json" "$OUT/seed$0" "$1" \
      > "$OUT/logs/seed$0-$(echo $1 | tr : _).log" 2>&1; [ "$1" = "qiskit:2:target:template" ] && [ $(($0 % 100)) -eq 0 ] \
      && echo "seed $0 done $(TZ=Europe/Zurich date +%H:%M:%S)"; true'
python -m toqb.task_loop classical "$P/plan_s$FIRST.json" "$OUT/seed$FIRST" > /dev/null 2>&1
echo "end $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')" | tee -a "$OUT/times.txt"
python -m toqb.score_loop_preg4 "$OUT" --seeds "$FIRST-$LAST" > "$OUT/logs/score.log" 2>&1
sed -n '1,/^## Reported/p' "$OUT/score.md"
python -m zipfile -c "$DAY/loop_n6_budget_results.zip" "$OUT" && echo "== DONE: $DAY/loop_n6_budget_results.zip"
