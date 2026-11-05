#!/bin/bash
# The hard problems H01-H03 of the daily pool (daily/pool.py HARD; owner 2026-11-06) on a pod with one GPU of 80 GB or
# more (gpu/daily_answers.py): H01 (B72) and H02 (B102) from light cones (<= 31 qubits at t 6), H03 (P32, t 9) from the
# whole 2^32 state; in the order tests -> checks -> answers, as gpu/daily_scale_pod.sh. From /workspace:
#   OUT=/workspace/hard nohup bash TOQB/gpu/daily_hard_pod.sh > hard.txt 2>&1 < /dev/null &
# STOP (no answer written) if a check fails:
#   K1 GPU single = CPU double at t 1-3 (numpy light cones; P32 against the GPU's whole state): 1e-4;
#   K2 GPU single = GPU double: the five largest cones of H01 and H02; H03's whole state at t 9 (double: 64 GB): 1e-4;
#   K3 theta_x = 0 (F1, B102 t 6 and P32 t 9): every <Z> = 1: 1e-5; Clifford point (theta_x = pi/2, theta_z = 0,
#      theta_zz = -pi/2; B102 t 6 and P32 t 9) = qiskit.quantum_info.Clifford: 1e-5.
# The raw answers (answers_hard.json) are sealed with daily/seal.py (hashes committed first; the owner lets the values
# be released after that, 2026-11-05).
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
IDS = [e[0] for e in P.HARD]

stage("K1 begin")
k1 = []
for fam, pa, par, pids in A.groups(IDS):
    ts = (1, 2, 3)
    cpu = {t: A.cones(P.circuit(fam, pa, par, t), "numpy", "double")["values"] for t in ts}
    if pa in A.FULL:
        gpu = A.full({t: P.circuit(fam, pa, par, t) for t in ts}, "cupy", "single")["values"]
    else:
        gpu = {t: A.cones(P.circuit(fam, pa, par, t), "cupy", "single")["values"] for t in ts}
    d = max(worst(gpu[t], cpu[t]) for t in ts)
    k1.append(dict(family=fam, patch=pa, params=P.params_text(par), ts=list(ts), max_diff=d, ok=d <= 1e-4))
    log(f"K1 {fam} {pa} {P.params_text(par)} t 1-3: max |GPU - CPU| {d:.2e}")
checks["K1"] = k1
if not all(x["ok"] for x in k1): stop("K1")

stage("K2 begin")
k2 = []
for pid in ("H01", "H02"):
    qc = P.problem_circuit(pid)
    sz = A.cone_sizes(qc)
    big = sorted(sz, key=lambda q: (sz[q], q))[-5:]
    s, d = A.cones(qc, "cupy", "single", only=big)["values"], A.cones(qc, "cupy", "double", only=big)["values"]
    m = worst(s, d)
    k2.append(dict(what=f"{pid} five largest cones", cones=sorted(sz[q] for q in big), max_diff=m, ok=m <= 1e-4))
    log(f"K2 {pid} cones {sorted(sz[q] for q in big)}: max |single - double| {m:.2e}")
qc = P.problem_circuit("H03"); t = P.entry("H03")[4]
s = A.full({t: qc}, "cupy", "single")["values"][t]
d = A.full({t: qc}, "cupy", "double")["values"][t]
m = worst(s, d)
k2.append(dict(what="H03 whole state t 9", max_diff=m, ok=m <= 1e-4)); log(f"K2 H03 whole state t 9: max |single - double| {m:.2e}")
checks["K2"] = k2
if not all(x["ok"] for x in k2): stop("K2")

stage("K3 begin")
from qiskit.quantum_info import Clifford, Pauli, StabilizerState
def stab(qc):
    st = StabilizerState(Clifford(qc.remove_final_measurements(inplace=False)))
    n = qc.num_qubits
    return {q: float(st.expectation_value(Pauli("I" * (n - 1 - q) + "Z" + "I" * q))) for q in A.program(qc)[1]}
qs, es = P.patch("B102")
q32, e32 = P.patch("P32")
k3 = []
for what, qc, kind, how in [("F1 theta_x 0, B102, t 6", P.f1(6, 0.0, 1.0, qs, es), None, "cone"),
                            ("F1 theta_x 0, P32, t 9", P.f1(9, 0.0, 1.0, q32, e32), None, "full"),
                            ("F1 Clifford, B102, t 6", P.f1(6, np.pi / 2, -np.pi / 2, qs, es, theta_z=0.0), "stab", "cone"),
                            ("F1 Clifford, P32, t 9", P.f1(9, np.pi / 2, -np.pi / 2, q32, e32, theta_z=0.0), "stab", "full")]:
    g = A.cones(qc, "cupy", "single")["values"] if how == "cone" else A.full({0: qc}, "cupy", "single")["values"][0]
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
          open(os.path.join(out, "answers_hard.json"), "w"))
print("answers_hard.json sha256", hashlib.sha256(open(os.path.join(out, "answers_hard.json"), "rb").read()).hexdigest())
PY
[ -f "$OUT/answers_hard.json" ] || { echo "STOP: no answers (see progress.txt, checks.json)"; exit 1; }
echo "end $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')" | tee -a "$OUT/times.txt"
echo "== DONE: $OUT/answers_hard.json"
