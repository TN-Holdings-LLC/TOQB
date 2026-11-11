"""Exact values of IBM's 2023 utility observables at deeper steps (home, 2026-11-11): the diagonal light-cone network
of utility_tn_diag, a sliced contraction tree so that the largest intermediate fits a memory budget, values written
to OUT.jsonl one by one and never printed (they may become the sealed answers of a later job).
Checks printed: theta_h = 0 and pi/2 against Aer's stabilizer method on the whole 127-qubit Eagle circuit (Clifford
points); |imag| of every value.
usage: python gpu/reach_tn.py OBS T OUT.jsonl [--extra-rx] [--max-time 300] [--target 27] [--ks 0-16 | 16,0,8,1-7,9-15] [--par 2]
OBS: z62 | z106 | w10 | w17 | w17b; T: number of steps; --target: log2 of the largest intermediate (complex128:
2^27 = 2 GB, 2^29 = 8 GB)."""
import argparse
import json
import math
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import utility_exact as UE  # noqa: E402
import utility_tn as T  # noqa: E402
import utility_tn_diag as WD  # noqa: E402

OBS = {"z62": {62: "Z"}, "z106": {106: "Z"}, "w10": UE.W10, "w17": UE.W17, "w17b": T.W17B}


def stabilizer_value(obs, t, extra_rx, theta, edges):
    """<P> on the full 127-qubit Eagle circuit by Aer's stabilizer method (theta = 0 or pi/2 only)."""
    from qiskit import QuantumCircuit
    from qiskit.quantum_info import Pauli
    from qiskit_aer import AerSimulator
    qc = QuantumCircuit(127)

    def rx_layer():
        if abs(theta - math.pi / 2) < 1e-12:
            for q in range(127):
                qc.sx(q)                       # R_X(pi/2) up to a global phase
        elif abs(theta) > 1e-12:
            raise ValueError("stabilizer check only at theta 0 or pi/2")
    for _ in range(t):
        rx_layer()
        for a, b in edges:
            qc.sdg(a); qc.sdg(b); qc.cz(a, b)  # R_ZZ(-pi/2) up to a global phase
    if extra_rx:
        rx_layer()
    label = ["I"] * 127
    for q, c in obs.items():
        label[126 - q] = c
    qc.save_expectation_value(Pauli("".join(label)), list(range(127)), label="p")
    return float(np.real(AerSimulator(method="stabilizer").run(qc, shots=1).result().data()["p"]))


def sliced_contract(arrays, inputs, output, size, tree):
    """Sum over the sliced indices by hand (tree.contract fails on hyper-edges, as in utility_tn): fix each sliced
    index in every tensor that carries it, then contract the rest with the tree's path."""
    import itertools
    import cotengra as ctg
    sl = list(tree.sliced_inds)
    path = tree.get_path()
    red = [tuple(i for i in ix if i not in sl) for ix in inputs]
    rsize = {i: d for i, d in size.items() if i not in sl}
    total = 0j
    for bits in itertools.product((0, 1), repeat=len(sl)):
        fix = dict(zip(sl, bits))
        arrs = []
        for arr, ix in zip(arrays, inputs):
            if any(i in fix for i in ix):
                arr = arr[tuple(fix.get(i, slice(None)) for i in ix)]
            arrs.append(arr)
        total += complex(ctg.array_contract(arrs, red, output, size_dict=rsize, optimize=path))
    return total


def ks_of(s):
    """'0-16' or a comma list of numbers and ranges in the order to compute, e.g. '16,0,8,1-7,9-15'."""
    out = []
    for part in s.split(","):
        a, b = (part.split("-") + [part])[:2]
        out += [k for k in range(int(a), int(b) + 1) if k not in out]
    return out


def main():
    import cotengra as ctg
    ap = argparse.ArgumentParser()
    ap.add_argument("obs", choices=sorted(OBS))
    ap.add_argument("t", type=int)
    ap.add_argument("out")
    ap.add_argument("--extra-rx", action="store_true")
    ap.add_argument("--max-time", type=float, default=300)
    ap.add_argument("--target", type=int, default=27)
    ap.add_argument("--ks", default="0-16")
    ap.add_argument("--par", type=int, default=2)
    a = ap.parse_args()
    edges = UE.eagle_edges()
    obs = OBS[a.obs]
    name = f"{a.obs}_t{a.t}" + ("x" if a.extra_rx else "")
    inputs, output, size, slots, nq = WD.network_diag(obs, a.t, a.extra_rx, edges)
    t0 = time.time()
    opt = ctg.HyperOptimizer(methods=["kahypar", "greedy"], max_time=a.max_time, max_repeats=10 ** 6,
                             minimize="flops", slicing_reconf_opts=dict(target_size=2 ** a.target),
                             parallel=a.par, progbar=False)
    tree = opt.search(inputs, output, size)
    plan = dict(obs=name, kind="tree", cone=nq, tensors=len(inputs), slices=int(tree.multiplicity),
                width=round(tree.contraction_width(), 1), log10_cost=round(math.log10(tree.contraction_cost()), 2),
                target=a.target, search_s=round(time.time() - t0))
    print(json.dumps(plan), flush=True)
    with open(a.out, "a") as f:
        f.write(json.dumps(plan) + "\n")
    for k in ks_of(a.ks):
        th = k * math.pi / 32
        tk = time.time()
        v = sliced_contract(WD.arrays_diag(slots, th), inputs, output, size, tree)
        rec = dict(obs=name, k=k, theta=th, re=v.real, im=v.imag, seconds=round(time.time() - tk, 1))
        with open(a.out, "a") as f:
            f.write(json.dumps(rec) + "\n")
        msg = f"{name} k {k}: {rec['seconds']} s, |imag| {abs(v.imag):.1e}"
        if k in (0, 16):
            s = stabilizer_value(obs, a.t, a.extra_rx, th, edges)
            msg += f"; Clifford check against Aer stabilizer (127 qubits): |diff| {abs(v.real - s):.1e}"
        print(msg, flush=True)


if __name__ == "__main__":
    main()
