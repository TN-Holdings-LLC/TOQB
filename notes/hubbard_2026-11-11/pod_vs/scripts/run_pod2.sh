#!/bin/bash
# run_pod.sh with three changes (reported): (1) threads = the pod's real vCPU count V (nproc shows the host's cores),
# also for numpy/BLAS; (2) once a quimb chi stops (2 h or error), the larger chis of the same (L, steps) are skipped
# (recorded as "skipped"); (3) a heartbeat line every 60 s in STEM_progress.log.
# Usage: V=16 bash run_pod2.sh "L1 ..." "S1 ..." "CHI1 ..." STEM
set -e
V=${V:?}
export OMP_NUM_THREADS=$V OPENBLAS_NUM_THREADS=$V MKL_NUM_THREADS=$V NUMBA_NUM_THREADS=$V
python3 -m venv /root/venv 2>/dev/null || true; export PATH=/root/venv/bin:$PATH
pip install -q "qiskit==2.6.1" "qiskit-aer==0.18.2" "quimb==1.16.0" numpy scipy
python -c "import qiskit, qiskit_aer, quimb, numpy; print('qiskit', qiskit.__version__, 'aer', qiskit_aer.__version__, 'quimb', quimb.__version__, 'numpy', numpy.__version__)"
echo "vCPU used $V (nproc shows $(nproc))"; free -g | head -2
( while true; do
    p=$(ps -eo etimes,pcpu,rss,args --sort=-pcpu | grep "[h]ub_cost.py" | head -1)
    echo "$(TZ=CET-1 date +%H:%M:%S) cases_done $(wc -l < $4_report.jsonl 2>/dev/null || echo 0) running: $p" >> $4_progress.log
    sleep 60
  done ) &
HB=$!
TZ=CET-1 date
echo "== smoke L 8 steps 4"
python3 hub_cost.py 8 4 quimb 256 $4_smoke_report.jsonl $4_smoke_values.npz
python3 hub_cost.py 8 4 aer $4_smoke_report.jsonl $4_smoke_values.npz --threads $V
for L in $1; do for S in $2; do
  skip=0
  for C in $3; do
    if [ $skip = 1 ]; then echo "{\"L\": $L, \"steps\": $S, \"method\": \"quimb\", \"chi\": $C, \"stopped\": \"skipped (a smaller chi stopped)\"}" >> $4_report.jsonl; continue; fi
    echo "== $(TZ=CET-1 date +%H:%M:%S) L $L steps $S quimb chi $C"
    timeout 7200 python3 hub_cost.py $L $S quimb $C $4_report.jsonl $4_values.npz || { echo "{\"L\": $L, \"steps\": $S, \"method\": \"quimb\", \"chi\": $C, \"stopped\": \"2 h limit or error\"}" >> $4_report.jsonl; skip=1; }
  done
  echo "== $(TZ=CET-1 date +%H:%M:%S) L $L steps $S aer"
  timeout 7200 python3 hub_cost.py $L $S aer $4_report.jsonl $4_values.npz --threads $V || echo "{\"L\": $L, \"steps\": $S, \"method\": \"aer\", \"stopped\": \"2 h limit or error\"}" >> $4_report.jsonl
done; done
TZ=CET-1 date
sha256sum $4_values.npz
kill $HB
echo ALLDONE
