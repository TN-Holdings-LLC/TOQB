#!/bin/bash
# TOQB S2R stage 0 (prereg/2026-10-17-s2r-stage0.md): seeds 9001-9020; per seed S2R and device-only SPSA, each with
# Qiskit level 2's template and PSF-Zero's (a22 + c61). Home, WSL; no network. Checks every fixed hash; writes its
# results outside the repository (OUT) and never overwrites them.
set -u
TOQB=${TOQB:-~/toqb_push_2026-10-15}
PSF=${PSF:-~/psf_zero_fresh_test}
DAY=${DAY:?set DAY to the folder that receives the zip}
PAR=${PAR:-10}
OUT=${OUT:-$HOME/toqb_runs_kept/s2r-stage0-2026-10-17}
P=prereg/s2r-stage0-2026-10-17
cd "$TOQB" || { echo "STOP: no $TOQB"; exit 1; }
echo "9fa868b7f1d4e2738d82720e06090fb384177bafe5c2a33d2356abde058c4857  prereg/2026-10-17-s2r-stage0.md" | sha256sum -c --quiet || { echo "STOP: pre-registration changed"; exit 1; }
echo "ee1cf452a67124f7bbbccb8baacc056899fb61c24b5de54dc40e27717c38ca1e  $P/SHA256SUMS" | sha256sum -c --quiet || { echo "STOP: plan list changed"; exit 1; }
echo "510baa0d78565503cb68b4cd6a46ffac225476febb3bc96dfb83d91c5a68ebac  $P/CODE_SHA256SUMS" | sha256sum -c --quiet || { echo "STOP: code list changed"; exit 1; }
( cd "$P" && sha256sum -c --quiet SHA256SUMS ) || { echo "STOP: a plan changed"; exit 1; }
sha256sum -c --quiet "$P/510baa0d78565503cb68b4cd6a46ffac225476febb3bc96dfb83d91c5a68ebacSUMS" || { echo "STOP: TOQB code differs from the pre-registered"; exit 1; }
( cd "$PSF" && printf '%s\n' \
  "254cfabc5924118a5c54e159fa2284202d21b87894202f447333de07f06b3728  patches/psf_compile_c61_2026-10-15/psf_compile.py" \
  "625f9431344cd0fad6715ea44dc347044b0c64507c008f69202145d03b14a8ce  patches/psf_ai_compile_a22_2026-10-15/psf_ai_compile.py" \
  | sha256sum -c --quiet ) || { echo "STOP: PSF-Zero files differ from the pre-registered ones"; exit 1; }
python -c "import qiskit, qiskit_aer; assert (qiskit.__version__, qiskit_aer.__version__) == ('2.5.2', '0.17.2')" \
  || { echo "STOP: needs Qiskit 2.5.2 and Aer 0.17.2"; exit 1; }
[ -e "$OUT" ] && { echo "STOP: $OUT exists; a run never overwrites another"; exit 1; }
mkdir -p "$OUT/logs"
for s in $(seq 9001 9020); do mkdir -p "$OUT/seed$s" && cp "$P/plan_s$s.json" "$OUT/seed$s/plan.json"; done
{ echo "toqb $(git log --oneline -1)"; echo "psf-zero $(git -C "$PSF" log --oneline -1)"; \
  python -c "import qiskit, qiskit_aer; print('qiskit', qiskit.__version__, 'aer', qiskit_aer.__version__)"; \
  echo "start $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')"; } | tee "$OUT/times.txt"
export PSF_ZERO_REPO="$PSF" PSF_COMPILE_FILE="$PSF/patches/psf_compile_c61_2026-10-15/psf_compile.py" \
  PSF_AI_FILE="$PSF/patches/psf_ai_compile_a22_2026-10-15/psf_ai_compile.py" PYTHONWARNINGS=ignore OUT P
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 RAYON_NUM_THREADS=1 QISKIT_NUM_PROCS=1 \
  NUMEXPR_NUM_THREADS=1 QISKIT_PARALLEL=FALSE
{ for k in s2r spsa; do for s in $(seq 9001 9020); do for a in psfai:template qiskit:2:target:template; do
  echo "$k $s $a"; done; done; done; } \
  | xargs -P "$PAR" -L 1 sh -c 'f=$(echo $2 | tr : _); python -m toqb.s2r "$0" "$OUT/seed$1/plan.json" \
      "$OUT/seed$1/$0-$f.json" "$2" > "$OUT/logs/seed$1-$0-$f.log" 2>&1; \
      echo "$0 seed $1 $2 done $(TZ=Europe/Zurich date +%H:%M:%S)"'
echo "end $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')" | tee -a "$OUT/times.txt"
python -m toqb.score_s2r "$OUT" > "$OUT/logs/score.log" 2>&1
sed -n '1,/^## Reported/p' "$OUT/score.md"
python -m zipfile -c "$DAY/s2r_stage0_results.zip" "$OUT" && echo "== DONE: $DAY/s2r_stage0_results.zip"
