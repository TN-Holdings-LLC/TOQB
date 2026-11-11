#!/bin/bash
# On a CPU POD, from this folder. Usage: bash run_pod.sh "L1 L2 ..." "S1 S2 ..." "CHI1 CHI2 ..." STEM
# Runs, per (L, steps): quimb at every chi (cheap first), then Aer exact; each case under a 2 h limit.
set -e
python3 -m venv /root/venv 2>/dev/null || true; export PATH=/root/venv/bin:$PATH
pip install -q "qiskit==2.6.1" "qiskit-aer==0.18.2" "quimb==1.16.0" numpy scipy
python -c "import qiskit, qiskit_aer, quimb; print('qiskit', qiskit.__version__, 'aer', qiskit_aer.__version__, 'quimb', quimb.__version__)"
nproc; free -g | head -2
TZ=Europe/Zurich date
for L in $1; do for S in $2; do
  for C in $3; do timeout 7200 python3 hub_cost.py $L $S quimb $C $4_report.jsonl $4_values.npz || echo "{\"L\": $L, \"steps\": $S, \"method\": \"quimb\", \"chi\": $C, \"stopped\": \"2 h limit or error\"}" >> $4_report.jsonl; done
  timeout 7200 python3 hub_cost.py $L $S aer $4_report.jsonl $4_values.npz --threads $(nproc) || echo "{\"L\": $L, \"steps\": $S, \"method\": \"aer\", \"stopped\": \"2 h limit or error\"}" >> $4_report.jsonl
done; done
TZ=Europe/Zurich date
sha256sum $4_values.npz
