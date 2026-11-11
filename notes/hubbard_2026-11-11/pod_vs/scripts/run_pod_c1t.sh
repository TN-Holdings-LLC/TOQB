#!/bin/bash
# On a CPU POD, from this folder. Usage: bash run_pod.sh "L1 L2 ..." "S1 S2 ..." "CHI1 CHI2 ..." STEM [BUDGET_HOURS]
# VS change (2026-11-11 ~04:05 CET): quimb runs with 1 thread for chi <= 512 and 8 for chi >= 1024 (measured on the pod: L 8 chi 256 took 1.2 s with 1 thread, 14.2 s with 4, 47 s with 16); Aer unchanged.
# Per (L, steps): quimb at every chi (small first), then Aer exact. Limits (2026-11-11b):
#   each case at most 2 h (timeout 7200);
#   the whole run at most BUDGET_HOURS (default 5.5 h): no new case starts after that, the rest is written "skipped";
#   a quimb chi that hits its limit skips the larger chi of the same (L, steps);
#   an Aer run that hits its limit skips Aer for the larger steps of the same L.
#   (2026-11-11c) a case already finished in STEM_report.jsonl (a row with "seconds") is not run again, so a run
#   stopped part way (or one begun with an earlier kit) can be resumed in the same folder with the same STEM;
#   pass as BUDGET_HOURS only the hours that are left.
# The script does NOT stop or delete the POD: delete it yourself when it ends (or use your own stopper).
set -e
python3 -m venv /root/venv 2>/dev/null || true; export PATH=/root/venv/bin:$PATH
pip install -q "qiskit==2.6.1" "qiskit-aer==0.18.2" "quimb==1.16.0" numpy scipy
python -c "import qiskit, qiskit_aer, quimb; print('qiskit', qiskit.__version__, 'aer', qiskit_aer.__version__, 'quimb', quimb.__version__)"
nproc; free -g | head -2
# CPU threads (2026-11-11c1): the cores this container may use (cgroup cpu.max), not the host's; numpy/BLAS (quimb)
# and Aer are given that number, so a 32-core share of a 128-core host does not run 128 threads.
NCPU=$(python3 -c "
import os
try:
    q, p = open('/sys/fs/cgroup/cpu.max').read().split()
    print(max(1, int(int(q) // int(p))) if q != 'max' else len(os.sched_getaffinity(0)))
except Exception:
    print(len(os.sched_getaffinity(0)))")
export OMP_NUM_THREADS=$NCPU OPENBLAS_NUM_THREADS=$NCPU MKL_NUM_THREADS=$NCPU NUMEXPR_NUM_THREADS=$NCPU
echo "threads: $NCPU (nproc $(nproc))"
TZ=Europe/Zurich date
BUDGET=$(python3 -c "print(int(float('${5:-5.5}') * 3600))")
START=$(date +%s)
left() { echo $(( BUDGET - ($(date +%s) - START) )); }
note() { echo "{\"L\": $1, \"steps\": $2, \"method\": \"$3\", \"chi\": $4, \"stopped\": \"$5\"}" >> $STEM_REPORT; }
STEM_REPORT=$4_report.jsonl
done_already() {  # L S method chi -> exit 0 if a finished row exists
  [ -f "$STEM_REPORT" ] || return 1
  python3 - "$STEM_REPORT" "$1" "$2" "$3" "$4" <<'PY'
import json, sys
f, L, S, m, c = sys.argv[1:]
c = None if c in ("null", "0") else int(c)
for line in open(f):
    try:
        r = json.loads(line)
    except Exception:
        continue
    if "seconds" in r and r["L"] == int(L) and r["steps"] == int(S) and r["method"] == m and (m == "aer" or r.get("chi") == c):
        sys.exit(0)
sys.exit(1)
PY
}
for L in $1; do
  AER_OK=1
  for S in $2; do
    CHI_OK=1
    for C in $3; do
      if done_already $L $S quimb $C; then echo "L $L steps $S quimb $C: already done"; continue; fi
      if [ $(left) -le 0 ]; then note $L $S quimb $C "skipped: run budget spent"; continue; fi
      if [ $CHI_OK -eq 0 ]; then note $L $S quimb $C "skipped: a smaller chi hit its limit"; continue; fi
      T=$(( $(left) < 7200 ? $(left) : 7200 ))
      QT=$(( C <= 512 ? 1 : 8 )); echo "quimb threads $QT for chi $C"
      OMP_NUM_THREADS=$QT OPENBLAS_NUM_THREADS=$QT MKL_NUM_THREADS=$QT NUMEXPR_NUM_THREADS=$QT timeout $T python3 hub_cost.py $L $S quimb $C $4_report.jsonl $4_values.npz || { note $L $S quimb $C "limit ${T} s or error"; CHI_OK=0; }
    done
    if done_already $L $S aer null; then echo "L $L steps $S aer: already done"; continue; fi
    if [ $(left) -le 0 ]; then note $L $S aer null "skipped: run budget spent"; continue; fi
    if [ $AER_OK -eq 0 ]; then note $L $S aer null "skipped: fewer steps hit the limit"; continue; fi
    T=$(( $(left) < 7200 ? $(left) : 7200 ))
    timeout $T python3 hub_cost.py $L $S aer $4_report.jsonl $4_values.npz --threads $NCPU || { note $L $S aer null "limit ${T} s or error"; AER_OK=0; }
  done
done
TZ=Europe/Zurich date
sha256sum $4_values.npz || true
echo "=== DONE. The POD is still running and billing: delete it now. ==="
