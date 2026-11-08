#!/bin/bash
set -u
cd "$(dirname "$0")"; W=${WORKERS:-60}; mkdir -p out
date "+start %F %T %Z"
P="--props inputs/fez_props_2026-11-07.json"
run() { python -W ignore expsim2.py "$@" --workers $W $P > out/$(basename $3 .json).log 2>&1; tail -n 2 out/$(basename $3 .json).log | head -1; grep -q "EXPSIM FINISHED" out/$(basename $3 .json).log || { echo "== E FAILED ($3)"; tail -5 out/$(basename $3 .json).log; exit 1; }; }
run inputs/heisB_mf.qpy inputs/heisB_mf_names.json out/heisB_mf.json --traj 160 --chunk 10
run inputs/isingA_mf.qpy inputs/isingA_mf_names.json out/isingA_mf.json --traj 160 --chunk 20
ISO="p2d_g3d3_th06_t1,p2d_g3d3_th06_t2,p2d_g3d3_th06_t3,p2d_g3d3_th06_t4,p2d_g3d3_th06_t5,p2d_g3d3_th06_t6"
for probe in base t2half czzz; do
  X=""; [ $probe = t2half ] && X="--t2-scale 0.5"; [ $probe = czzz ] && X="--cz-zz 0.02"
  run inputs/heisB.qpy inputs/heisB_names.json out/heisB_$probe.json --traj 160 --chunk 10 $X
  run inputs/isingA.qpy inputs/isingA_names.json out/isingA_$probe.json --traj 160 --chunk 20 --only $ISO $X
done
python compare_e.py . > out/compare_e.txt 2>&1 || { echo "== E FAILED (compare)"; tail out/compare_e.txt; exit 1; }
cat out/compare_e.txt
date "+end %F %T %Z"
echo "== E FINISHED"
