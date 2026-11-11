"""2D Fermi-Hubbard on an R x W grid, one Trotter step on a line of qubits (for a chain on heavy-hex), CZ count.

Jordan-Wigner along the snake order of the sites (row 0 left to right, row 1 right to left, ...), interleaved spins
(u0 d0 u1 d1 ... on the line), as in hub_count.py (1D). One step:
  1. onsite U on every site (RZZ + RZ),
  2. the bonds that are neighbours in the snake order (all horizontal bonds and the vertical bond at each row turn),
     even then odd, exactly as the 1D step (FSWAP inside the site pair, two XX+YY hops, FSWAP back),
  3. the other vertical bonds, for each pair of rows (0,1), (2,3), ... then (1,2), ...: an odd-even transposition of
     whole sites inside the two rows' block (a site swap = 4 FSWAPs) until every vertical pair of that block has
     been neighbours once; each pair is hopped when it first becomes neighbours; then the swaps are undone, so the
     site order at the end of the step is the start order.
FSWAP = SWAP . CZ. Counts CZ and CZ layers after transpiling to cz / rz / sx / x on a line, no routing.
Check (2 x 2, 8 qubits): the circuit against the product of exp(-i dt h) of every applied term, in the applied
order, built from fermion operators (Jordan-Wigner in the start order).

usage: python hub2d_count.py      (prints the 4 x 4 count, the 1D L = 16 reference and the 2 x 2 check)
"""
import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit.circuit.library import XXPlusYYGate
from qiskit.transpiler import CouplingMap

J, U, DT = 1.0, 4.0, 0.25


def snake(R, W):
    """site label (r, c) at each snake position."""
    return [(r, c if r % 2 == 0 else W - 1 - c) for r in range(R) for c in range(W)]


def fswap(qc, a, b):
    qc.swap(a, b)
    qc.cz(a, b)


class Line:
    """Sites on a line of 2 * n qubits; order[k] = the site at line position k."""

    def __init__(self, qc, order, log):
        self.qc, self.order, self.log = qc, list(order), log

    def hop(self, k):
        """hop between the sites at positions k, k+1 (both spins)."""
        qc, q = self.qc, 2 * k
        fswap(qc, q + 1, q + 2)
        qc.append(XXPlusYYGate(-2 * J * DT), [q, q + 1])
        qc.append(XXPlusYYGate(-2 * J * DT), [q + 2, q + 3])
        fswap(qc, q + 1, q + 2)
        self.log.append(("hop", self.order[k], self.order[k + 1]))

    def swap_sites(self, k):
        qc, q = self.qc, 2 * k
        fswap(qc, q + 1, q + 2)
        fswap(qc, q, q + 1)
        fswap(qc, q + 2, q + 3)
        fswap(qc, q + 1, q + 2)
        self.order[k], self.order[k + 1] = self.order[k + 1], self.order[k]


def step(qc, R, W, log):
    sites = snake(R, W)
    line = Line(qc, sites, log)
    n = R * W
    for k in range(n):
        qc.rzz(U * DT / 2, 2 * k, 2 * k + 1)
        qc.rz(-U * DT / 2, 2 * k)
        qc.rz(-U * DT / 2, 2 * k + 1)
        log.append(("U", sites[k]))
    for par in (0, 1):
        for k in range(par, n - 1, 2):
            line.hop(k)
    done = {frozenset(p) for kind, *p in log if kind == "hop"}
    for start in (0, 1):
        for r in range(start, R - 1, 2):
            lo, hi = r * W, (r + 2) * W                       # the block of rows r, r+1 on the line
            want = {frozenset({(r, c), (r + 1, c)}) for c in range(W)} - done
            swaps = []
            layer = 0
            while want:
                for k in range(lo, hi - 1):                   # hop every wanted pair that is now neighbours
                    p = frozenset({line.order[k], line.order[k + 1]})
                    if p in want:
                        line.hop(k)
                        want.discard(p)
                        done.add(p)
                if not want:
                    break
                for k in range(lo + layer % 2, hi - 1, 2):    # one odd-even transposition layer
                    line.swap_sites(k)
                    swaps.append(k)
                layer += 1
                if layer > 4 * W:
                    raise RuntimeError("block did not meet all pairs")
            for k in reversed(swaps):                         # undo
                line.swap_sites(k)
    assert line.order == sites
    return log


def count(qc, level=1):
    t = transpile(qc, coupling_map=CouplingMap.from_line(qc.num_qubits), basis_gates=["cz", "rz", "sx", "x"],
                  optimization_level=level, initial_layout=list(range(qc.num_qubits)), routing_method="none",
                  seed_transpiler=0)
    return t.count_ops().get("cz", 0), t.depth(lambda i: i.operation.name == "cz")


def one_d(L):
    """the 1D step of hub_count.py on L sites (same gates as step() with R = 1)."""
    qc = QuantumCircuit(2 * L)
    step(qc, 1, L, [])
    return qc


def check(R, W):
    from scipy.linalg import expm
    from qiskit.quantum_info import Operator, SparsePauliOp
    sites = snake(R, W)
    n = 2 * R * W
    pos = {s: k for k, s in enumerate(sites)}

    def lowering(m):
        lab = ["I"] * n
        for j in range(m):
            lab[j] = "Z"
        a = lab.copy(); a[m] = "X"
        b = lab.copy(); b[m] = "Y"
        return SparsePauliOp(["".join(reversed(a)), "".join(reversed(b))], [0.5, 0.5j])

    c = [lowering(m) for m in range(n)]
    cd = [x.adjoint() for x in c]
    num = [(cd[m] @ c[m]).simplify() for m in range(n)]
    qc = QuantumCircuit(n)
    log = step(qc, R, W, [])
    T = np.eye(2 ** n, dtype=complex)
    for kind, *p in log:
        if kind == "U":
            k = pos[p[0]]
            h = U * (num[2 * k] @ num[2 * k + 1])
        else:
            a, b = pos[p[0]], pos[p[1]]
            h = SparsePauliOp("I" * n, 0)
            for s in (0, 1):
                h = h + (-J) * (cd[2 * a + s] @ c[2 * b + s] + cd[2 * b + s] @ c[2 * a + s])
        T = expm(-1j * DT * h.simplify().to_matrix()) @ T
    V = Operator(qc).data
    f = abs(np.trace(V.conj().T @ T)) / 2 ** n
    # bonds covered: every grid bond exactly once
    bonds = sorted(tuple(sorted(p)) for kind, *p in log if kind == "hop")
    grid = sorted(tuple(sorted(((r, c), (r2, c2)))) for r in range(R) for c in range(W)
                  for r2, c2 in ((r + 1, c), (r, c + 1)) if r2 < R and c2 < W)
    # statevector check from a Neel-like start (up on even sites, down on odd sites)
    psi0 = np.zeros(2 ** n, dtype=complex)
    idx = sum(1 << (2 * k + ((sites[k][0] + sites[k][1]) % 2)) for k in range(R * W))
    psi0[idx] = 1
    tr = np.trace(V.conj().T @ T)
    phase = tr / abs(tr)                                      # the circuit drops a global phase (constant of H_U)
    sv = np.linalg.norm(phase * (V @ psi0) - T @ psi0)
    return 1 - f, sv, bonds == grid, len(log)


if __name__ == "__main__":
    R, W = 4, 4
    qc = QuantumCircuit(2 * R * W)
    log = step(qc, R, W, [])
    hops = sum(1 for k, *_ in log if k == "hop")
    for lev in (1, 3):
        cz, ly = count(qc, lev)
        cz1, ly1 = count(one_d(R * W), lev)
        print(f"opt level {lev}: 2D {R}x{W} ({2 * R * W} qubits, {hops} bonds): CZ {cz}, CZ layers {ly}, CZ/qubit "
              f"{cz / (2 * R * W):.2f} | 1D L {R * W}: CZ {cz1}, CZ layers {ly1}")
    one_minus_f, sv, ok, nterms = check(2, 2)
    print(f"check 2x2 (8 qubits, {nterms} terms): 1 - |Tr(V^dag T)|/d = {one_minus_f:.1e}; "
          f"|V psi - T psi| up to the global phase (Neel start) = {sv:.1e}; every bond once: {ok}")
