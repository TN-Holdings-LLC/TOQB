#!/bin/bash
# Test 2 (prereg/drafts-2026-10-30/echo_hz_note.md), the twin rehearsal on a pod: the mirror circuits of
# toqb.kising_echo at n = 20 for fold:rule and fold:zipcyc (no Qiskit in pod simulations), hz = 0, 0.1, 0.3, one-way
# L = 12, 25, 50 (full depth 24, 50, 100), compiled on the published marrakesh snapshot (s2rc_device snapshot) and run
# on TOQB's stand-in (T1, T2, static ZZ; trajectories). A GPU is strongly advised (TOQB_XP=cupy): at n = 20 one
# trajectory of depth 24 takes about 7 s on one CPU core. From /workspace:
#   OUT=/workspace/echo_twin T=64 PAR=2 TOQB_XP=cupy nohup bash TOQB/gpu/echo_hz_twin.sh > echo_twin.txt 2>&1 &
set -u
W=$(pwd); TQ=${TOQB_DIR:-$W/TOQB}; OUT=${OUT:?set OUT}; T=${T:-64}; PAR=${PAR:-2}
NS=${NS:-20}; HZS=${HZS:-"0 0.1 0.3"}; LS=${LS:-"12 25 50"}; ARMS="fold:rule fold:zipcyc"
[ -d "$TQ" ] || { echo "STOP: no TOQB"; exit 1; }
[ -e "$OUT" ] && { echo "STOP: $OUT exists"; exit 1; }
[ -n "${VENV_ACT:-}" ] && . "$VENV_ACT"
mkdir -p "$OUT"
export PYTHONPATH="$TQ" PYTHONWARNINGS=ignore OMP_NUM_THREADS=${OMP_NUM_THREADS:-2}
cd "$TQ" || exit 1
python -m pytest -q tests/test_kising_echo.py > "$OUT/check_tests.log" 2>&1
tail -1 "$OUT/check_tests.log" | grep -q " passed" && ! tail -1 "$OUT/check_tests.log" | grep -q "failed" || { echo "STOP: tests (see check_tests.log)"; exit 1; }
{ echo "toqb $(git log --oneline -1 | cut -c1-60)"; echo "note $(sha256sum prereg/drafts-2026-10-30/echo_hz_note.md)";
  echo "tests $(tail -1 "$OUT/check_tests.log")"; echo "T $T PAR $PAR XP ${TOQB_XP:-numpy}";
  echo "start $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')"; } | tee "$OUT/times.txt"
python -m toqb.s2rc_device snapshot --out "$OUT/fetch" | tee -a "$OUT/times.txt"
J="$OUT/jobs.txt"; : > "$J"
for arm in $ARMS; do
  for hz in $HZS; do
    R="$OUT/runs_${arm//:/_}_hz$hz"
    for L in $LS; do
      python -m toqb.kising_echo build "$OUT/fetch" "$R" --arm "$arm" --n $NS --L "$L" --hz "$hz" --shots 500 2>&1 | grep -v Warn | tail -1 | tee -a "$OUT/build.txt"
    done
    echo "$R $R/twin.json" >> "$J"
  done
done
grep -q "REJECTED" "$OUT/build.txt" && echo "NOTE: a record failed the two-qubit acceptance (see build.txt); it is skipped, not replaced"
xargs -P "$PAR" -L 1 sh -c 'python -m toqb.kising_echo standin "$0" "$1" --T '"$T"' --n '"$NS"' || echo "RUN FAILED: $0"' < "$J" 2>&1 | grep -v Warn | tee -a "$OUT/progress.txt"
echo "end $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')" | tee -a "$OUT/times.txt"
cd "$W" && python -m zipfile -c "$W/echo_twin.zip" "$OUT" && echo "== DONE: $W/echo_twin.zip"
