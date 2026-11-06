"""Prototype "3D OS" layer (exploratory, not declared): a kicked Ising circuit on an L x M x N cubic lattice placed on
the Heron r2 heavy-hex by fixed rules (no search, no calibration number), checked against the lattice's own
statevector.

Layout. Lattice column x -> heavy-hex column x (L a multiple of 4); every lattice row (y, z) -> one heavy-hex row.
x-bonds are native. Bonds between two lattice rows that sit on adjacent heavy-hex rows go through the bridge qubit
(SWAP, RZZ, SWAP) during a "pass": block-local odd-even transposition rounds (blocks of 4 columns, the same rounds
in every row) until every column has met its bridge column, ending on the identity (a multiple of 8 rounds).
Lattice rows that must bond but are not adjacent are brought together by an odd-even transposition sort of the
heavy-hex rows' contents: an "exchange pass" swaps the sites of two adjacent rows column by column through the
bridge (SWAP, SWAP, SWAP). Each step: x-bonds, then alternate bond passes and exchange passes until every y- and
z-bond of the step is done; the row order left at the end of a step is kept for the next step.

usage: python grid3d.py DEVICE_JSON
"""
import json
import sys

import numpy as np

sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
from rowpass import bridges  # noqa: E402


class Builder:
    def __init__(self, L, M, N, adj):
        from qiskit import QuantumCircuit
        assert L % 4 == 0
        self.L, self.M, self.N = L, M, N
        R = M * N
        br = bridges(adj, R)
        if len(br) < R - 1:
            raise RuntimeError("not enough heavy-hex rows")
        self.bcols = {h: {c: b for b, c in br[h] if c < L} for h in br}
        self.qc = QuantumCircuit(20 * R + 16)
        self.rowlab = [(y, z) for y in range(M) for z in range(N)]  # heavy-hex row h holds lattice row rowlab[h]
        self.col = list(range(L))  # col[i]: lattice column at heavy-hex column i (the same in every row)
        self.passes = 0

    def lab(self, h, i):
        return 20 * h + i

    def run_pass(self, jobs):
        """jobs: {h: 'bond' | 'exchange'} for row pairs (h, h+1). One block-local pass; returns when every column of
        every job has met its bridge column and the columns are back to the identity."""
        L = self.L
        todo = {h: set(range(L)) for h in jobs}
        r = 0
        while True:
            for h, kind in jobs.items():
                for c, b in self.bcols[h].items():
                    x = self.col[c]
                    if x in todo[h]:
                        a, p = self.lab(h, c), self.lab(h + 1, c)
                        if kind == "bond":
                            self.qc.swap(a, b)
                            self.qc.rzz(-np.pi / 2, b, p)
                            self.qc.swap(a, b)
                        else:  # exchange the two rows' sites of this lattice column through the bridge
                            self.qc.swap(a, b)
                            self.qc.swap(b, p)
                            self.qc.swap(a, b)
                        todo[h].discard(x)
            if all(not v for v in todo.values()) and r % 8 == 0:
                break
            for blk in range(0, L, 4):
                for i in range(blk + r % 2, blk + 3, 2):
                    for h in range(len(self.rowlab)):
                        self.qc.swap(self.lab(h, i), self.lab(h, i + 1))
                    self.col[i], self.col[i + 1] = self.col[i + 1], self.col[i]
            r += 1
            if r > 48:
                raise RuntimeError("pass did not close")
        for h, kind in jobs.items():
            if kind == "exchange":
                self.rowlab[h], self.rowlab[h + 1] = self.rowlab[h + 1], self.rowlab[h]
        self.passes += 1

    def step(self, theta):
        L, M, N = self.L, self.M, self.N
        R = M * N
        for h in range(R):
            for i in range(L - 1):
                self.qc.rzz(-np.pi / 2, self.lab(h, i), self.lab(h, i + 1))
        need = set()
        for y in range(M):
            for z in range(N):
                if z + 1 < N:
                    need.add(frozenset(((y, z), (y, z + 1))))
                if y + 1 < M:
                    need.add(frozenset(((y, z), (y + 1, z))))
        done, k = set(), 0
        while True:
            bonds = {h: "bond" for h in range(R - 1)
                     if frozenset((self.rowlab[h], self.rowlab[h + 1])) in need - done}
            # a row can bond with both neighbours in one pass only through different bridge columns: keep the jobs
            # of one pass disjoint by parity when the two neighbours share a bridge column
            if bonds:
                self.run_pass(bonds)
                done |= {frozenset((self.rowlab[h], self.rowlab[h + 1])) for h in bonds}
            if done == need:
                break
            ex = {h: "exchange" for h in range(k % 2, R - 1, 2)}
            self.run_pass(ex)
            k += 1
            if k > 4 * R:
                raise RuntimeError("row sort did not close")
        for h in range(R):
            for i in range(L):
                self.qc.rx(theta, self.lab(h, i))

    def site_labels(self):
        return {(self.col[i], y, z): self.lab(h, i) for h, (y, z) in enumerate(self.rowlab) for i in range(self.L)}


def main(dev_json):
    from qiskit import QuantumCircuit, transpile
    from qiskit.quantum_info import Statevector
    from qiskit.transpiler import CouplingMap
    from os3d_study import cz_stats, exact_z, logical, cubic
    d = json.load(open(dev_json))
    cpl = [tuple(c) for c in d["couplers"]]
    adj = {}
    for a, b in cpl:
        adj.setdefault(a, set()).add(b)
        adj.setdefault(b, set()).add(a)
    cmap = CouplingMap([list(c) for c in cpl] + [[b, a] for a, b in cpl])
    basis = ["cz", "rz", "sx", "x"]
    for (L, M, N) in ((4, 2, 1), (4, 1, 2), (4, 2, 2), (4, 3, 2), (8, 2, 2), (4, 2, 3)):
        t, theta = 2, 0.8
        B = Builder(L, M, N, adj)
        for _ in range(t):
            B.step(theta)
        qc = B.qc
        f_cz, f_l = cz_stats(transpile(qc, basis_gates=basis, optimization_level=1, seed_transpiler=7))
        n, edges = cubic(L, M, N)
        lg = logical(n, edges, t, theta)
        s_cz, s_l = cz_stats(transpile(lg, coupling_map=cmap, basis_gates=basis, optimization_level=3, seed_transpiler=7))
        check = "-"
        used = sorted({qc.find_bit(q).index for ins in qc.data for q in ins.qubits})
        if len(used) <= 24:
            m = {u: i for i, u in enumerate(used)}
            small = QuantumCircuit(len(used))
            for ins in qc.data:
                small.append(ins.operation, [m[qc.find_bit(q).index] for q in ins.qubits])
            p = Statevector(small).probabilities()
            idx = np.arange(len(p))
            ez = exact_z(lg)
            order = {s: i for i, s in enumerate(__import__("itertools").product(range(L), range(M), range(N)))}
            worst = max(abs(float(np.sum(p * (1 - 2 * ((idx >> m[l]) & 1)))) - ez[order[s]])
                        for s, l in B.site_labels().items())
            check = f"{worst:.1e}"
        print(f"{L}x{M}x{N}: ideal {2 * len(edges)}  SABRE {s_cz} ({s_l})  grid3d {f_cz} ({f_l})  passes {B.passes}  "
              f"qubits {len(used)}  check {check}", flush=True)


if __name__ == "__main__":
    main(sys.argv[1])
