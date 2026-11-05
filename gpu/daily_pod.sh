#!/bin/bash
# The daily pool's sealed answers on a pod (daily/pool.py: D01-D32 and FX-B; FX-A only checked): exact statevector on one
# GPU with 80 GB or more (gpu/daily_answers.py), in the order tests -> checks -> answers -> K4 -> seal. From /workspace:
#   pip install "qiskit==2.5.2" "qiskit-aer==0.18.0" "cupy-cuda12x==14.2.0" pytest
#   OUT=/workspace/daily nohup bash TOQB/gpu/daily_pod.sh > daily.txt 2>&1 < /dev/null &
# STOP (no answer written) if a check fails:
#   K1 GPU single = CPU double (numpy light cones): P32 and B42/B72 at t 1-3, C33 at t 1-4 (every qubit): 1e-4;
#   K2 GPU single = GPU double: P32 whole patch on D13, D09, D21, D08; the five largest cones of D12, D19, D28 (B72) and
#      D23 (B42); C33 at N = 25 to each kick's largest t: 1e-4;
#   K3 known points: theta_x = 0 (F1) and theta = 0 (F2): every <Z> = 1; Clifford points (F1 theta_x = pi/2,
#      theta_z = 0, theta_zz = -pi/2; F2 theta = pi/2) = qiskit.quantum_info.Clifford: 1e-5; F3 at the dual-unitary
#      point b = pi/4 = psf_os.dual.exact: N = 25 double 1e-5, N = 33 single 1e-4;
#   K4 FX-A (F3 h 0.15, b pi/4 - 0.3, t 12) from this run = the answer sealed on 2026-11-04: 1e-4.
set -u
W=$(pwd); TQ=${TOQB_DIR:-$W/TOQB}; PO=${PSFOS_DIR:-$W/psf-os}; OUT=${OUT:?set OUT}
[ -d "$TQ" ] && [ -d "$PO" ] || { echo "STOP: TOQB or psf-os missing"; exit 1; }
[ -e "$OUT" ] && { echo "STOP: $OUT exists"; exit 1; }
mkdir -p "$OUT"
export PYTHONPATH="$PO:$TQ" PYTHONWARNINGS=ignore
cd "$TQ" || exit 1
python -m pytest -q tests/test_daily.py tests/test_du_answers.py > "$OUT/check_tests.log" 2>&1
tail -1 "$OUT/check_tests.log" | grep -q " passed" && ! tail -1 "$OUT/check_tests.log" | grep -q "failed" || { echo "STOP: tests (see check_tests.log)"; exit 1; }
{ echo "toqb $( (git log --oneline -1 2>/dev/null || cat COMMIT.txt) | cut -c1-60)";
  echo "psf-os $( (git -C "$PO" log --oneline -1 2>/dev/null || cat "$PO/COMMIT.txt") | cut -c1-60)";
  echo "pool $(sha256sum daily/pool.py)"; echo "script $(sha256sum gpu/daily_answers.py)";
  echo "sealed FX-A $(sha256sum results/bank-2026-11-04/pod/du_bank/answers.json)";
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
IDS = [e[0] for e in P.POOL] + ["FX-B"]
G = A.groups(IDS)

# K1 GPU single = CPU double from the light cones (numpy)
stage("K1 begin")
k1 = []
for fam, pa, par, pids in G:
    ts = (1, 2, 3, 4) if pa == "C33" else (1, 2, 3)
    if pa in A.FULL:
        g = A.full({t: P.circuit(fam, pa, par, t) for t in ts}, "cupy", "single")["values"]
    else:
        g = {t: A.cones(P.circuit(fam, pa, par, t), "cupy", "single")["values"] for t in ts}
    d = max(worst(g[t], A.cones(P.circuit(fam, pa, par, t), "numpy", "double")["values"]) for t in ts)
    k1.append(dict(family=fam, patch=pa, params=P.params_text(par), ts=list(ts), max_diff=d, ok=d <= 1e-4))
    log(f"K1 {fam} {pa} {P.params_text(par)} t {ts[0]}-{ts[-1]}: max |GPU - CPU| {d:.2e}")
checks["K1"] = k1
if not all(x["ok"] for x in k1): stop("K1")

# K2 GPU single = GPU double
stage("K2 begin")
k2 = []
for pid in ("D13", "D09", "D21", "D08"):
    _, fam, pa, par, t, _, _ = P.entry(pid)
    s = A.full({t: P.circuit(fam, pa, par, t)}, "cupy", "single")["values"][t]
    d = A.full({t: P.circuit(fam, pa, par, t)}, "cupy", "double")["values"][t]
    m = worst(s, d)
    k2.append(dict(what=f"{pid} whole patch", max_diff=m, ok=m <= 1e-4)); log(f"K2 {pid} P32 whole: max |single - double| {m:.2e}")
for pid in ("D12", "D19", "D28", "D23"):
    qc = P.problem_circuit(pid)
    sz = A.cone_sizes(qc)
    big = sorted(sz, key=lambda q: (sz[q], q))[-5:]
    s, d = A.cones(qc, "cupy", "single", only=big)["values"], A.cones(qc, "cupy", "double", only=big)["values"]
    m = worst(s, d)
    k2.append(dict(what=f"{pid} five largest cones", cones=sorted(sz[q] for q in big), max_diff=m, ok=m <= 1e-4))
    log(f"K2 {pid} cones {sorted(sz[q] for q in big)}: max |single - double| {m:.2e}")
for fam, pa, par, pids in G:
    if pa != "C33":
        continue
    ts = list(range(1, max(P.entry(p)[4] for p in pids) + 1))
    cs = {t: P.circuit(fam, pa, par, t, chain=P.PC.CHAIN[:25]) for t in ts}
    s, d = A.full(cs, "cupy", "single")["values"], A.full(cs, "cupy", "double")["values"]
    m = max(worst(s[t], d[t]) for t in ts)
    k2.append(dict(what=f"F3 {P.params_text(par)} N 25 t 1-{ts[-1]}", max_diff=m, ok=m <= 1e-4))
    log(f"K2 F3 {P.params_text(par)} N 25 t 1-{ts[-1]}: max |single - double| {m:.2e}")
checks["K2"] = k2
if not all(x["ok"] for x in k2): stop("K2")

# K3 known points
stage("K3 begin")
from qiskit.quantum_info import Clifford, Pauli, StabilizerState
from psf_os import dual as DU
k3 = []
def gpu(qc, pa):
    if pa in A.FULL:
        return A.full({0: qc}, "cupy", "single")["values"][0]
    return A.cones(qc, "cupy", "single")["values"]
def stab(qc):
    st = StabilizerState(Clifford(qc.remove_final_measurements(inplace=False)))
    n = qc.num_qubits
    return {q: float(st.expectation_value(Pauli("I" * (n - 1 - q) + "Z" + "I" * q))) for q in A.program(qc)[1]}
cases = [("F1 theta_x 0, P32, t 4", P.f1(4, 0.0, 1.0, *P.patch("P32")), "P32", None),
         ("F2 theta 0, P32, t 4", P.f2(4, 0.0, *P.patch("P32")), "P32", None),
         ("F2 theta 0, B42, t 6", P.f2(6, 0.0, *P.patch("B42")), "B42", None),
         ("F2 theta 0, B72, t 6", P.f2(6, 0.0, *P.patch("B72")), "B72", None),
         ("F1 Clifford, P32, t 4", P.f1(4, np.pi / 2, -np.pi / 2, *P.patch("P32"), theta_z=0.0), "P32", "stab"),
         ("F2 Clifford, P32, t 4", P.f2(4, np.pi / 2, *P.patch("P32")), "P32", "stab"),
         ("F2 Clifford, B42, t 6", P.f2(6, np.pi / 2, *P.patch("B42")), "B42", "stab"),
         ("F2 Clifford, B72, t 6", P.f2(6, np.pi / 2, *P.patch("B72")), "B72", "stab")]
for what, qc, pa, kind in cases:
    g = gpu(qc, pa)
    ref = stab(qc) if kind == "stab" else {q: 1.0 for q in g}
    m = worst(g, ref)
    k3.append(dict(what=what, max_diff=m, ok=m <= 1e-5)); log(f"K3 {what}: max |GPU - known| {m:.2e}")
for n, prec, tol in ((25, "double", 1e-5), (33, "single", 1e-4)):
    chain = P.PC.CHAIN[:n]
    r = A.full({t: P.circuit("F3", "C33", dict(h=0.15, b=P.PI4), t, chain=chain) for t in range(1, 9)}, "cupy", prec)["values"]
    m = max(abs(r[t][chain[k]] - DU.exact(n, t, 0.15)[k]) for t in range(1, 9) for k in range(n))
    k3.append(dict(what=f"F3 b pi/4 N {n} {prec} t 1-8 = dual.exact", max_diff=m, ok=m <= tol))
    log(f"K3 F3 dual-unitary point N {n} {prec} t 1-8: max |GPU - exact| {m:.2e}")
checks["K3"] = k3
if not all(x["ok"] for x in k3): stop("K3")
save()

# the answers (FX-A computed with its group for K4, not sealed)
stage("answers begin")
res, _ = A.solve(IDS + ["FX-A"], "cupy", "single", log=log)
stage("answers end")
for pid in IDS:
    s = A.summary(res[pid]["values"])
    log(f"{pid}: {s['n']} qubits{' FAILED' if res[pid]['failed'] else ''}, M {s['M']:+.6f}, "
        f"|<.>| {s['abs_min']:.4f}-{s['abs_max']:.4f}")
checks["norm"] = {p: res[p]["norm"] for p in res if "norm" in res[p]}
checks["failed"] = [p for p in IDS if res[p]["failed"]]

# K4 FX-A against the answer sealed on 2026-11-04
f, key = P.FXA_SEALED
x = json.load(open(f))[key]["x"][12]
m = max(abs(res["FX-A"]["values"][q] - x[k]) for k, q in enumerate(P.PC.CHAIN))
checks["K4"] = dict(sealed=f, key=key, t=12, max_diff=m, ok=m <= 1e-4)
log(f"K4 FX-A t 12: max |this run - sealed 11-04| {m:.2e}")
if not checks["K4"]["ok"]: stop("K4")

# seal
ans = {}
for pid in IDS:
    _, fam, pa, par, t, layers, g = P.entry(pid)
    r = res[pid]
    ans[pid] = dict(family=fam, patch=pa, params=par, params_text=P.params_text(par), t=t, cz_layers=layers, grade=g,
                    readout=P.READOUT[fam], method=r["method"], failed=r["failed"],
                    values={str(q): v for q, v in r["values"].items()},
                    **({"cone": {str(q): c for q, c in r["cone"].items()}} if "cone" in r else {}))
save()
json.dump(ans, open(os.path.join(out, "answers.json"), "w"))
print("answers.json sha256", hashlib.sha256(open(os.path.join(out, "answers.json"), "rb").read()).hexdigest())
PY
[ -f "$OUT/answers.json" ] || { echo "STOP: no answers (see progress.txt, checks.json)"; exit 1; }
echo "end $(TZ=Europe/Zurich date '+%Y-%m-%d %H:%M:%S %Z')" | tee -a "$OUT/times.txt"
cd "$W" && python -m zipfile -c "$W/$(basename "$OUT")_answers.zip" "$OUT" && echo "== DONE: $W/$(basename "$OUT")_answers.zip"
