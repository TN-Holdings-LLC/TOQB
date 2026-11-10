"""Weight-10, weight-17 and Fig. 4a values with the diagonal (hyper-edge) network, on a PC (home VS Claude,
2026-11-10). One tree per observable (searched once), reused for theta_h = k pi / 32, k = 0..16; each value is
appended to OUT_DIR/<obs>.jsonl as soon as it is computed; no value is printed (sealed).
Checks: weight-10 against utility_exact.tn_value at every k; theta_h = 0 and pi/2 against Aer's stabilizer method on
the whole 127-qubit Eagle circuit (Clifford points).
usage: python local_run.py OUT_DIR"""
import json, math, os, sys, time
import numpy as np
import cotengra as ctg
import utility_tn_diag as WD
import utility_tn as T, utility_exact as UE

out_dir = sys.argv[1]
os.makedirs(out_dir, exist_ok=True)
edges = UE.eagle_edges()
report = []


def stabilizer_value(obs, t, extra_rx, theta):
    """<P> on the full 127-qubit Eagle circuit by Aer's stabilizer method (theta = 0 or pi/2 only)."""
    from qiskit import QuantumCircuit
    from qiskit.quantum_info import Pauli
    from qiskit_aer import AerSimulator
    # Clifford forms (up to global phases): R_X(0) = I, R_X(pi/2) = SX; R_ZZ(-pi/2) = CZ (Sdg x Sdg)
    qc = QuantumCircuit(127)

    def rx_layer():
        if abs(theta - math.pi / 2) < 1e-12:
            for q in range(127):
                qc.sx(q)
        elif abs(theta) > 1e-12:
            raise ValueError("stabilizer check only at theta 0 or pi/2")
    for _ in range(t):
        rx_layer()
        for a, b in edges:
            qc.sdg(a); qc.sdg(b); qc.cz(a, b)
    if extra_rx:
        rx_layer()
    label = ["I"] * 127
    for q, c in obs.items():
        label[126 - q] = c
    qc.save_expectation_value(Pauli("".join(label)), list(range(127)), label="p")
    sim = AerSimulator(method="stabilizer")
    return float(np.real(sim.run(qc, shots=1).result().data()["p"]))


for name in ("w10_t5", "w17_t5", "w17b_t5x"):
    obs, t, ex = T.OBS[name]
    inputs, output, size, slots, nq = WD.network_diag(obs, t, ex, edges)
    t0 = time.time()
    opt = ctg.HyperOptimizer(methods=["kahypar", "greedy"], max_time=180, max_repeats=10 ** 6, minimize="flops",
                             parallel=3, progbar=False)
    tree = opt.search(inputs, output, size)
    path = tree.get_path()
    w, c = tree.contraction_width(), math.log10(tree.contraction_cost())
    line = f"{name}: cone {nq} qubits, {len(inputs)} tensors; tree width {w:.1f}, cost 10^{c:.2f}; search {time.time() - t0:.0f} s"
    print(line, flush=True); report.append(line)
    fn = os.path.join(out_dir, f"{name}.jsonl")
    with open(fn, "w") as f:
        f.write(json.dumps(dict(obs=name, kind="tree", width=w, log10_cost=c, form="diagonal hyper-edge")) + "\n")
    worst_ref, times = 0.0, []
    for k in range(17):
        th = k * math.pi / 32
        tk = time.time()
        v = complex(ctg.array_contract(WD.arrays_diag(slots, th), inputs, output, size_dict=size, optimize=path))
        times.append(time.time() - tk)
        with open(fn, "a") as f:
            f.write(json.dumps(dict(obs=name, k=k, theta=th, re=v.real, im=v.imag, seconds=round(times[-1], 2))) + "\n")
        if name == "w10_t5":
            worst_ref = max(worst_ref, abs(v.real - UE.tn_value(obs, edges, th, t, ex)[0]))
        if k in (0, 16):
            s = stabilizer_value(obs, t, ex, th)
            line = f"{name} k {k}: Clifford check against Aer stabilizer (127 qubits): |diff| {abs(v.real - s):.1e}, |imag| {abs(v.imag):.1e}"
            print(line, flush=True); report.append(line)
    line = f"{name}: 17 values, {min(times):.1f}-{max(times):.1f} s each, {sum(times):.0f} s in all" + \
           (f"; against utility_exact.tn_value at all 17: worst {worst_ref:.1e}" if name == "w10_t5" else "")
    print(line, flush=True); report.append(line)
open(os.path.join(out_dir, "run_report.txt"), "w").write("\n".join(report) + "\n")
