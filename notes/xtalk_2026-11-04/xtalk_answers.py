"""Sealed answers for the crosstalk job (draft; not declared): per qubit <Z_q> (P5's causal cone, kim.answers) and,
for every lattice edge (a, b), the triple (<Z_a>, <Z_b>, <Z_a Z_b>) from a statevector of the union of the two causal
cones (the correlations note's method), for theta 0.4 and 0.8 at t = 1..5. Both arms have the same answers (the RZZs
commute; psf-os tests/test_crosstalk2d.py). A pair whose union has more than MAXQ qubits is left unanswered and counted.

usage: PYTHONPATH=<psf-os> python notes/xtalk_2026-11-04/xtalk_answers.py BUILD_OUT ANSWERS.json [--tmax 5] [--maxq 24]
"""
import argparse
import json
import os
import time

from psf_os import kim as K


def pair_triple(edges, a, b, theta, t, maxq):
    from qiskit import QuantumCircuit
    from qiskit.quantum_info import Pauli
    from qiskit_aer import AerSimulator
    u = sorted(set(K.ball(edges, a, max(t - 1, 0))) | set(K.ball(edges, b, max(t - 1, 0))))
    if len(u) > maxq:
        return None, len(u)
    s = set(u)
    ue = [e for e in edges if e[0] in s and e[1] in s]
    idx = {p: k for k, p in enumerate(u)}
    n = len(u)
    qc = QuantumCircuit(n)
    for op in K.ops(u, ue, theta, t):
        if op[0] == "cz":
            qc.cz(idx[op[1]], idx[op[2]])
        else:
            getattr(qc, op[0])(op[1], idx[op[2]])

    def P(qs):
        lab = ["I"] * n
        for q in qs:
            lab[n - 1 - idx[q]] = "Z"
        return Pauli("".join(lab))
    for lab, qs in (("za", [a]), ("zb", [b]), ("zz", [a, b])):
        qc.save_expectation_value(P(qs), list(range(n)), label=lab)
    d = AerSimulator(method="statevector", precision="double").run(qc).result().data(0)
    return (float(d["za"]), float(d["zb"]), float(d["zz"])), n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("build")
    ap.add_argument("out")
    ap.add_argument("--tmax", type=int, default=5)
    ap.add_argument("--maxq", type=int, default=24)
    ap.add_argument("--thetas", default="0.4,0.8")
    a = ap.parse_args()
    if os.path.exists(a.out):
        raise SystemExit(f"STOP: {a.out} exists")
    runs = os.path.join(a.build, "V", "runs")
    rec = json.load(open(os.path.join(runs, sorted(f for f in os.listdir(runs) if f.startswith("pxtalk0"))[0])))
    qubits, edges = rec["qubits"], [tuple(e) for e in rec["edges"]]
    out = dict(device=rec["device"], qubits=qubits, edges=[list(e) for e in edges], maxq=a.maxq, answers={})
    for th in [float(x) for x in a.thetas.split(",")]:
        out["answers"][f"{th:g}"] = {}
        for t in range(1, a.tmax + 1):
            t0 = time.time()
            z = K.answers(qubits, edges, th, t, max_qubits=a.maxq)
            pairs, skipped, big = {}, 0, 0
            for e in edges:
                tr, m = pair_triple(edges, e[0], e[1], th, t, a.maxq)
                big = max(big, m)
                if tr is None:
                    skipped += 1
                else:
                    pairs[f"{e[0]},{e[1]}"] = list(tr)
            out["answers"][f"{th:g}"][str(t)] = dict(z=z["z"], cone_max=z["cone_max"], pairs=pairs,
                                                     pairs_skipped=skipped, union_max=big)
            print(f"theta {th:g} t {t}: cone max {z['cone_max']}, pairs {len(pairs)}/{len(edges)} "
                  f"(union max {big}), {time.time() - t0:.0f} s", flush=True)
    json.dump(out, open(a.out, "w"))


if __name__ == "__main__":
    main()
