"""Post hoc, synthetic noise: can plain two-qubit gate noise (no crosstalk) amplify P5's connected correlations at
theta 0.4 and attenuate them at 0.8 / 1.0? P5 step (RZZ(-pi/2) = CZ with RZ(-pi/2) on both ends, then RX(theta)) on the
10-qubit piece of s1_sim; connected C on the distance-1 pairs, t 2-5, under (a) two-qubit depolarizing on every CZ
(correlated), (b) the same strength as independent one-qubit depolarizing on both ends (no correlated part),
usage: python notes/xtalk_2026-11-05/xtalk_sim.py OUT.json P   (P = 0.02 and 0.005 were run, each once) Ratio = mean measured C / mean exact C over pairs with |C| >= 0.01."""
import json, sys
import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import SparsePauliOp
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, depolarizing_error
S = [16, 17, 21, 22, 23, 24, 25, 26, 27, 28]
E = [(16, 23), (24, 25), (17, 27), (21, 22), (23, 24), (25, 26), (27, 28), (22, 23), (26, 27)]
I = {q: i for i, q in enumerate(S)}; N = len(S)
EI = [(I[a], I[b]) for a, b in E]
def lab(qs):
    s = ["I"] * N
    for q in qs: s[N - 1 - q] = "Z"
    return "".join(s)
def run(theta, model, p):
    qc = QuantumCircuit(N)
    for t in range(1, 6):
        for a, b in EI:
            qc.rz(-np.pi / 2, a); qc.rz(-np.pi / 2, b); qc.cz(a, b)
        for q in range(N): qc.rx(theta, q)
        for q in range(N): qc.save_expectation_value(SparsePauliOp(lab([q])), range(N), label=f"{t}_{q}")
        for a, b in EI: qc.save_expectation_value(SparsePauliOp(lab([a, b])), range(N), label=f"{t}_{a}_{b}")
    nm = None
    if model == "dep2":
        nm = NoiseModel(); nm.add_all_qubit_quantum_error(depolarizing_error(p, 2), ["cz"])
    if model == "dep1x2":
        # same infidelity spread as independent one-qubit depolarizing after the CZ (applied via an id-like rz(0)? use explicit ops)
        nm = NoiseModel(); e1 = depolarizing_error(p * 0.6, 1)  # 2q dep p ~ 1q dep 0.6p on each end in average fidelity terms (rough)
        nm.add_all_qubit_quantum_error(e1.tensor(e1), ["cz"])
    sim = AerSimulator(method="density_matrix" if model != "none" else "statevector", noise_model=nm)
    return sim.run(qc).result().data()
out = {}
for theta in (0.4, 0.8, 1.0):
    ex = run(theta, "none", 0)
    for model in ("dep2", "dep1x2"):
        d = run(theta, model, float(sys.argv[2]))
        rows = []
        for t in range(2, 6):
            Cx = [ex[f"{t}_{a}_{b}"] - ex[f"{t}_{a}"] * ex[f"{t}_{b}"] for a, b in EI]
            Cm = [d[f"{t}_{a}_{b}"] - d[f"{t}_{a}"] * d[f"{t}_{b}"] for a, b in EI]
            k = [i for i in range(len(EI)) if abs(Cx[i]) >= 0.01]
            r = np.mean([Cm[i] for i in k]) / np.mean([Cx[i] for i in k]) if k else float("nan")
            mz = np.mean([d[f"{t}_{q}"] for q in range(N)]); mx = np.mean([ex[f"{t}_{q}"] for q in range(N)])
            rows.append((t, round(float(r), 3), round(float(mx), 3), round(float(mz), 3)))
        out[f"{theta} {model}"] = rows
        print(theta, model, rows, flush=True)
json.dump(out, open(sys.argv[1], "w"), indent=1)
