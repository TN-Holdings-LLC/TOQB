#!/bin/bash
# The prototype on a 64-core POD: both fez comparisons with FakeFez's noise and with fez's saved calibration of
# 2026-11-06 23:22 CET (fez_props_2026-11-07.json), 160 trajectories each; Heisenberg alone first (speed target), and
# one independent 640-trajectory repeat of Heisenberg with FakeFez (stability). Nothing is fitted.
set -u
cd "$(dirname "$0")"
W=${WORKERS:-60}
mkdir -p out
date "+start %F %T %Z"
python -c "import qiskit, qiskit_aer, qiskit_ibm_runtime; print('qiskit', qiskit.__version__, 'aer', qiskit_aer.__version__, 'runtime', qiskit_ibm_runtime.__version__)"
nproc
for N in fake props; do
  P=""; [ $N = props ] && P="--props inputs/fez_props_2026-11-07.json"
  python -W ignore expsim.py inputs/heisB.qpy inputs/heisB_names.json out/heisB_$N.json --traj 160 --chunk 10 --workers $W $P > out/heisB_$N.log 2>&1
  tail -n 2 out/heisB_$N.log | head -1; grep -q "EXPSIM FINISHED" out/heisB_$N.log || { echo "== PROTO FAILED (heisB $N)"; tail -5 out/heisB_$N.log; exit 1; }
  python -W ignore expsim.py inputs/isingA.qpy inputs/isingA_names.json out/isingA_$N.json --traj 160 --chunk 20 --workers $W $P > out/isingA_$N.log 2>&1
  tail -n 2 out/isingA_$N.log | head -1; grep -q "EXPSIM FINISHED" out/isingA_$N.log || { echo "== PROTO FAILED (isingA $N)"; tail -5 out/isingA_$N.log; exit 1; }
done
python -W ignore expsim.py inputs/heisB.qpy inputs/heisB_names.json out/heisB_fake640.json --traj 640 --chunk 40 --workers $W --seed 1 > out/heisB_fake640.log 2>&1
tail -n 2 out/heisB_fake640.log | head -1; grep -q "EXPSIM FINISHED" out/heisB_fake640.log || { echo "== PROTO FAILED (heisB 640)"; exit 1; }
{
for N in fake props; do
  echo "=== Heisenberg B (fez, place 0) — $N"; python compare.py out/heisB_$N.json inputs/heisB_answers.json inputs/heisB_device_scores.json heis
  echo "=== Ising A 4x2x2 (fez, place 3) — $N"; python compare.py out/isingA_$N.json inputs/isingA_answers.json inputs/isingA_device_scores.json ising
done
echo "=== Heisenberg B — FakeFez, independent repeat with 640 trajectories"; python compare.py out/heisB_fake640.json inputs/heisB_answers.json inputs/heisB_device_scores.json heis
} > out/compare.txt 2>&1 || { echo "== PROTO FAILED (compare)"; tail -20 out/compare.txt; exit 1; }
cat out/compare.txt
date "+end %F %T %Z"
echo "== PROTO FINISHED"
