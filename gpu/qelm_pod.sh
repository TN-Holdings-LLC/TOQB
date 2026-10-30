#!/bin/bash
# QELM task A (prereg/drafts-2026-10-30/qelm_A_note.md) on a pod: the teacher task (n = 20, L = 19 by
# qelm.depth_formula), the declared predictions, then the features of fold:rule and fold:zipcyc on TOQB's stand-in
# (T1 / T2 on idles, static ZZ; trajectories) and the rehearsal score. Qiskit is not in pod simulations (owner,
# 2026-10-28); its arm runs only on the device. A GPU is strongly advised (TOQB_XP=cupy): at L = 19 every local feature
# depends on the whole ring, so each circuit is a 20-qubit trajectory simulation. From /workspace:
#   OUT=/workspace/qelmA T=64 TOQB_XP=cupy nohup bash TOQB/gpu/qelm_pod.sh > qelmA.txt 2>&1 &
# Optional: A_FROM=<folder with the workplace's noiseless.json> reuses the teacher task (its SHA-256 is recorded).
set -u
W=$(pwd); TQ=${TOQB_DIR:-$W/TOQB}; OUT=${OUT:?set OUT}; T=${T:-64}
NQ=${NQ:-20}; LQ=${LQ:-19}; ARMS=${ARMS:-fold:rule,fold:zipcyc}
LSTAR=${LSTAR:-fold:rule=56.5,fold:zipcyc=15.1,qiskit:2:blind:template=26.4}  # marrakesh n = 20, 2026-10-29
[ -d "$TQ" ] || { echo "STOP: no TOQB"; exit 1; }
[ -e "$OUT" ] && { echo "STOP: $OUT exists"; exit 1; }
[ -n "${VENV_ACT:-}" ] && . "$VENV_ACT"
mkdir -p "$OUT"
export PYTHONPATH="$TQ" PYTHONWARNINGS=ignore QELM_PROCS=${QELM_PROCS:-$(nproc)}
cd "$TQ" || exit 1
python -m pytest -q tests/test_qelm.py > "$OUT/check_tests.log" 2>&1
tail -1 "$OUT/check_tests.log" | grep -q " passed" && ! tail -1 "$OUT/check_tests.log" | grep -q "failed" || { echo "STOP: tests (see check_tests.log)"; exit 1; }
{ echo "toqb $(git log --oneline -1 | cut -c1-60)"; [ -f prereg/drafts-2026-10-30/qelm_A_note.md ] && echo "note $(sha256sum prereg/drafts-2026-10-30/qelm_A_note.md)";
  echo "tests $(tail -1 "$OUT/check_tests.log")"; echo "n $NQ L $LQ T $T arms $ARMS XP ${TOQB_XP:-numpy} procs $QELM_PROCS";
  echo "start $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')"; } | tee "$OUT/times.txt"
python -m toqb.s2rc_device snapshot --out "$OUT/fetch" | tee -a "$OUT/times.txt"
if [ -n "${A_FROM:-}" ]; then
  cp "$A_FROM/noiseless.json" "$OUT/noiseless.json" && echo "teacher reused: $(sha256sum "$OUT/noiseless.json")" | tee -a "$OUT/times.txt"
else
  python -m toqb.qelm teacher "$OUT" --n "$NQ" --L "$LQ" 2>&1 | grep -v Warn | tee -a "$OUT/times.txt"
fi
[ -f "$OUT/noiseless.json" ] || { echo "STOP: no teacher task"; exit 1; }
python -m toqb.qelm predict "$OUT" --lstar "$LSTAR" 2>&1 | grep -v Warn | tee "$OUT/predict.txt"
python -m toqb.qelm run "$OUT" --task teacher --standin toqb --T "$T" --device "file:$OUT/fetch/target.pkl" --arms "$ARMS" 2>&1 | grep -v Warn | tee -a "$OUT/progress.txt"
python -m toqb.qelm score "$OUT" 2>&1 | grep -v Warn > "$OUT/score.txt"
echo "end $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')" | tee -a "$OUT/times.txt"
cd "$W" && python -m zipfile -c "$W/qelmA.zip" "$OUT" && echo "== DONE: $W/qelmA.zip"
# Task B (declared first, run once; not part of this script): python -m toqb.qelm run OUT_B --task breast --L 1 --enc pi/4 ...
