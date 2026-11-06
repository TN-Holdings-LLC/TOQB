"""Exploratory: a structured formula embedding of an L x M square lattice (and the cost of adding z-layers) on the
Heron r2 heavy-hex, no search.

Grid row y -> heavy-hex row y, grid column x -> heavy-hex column w + x (a window of L columns holding both bridge
columns 1 and 3). Horizontal bonds are native. Vertical bonds use the bridge qubit between two rows: every row runs
the same odd-even transposition rounds, so the sites of one grid column stay in one heavy-hex column; whenever a
column sits on the bridge column of a row pair, the vertical gate is done through the bridge:
SWAP(site, bridge), RZZ(bridge, partner), SWAP(site, bridge). Rounds continue until every vertical bond of the step
is done and the rows are back in order or fully reversed (a multiple of L rounds), so horizontal bonds stay native. All moves follow fixed rules; nothing is chosen by a cost.

usage: python rowpass.py DEVICE_JSON
"""
import json
import sys

import numpy as np


def bridges(adj, rows):
    """bridge label and its column for each row pair (r, r+1) within columns 0..15 (from the coupling graph)."""
    out = {}
    for r in range(rows - 1):
        row, nxt = set(range(20 * r, 20 * r + 16)), set(range(20 * (r + 1), 20 * (r + 1) + 16))
        for b in adj:
            if b in row or b in nxt or not (20 * r + 16 <= b <= 20 * r + 19):
                continue
            up = [q for q in adj[b] if q in row]
            dn = [q for q in adj[b] if q in nxt]
            if up and dn and up[0] - 20 * r == dn[0] - 20 * (r + 1):
                out.setdefault(r, []).append((b, up[0] - 20 * r))
    return out


def build(L, M, t, theta, adj):
    from qiskit import QuantumCircuit
    br = bridges(adj, M)
    cols = {r: [c for _, c in br[r]] for r in br}
    # window of L columns containing a bridge column for every row pair
    w = next(w for w in range(0, 17 - L) if all(any(w <= c < w + L for c in cols[r]) for r in range(M - 1)))
    bcol = {r: next((b, c) for b, c in br[r] if w <= c < w + L) for r in range(M - 1)}
    lab = lambda y, col: 20 * y + col
    nq = 20 * M + 16
    qc = QuantumCircuit(nq)
    pos = [list(range(L)) for _ in range(M)]  # pos[y][i] = grid column x at window position i (same for all rows)
    hor = [(x, x + 1) for x in range(L - 1)]
    rounds_total = 0
    for _ in range(t):
        # horizontal bonds: neighbours in every row are adjacent (reversals keep adjacency)
        for y in range(M):
            for i in range(L - 1):
                qc.rzz(-np.pi / 2, lab(y, w + i), lab(y, w + i + 1))
        done = set()
        need = {(x, y) for x in range(L) for y in range(M - 1)}
        r = 0
        while True:
            for y in range(M - 1):  # vertical bonds at the bridge columns, before this round's swaps
                b, c = bcol[y]
                x = pos[y][c - w]
                if (x, y) in need and (x, y) not in done:
                    a, p = lab(y, c), lab(y + 1, c)
                    qc.swap(a, b)
                    qc.rzz(-np.pi / 2, b, p)
                    qc.swap(a, b)
                    done.add((x, y))
            if done == need and r % L == 0:  # finish on a full reversal or the identity: rows stay adjacent
                break
            for y in range(M):
                for i in range(r % 2, L - 1, 2):
                    qc.swap(lab(y, w + i), lab(y, w + i + 1))
                    pos[y][i], pos[y][i + 1] = pos[y][i + 1], pos[y][i]
            r += 1
            rounds_total += 1
            if r > 6 * L:
                raise RuntimeError("vertical bonds not reachable")
        for y in range(M):
            for i in range(L):
                qc.rx(theta, lab(y, w + i))
    site_label = {(pos[y][i], y): lab(y, w + i) for y in range(M) for i in range(L)}
    return qc, site_label, rounds_total


def main(dev_json):
    from qiskit import QuantumCircuit, transpile
    from qiskit.quantum_info import Statevector
    sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
    from os3d_study import cz_stats, exact_z, logical, cubic
    d = json.load(open(dev_json))
    adj = {}
    for a, b in d["couplers"]:
        adj.setdefault(a, set()).add(b)
        adj.setdefault(b, set()).add(a)
    for L, M in ((3, 3), (4, 4), (4, 3)):
        t, theta = 2, 0.8
        qc, site_label, rounds = build(L, M, t, theta, adj)
        cq = transpile(qc, basis_gates=["cz", "rz", "sx", "x"], optimization_level=1, seed_transpiler=7)
        ncz, layers = cz_stats(cq)
        # noiseless check: the grid's own logical circuit, site (x, y) = index x + L*y... use cubic(L, M, 1) order
        n, edges = cubic(L, M, 1)  # sites (x, y, 0), idx = x*M + y in itertools.product order
        lg = logical(n, edges, t, theta)
        ez = exact_z(lg)
        used = sorted({qc.find_bit(q).index for ins in qc.data for q in ins.qubits})
        small = QuantumCircuit(len(used))
        m = {u: i for i, u in enumerate(used)}
        for ins in qc.data:
            small.append(ins.operation, [m[qc.find_bit(q).index] for q in ins.qubits])
        p = Statevector(small).probabilities()
        idx = np.arange(len(p))
        worst = 0.0
        for (x, y), l in site_label.items():
            j = m[l]
            z = float(np.sum(p * (1 - 2 * ((idx >> j) & 1))))
            worst = max(worst, abs(z - ez[x * M + y]))
        print(f"{L}x{M}: rowpass CZ {ncz} (layers {layers}), rounds {rounds}, qubits used {len(used)}, check {worst:.1e}")


if __name__ == "__main__":
    main(sys.argv[1])
