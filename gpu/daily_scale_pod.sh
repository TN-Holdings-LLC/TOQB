#!/bin/bash
# The scale problems S01-S06 of the daily pool (daily/pool.py SCALE, patch B102) on a pod, light cones on one GPU with
# 80 GB or more (gpu/daily_answers.py), in the order tests -> checks -> answers, as gpu/daily_pod.sh. From /workspace:
#   OUT=/workspace/scale nohup bash TOQB/gpu/daily_scale_pod.sh > scale.txt 2>&1 < /dev/null &
# STOP (no answer written) if a check fails:
#   K1 GPU single = CPU double (numpy light cones) at t 1-3 for every family and parameter of SCALE: 1e-4;
#   K2 GPU single = GPU double on the five largest cones of S04 and S05: 1e-4;
#   K3 theta_x = 0 (F1, t 5) and theta = 0 (F2, t 6): every <Z> = 1; Clifford points (F1 theta_x = pi/2, theta_z = 0,
#      theta_zz = -pi/2, t 5; F2 theta = pi/2, t 6) = qiskit.quantum_info.Clifford: 1e-5.
# The raw answers (answers_scale.json) carry the values: they are sealed with daily/seal.py and never committed.
set -u
W=$(pwd); TQ=${TOQB_DIR:-$W/TOQB}; PO=${PSFOS_DIR:-$W/psf-os}; OUT=${OUT:?set OUT}
[ -d "$TQ" ] && [ -d "$PO" ] || { echo "STOP: TOQB or psf-os missing"; exit 1; }
[ -e "$OUT" ] && { echo "STOP: $OUT exists"; exit 1; }
mkdir -p "$OUT"
export PYTHONPATH="$PO:$TQ" PYTHONWARNINGS=ignore
cd "$TQ" || exit 1
python -m pytest -q tests/test_daily.py > "$OUT/check_tests.log" 2>&1
tail -1 "$OUT/check_tests.log" | grep -q " passed" && ! tail -1 "$OUT/check_tests.log" | grep -q "failed" || { echo "STOP: tests (see check_tests.log)"; exit 1; }
{ echo "toqb $( (git log --oneline -1 2>/dev/null || cat COMMIT.txt) | cut -c1-60)";
  echo "psf-os $( (git -C "$PO" log --oneline -1 2>/dev/null || cat "$PO/COMMIT.txt") | cut -c1-60)";
  echo "pool $(sha256sum daily/pool.py)"; echo "script $(sha256sum gpu/daily_answers.py)";
  nvidia-smi --query-gpu=name,memory.total --format=csv,noheader;
  echo "tests $(tail -1 "$OUT/check_tests.log")";
  echo "start $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')"; } | tee "$OUT/times.txt"
python - "$OUT" <<'PY' 2>&1 | tee -a "$OUT/progress.txt"
import hashlib, json, os, subprocess, sys, time
import numpy as np
sys.path.insert(0, "gpu")
import daily_answers as A
from daily import pool as P
out = sys.argv[1]
checks, log = {}, (lambda s: print(s, flush=True))
def now():
    return subprocess.run(["date", "+%Y-%m-%d %H:%M:%S %Z"], env=dict(os.environ, TZ="Europe/Zurich"),
                          capture_output=True, text=True).stdout.strip()
T0 = [time.time()]
def stage(name):
    line = f"{name} {now()} ({time.time() - T0[0]:.0f} s since the last stage)"
    T0[0] = time.time()
    open(os.path.join(out, "times.txt"), "a").write(line + "\n"); log("== " + line)
def save():
    json.dump(checks, open(os.path.join(out, "checks.json"), "w"), indent=1)
def stop(m):
    save(); print("STOP:", m); sys.exit(1)
def worst(a, b):
    return max(abs(a[q] - b[q]) for q in a if a[q] is not None)
IDS = [e[0] for e in P.SCALE]

stage("K1 begin")
k1 = []
for fam, pa, par, pids in A.groups(IDS):
    ts = (1, 2, 3)
    d = max(worst(A.cones(P.circuit(fam, pa, par, t), "cupy", "single")["values"],
                  A.cones(P.circuit(fam, pa, par, t), "numpy", "double")["values"]) for t in ts)
    k1.append(dict(family=fam, patch=pa, params=P.params_text(par), ts=list(ts), max_diff=d, ok=d <= 1e-4))
    log(f"K1 {fam} {pa} {P.params_text(par)} t 1-3: max |GPU - CPU| {d:.2e}")
checks["K1"] = k1
if not all(x["ok"] for x in k1): stop("K1")

stage("K2 begin")
k2 = []
for pid in ("S04", "S05"):
    qc = P.problem_circuit(pid)
    sz = A.cone_sizes(qc)
    big = sorted(sz, key=lambda q: (sz[q], q))[-5:]
    s, d = A.cones(qc, "cupy", "single", only=big)["values"], A.cones(qc, "cupy", "double", only=big)["values"]
    m = worst(s, d)
    k2.append(dict(what=f"{pid} five largest cones", cones=sorted(sz[q] for q in big), max_diff=m, ok=m <= 1e-4))
    log(f"K2 {pid} cones {sorted(sz[q] for q in big)}: max |single - double| {m:.2e}")
checks["K2"] = k2
if not all(x["ok"] for x in k2): stop("K2")

stage("K3 begin")
from qiskit.quantum_info import Clifford, Pauli, StabilizerState
def stab(qc):
    st = StabilizerState(Clifford(qc.remove_final_measurements(inplace=False)))
    n = qc.num_qubits
    return {q: float(st.expectation_value(Pauli("I" * (n - 1 - q) + "Z" + "I" * q))) for q in A.program(qc)[1]}
qs, es = P.patch("B102")
k3 = []
for what, qc, kind in [("F1 theta_x 0, B102, t 5", P.f1(5, 0.0, 1.0, qs, es), None),
                       ("F2 theta 0, B102, t 6", P.f2(6, 0.0, qs, es), None),
                       ("F1 Clifford, B102, t 5", P.f1(5, np.pi / 2, -np.pi / 2, qs, es, theta_z=0.0), "stab"),
                       ("F2 Clifford, B102, t 6", P.f2(6, np.pi / 2, qs, es), "stab")]:
    g = A.cones(qc, "cupy", "single")["values"]
    ref = stab(qc) if kind == "stab" else {q: 1.0 for q in g}
    m = worst(g, ref)
    k3.append(dict(what=what, max_diff=m, ok=m <= 1e-5)); log(f"K3 {what}: max |GPU - known| {m:.2e}")
checks["K3"] = k3
if not all(x["ok"] for x in k3): stop("K3")
save()

stage("answers begin")
res, _ = A.solve(IDS, "cupy", "single", log=log)
stage("answers end")
for pid in IDS:
    s = A.summary(res[pid]["values"])
    log(f"{pid}: {s['n']} qubits{' FAILED' if res[pid]['failed'] else ''}, largest cone {max(res[pid]['cone'].values())}, "
        f"M {s['M']:+.6f}, |<.>| {s['abs_min']:.4f}-{s['abs_max']:.4f}")
checks["failed"] = [p for p in IDS if res[p]["failed"]]
save()
json.dump({p: dict(r, values={str(q): v for q, v in r["values"].items()},
                   cone={str(q): c for q, c in r["cone"].items()}) for p, r in res.items()},
          open(os.path.join(out, "answers_scale.json"), "w"))
print("answers_scale.json sha256", hashlib.sha256(open(os.path.join(out, "answers_scale.json"), "rb").read()).hexdigest())
PY
[ -f "$OUT/answers_scale.json" ] || { echo "STOP: no answers (see progress.txt, checks.json)"; exit 1; }
echo "end $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')" | tee -a "$OUT/times.txt"
echo "== DONE: $OUT/answers_scale.json"
