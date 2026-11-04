"""Practice test on ibm_fez: the same user circuits as gpu/practice_circuits.py (P4 unchanged), with P5 on fez's own
lattice of 3 November (153 qubits, 170 edges; failed qubit 72 and coupler (32, 33), as fetched on 4 November).

Answers (sealed on 3 November): t 1-5 results/bank-2026-11-04/p5_fez/answers_cpu.json (same lattice and values as
results/kim-e-2026-11-03/X/answers_cpu.json), t 6-8 results/kim-e-2026-11-03/X/answers_pod/answers_C.json
(SHA-256 4c0b7ce9..., commit 3087056).

usage: python gpu/practice_fez.py OUT_DIR [--check]
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import practice_circuits as PC  # noqa: E402

CPU = "results/bank-2026-11-04/p5_fez/answers_cpu.json"
POD = "results/kim-e-2026-11-03/X/answers_pod/answers_C.json"


def lattice():
    a = json.load(open(CPU))
    return a["qubits"], [tuple(e) for e in a["edges"]]


def answers():
    out = {k: v for k, v in PC.answers().items() if k.startswith("p4_")}  # P4: the same sealed answers
    qs, _ = lattice()
    cpu = json.load(open(CPU))["answers"]
    pod = json.load(open(POD))
    for kt, th in PC.P5_THETAS.items():
        key = f"{th:.6f}"
        for t in PC.P5_TS:
            z = (cpu[key] if str(t) in cpu[key] else pod[key])[str(t)]["z"]
            out[f"p5_{kt}_t{t}"] = {str(q): float(v) for q, v in zip(qs, z) if v is not None}
    return out


def check():
    """P5 on fez's lattice: causal cones of sample qubits, statevector, t 2 and 3, against the sealed answers."""
    from qiskit.quantum_info import Pauli, Statevector
    qs, es = lattice()
    cpu = json.load(open(CPU))["answers"]
    adj = {}
    for a, c in es:
        adj.setdefault(a, set()).add(c)
        adj.setdefault(c, set()).add(a)
    worst = {}
    for kt, th in PC.P5_THETAS.items():
        for t in (2, 3):
            ans = {q: v for q, v in zip(qs, cpu[f"{th:.6f}"][str(t)]["z"]) if v is not None}
            dev = 0.0
            for q in qs[::10]:
                ball, fr = {q}, {q}
                for _ in range(t - 1):
                    fr = {y for x in fr for y in adj[x]} - ball
                    ball |= fr
                cq = sorted(ball)
                idx = {x: i for i, x in enumerate(cq)}
                small = PC.p5(t, th, list(range(len(cq))), [(idx[x], idx[y]) for x, y in es if x in ball and y in ball])
                sv = Statevector(small.remove_final_measurements(inplace=False))
                n = len(cq)
                z = float(sv.expectation_value(Pauli("I" * (n - 1 - idx[q]) + "Z" + "I" * idx[q])).real)
                dev = max(dev, abs(z - ans[q]))
            worst[f"p5_{kt}_t{t}"] = dev
    return worst


def main(out):
    from qiskit import qpy
    if os.path.exists(out):
        raise SystemExit(f"STOP: {out} exists")
    os.makedirs(out)
    qs, es = lattice()
    files = [(f"p4_{kt}_t{t:02d}", PC.p4(t, b)) for kt, b in PC.KICKS.items() for t in PC.P4_TS]
    files += [(f"p5_{kt}_t{t}", PC.p5(t, th, qs, es)) for kt, th in PC.P5_THETAS.items() for t in PC.P5_TS]
    for tag, qc in files:
        with open(os.path.join(out, tag + ".qpy"), "wb") as f:
            qpy.dump(qc, f)
    json.dump(answers(), open(os.path.join(out, "answers.json"), "w"))
    print(f"{len(files)} circuits and answers.json written to {out}")


if __name__ == "__main__":
    if "--check" in sys.argv:
        w = check()
        print(json.dumps({k: float(f"{v:.2e}") for k, v in w.items()}), "max", max(w.values()))
    else:
        main(sys.argv[1])
