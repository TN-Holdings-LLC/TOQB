#!/bin/bash
# As run_pod.sh (workplace, 2026-11-12), with one change (VS Claude, owner's choice of 3 pods): the bias m comes from
# the third argument, so that each pod runs one m. usage: bash run_pod_m.sh STEM BUDGET_HOURS M
set -u
STEM=${1:?STEM}; BUDGET=${2:-2.0}; M=${3:?M}
NCPU=$(python3 -c "import os; print(len(os.sched_getaffinity(0)))")
if [ -r /sys/fs/cgroup/cpu.max ]; then
  read Q P < /sys/fs/cgroup/cpu.max
  if [ "$Q" != "max" ]; then NCPU=$(( Q / P )); fi
fi
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
echo "start $(TZ=Europe/Zurich date)  cpus $NCPU  m $M  python $(python3 -V 2>&1)  quimb $(python3 -c 'import quimb; print(quimb.__version__)')"
timeout $(python3 -c "print(int($BUDGET*3600))") python3 design_pod.py ${STEM}_design.jsonl --N 40 --K 100 --cycles 6 \
  --m $M --arms A0 A1 A2 A2h2 B1 B2 --procs $NCPU 2>&1 | grep -v -i warn | tee ${STEM}_screen.log
echo "end $(TZ=Europe/Zurich date)  exit ${PIPESTATUS[0]}"
sha256sum ${STEM}_design.jsonl
