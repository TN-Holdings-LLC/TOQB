#!/bin/bash
# The problem bank of 2026-11-04 on one pod, one part after the other (each stops on its own checks; a STOP in one part
# does not stop the next). From /workspace, after `pip install "qiskit==2.5.2" "qiskit-aer==0.18.0" "cupy-cuda12x==14.2.0" pytest`:
#   nohup bash TOQB/gpu/bank_pod.sh > bank.txt 2>&1 < /dev/null &
W=$(pwd)
OUT=$W/p6_tx0.3 TX=0.3 CPU=$W/p6_tx0.3_answers_cpu.json bash TOQB/gpu/ising2d_pod.sh > $W/p6_tx0.3.txt 2>&1; tail -1 $W/p6_tx0.3.txt
OUT=$W/p6_tx0.8 TX=0.8 CPU=$W/p6_tx0.8_answers_cpu.json bash TOQB/gpu/ising2d_pod.sh > $W/p6_tx0.8.txt 2>&1; tail -1 $W/p6_tx0.8.txt
OUT=$W/du_bank KICKS=0.7353981634,0.4853981634 bash TOQB/gpu/du_bank_pod.sh > $W/du_bank.txt 2>&1; tail -1 $W/du_bank.txt
OUT=$W/p5_marrakesh LAT=$W/lattice_marrakesh.json bash TOQB/gpu/kim_e_pod.sh > $W/p5_marrakesh.txt 2>&1; tail -1 $W/p5_marrakesh.txt
echo "== BANK FINISHED $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')"
