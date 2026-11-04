#!/bin/bash
# Problem bank, P4 (psf_os/dual.py chain, N = 33, t <= 16, h = 0.15) at further kicks b, on one GPU with 80 GB or more,
# after two checks (as gpu/du_answers_pod.sh): C1 GPU = numpy at N = 21, t <= 10 (single 1e-4, double 1e-10);
# C2 single = double at N = 31, t <= 14 (1e-4). From /workspace:
#   OUT=/workspace/du_bank KICKS=0.7353981634,0.4853981634 nohup bash TOQB/gpu/du_bank_pod.sh > du_bank.txt 2>&1 < /dev/null &
set -u
W=$(pwd); TQ=${TOQB_DIR:-$W/TOQB}; PO=${PSFOS_DIR:-$W/psf-os}; OUT=${OUT:?set OUT}; KICKS=${KICKS:?set KICKS}
[ -d "$TQ" ] && [ -d "$PO" ] || { echo "STOP: TOQB or psf-os missing"; exit 1; }
[ -e "$OUT" ] && { echo "STOP: $OUT exists"; exit 1; }
mkdir -p "$OUT"
export PYTHONPATH="$PO:$TQ" PYTHONWARNINGS=ignore
cd "$TQ" || exit 1
python -m pytest -q tests/test_du_answers.py > "$OUT/check_tests.log" 2>&1
tail -1 "$OUT/check_tests.log" | grep -q " passed" && ! tail -1 "$OUT/check_tests.log" | grep -q "failed" || { echo "STOP: tests"; exit 1; }
{ echo "toqb $( (git log --oneline -1 2>/dev/null || cat COMMIT.txt) | cut -c1-60)"; echo "script $(sha256sum gpu/du_answers.py)";
  echo "kicks $KICKS"; nvidia-smi --query-gpu=name,memory.total --format=csv,noheader;
  echo "start $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')"; } | tee "$OUT/times.txt"
python - "$OUT" "$KICKS" <<'PY' 2>&1 | tee -a "$OUT/progress.txt"
import json, os, sys, hashlib
import numpy as np
sys.path.insert(0, "gpu")
import du_answers as A
out, kicks = sys.argv[1], [float(k) for k in sys.argv[2].split(",")]
checks = {}
def stop(m):
    json.dump(checks, open(os.path.join(out, "checks.json"), "w"), indent=1); print("STOP:", m); sys.exit(1)
d1 = []
for b in kicks:
    for prec, tol in (("single", 1e-4), ("double", 1e-10)):
        g, c = A.run(21, 10, 0.15, b, "cupy", prec), A.run(21, 10, 0.15, b, "numpy", prec)
        d = float(np.max(np.abs(np.array(g["x"]) - np.array(c["x"]))))
        d1.append(dict(b=b, precision=prec, max_diff=d, ok=d <= tol)); print(f"C1 b {b:.6f} {prec}: max |GPU - numpy| {d:.2e}", flush=True)
checks["C1"] = d1
if not all(x["ok"] for x in d1): stop("C1")
d2 = []
for b in kicks:
    s, d = A.run(31, 14, 0.15, b, "cupy", "single"), A.run(31, 14, 0.15, b, "cupy", "double")
    m = float(np.max(np.abs(np.array(s["x"]) - np.array(d["x"]))))
    d2.append(dict(b=b, max_diff=m, ok=m <= 1e-4)); print(f"C2 b {b:.6f}: max |single - double| {m:.2e}", flush=True)
checks["C2"] = d2
if not all(x["ok"] for x in d2): stop("C2")
res = {f"h0.15_b{b:.6f}": A.run(33, 16, 0.15, b, "cupy", "single", log=lambda s: print(s, flush=True)) for b in kicks}
for k, r in res.items():
    n = float(np.max(np.abs(np.array(r["norm"]) - 1)))
    checks.setdefault("norm", {})[k] = n
    if n > 1e-4: stop(f"norm {k}")
json.dump(checks, open(os.path.join(out, "checks.json"), "w"), indent=1)
json.dump(res, open(os.path.join(out, "answers.json"), "w"))
print("answers.json sha256", hashlib.sha256(open(os.path.join(out, "answers.json"), "rb").read()).hexdigest())
PY
[ -f "$OUT/answers.json" ] || { echo "STOP: no answers"; exit 1; }
echo "end $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')" | tee -a "$OUT/times.txt"
cd "$W" && python -m zipfile -c "$W/$(basename "$OUT")_answers.zip" "$OUT" && echo "== DONE: $W/$(basename "$OUT")_answers.zip"
