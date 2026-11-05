"""Practice test: the user's circuits, written as a user would, in plain Qiskit from the problems' definitions (no psf-os
code), on Heron r2 labels; then checked on CPU against the sealed bank answers before anything is sent.

  P4 (arXiv 2411.00765, SI Eq. S5): open chain of N = 33 sites, |+> on site 0, Bell pairs on (1, 2), (3, 4), ...;
     t brickwork layers, even pairs first; gate U = e^{-ihZ_a} e^{-iJ ZZ} e^{-ib(X_a + X_b)} e^{-iJ ZZ} e^{-ihZ_a},
     J = pi/4, h = 0.15, b = pi/4 - 0.05 and pi/4 - 0.3; X readout (H, then Z) of every site.
     Chain on labels: row 0 (0..15), bridge 19, row 1 backwards (35..20).
  P5 (Kim et al. 2023 form): the marrakesh lattice of the bank (151 qubits, 166 edges); each step RZZ(-pi/2) on every
     edge, then RX(theta) on every qubit; Z readout.

usage: python gpu/practice_circuits.py OUT_DIR [--check]
"""
import json
import os
import sys

import numpy as np

H, J = 0.15, np.pi / 4
KICKS = {"b0.735": np.pi / 4 - 0.05, "b0.485": np.pi / 4 - 0.3}
P4_TS = [2, 4, 8, 12, 16]
P5_THETAS = {"tx0.4": 0.4, "tx0.8": 0.8, "tx1.0": 1.0}
P5_TS = [2, 4, 6, 8]
CHAIN = list(range(0, 16)) + [19] + list(range(35, 19, -1))
BANK = "results/bank-2026-11-04"


def p4(t, b, chain=CHAIN, h=H):
    from qiskit import QuantumCircuit
    n = len(chain)
    qc = QuantumCircuit(max(chain) + 1, n)
    s = chain  # site k -> label
    qc.h(s[0])
    for i in range(1, n - 1, 2):
        qc.h(s[i])
        qc.cx(s[i], s[i + 1])
    for k in range(t):
        for i in range(k % 2, n - 1, 2):
            a, c = s[i], s[i + 1]
            qc.rz(2 * h, a)
            qc.rzz(2 * J, a, c)
            qc.rx(2 * b, a)
            qc.rx(2 * b, c)
            qc.rzz(2 * J, a, c)
            qc.rz(2 * h, a)
    for k in range(n):
        qc.h(s[k])
    for k in range(n):
        qc.measure(s[k], k)
    return qc


def p5(t, theta, qubits, edges):
    from qiskit import QuantumCircuit
    qc = QuantumCircuit(max(qubits) + 1, len(qubits))
    for _ in range(t):
        for a, c in edges:
            qc.rzz(-np.pi / 2, a, c)
        for q in qubits:
            qc.rx(theta, q)
    for k, q in enumerate(qubits):
        qc.measure(q, k)
    return qc


def lattice():
    a = json.load(open(f"{BANK}/p5_marrakesh/answers_cpu.json"))
    return a["qubits"], [tuple(e) for e in a["edges"]]


def answers():
    """{tag: {label: exact <Z> of the measured qubit}} from the sealed bank files."""
    out = {}
    du = json.load(open(f"{BANK}/pod/du_bank/answers.json"))
    for kt, b in KICKS.items():
        x = du[f"h0.15_b{b:.6f}"]["x"]
        for t in P4_TS:
            out[f"p4_{kt}_t{t:02d}"] = {str(CHAIN[k]): float(x[t][k]) for k in range(len(CHAIN))}
    qs, _ = lattice()
    cpu = json.load(open(f"{BANK}/p5_marrakesh/answers_cpu.json"))["answers"]
    pod = json.load(open(f"{BANK}/pod/p5_marrakesh/answers_C.json"))
    for kt, th in P5_THETAS.items():
        key = f"{th:.6f}"
        for t in P5_TS:
            z = (cpu[key] if str(t) in cpu[key] else pod[key])[str(t)]["z"]
            out[f"p5_{kt}_t{t}"] = {str(q): float(v) for q, v in zip(qs, z) if v is not None}
    return out


def check():
    """CPU checks of the user circuits against the sealed answers (shallow depths, exact simulation)."""
    from qiskit.quantum_info import Pauli, Statevector
    from qiskit_aer import AerSimulator
    ans = answers()
    worst = {}
    # P4: matrix-product-state simulation of the whole 33-site chain (sites relabelled 0..32 so the chain is linear)
    sim = AerSimulator(method="matrix_product_state")
    n = len(CHAIN)
    for kt, b in KICKS.items():
        for t in (2, 4, 8):
            qc = p4(t, b, chain=list(range(n))).remove_final_measurements(inplace=False)
            for k in range(n):
                qc.save_expectation_value(Pauli("Z"), [k], label=f"z{k}")
            r = sim.run(qc).result().data()
            a = ans[f"p4_{kt}_t{t:02d}"]
            worst[f"p4_{kt}_t{t:02d}"] = max(abs(float(r[f"z{k}"]) - a[str(CHAIN[k])]) for k in range(n))
    # P5: the causal cone of radius t - 1 around sample qubits, statevector, t = 2, 3 (cone <= 20 qubits)
    qs, es = lattice()
    adj = {}
    for a, c in es:
        adj.setdefault(a, set()).add(c)
        adj.setdefault(c, set()).add(a)
    for kt, th in P5_THETAS.items():
        for t in (2, 3):
            cpu = json.load(open(f"{BANK}/p5_marrakesh/answers_cpu.json"))["answers"][f"{th:.6f}"][str(t)]["z"]
            a = {str(q): v for q, v in zip(qs, cpu) if v is not None}
            dev = 0.0
            for q in qs[::10]:
                ball, fr = {q}, {q}
                for _ in range(t - 1):
                    fr = {y for x in fr for y in adj[x]} - ball
                    ball |= fr
                cq = sorted(ball)
                ce = [e for e in es if e[0] in ball and e[1] in ball]
                idx = {x: i for i, x in enumerate(cq)}
                small = p5(t, th, list(range(len(cq))), [(idx[x], idx[y]) for x, y in ce])
                sv = Statevector(small.remove_final_measurements(inplace=False))
                n = len(cq)
                z = float(sv.expectation_value(Pauli("I" * (n - 1 - idx[q]) + "Z" + "I" * idx[q])).real)
                dev = max(dev, abs(z - a[str(q)]))
            worst[f"p5_{kt}_t{t}"] = dev
    return worst


def main(out):
    from qiskit import qpy
    if os.path.exists(out):
        raise SystemExit(f"STOP: {out} exists")
    os.makedirs(out)
    qs, es = lattice()
    files = []
    for kt, b in KICKS.items():
        for t in P4_TS:
            files.append((f"p4_{kt}_t{t:02d}", p4(t, b)))
    for kt, th in P5_THETAS.items():
        for t in P5_TS:
            files.append((f"p5_{kt}_t{t}", p5(t, th, qs, es)))
    for tag, qc in files:
        with open(os.path.join(out, tag + ".qpy"), "wb") as f:
            qpy.dump(qc, f)
    json.dump(answers(), open(os.path.join(out, "answers.json"), "w"))
    print(f"{len(files)} circuits and answers.json written to {out}")


if __name__ == "__main__":
    if "--check" in sys.argv:
        w = check()
        print(json.dumps({k: round(v, 6) for k, v in w.items()}, indent=1))
        print("max deviation", max(w.values()))
    else:
        main(sys.argv[1])
