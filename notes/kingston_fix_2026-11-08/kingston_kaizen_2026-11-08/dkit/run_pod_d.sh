#!/bin/bash
set -u
cd "$(dirname "$0")"; mkdir -p out
date "+start %F %T %Z"
python -W ignore expsim3.py inputs/kng.qpy inputs/kng_names.json out/kng.json --traj 160 --chunk 10 --workers ${WORKERS:-60} --props inputs/fez_props_2026-11-07.json > out/kng.log 2>&1
tail -n 2 out/kng.log | head -1; grep -q "EXPSIM FINISHED" out/kng.log || { echo "== D FAILED"; tail -5 out/kng.log; exit 1; }
python compare_d.py > out/compare_d.txt 2>&1 || { echo "== D FAILED (compare)"; tail out/compare_d.txt; exit 1; }
cat out/compare_d.txt
date "+end %F %T %Z"
echo "== D FINISHED"
