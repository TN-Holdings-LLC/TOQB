# 2026-11-10: the reusable-tree failure ("tuple index out of range" in tree.contract) is worked around by contracting
# with the tree's path (value()); see value() for the check.
"""Exact utility-experiment observables by one reusable tensor-network contraction (home, 2026-11-10; for the pod run
of the weight-17 observables; prototype, not declared).

<0| U^dag P U |0> as one network with fixed index names, built only from the gates inside the observable's backward
light cone (all ZZ rotations commute, so after the last layer the support grows by one edge per ZZ layer; every gate
outside cancels exactly between ket and bra):
  ket: |0> on each cone qubit; per step R_X(theta) (a 2 x 2 matrix, new index), then R_ZZ(-pi/2) on each edge as a
  diagonal 4-index tensor (new indices on both qubits); the observable's Paulis join the
  final ket and bra indices (identity elsewhere: the same index); the bra is the conjugate.
The network's structure does not depend on theta, so the contraction tree is searched once (cotengra) and reused for
every theta; each value is written to the output file as soon as it is computed.

usage: python gpu/utility_tn.py check
       python gpu/utility_tn.py plan OBS [--max-time 60]                (search a tree; print its width and cost)
       python gpu/utility_tn.py run OBS OUT.jsonl [--max-time 600] [--ks 0-16]
OBS: z106_t4 | w10_t5 | w17_t5 | w17b_t5x (Fig. 4a: Y and Z exchanged, five steps then one more R_X layer)
"""
import json
import math
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import utility_exact as UE  # noqa: E402

W17B = {q: ("X" if c == "X" else ("Z" if c == "Y" else "Y")) for q, c in UE.W17.items()}
OBS = {"z106_t4": ({106: "Z"}, 4, False), "w10_t5": (UE.W10, 5, False), "w17_t5": (UE.W17, 5, False),
       "w17b_t5x": (W17B, 5, True)}
# Deeper steps (home, 2026-11-11, depth scan; exact values by gpu/reach_tn.py, sealed): same observables, more steps.
OBS.update({f"z106_t{t}": ({106: "Z"}, t, False) for t in (5, 6, 7, 8)})
OBS.update({"w10_t6": (UE.W10, 6, False), "w10_t7": (UE.W10, 7, False)})


def network(obs, t, extra_rx, edges):
    """(inputs, output, size_dict, slots): inputs are index tuples; slots says which array goes where:
    ("ket0",) / ("rx", conj) / ("zz", conj) / ("pauli", letter)."""
    import rustworkx as rx_
    g = rx_.PyGraph()
    g.add_nodes_from(range(127))
    g.add_edges_from_no_data(edges)
    D = rx_.distance_matrix(g)
    dist = {q: min(D[q][s] for s in obs) for q in range(127)}
    layers = []                                   # time order: ("rx", qubits) / ("zz", edges)
    for s in range(1, t + 1):
        r = t - s                                  # cone radius after this step's ZZ layer, seen from the end
        layers.append(("rx", sorted(q for q in range(127) if dist[q] <= r + 1)))
        layers.append(("zz", [(a, b) for a, b in edges if min(dist[a], dist[b]) <= r]))
    if extra_rx:
        layers.append(("rx", sorted(q for q in range(127) if dist[q] <= 0)))
    qubits = sorted({q for kind, xs in layers for q in (xs if kind == "rx" else [v for e in xs for v in e])}
                    | set(obs))
    inputs, slots = [], []
    for side in ("k", "b"):
        cur = {q: f"{side}{q}_0" for q in qubits}
        n = {q: 0 for q in qubits}
        for q in qubits:
            inputs.append((cur[q],))
            slots.append(("ket0",))
        for kind, xs in layers:
            if kind == "rx":
                for q in xs:
                    n[q] += 1
                    new = f"{side}{q}_{n[q]}"
                    inputs.append((new, cur[q]))
                    slots.append(("rx", side == "b"))
                    cur[q] = new
            else:
                for a, b in xs:              # a 4-index gate tensor (new indices on both qubits; no hyper-edge)
                    n[a] += 1
                    n[b] += 1
                    na, nb = f"{side}{a}_{n[a]}", f"{side}{b}_{n[b]}"
                    inputs.append((na, nb, cur[a], cur[b]))
                    slots.append(("zz", side == "b"))
                    cur[a], cur[b] = na, nb
        if side == "k":
            ket_final = dict(cur)
        else:
            bra_final = dict(cur)
    # join: Pauli on the observable's qubits, identity (one index) elsewhere
    ren = {}
    for q in qubits:
        if q in obs:
            inputs.append((bra_final[q], ket_final[q]))
            slots.append(("pauli", obs[q]))
        else:
            ren[bra_final[q]] = ket_final[q]
    inputs = [tuple(ren.get(i, i) for i in ix) for ix in inputs]
    size = {i: 2 for ix in inputs for i in ix}
    return inputs, (), size, slots, len(qubits)


def arrays(slots, theta):
    rx = np.array([[math.cos(theta / 2), -1j * math.sin(theta / 2)],
                   [-1j * math.sin(theta / 2), math.cos(theta / 2)]])
    d = np.exp(1j * math.pi / 4 * np.array([1, -1, -1, 1]))            # exp(-i theta_J / 2 z z), theta_J = -pi/2
    zz = np.diag(d).reshape(2, 2, 2, 2)                                # (out a, out b, in a, in b)
    out = []
    for sl in slots:
        if sl[0] == "ket0":
            out.append(np.array([1.0 + 0j, 0.0]))
        elif sl[0] == "rx":
            out.append(rx.conj() if sl[1] else rx)
        elif sl[0] == "zz":
            out.append(zz.conj() if sl[1] else zz)
        else:
            out.append(UE.P1[sl[1]])
    return out


def find_tree(inputs, output, size, max_time):
    import cotengra as ctg
    opt = ctg.HyperOptimizer(max_time=max_time, max_repeats=10 ** 6, minimize="combo", progbar=False,
                             parallel=False)
    return opt.search(inputs, output, size)


def value(tree, slots, theta, inputs=None, output=(), size=None):
    """Contract with the searched tree's path. Fix (home VS Claude, 2026-11-10): tree.contract(arrays) and
    array_contract(optimize=tree) stop in cotengra 0.8.3 with "tuple index out of range" inside tensordot on this
    network, while the same tree's path (tree.get_path(), a list of pairs) passed to array_contract gives the exact
    value (6e-15 against utility_exact.tn_value on Z106 t3). The path does not depend on theta: taken once, reused."""
    import cotengra as ctg
    if not hasattr(tree, "_path_cache"):
        tree._path_cache = tree.get_path()
    inputs = inputs if inputs is not None else [tuple(ix) for ix in tree.inputs]
    size = size if size is not None else tree.size_dict
    return complex(ctg.array_contract(arrays(slots, theta), inputs, output, size_dict=size,
                                      optimize=tree._path_cache))


def check():
    edges = UE.eagle_edges()
    worst = 0.0
    for obs, t, ex in (({106: "Z"}, 3, False), ({13: "X", 9: "Y", 8: "Z"}, 2, True), (UE.W10, 2, False),
                       (UE.W10, 3, False), (UE.W10, 5, False)):
        inputs, output, size, slots, nq = network(obs, t, ex, edges)
        # a 10 s search leaves the weight-10 / 5-step tree at width 30 (17 GB, out of memory on a 16 GB PC); 60 s
        # gives width 26 (1 GB, 5 s per value) (home VS Claude, 2026-11-10)
        tree = find_tree(inputs, output, size, 60 if nq > 30 else 10)
        for th in (0.3, 0.9, math.pi / 2):
            a = value(tree, slots, th, inputs, output, size).real
            b = UE.tn_value(obs, edges, th, t, ex)[0] if len(obs) <= 12 else None
            worst = max(worst, abs(a - b))
    print(f"reusable network against utility_exact.tn_value (incl. weight-10 at 5 steps): worst {worst:.2e}")
    return worst < 1e-10


def main():
    cmd = sys.argv[1]
    if cmd == "check":
        sys.exit(0 if check() else 1)
    name = sys.argv[2]
    obs, t, ex = OBS[name]
    edges = UE.eagle_edges()
    inputs, output, size, slots, nq = network(obs, t, ex, edges)
    mt = float(sys.argv[sys.argv.index("--max-time") + 1]) if "--max-time" in sys.argv else (60 if cmd == "plan" else 600)
    t0 = time.time()
    tree = find_tree(inputs, output, size, mt)
    w, c = tree.contraction_width(), math.log10(max(tree.contraction_cost(), 1))
    print(f"{name}: cone {nq} qubits, {len(inputs)} tensors; tree width {w:.1f} (largest intermediate 2^{w:.0f} entries, "
          f"{16 * 2 ** w / 1e9:.1f} GB complex128), cost 10^{c:.1f} flops; search {time.time() - t0:.0f} s", flush=True)
    if cmd == "plan":
        return
    out = sys.argv[3]
    ks = range(17)
    if "--ks" in sys.argv:
        a, b = sys.argv[sys.argv.index("--ks") + 1].split("-")
        ks = range(int(a), int(b) + 1)
    with open(out, "a") as f:
        f.write(json.dumps(dict(obs=name, kind="tree", width=w, log10_cost=c)) + "\n")
        for k in ks:
            t1 = time.time()
            v = value(tree, slots, k * math.pi / 32, inputs, output, size)
            f.write(json.dumps(dict(obs=name, k=k, theta=k * math.pi / 32, re=v.real, im=v.imag,
                                    seconds=round(time.time() - t1, 1))) + "\n")
            f.flush()
            print(f"{name} k {k}: done in {time.time() - t1:.0f} s", flush=True)   # no value printed (sealed)


if __name__ == "__main__":
    main()
