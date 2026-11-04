#!/bin/bash
# P6 answers on a pod: <Z_q> of the Qedma tutorial's 35-qubit patch (psf_os/ising2d.py) at t = 6, 7, 8, 9 for every qubit
# whose causal cone has at most 33 qubits (single precision, one GPU with 80 GB or more), after three checks.
# Needs TOQB and psf-os side by side and answers_cpu.json (t = 1..5, from the CPU) in the working folder. From /workspace:
#   pip install "qiskit==2.5.2" "qiskit-aer==0.18.0" "cupy-cuda12x==14.2.0" pytest
#   OUT=/workspace/p6 nohup bash TOQB/gpu/ising2d_pod.sh > p6.txt 2>&1 < /dev/null &
# STOP (no answer written) if a check fails:
#   K1 GPU single = the CPU answers at t = 5 (every qubit): 1e-4;
#   K2 GPU single = GPU double on the five largest cones at t = 6: 1e-4;
#   K3 t = 1 = cos(theta_x) on every qubit: 1e-5.
set -u
W=$(pwd); TQ=${TOQB_DIR:-$W/TOQB}; PO=${PSFOS_DIR:-$W/psf-os}; OUT=${OUT:?set OUT}; CPU=${CPU:-$W/answers_cpu.json}
[ -d "$TQ" ] && [ -d "$PO" ] && [ -f "$CPU" ] || { echo "STOP: TOQB, psf-os or answers_cpu.json missing"; exit 1; }
[ -e "$OUT" ] && { echo "STOP: $OUT exists"; exit 1; }
mkdir -p "$OUT"
export PYTHONPATH="$PO:$TQ" PYTHONWARNINGS=ignore
cd "$TQ" || exit 1
python -m pytest -q tests/test_ising2d_answers.py tests/test_du_answers.py > "$OUT/check_tests.log" 2>&1
tail -1 "$OUT/check_tests.log" | grep -q " passed" && ! tail -1 "$OUT/check_tests.log" | grep -q "failed" || { echo "STOP: tests (see check_tests.log)"; exit 1; }
{ echo "toqb $( (git log --oneline -1 2>/dev/null || cat COMMIT.txt) | cut -c1-60)"; echo "cpu $(sha256sum "$CPU")";
  echo "script $(sha256sum gpu/ising2d_answers.py)"; nvidia-smi --query-gpu=name,memory.total --format=csv,noheader;
  echo "start $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')"; } | tee "$OUT/times.txt"
python - "$OUT" "$CPU" <<'PY' 2>&1 | tee -a "$OUT/progress.txt"
import json, os, sys, hashlib
import numpy as np
sys.path.insert(0, "gpu")
import ising2d_answers as A
from psf_os import ising2d as I
out, cpu = sys.argv[1], json.load(open(sys.argv[2]))
checks = {}
log = lambda s: print(s, flush=True)
def stop(m):
    json.dump(checks, open(os.path.join(out, "checks.json"), "w"), indent=1); print("STOP:", m); sys.exit(1)
g = A.run([5], "cupy", "single")["5"]["z"]
d = float(np.max(np.abs(np.array(g) - np.array(cpu["answers"]["5"]))))
checks["K1"] = dict(max_diff=d, ok=d <= 1e-4); log(f"K1 t 5: max |GPU - CPU| {d:.2e}")
if not checks["K1"]["ok"]: stop("K1")
sizes = [len(I.cone(q, 6)[0]) for q in I.QUBITS]
big = {I.QUBITS[i] for i in np.argsort(sizes)[-5:]}
s = A.run([6], "cupy", "single", only=big)["6"]["z"]; dd = A.run([6], "cupy", "double", only=big)["6"]["z"]
d = max(abs(a - b) for a, b in zip(s, dd) if a is not None)
checks["K2"] = dict(cones=sorted(sizes)[-5:], max_diff=float(d), ok=d <= 1e-4); log(f"K2 cones {sorted(sizes)[-5:]}: max |single - double| {d:.2e}")
if not checks["K2"]["ok"]: stop("K2")
g1 = A.run([1], "cupy", "single")["1"]["z"]
d = float(np.max(np.abs(np.array(g1) - np.cos(I.THETA_X))))
checks["K3"] = dict(max_diff=d, ok=d <= 1e-5); log(f"K3 t 1: max |GPU - cos(theta_x)| {d:.2e}")
if not checks["K3"]["ok"]: stop("K3")
res = A.run([6, 7, 8, 9], "cupy", "single", log=log)
json.dump(checks, open(os.path.join(out, "checks.json"), "w"), indent=1)
json.dump(res, open(os.path.join(out, "answers_gpu.json"), "w"))
print("answers_gpu.json sha256", hashlib.sha256(open(os.path.join(out, "answers_gpu.json"), "rb").read()).hexdigest())
PY
[ -f "$OUT/answers_gpu.json" ] || { echo "STOP: no answers (see progress.txt, checks.json)"; exit 1; }
echo "end $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')" | tee -a "$OUT/times.txt"
cd "$W" && python -m zipfile -c "$W/$(basename "$OUT")_answers.zip" "$OUT" && echo "== DONE: $W/$(basename "$OUT")_answers.zip"
