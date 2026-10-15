#!/bin/bash
# TOQB loop standard run, n = 6, L = 8, seeds 101-120: Qiskit level 2's template against PSF-Zero's (a22 + c61).
# Pre-registration: prereg/2026-10-15-loop-n6-standard.md (pushed before this run). Home, WSL; no network needed.
# Checks every fixed hash, then runs ten seeds at a time, scores, and zips the results next to the day's files.
# Never overwrites: refuses an existing output folder.
set -u
TOQB=${TOQB:-~/toqb_push_2026-10-15}
PSF=${PSF:-~/psf_zero_fresh_test}
DAY=${DAY:?set DAY to the folder that receives the zip}
PAR=${PAR:-10}
SEEDS=${SEEDS:-$(seq 101 120)}
OUT=${OUT:-results/loop-n6-standard-2026-10-15}
P=prereg/loop-n6-standard-2026-10-15
cd "$TOQB" || { echo "STOP: no $TOQB"; exit 1; }
echo "e584bbcda3551dd012ea4c7ee117d17902ab536dc1cfc90078f389f1ff9ef8da  prereg/2026-10-15-loop-n6-standard.md" | sha256sum -c --quiet || { echo "STOP: pre-registration changed"; exit 1; }
echo "adae963387b8648468d9d0533d266f811514d693fb200362873d3cb892d7270d  toqb/score_loop_preg.py" | sha256sum -c --quiet \
  || { echo "STOP: scoring script changed"; exit 1; }
echo "7f8e7a3fa52ab68956fcbe172dee83c445587ca9e2c85edac0041e490251e067  $P/SHA256SUMS" | sha256sum -c --quiet \
  || { echo "STOP: plan list changed"; exit 1; }
( cd "$P" && sha256sum -c --quiet SHA256SUMS ) || { echo "STOP: a plan changed"; exit 1; }
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
printf '%s\n' $SEEDS | xargs -P "$PAR" -I{} sh -c \
  'python -m toqb.task_loop run "$P/plan_s{}.json" "$OUT/seed{}" > "$OUT/logs/seed{}.log" 2>&1; \
   echo "seed {} done $(TZ=Europe/Zurich date +%H:%M:%S)"'
echo "end $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')" | tee -a "$OUT/times.txt"
python -m toqb.score_loop_preg "$OUT" --seeds "$(printf '%s,' $SEEDS | sed 's/,$//')" > "$OUT/logs/score.log" 2>&1
sed -n '1,/^## Reported/p' "$OUT/score.md"
python -m zipfile -c "$DAY/loop_n6_standard_results.zip" "$OUT" && echo "== DONE: $DAY/loop_n6_standard_results.zip"
