"""Prototype (analysis, 2026-10-25): a CZ ring of n logical qubits on a physical cycle of m >= n qubits with
h = m - n idle qubits ("holes", in |0>). Per layer: CZ on every ring edge already adjacent on the cycle; for each hole
between ring neighbours a and b, move a into the hole (CX a->hole, CX hole->a: the hole starts in |0>, so a's state
moves and a's old site becomes |0>), then CZ on (a, b). n + 2h two-qubit gates per layer."""
import numpy as np
from qiskit import QuantumCircuit


def place(n, m):
    """Cycle positions of the ring's nodes: holes spread as evenly as the counts allow. Returns occ: position -> ring
    index or None."""
    h = m - n
    occ, q = [], 0
    holes_at = {round((k + 0.5) * m / h) % m for k in range(h)} if h else set()
    while len(holes_at) < h:
        holes_at.add(max(set(range(m)) - holes_at))
    for p in range(m):
        if p in holes_at:
            occ.append(None)
        else:
            occ.append(q); q += 1
    return occ


def build(rot_layers, final_rot, n, m):
    """rot_layers: per layer a list of (gate, angle) per logical qubit applied before the ring's CZs; final_rot after
    the last layer. Returns (physical circuit on m qubits, final position of each ring index, two-qubit count)."""
    occ = place(n, m)
    qc = QuantumCircuit(m)
    n2 = 0
    for layer in rot_layers:
        pos = {r: p for p, r in enumerate(occ) if r is not None}
        for r in range(n):
            for g, a in layer[r]:
                getattr(qc, g)(a, pos[r])
        # CZ on the ring edges adjacent on the cycle
        done = set()
        for p in range(m):
            a, b = occ[p], occ[(p + 1) % m]
            if a is not None and b is not None and ((a + 1) % n == b or (b + 1) % n == a):
                qc.cz(p, (p + 1) % m); n2 += 1; done.add(frozenset((a, b)))
        # each hole: the ring node before it (along the cycle) moves into it, then CZ with the node after it
        starts = [p for p in range(m) if occ[p] is None and occ[(p - 1) % m] is not None]  # first hole of each run
        for p in starts:
            if True:
                pa, pb = (p - 1) % m, (p + 1) % m
                k = 1
                while occ[pb] is None:  # a run of holes: move across all of them
                    pb = (pb + 1) % m; k += 1
                a = occ[pa]
                if a is None:
                    continue
                cur = pa
                for step in range(k):
                    nxt = (cur + 1) % m
                    qc.cx(cur, nxt); qc.cx(nxt, cur); n2 += 2
                    occ[nxt], occ[cur] = occ[cur], None
                    cur = nxt
                b = occ[pb]
                e = frozenset((occ[cur], b))
                assert e not in done and ((occ[cur] + 1) % n == b or (b + 1) % n == occ[cur]), (occ, p)
                qc.cz(cur, pb); n2 += 1; done.add(e)
        assert len(done) == n, (len(done), n)
    pos = {r: p for p, r in enumerate(occ) if r is not None}
    for r in range(n):
        for g, a in final_rot[r]:
            getattr(qc, g)(a, pos[r])
    return qc, pos, n2


def logical(rot_layers, final_rot, n):
    qc = QuantumCircuit(n)
    for layer in rot_layers:
        for r in range(n):
            for g, a in layer[r]:
                getattr(qc, g)(a, r)
        for r in range(n):
            qc.cz(r, (r + 1) % n)
    for r in range(n):
        for g, a in final_rot[r]:
            getattr(qc, g)(a, r)
    return qc


if __name__ == "__main__":
    from qiskit.quantum_info import Statevector
    rng = np.random.default_rng(1)
    for n, m in [(5, 6), (7, 8), (9, 12), (10, 12), (11, 12), (6, 12), (8, 12)]:
        for L in (1, 2, 3, 4):
            rl = [[[("ry", rng.uniform(-3, 3)), ("rz", rng.uniform(-3, 3))] for _ in range(n)] for _ in range(L)]
            fr = [[("ry", rng.uniform(-3, 3))] for _ in range(n)]
            pq, pos, n2 = build(rl, fr, n, m)
            lq = logical(rl, fr, n)
            # compare marginals: every logical qubit's P(1), and the full distribution over the ring's qubits
            sp, sl = Statevector(pq), Statevector(lq)
            order = [pos[r] for r in range(n)]
            pp = sp.probabilities(order)
            pl = sl.probabilities(list(range(n)))
            holes = [p for p in range(m) if p not in pos.values()]
            ph = sp.probabilities(holes)[0] if holes else 1.0
            print(f"n {n} m {m} L {L}: 2q per layer {n2 / L:.1f} (n + 2h = {n + 2 * (m - n)}); max |dP| {np.abs(pp - pl).max():.1e}; holes in |0>: {ph:.6f}")
