"""Exploratory: block-local variant of rowpass.py. Odd-even transposition rounds run inside each block of 4
heavy-hex columns (every block holds a bridge column for both kinds of row pair); a step ends when every vertical
bond is done and the blocks are back to the identity (a multiple of 8 rounds), so every horizontal bond is native.

usage: python blockpass.py DEVICE_JSON
"""
import json
import sys

import numpy as np

sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
from rowpass import bridges  # noqa: E402


def build(L, M, t, theta, adj):
    from qiskit import QuantumCircuit
    assert L % 4 == 0
    br = bridges(adj, M)
    bcols = {r: {c: b for b, c in br[r]} for r in br}
    lab = lambda y, col: 20 * y + col
    qc = QuantumCircuit(20 * M + 16)
    pos = list(range(L))  # the same permutation in every row: pos[i] = grid column at heavy-hex column i
    for _ in range(t):
        assert pos == list(range(L))
        for y in range(M):
            for i in range(L - 1):
                qc.rzz(-np.pi / 2, lab(y, i), lab(y, i + 1))
        need = {(x, y) for x in range(L) for y in range(M - 1)}
        done, r = set(), 0
        while True:
            for y in range(M - 1):
                for c, b in bcols[y].items():
                    if c >= L:
                        continue
                    x = pos[c]
                    if (x, y) in need and (x, y) not in done:
                        a, p = lab(y, c), lab(y + 1, c)
                        qc.swap(a, b)
                        qc.rzz(-np.pi / 2, b, p)
                        qc.swap(a, b)
                        done.add((x, y))
            if done == need and r % 8 == 0:
                break
            for blk in range(0, L, 4):
                for i in range(blk + r % 2, blk + 3, 2):
                    for y in range(M):
                        qc.swap(lab(y, i), lab(y, i + 1))
                    pos[i], pos[i + 1] = pos[i + 1], pos[i]
            r += 1
            if r > 40:
                raise RuntimeError("not reachable")
        for y in range(M):
            for i in range(L):
                qc.rx(theta, lab(y, i))
    return qc


def main(dev_json):
    from qiskit import transpile
    from qiskit.transpiler import CouplingMap
    from os3d_study import cz_stats, logical, cubic
    d = json.load(open(dev_json))
    cpl = [tuple(c) for c in d["couplers"]]
    adj = {}
    for a, b in cpl:
        adj.setdefault(a, set()).add(b)
        adj.setdefault(b, set()).add(a)
    cmap = CouplingMap([list(c) for c in cpl] + [[b, a] for a, b in cpl])
    for L, M in ((4, 3), (8, 3), (12, 3), (16, 3), (8, 4)):
        qc = build(L, M, 2, 0.8, adj)
        b_cz, b_l = cz_stats(transpile(qc, basis_gates=["cz", "rz", "sx", "x"], optimization_level=1, seed_transpiler=7))
        n, edges = cubic(L, M, 1)
        s = transpile(logical(n, edges, 2, 0.8), coupling_map=cmap, basis_gates=["cz", "rz", "sx", "x"],
                      optimization_level=3, seed_transpiler=7)
        s_cz, s_l = cz_stats(s)
        print(f"{L}x{M}: ideal {2 * len(edges)}  SABRE {s_cz} ({s_l})  blockpass {b_cz} ({b_l})  ratio {b_cz / s_cz:.2f}")


if __name__ == "__main__":
    main(sys.argv[1])
