"""Exploratory study (owner 2026-11-06 04:32 CET, not declared): what a "3D OS" would cost on heavy-hex.

Problem: kicked Ising on an L x M x N cubic lattice (each step RZZ(-pi/2) on every edge, then RX(theta) on every
site; the P5 rules in 3D). Exact answers by statevector (<= 27 qubits).

Two ways to put it on Heron r2 (no calibration number read; coupling graph only):
  formula  the sites on a heavy-hex chain in a fixed order; each step applies its RZZ gates through the fixed
           odd-even transposition swap network on the chain (N rounds bring every pair adjacent once; a gate on a
           lattice edge is fused with that SWAP: RZZ then SWAP = 3 CZ, a bare SWAP = 3 CZ). No search.
  sabre    Qiskit's preset pass manager (optimization level 3, SabreLayout + SabreSwap, fixed seed) on the coupling
           graph: the search-based reference, compile only.
Also the 2D square lattice of similar sizes for comparison.

usage: python os3d_study.py DEVICE_JSON
"""
import itertools
import json
import sys

import numpy as np


def cubic(L, M, N):
    sites = list(itertools.product(range(L), range(M), range(N)))
    idx = {s: i for i, s in enumerate(sites)}
    edges = []
    for (x, y, z) in sites:
        for dx, dy, dz in ((1, 0, 0), (0, 1, 0), (0, 0, 1)):
            t = (x + dx, y + dy, z + dz)
            if t in idx:
                edges.append((idx[(x, y, z)], idx[t]))
    return len(sites), edges


def logical(n, edges, t, theta):
    from qiskit import QuantumCircuit
    qc = QuantumCircuit(n)
    for _ in range(t):
        for a, b in edges:
            qc.rzz(-np.pi / 2, a, b)
        for q in range(n):
            qc.rx(theta, q)
    return qc


def exact_z(qc):
    from qiskit.quantum_info import Statevector
    p = Statevector(qc).probabilities()
    n = qc.num_qubits
    idx = np.arange(len(p))
    return np.array([float(np.sum(p * (1 - 2 * ((idx >> q) & 1)))) for q in range(n)])


def swap_network(n, edges, t, theta):
    """Logical circuit on a line of n positions: per step, odd-even transposition rounds; when the two sites at
    positions (i, i+1) form a lattice edge not yet applied this step, apply RZZ fused with the swap. After each step
    the order is reversed (n rounds reverse it), so the next step runs the network backwards. Returns the circuit on
    positions and the final position of each site."""
    from qiskit import QuantumCircuit
    E = {frozenset(e) for e in edges}
    qc = QuantumCircuit(n)
    pos = list(range(n))  # pos[i] = site at position i
    for _ in range(t):
        done = set()
        for r in range(n):
            for i in range(r % 2, n - 1, 2):
                a, b = pos[i], pos[i + 1]
                e = frozenset((a, b))
                if e in E and e not in done:
                    qc.rzz(-np.pi / 2, i, i + 1)
                    done.add(e)
                qc.swap(i, i + 1)
                pos[i], pos[i + 1] = b, a
        assert done == E, "every edge applied once per step"
        for i in range(n):
            qc.rx(theta, i)  # RX on every position = on every site
    return qc, pos


def chain_on_device(adj, n):
    """A heavy-hex chain of n labels by the fixed snake of rows (the P4 chain extended); None if too long."""
    row = lambda r: set(range(20 * r, 20 * r + 16))
    def down(q, r):
        for b in adj.get(q, ()):
            if b in row(r) or b in row(r - 1):
                continue
            for e in adj.get(b, ()):
                if e in row(r + 1):
                    return b, e
        return None
    path, r, q, right = [], 0, 0, True
    while True:
        seg = [x for x in sorted(row(r), reverse=not right) if (x >= q if right else x <= q)]
        exits = [x for x in seg if down(x, r)]
        if len(path) + len(seg) >= n or not exits:
            path += seg
            return path[:n] if len(path) >= n else None
        last = exits[-1]
        path += seg[:seg.index(last) + 1]
        b, e = down(last, r)
        path.append(b)
        r, q, right = r + 1, e, not right


def cz_stats(c):
    last, layers, n = {}, 0, 0
    for ins in c.data:
        if ins.operation.name == "cz":
            n += 1
            qs = [c.find_bit(x).index for x in ins.qubits]
            k = max(last.get(q, 0) for q in qs) + 1
            for q in qs:
                last[q] = k
            layers = max(layers, k)
    return n, layers


def main(dev_json):
    from qiskit import transpile
    from qiskit.transpiler import CouplingMap
    d = json.load(open(dev_json))
    cpl = [tuple(c) for c in d["couplers"]]
    adj = {}
    for a, b in cpl:
        adj.setdefault(a, set()).add(b)
        adj.setdefault(b, set()).add(a)
    cmap = CouplingMap([list(c) for c in cpl] + [[b, a] for a, b in cpl])
    basis = ["cz", "rz", "sx", "x"]
    rows = []
    for name, (L, M, N) in (("2D 3x3", (3, 3, 1)), ("2D 4x4", (4, 4, 1)), ("3D 2x2x2", (2, 2, 2)),
                            ("3D 3x3x2", (3, 3, 2)), ("3D 3x3x3", (3, 3, 3))):
        n, edges = cubic(L, M, N)
        t, theta = 2, 0.8
        lg = logical(n, edges, t, theta)
        # sabre reference
        cs = transpile(lg, coupling_map=cmap, basis_gates=basis, optimization_level=3, seed_transpiler=7)
        s_cz, s_layers = cz_stats(cs)
        # formula: swap network on a chain
        sn, pos = swap_network(n, edges, t, theta)
        chain = chain_on_device(adj, n)
        layout = {i: chain[i] for i in range(n)}
        from qiskit import QuantumCircuit
        phys = QuantumCircuit(max(chain) + 1)
        for ins in sn.data:
            phys.append(ins.operation, [layout[sn.find_bit(q).index] for q in ins.qubits])
        cf = transpile(phys, basis_gates=basis, optimization_level=1, seed_transpiler=7)  # no routing needed
        f_cz, f_layers = cz_stats(cf)
        # noiseless check of the formula network (logical level) for n <= 18
        check = None
        if n <= 18:
            ez = exact_z(lg)
            zz = exact_z(sn)
            check = float(max(abs(zz[i] - ez[pos[i]]) for i in range(n)))
        rows.append(dict(name=name, n=n, edges=len(edges), ideal_cz=len(edges) * t, sabre_cz=s_cz, sabre_layers=s_layers,
                         formula_cz=f_cz, formula_layers=f_layers, formula_check=check))
        print(rows[-1], flush=True)
    json.dump(rows, open("os3d_rows.json", "w"), indent=1)


if __name__ == "__main__":
    main(sys.argv[1])
