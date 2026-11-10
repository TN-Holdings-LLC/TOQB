#!/bin/bash
set -u
cd "$(dirname "$0")"; mkdir -p out
W=${WORKERS:-24}
date "+start %F %T %Z"
ONLY="p2d_q32f0_t1,p2d_q32f0_t2,p2d_q32f0_t3,p2d_q32f0_t4,p2d_q32l0_t1,p2d_q32l0_t2,p2d_q32l0_t3,p2d_q32l0_t4"
python -W ignore expsim.py inputs/q32.qpy inputs/q32_names.json out/q32.json --traj 20 --chunk 1 --workers $W --only $ONLY > out/q32.log 2>&1
tail -n 2 out/q32.log | head -1; grep -q "EXPSIM FINISHED" out/q32.log || { echo "== C FAILED"; tail -5 out/q32.log; exit 1; }
python compare_c.py > out/compare_c.txt 2>&1 || { echo "== C FAILED (compare)"; tail out/compare_c.txt; exit 1; }
cat out/compare_c.txt
date "+end %F %T %Z"
echo "== C FINISHED"
