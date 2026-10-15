#!/bin/bash
# TOQB loop standard run 2, n = 6, L = 8, seeds 1001-1200, calibrated SPSA, fast engine: Qiskit level 2's template
# against PSF-Zero's (a22 + c61). Pre-registration: prereg/2026-10-15-loop-n6-standard-2.md (pushed before this run).
# Home, WSL; no network needed. Checks every fixed hash, runs ten seeds at a time, scores, zips into $DAY.
# Never overwrites: refuses an existing output folder.
set -u
TOQB=${TOQB:-~/toqb_push_2026-10-15}
PSF=${PSF:-~/psf_zero_fresh_test}
DAY=${DAY:?set DAY to the folder that receives the zip}
PAR=${PAR:-10}
FIRST=${FIRST:-1001}
LAST=${LAST:-1200}
OUT=${OUT:-results/loop-n6-standard-2-2026-10-15}
P=prereg/loop-n6-standard-2-2026-10-15
cd "$TOQB" || { echo "STOP: no $TOQB"; exit 1; }
echo "d1126e62df5469175eb54a52437533f5a1a8c0cacd8ff2b07a8b5531b87ffcbd  prereg/2026-10-15-loop-n6-standard-2.md" | sha256sum -c --quiet || { echo "STOP: pre-registration changed"; exit 1; }
echo "b77a961f1012faec71356b8a0845d91b15feedaacc5aff905a2153051f35b3f9  $P/SHA256SUMS" | sha256sum -c --quiet \
  || { echo "STOP: plan list changed"; exit 1; }
echo "808c6a55ffd3c07468f44b12fe7d27579b37e00ac19fa4062b38cfd2c0ddabcf  $P/CODE_SHA256SUMS" | sha256sum -c --quiet \
  || { echo "STOP: code list changed"; exit 1; }
( cd "$P" && sha256sum -c --quiet SHA256SUMS ) || { echo "STOP: a plan changed"; exit 1; }
sha256sum -c --quiet "$P/CODE_SHA256SUMS" || { echo "STOP: TOQB code differs from the pre-registered"; exit 1; }
( cd "$PSF" && printf '%s\n' \
  "254cfabc5924118a5c54e159fa2284202d21b87894202f447333de07f06b3728  patches/psf_compile_c61_2026-10-15/psf_compile.py" \
  "625f9431344cd0fad6715ea44dc347044b0c64507c008f69202145d03b14a8ce  patches/psf_ai_compile_a22_2026-10-15/psf_ai_compile.py" \
  | sha256sum -c --quiet ) || { echo "STOP: PSF-Zero files differ from the pre-registered ones"; exit 1; }
python -c "import qiskit, qiskit_aer; assert (qiskit.__version__, qiskit_aer.__version__) == ('2.5.2', '0.17.2'), \
  (qiskit.__version__, qiskit_aer.__version__)" || { echo "STOP: needs Qiskit 2.5.2 and Aer 0.17.2"; exit 1; }
[ -e "$OUT" ] && { echo "STOP: $OUT exists; a run never overwrites another"; exit 1; }
mkdir -p "$OUT/logs"
{ echo "toqb $(git log --oneline -1)"; echo "psf-zero $(git -C "$PSF" log --oneline -1)"; \
  echo "start $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')"; } | tee "$OUT/times.txt"
export PSF_ZERO_REPO="$PSF" PSF_COMPILE_FILE="$PSF/patches/psf_compile_c61_2026-10-15/psf_compile.py" \
  PSF_AI_FILE="$PSF/patches/psf_ai_compile_a22_2026-10-15/psf_ai_compile.py" PYTHONWARNINGS=ignore OUT P
seq "$FIRST" "$LAST" | xargs -P "$PAR" -I{} sh -c \
  'python -m toqb.task_loop run "$P/plan_s{}.json" "$OUT/seed{}" > "$OUT/logs/seed{}.log" 2>&1; \
   echo "seed {} done $(TZ=Europe/Zurich date +%H:%M:%S)"'
echo "end $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')" | tee -a "$OUT/times.txt"
python -m toqb.score_loop_preg2 "$OUT" --seeds "$FIRST-$LAST" > "$OUT/logs/score.log" 2>&1
sed -n '1,/^## Reported/p' "$OUT/score.md"
python -m zipfile -c "$DAY/loop_n6_standard_2_results.zip" "$OUT" && echo "== DONE: $DAY/loop_n6_standard_2_results.zip"
