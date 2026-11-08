#!/bin/bash
# rerun of every eps > 0 and the sx run with the noiseless error gates (the eps = 0 runs are unaffected and kept)
set -u
cd "$(dirname "$0")"; W=${WORKERS:-60}; mkdir -p out out_first_run
cp out/*_0.01.* out/*_0.02.* out/*_0.04.* out/*_dx.* out/compare_m.txt out_first_run/ 2>/dev/null
date "+start %F %T %Z"
python check_err.py
P="--props inputs/fez_props_2026-11-07.json"
run() { local out=$3; python -W ignore expsim3.py "$@" --workers $W $P > out/$(basename $out .json).log 2>&1; tail -n 2 out/$(basename $out .json).log | head -1;
        grep -q "EXPSIM FINISHED" out/$(basename $out .json).log || { echo "== MIRROR FAILED ($out)"; tail -5 out/$(basename $out .json).log; exit 1; }; }
I9="p2d_g3d3_th04_t1,p2d_g3d3_th04_t3,p2d_g3d3_th04_t6,p2d_g3d3_th06_t1,p2d_g3d3_th06_t3,p2d_g3d3_th06_t6,p2d_g3d3_th08_t1,p2d_g3d3_th08_t3,p2d_g3d3_th08_t6"
for e in 0.01 0.02 0.04; do
  for set in heisB_mf isingA_m9; do
    run inputs/$set.qpy inputs/${set}_names.json out/${set}_m1_$e.json --traj 160 --chunk 20 --cz-zz $e
    run inputs/$set.qpy inputs/${set}_names.json out/${set}_m2_$e.json --traj 160 --chunk 10 --twirl --cz-zz $e
  done
  run inputs/heisB.qpy inputs/heisB_names.json out/heisB_fwd_$e.json --traj 160 --chunk 10 --cz-zz $e
  run inputs/isingA.qpy inputs/isingA_names.json out/isingA_f9_fwd_$e.json --traj 160 --chunk 20 --only $I9 --cz-zz $e
done
for set in heisB_mf isingA_m9; do
  run inputs/$set.qpy inputs/${set}_names.json out/${set}_m1_dx.json --traj 160 --chunk 20 --sx-dx 0.01
  run inputs/$set.qpy inputs/${set}_names.json out/${set}_m2_dx.json --traj 160 --chunk 10 --twirl --sx-dx 0.01
done
python compare_m.py . > out/compare_m.txt 2>&1 || { echo "== MIRROR FAILED (compare)"; tail -20 out/compare_m.txt; exit 1; }
cat out/compare_m.txt
date "+end %F %T %Z"
echo "== MIRROR FINISHED"
