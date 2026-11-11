#!/bin/bash
# On a CPU POD, from this folder. Usage: bash run_pod.sh "L1 L2 ..." "S1 S2 ..." "CHI1 CHI2 ..." STEM [BUDGET_HOURS]
# Per (L, steps): quimb at every chi (small first), then Aer exact. Limits (2026-11-11b):
#   each case at most 2 h (timeout 7200);
#   the whole run at most BUDGET_HOURS (default 5.5 h): no new case starts after that, the rest is written "skipped";
#   a quimb chi that hits its limit skips the larger chi of the same (L, steps);
#   an Aer run that hits its limit skips Aer for the larger steps of the same L.
# The script does NOT stop or delete the POD: delete it yourself when it ends (or use your own stopper).
set -e
python3 -m venv /root/venv 2>/dev/null || true; export PATH=/root/venv/bin:$PATH
pip install -q "qiskit==2.6.1" "qiskit-aer==0.18.2" "quimb==1.16.0" numpy scipy
python -c "import qiskit, qiskit_aer, quimb; print('qiskit', qiskit.__version__, 'aer', qiskit_aer.__version__, 'quimb', quimb.__version__)"
nproc; free -g | head -2
TZ=Europe/Zurich date
BUDGET=$(python3 -c "print(int(float('${5:-5.5}') * 3600))")
START=$(date +%s)
left() { echo $(( BUDGET - ($(date +%s) - START) )); }
note() { echo "{\"L\": $1, \"steps\": $2, \"method\": \"$3\", \"chi\": $4, \"stopped\": \"$5\"}" >> $STEM_REPORT; }
STEM_REPORT=$4_report.jsonl
for L in $1; do
  AER_OK=1
  for S in $2; do
    CHI_OK=1
    for C in $3; do
      if [ $(left) -le 0 ]; then note $L $S quimb $C "skipped: run budget spent"; continue; fi
      if [ $CHI_OK -eq 0 ]; then note $L $S quimb $C "skipped: a smaller chi hit its limit"; continue; fi
      T=$(( $(left) < 7200 ? $(left) : 7200 ))
      timeout $T python3 hub_cost.py $L $S quimb $C $4_report.jsonl $4_values.npz || { note $L $S quimb $C "limit ${T} s or error"; CHI_OK=0; }
    done
    if [ $(left) -le 0 ]; then note $L $S aer null "skipped: run budget spent"; continue; fi
    if [ $AER_OK -eq 0 ]; then note $L $S aer null "skipped: fewer steps hit the limit"; continue; fi
    T=$(( $(left) < 7200 ? $(left) : 7200 ))
    timeout $T python3 hub_cost.py $L $S aer $4_report.jsonl $4_values.npz --threads $(nproc) || { note $L $S aer null "limit ${T} s or error"; AER_OK=0; }
  done
done
TZ=Europe/Zurich date
sha256sum $4_values.npz || true
echo "=== DONE. The POD is still running and billing: delete it now. ==="
