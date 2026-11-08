#!/bin/bash
set -u
cd "$(dirname "$0")"; W=${WORKERS:-60}; mkdir -p out
date "+start %F %T %Z"
P="--props inputs/fez_props_2026-11-07.json"
run() { local out=$3; python -W ignore expsim3.py "$@" --workers $W $P > out/$(basename $out .json).log 2>&1; tail -n 2 out/$(basename $out .json).log | head -1;
        grep -q "EXPSIM FINISHED" out/$(basename $out .json).log || { echo "== MIRROR FAILED ($out)"; tail -5 out/$(basename $out .json).log; exit 1; }; }
I9="p2d_g3d3_th04_t1,p2d_g3d3_th04_t3,p2d_g3d3_th04_t6,p2d_g3d3_th06_t1,p2d_g3d3_th06_t3,p2d_g3d3_th06_t6,p2d_g3d3_th08_t1,p2d_g3d3_th08_t3,p2d_g3d3_th08_t6"
for e in 0 0.01 0.02 0.04; do
  Z=""; [ $e != 0 ] && Z="--cz-zz $e"
  for set in heisB_mf isingA_m9; do
    run inputs/$set.qpy inputs/${set}_names.json out/${set}_m1_$e.json --traj 160 --chunk 20 $Z
    run inputs/$set.qpy inputs/${set}_names.json out/${set}_m2_$e.json --traj 160 --chunk 10 --twirl $Z
  done
  run inputs/heisB.qpy inputs/heisB_names.json out/heisB_fwd_$e.json --traj 160 --chunk 10 $Z
  run inputs/isingA.qpy inputs/isingA_names.json out/isingA_f9_fwd_$e.json --traj 160 --chunk 20 --only $I9 $Z
done
for set in heisB_mf isingA_m9; do
  run inputs/$set.qpy inputs/${set}_names.json out/${set}_m1_dx.json --traj 160 --chunk 20 --sx-dx 0.01
  run inputs/$set.qpy inputs/${set}_names.json out/${set}_m2_dx.json --traj 160 --chunk 10 --twirl --sx-dx 0.01
done
python compare_m.py . > out/compare_m.txt 2>&1 || { echo "== MIRROR FAILED (compare)"; tail -20 out/compare_m.txt; exit 1; }
cat out/compare_m.txt
date "+end %F %T %Z"
echo "== MIRROR FINISHED"
