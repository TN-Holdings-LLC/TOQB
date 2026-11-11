"""Classical verification cost of the 1D Fermi-Hubbard Trotter circuit (workplace, 2026-11-11; for a POD).

The circuit is exactly the one a device would run (interleaved Jordan-Wigner, fermionic swaps; `hub_count.py`,
checked exact in `hub_check.py`): Neel-like start (site i holds up if i is even, down if odd; half filling),
U = 4 J, dt = 0.25 / J, first-order Trotter, `steps` steps. It is simulated by
  aer   : Aer matrix_product_state without truncation (the reference where it finishes);
  quimb : quimb CircuitMPS with a bond cap chi (cutoff 1e-12), reporting the discarded weight.
Per case the report gives time, peak bond dimension, quimb's error estimate, the conserved checks (sum <Z> = 0 at
half filling, sum over up modes - sum over down modes = 0) and, between cases of the same (L, steps), the largest
difference of the per-mode <Z>. **The per-mode <Z> values themselves go only to VALUES_OUT** (they are a future
declaration's answers; never put them in a report).

Kit d (2026-11-11): runs of gates on the same qubit pair are merged into single two-qubit unitaries before
simulation (`blocks`), so truncation happens once per block (about a third as often as per CX); rows carry kit="d".

usage: python hub_cost.py L STEPS METHOD [CHI] REPORT.jsonl VALUES_OUT.npz [--threads N]
"""
import argparse
import json
import os
import resource
import time

import numpy as np

J, U, DT = 1.0, 4.0, 0.25


def circuit(L, steps):
    from qiskit import QuantumCircuit, transpile
    from qiskit.circuit.library import XXPlusYYGate
    n = 2 * L
    qc = QuantumCircuit(n)
    for i in range(L):
        qc.x(2 * i + (i % 2))
    for _ in range(steps):
        for i in range(L):
            qc.rzz(U * DT / 2, 2 * i, 2 * i + 1)
            qc.rz(-U * DT / 2, 2 * i)
            qc.rz(-U * DT / 2, 2 * i + 1)
        for par in (0, 1):
            for i in range(par, L - 1, 2):
                qc.swap(2 * i + 1, 2 * i + 2)
                qc.cz(2 * i + 1, 2 * i + 2)
                qc.append(XXPlusYYGate(-2 * J * DT), [2 * i, 2 * i + 1])
                qc.append(XXPlusYYGate(-2 * J * DT), [2 * i + 2, 2 * i + 3])
                qc.swap(2 * i + 1, 2 * i + 2)
                qc.cz(2 * i + 1, 2 * i + 2)
    return qc


def blocks(qc):
    """The circuit with every run of gates on the same two qubits merged into one 2x2-qubit unitary (and single-qubit
    gates absorbed into them): each MPS method then truncates once per merged block, not once per CX (2026-11-11d)."""
    from qiskit.transpiler import PassManager
    from qiskit.transpiler.passes import Collect2qBlocks, ConsolidateBlocks
    return PassManager([Collect2qBlocks(), ConsolidateBlocks(force_consolidate=True)]).run(qc)


def cx_count(qc):
    from qiskit import transpile
    return int(transpile(qc, basis_gates=["cx", "u", "rz", "x"], optimization_level=1).count_ops().get("cx", 0))


def run_aer(qc, threads):
    from qiskit.quantum_info import Pauli
    from qiskit_aer import AerSimulator
    c = qc.copy()
    for k in range(c.num_qubits):
        c.save_expectation_value(Pauli("Z"), [k], label=f"z{k}")
    sim = AerSimulator(method="matrix_product_state", max_parallel_threads=threads,
                       mps_log_data=True)
    r = sim.run(c, shots=1).result()
    d = r.data()
    z = np.array([float(np.real(d[f"z{k}"])) for k in range(c.num_qubits)])
    log = r.results[0].metadata.get("MPS_log_data", "")
    bonds = [int(x) for x in __import__("re").findall(r"BD=\[([0-9 ,]+)\]", str(log))[-1].replace(",", " ").split()] \
        if "BD=" in str(log) else []
    return z, (max(bonds) if bonds else None), None


def run_quimb(qc, chi):
    import quimb.tensor as qtn
    n = qc.num_qubits
    circ = qtn.CircuitMPS(n, max_bond=chi, cutoff=1e-12)
    for ins in qc.data:
        qs = [qc.find_bit(q).index for q in ins.qubits]
        G = ins.operation.to_matrix()
        circ.apply_gate_raw(G, tuple(reversed(qs)))   # qiskit little-endian -> quimb big-endian
    psi = circ.psi
    Z = np.diag([1.0, -1.0])
    z = np.array([float(np.real(psi.local_expectation(Z, k))) for k in range(n)])
    err = circ.error_estimate() if hasattr(circ, "error_estimate") else None
    return z, psi.max_bond(), err


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("L", type=int)
    ap.add_argument("steps", type=int)
    ap.add_argument("method", choices=("aer", "quimb"))
    ap.add_argument("chi", type=int, nargs="?", default=0)
    ap.add_argument("report")
    ap.add_argument("values_out")
    ap.add_argument("--threads", type=int, default=os.cpu_count())
    a = ap.parse_args()
    logical = circuit(a.L, a.steps)
    qc = blocks(logical)
    t0 = time.time()
    z, bond, err = run_aer(qc, a.threads) if a.method == "aer" else run_quimb(qc, a.chi)
    sec = time.time() - t0
    up, dn = z[0::2].sum(), z[1::2].sum()
    row = dict(L=a.L, qubits=2 * a.L, steps=a.steps, Jt=a.steps * DT, method=a.method, chi=a.chi or None,
               seconds=round(sec, 1), peak_rss_gb=round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6, 2),
               max_bond=bond, error_estimate=err, check_sum_z=float(z.sum()), check_sz=float(up - dn),
               cx_transpiled=cx_count(logical), two_qubit_blocks=sum(1 for i in qc.data if len(i.qubits) == 2),
               kit="d")
    key = f"L{a.L}_s{a.steps}_{a.method}{a.chi or ''}"
    old = dict(np.load(a.values_out)) if os.path.exists(a.values_out) else {}
    old[key] = z
    np.savez(a.values_out, **old)
    others = {k: v for k, v in old.items() if k.startswith(f"L{a.L}_s{a.steps}_") and k != key}
    row["max_diff_to"] = {k: float(np.max(np.abs(v - z))) for k, v in others.items()}
    with open(a.report, "a") as f:
        f.write(json.dumps(row) + "\n")
    print(json.dumps(row))


if __name__ == "__main__":
    main()
