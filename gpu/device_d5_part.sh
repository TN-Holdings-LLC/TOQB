#!/bin/bash
# D5 amendment 3 (prereg/drafts-2026-10-28/device_d5_amend3.md): one part's job from the cells device_d5b.sh built.
#   PART=A FETCH=/root/d3_fetch_2026-10-28 OUT=/workspace/d5 bash TOQB/gpu/device_d5_part.sh   (only A; amendment 3)
set -u
W=$(pwd); TQ=${TOQB_DIR:-$W/TOQB}; VA=${VENV_ACT:-$W/venv/bin/activate}
PART=${PART:?set PART to A, B or C}; FETCH=${FETCH:?set FETCH}; OUT=${OUT:?set OUT}
case "$PART" in
  A) CELLS="lam_n20_L16_m0-fold_rule lam_n20_L16_m0-fold_zipcyc lam_n20_L16_m0-qiskit_2_target_template"; MAX=90 ;;
  C|B) echo "STOP: parts B and C are not run (amendment 3)"; exit 1 ;;
  *) echo "STOP: PART must be A, B or C"; exit 1 ;;
esac
R="$OUT/runs_$PART"; J="$OUT/job_$PART"
[ -e "$R" ] || [ -e "$J" ] && { echo "STOP: $R or $J exists"; exit 1; }
for c in $CELLS; do [ -f "$OUT/runs/$c.json" ] && [ -f "$OUT/runs/$c.qpy" ] || { echo "STOP: $c not built yet"; exit 1; }; done
. "$VA"; export PYTHONPATH="$TQ" PYTHONWARNINGS=ignore
mkdir -p "$R"; for c in $CELLS; do cp -p "$OUT/runs/$c.json" "$OUT/runs/$c.qpy" "$R/"; done
cd "$TQ" || exit 1
{ echo "part $PART: amend3 $(sha256sum prereg/drafts-2026-10-28/device_d5_amend3.md | cut -c1-64); toqb $(git log --oneline -1 | cut -c1-7)"; \
  echo "part $PART start $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')"; } | tee -a "$OUT/times.txt"
python -m toqb.lam_device rehearse "$R" --reps 2000 2>&1 | grep -v Warn | tee "$OUT/rehearse_$PART.txt"
python -m toqb.s2rc_device assemble --fetch "$FETCH" --runs "$R" --out "$J" --max-seconds $MAX | tee "$OUT/assemble_$PART.txt"
[ -f "$J/manifest.json" ] || { echo "STOP: no job"; exit 1; }
cd "$W" && python -m zipfile -c "$W/d5${PART}_job.zip" "$OUT/runs_$PART" "$OUT/job_$PART" "$OUT/times.txt" "$OUT/build.txt" \
  "$OUT/rehearse_$PART.txt" "$OUT/assemble_$PART.txt" && echo "== DONE: $W/d5${PART}_job.zip"
