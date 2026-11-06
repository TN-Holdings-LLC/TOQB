#!/bin/bash
# rule fixed 2026-11-06 06:32 CET before any run: FakeFez with the snapshot's dead couplers marked, 4x2x2 t3, v3 and SABRE,
# 400 trajectories, Aer seeds 1, 2, 3, 4, 5 (06c used 11); report R per seed, its range, mean and sd; no seed dropped.
# usage (from notes/os3d_sim_2026-11-06): bash seeds_t3/run.sh PSF_OS_CHECKOUT
for s in 1 2 3 4 5; do
  python3 sim3d.py "$1" ../../results/daily/2026-11-05/ibm_fez/dev seeds_t3/t3_seed$s.json \
    --model fakefez --mark-fakefez-dead --ts 3 --trajectories 400 --variants v3,sabre --sim-seed $s 2>&1 | grep -v -i "deprec\|from_dict"
done
