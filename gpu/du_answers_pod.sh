#!/bin/bash
# P4 stage 2b answers on a pod (prereg/drafts-2026-11-03/du_stage2_note.md): N = 33 chain, t <= 16, by statevector in
# single precision on one GPU with 80 GB or more (2^33 amplitudes = 64 GB), after three checks of the GPU code.
# Needs TOQB and psf-os side by side in the working folder, Python with qiskit, numpy and cupy (cupy-cuda12x). From
# /workspace:
#   pip install "qiskit==2.5.2" cupy-cuda12x pytest
#   OUT=/workspace/du2 nohup bash TOQB/gpu/du_answers_pod.sh > du2.txt 2>&1 &
# STOP (no answer is written) if a check fails:
#   C1 GPU = numpy (N = 21, t <= 10, b = pi/4, pi/4 - 0.1, pi/4 - 0.2): single 1e-4, double 1e-10, every site;
#   C2 single = double on the GPU (N = 31, t <= 14, the two off-point b): 1e-4;
#   C3 the controls at N = 33 equal the closed form (psf_os.dual.exact; h = 0 and 0.15 at b = pi/4): 1e-4; norm 1e-4.
set -u
W=$(pwd); TQ=${TOQB_DIR:-$W/TOQB}; PO=${PSFOS_DIR:-$W/psf-os}; OUT=${OUT:?set OUT}
[ -d "$TQ" ] && [ -d "$PO" ] || { echo "STOP: TOQB or psf-os missing"; exit 1; }
[ -e "$OUT" ] && { echo "STOP: $OUT exists"; exit 1; }
[ -n "${VENV_ACT:-}" ] && . "$VENV_ACT"
mkdir -p "$OUT"
export PYTHONPATH="$PO:$TQ" PYTHONWARNINGS=ignore
cd "$TQ" || exit 1
python -m pytest -q tests/test_du_answers.py > "$OUT/check_tests.log" 2>&1
tail -1 "$OUT/check_tests.log" | grep -q " passed" && ! tail -1 "$OUT/check_tests.log" | grep -q "failed" || { echo "STOP: tests (see check_tests.log)"; exit 1; }
{ echo "toqb $( (git log --oneline -1 2>/dev/null || cat COMMIT.txt) | cut -c1-60)"; echo "note $(sha256sum prereg/drafts-2026-11-03/du_stage2_note.md)";
  echo "script $(sha256sum gpu/du_answers.py)"; nvidia-smi --query-gpu=name,memory.total --format=csv,noheader;
  echo "start $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')"; } | tee "$OUT/times.txt"
python - "$OUT" <<'EOF' 2>&1 | tee -a "$OUT/progress.txt"
import json, os, sys, hashlib
import numpy as np
sys.path.insert(0, "gpu")
import du_answers as A
from psf_os import dual as DU
out = sys.argv[1]
P4, OFF = np.pi / 4, (np.pi / 4 - 0.1, np.pi / 4 - 0.2)
checks = {}
def stop(msg):
    json.dump(checks, open(os.path.join(out, "checks.json"), "w"), indent=1)
    print("STOP:", msg); sys.exit(1)
# C1
d1 = []
for b in (P4,) + OFF:
    for prec, tol in (("single", 1e-4), ("double", 1e-10)):
        g = A.run(21, 10, 0.15, b, "cupy", prec)
        c = A.run(21, 10, 0.15, b, "numpy", prec)
        d = float(np.max(np.abs(np.array(g["x"]) - np.array(c["x"]))))
        d1.append(dict(b=b, precision=prec, max_diff=d, tol=tol, ok=d <= tol))
        print(f"C1 b {b:.6f} {prec}: max |GPU - numpy| {d:.2e}", flush=True)
checks["C1"] = d1
if not all(x["ok"] for x in d1): stop("C1")
# C2
d2 = []
for b in OFF:
    s = A.run(31, 14, 0.15, b, "cupy", "single"); d = A.run(31, 14, 0.15, b, "cupy", "double")
    m = float(np.max(np.abs(np.array(s["x"]) - np.array(d["x"]))))
    d2.append(dict(b=b, max_diff=m, tol=1e-4, ok=m <= 1e-4, seconds=[s["seconds"], d["seconds"]]))
    print(f"C2 b {b:.6f}: max |single - double| {m:.2e}", flush=True)
checks["C2"] = d2
if not all(x["ok"] for x in d2): stop("C2")
# main + C3
log = lambda s: print(s, flush=True)
res = {}
for h, b in ((0.0, P4), (0.15, P4)) + tuple((0.15, x) for x in OFF):
    res[f"h{h:g}_b{b:.6f}"] = A.run(33, 16, h, b, "cupy", "single", log=log)
d3 = []
for h in (0.0, 0.15):
    r = res[f"h{h:g}_b{P4:.6f}"]
    m = max(float(np.max(np.abs(np.array(r["x"][t]) - np.array(DU.exact(33, t, h))))) for t in range(17))
    n = float(np.max(np.abs(np.array(r["norm"]) - 1)))
    d3.append(dict(h=h, max_diff=m, norm_diff=n, ok=m <= 1e-4 and n <= 1e-4))
    print(f"C3 h {h}: max |GPU - closed form| {m:.2e}, norm {n:.2e}", flush=True)
for b in OFF:
    n = float(np.max(np.abs(np.array(res[f"h0.15_b{b:.6f}"]["norm"]) - 1)))
    d3.append(dict(b=b, norm_diff=n, ok=n <= 1e-4))
checks["C3"] = d3
if not all(x["ok"] for x in d3): stop("C3")
json.dump(checks, open(os.path.join(out, "checks.json"), "w"), indent=1)
json.dump(res, open(os.path.join(out, "answers.json"), "w"))
print("answers.json sha256", hashlib.sha256(open(os.path.join(out, "answers.json"), "rb").read()).hexdigest())
EOF
[ -f "$OUT/answers.json" ] || { echo "STOP: no answers (see progress.txt, checks.json)"; exit 1; }
echo "end $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')" | tee -a "$OUT/times.txt"
cd "$W" && python -m zipfile -c "$W/du2_answers.zip" "$OUT" && echo "== DONE: $W/du2_answers.zip"
