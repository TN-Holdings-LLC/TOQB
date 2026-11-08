"""3D Heisenberg (XXZ) Trotter circuits on the folded layout of psf-os grid3d (2026-11-07, draft B of
prereg/drafts-2026-11-07/os3d_physics_DRAFT.md; owner 19:49 JST "1・2 OK", 22:48 JST "B").

The folded layout (psf_os.grid3d._Fold, v3.1) is kept as it is: the same block schedules, the same bridges, the same
order of bonds. Only the bond gate changes, from RZZ(-pi/2) to the two-qubit unitary
    U = exp(-i dt (XX + YY + delta ZZ))
on every lattice edge, and there is no RX layer. Initial state: the Neel state (X on the sites with x + y + z odd).
  - an x- or z-bond between neighbouring positions: U as one two-qubit block (Qiskit's unitary synthesis decomposes it
    analytically by the KAK / Weyl decomposition, at most 3 CZ; nothing is searched);
  - an x-bond carried by the swap of its two columns: SWAP . U as one block (still at most 3 CZ);
  - a y-bond through the bridge b (|0> between uses): move a onto b (CX(a, b) CX(b, a)), U on (b, q), move back
    (CX(b, a) CX(a, b)); b is |0> again afterwards.
Every bond applied is logged as a pair of lattice sites, in order; `logical_from_log` rebuilds the same product of U
on 16 (or more) lattice qubits, so the exact answer is that of the very Trotter product the device runs (the order of
non-commuting bonds is the layout's, not a textbook order).
"""
import numpy as np
from scipy.linalg import expm

from psf_os import grid3d as G

X = np.array([[0, 1], [1, 0]], dtype=complex)
Y = np.array([[0, -1j], [1j, 0]])
Z = np.diag([1.0 + 0j, -1.0])
SWAP = np.array([[1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0], [0, 0, 0, 1]], dtype=complex)


def bond_unitary(dt, delta=1.0):
    """exp(-i dt (XX + YY + delta ZZ)), symmetric under exchange of the two qubits."""
    h = np.kron(X, X) + np.kron(Y, Y) + delta * np.kron(Z, Z)
    return expm(-1j * dt * h)


def neel_sites(L, M, N):
    return [i for i, (x, y, z) in enumerate(G.sites(L, M, N)) if (x + y + z) % 2 == 1]


class FoldHeis(G._Fold):
    """carry (2026-11-08, not yet declared for a device run): an x-bond is not applied at a round boundary when a
    later round of the same step swaps its two columns; it rides on that swap as SWAP . U (3 CZ, the cost of the
    plain swap alone). The fixed schedules of 6 swaps are reduced words of the reversal of the four columns, so every
    pair of columns is swapped exactly once per step and all three x-bonds of a row ride on swaps: per row and step
    3 plain swaps instead of 5 (4 x 2 x 2: 152 CZ per step instead of 176). Without carry the layout is the declared
    one of 2026-11-07 (the x-bonds are taken at the first boundary where their columns are adjacent)."""

    def __init__(self, M, N, adj, r0, c0, dt, delta=1.0, merge=True, carry=False):
        super().__init__(M, N, adj, r0, c0, merge=merge)
        self.carry = carry
        from qiskit.circuit.library import UnitaryGate
        self.U = UnitaryGate(bond_unitary(dt, delta), label="heis")
        self.SU = UnitaryGate(SWAP @ bond_unitary(dt, delta), label="swap_heis")
        self.log = []   # bonds in order, as layout keys (kind, y, z, x); converted to sites by `bond_sites`

    def _bonds(self, todo, with_x=True, later=frozenset()):
        """later: column pairs (min, max) that a later round of this step swaps (their x-bond waits for the swap)."""
        M, N = self.M, self.N
        for y in range(M):
            for z in range(N):
                for i in range(3 if with_x else 0):
                    x, w = self.col[i], self.col[i + 1]
                    key = ("x", y, z, min(x, w))
                    if abs(x - w) == 1 and key in todo and (min(x, w), max(x, w)) not in later:
                        self.qc.append(self.U, [self.lab(y, z, i), self.lab(y, z, i + 1)])
                        self.log.append(key)
                        todo.discard(key)
                if z + 1 < N:
                    jp = 3 if z % 2 == 0 else 0
                    key = ("z", y, z, self.col[jp])
                    if key in todo:
                        self.qc.append(self.U, [self.lab(y, z, jp), self.lab(y, z + 1, jp)])
                        self.log.append(key)
                        todo.discard(key)
                if y + 1 < M:
                    b, bp = self.bridge[(y, z)]
                    key = ("y", y, z, self.col[bp])
                    if key in todo:
                        a, q = self.lab(y, z, bp), self.lab(y + 1, z, bp)
                        self.qc.cx(a, b)          # move a onto the empty bridge b
                        self.qc.cx(b, a)
                        self.qc.append(self.U, [b, q])
                        self.qc.cx(b, a)          # move back; b is |0> again
                        self.qc.cx(a, b)
                        self.log.append(key)
                        todo.discard(key)

    def step(self, theta=None):
        """One Trotter step: every lattice edge once, in the layout's order. theta is ignored (no field)."""
        M, N = self.M, self.N
        todo = ({("x", y, z, x) for y in range(M) for z in range(N) for x in range(3)}
                | {("z", y, z, x) for y in range(M) for z in range(N - 1) for x in range(4)}
                | {("y", y, z, x) for y in range(M - 1) for z in range(N) for x in range(4)})
        moving = any(k[0] != "x" for k in todo)
        self._bonds(todo, with_x=not (self.merge and moving))
        if moving:
            sched = list(self.schedule())
            for r, rnd in enumerate(sched):
                for z in range(N):
                    for i in rnd:
                        x, w = self.col[i], self.col[i + 1]
                        for y in range(M):
                            a, b = self.lab(y, z, i), self.lab(y, z, i + 1)
                            key = ("x", y, z, min(x, w))
                            if self.merge and abs(x - w) == 1 and key in todo:
                                self.qc.append(self.SU, [a, b])   # the x-bond rides on the swap
                                self.log.append(key)
                                todo.discard(key)
                            else:
                                self.qc.swap(a, b)
                for i in rnd:
                    self.col[i], self.col[i + 1] = self.col[i + 1], self.col[i]
                self._bonds(todo, later=self._later(sched[r + 1:]) if self.carry else frozenset())
            self.passes += 1
        if todo:
            raise RuntimeError(f"bonds left over: {sorted(todo)[:4]}")


def _later_pairs(col, rounds):
    """Column pairs (min, max) swapped by the given rounds, starting from the arrangement col."""
    c, out = list(col), set()
    for rnd in rounds:
        for i in rnd:
            out.add((min(c[i], c[i + 1]), max(c[i], c[i + 1])))
            c[i], c[i + 1] = c[i + 1], c[i]
    return frozenset(out)


FoldHeis._later = lambda self, rounds: _later_pairs(self.col, rounds)


def bond_sites(key, L, M, N, swapped):
    """Layout key (kind, y, z, x) -> the two lattice site indices (fold coordinates (y, z) are lattice (z, y) when
    the layout is swapped)."""
    idx = {s: i for i, s in enumerate(G.sites(L, M, N))}
    kind, y, z, x = key
    a = (x, y, z)
    b = {"x": (x + 1, y, z), "z": (x, y, z + 1), "y": (x, y + 1, z)}[kind]
    if swapped:
        a, b = (a[0], a[2], a[1]), (b[0], b[2], b[1])
    return idx[a], idx[b]


def physical(dev, M, N, t, dt, delta=1.0, avoid=(), merge=True, carry=False):
    """The placed Heisenberg circuit (Neel state, t steps), the site -> label map at the end, the labels used, the
    bond log as site pairs and where it was placed. The first fold translation in psf-os's fixed order that touches
    no failed element (as psf_os.grid3d.physical); Refused if none."""
    from qiskit import QuantumCircuit
    L = 4
    avoid = {tuple(a) for a in avoid}
    adj = {}
    for a, b in dev.couplers:
        adj.setdefault(a, set()).add(b)
        adj.setdefault(b, set()).add(a)
    bad, badc = set(dev.failed_qubits), {frozenset(c) for c in dev.failed_couplers}
    cpl = {frozenset(c) for c in dev.couplers}
    first = None
    for swapped, r0, c0 in G.fold_offsets(M, N):
        if (r0, c0) in avoid:
            continue
        try:
            B = FoldHeis(N if swapped else M, M if swapped else N, adj, r0, c0, dt, delta, merge=merge, carry=carry)
        except G.Refused as e:
            first = first or str(e)
            continue
        start = B.placed(swapped)
        for _ in range(t):
            B.step()
        qc = QuantumCircuit(B.qc.num_qubits)
        for s in neel_sites(L, M, N):
            qc.x(start[s])
        qc.compose(B.qc, inplace=True)
        used = sorted({qc.find_bit(q).index for ins in qc.data for q in ins.qubits})
        pairs = {frozenset(qc.find_bit(q).index for q in ins.qubits) for ins in qc.data if len(ins.qubits) == 2}
        if qc.num_qubits > dev.num_qubits or pairs - cpl or bad & set(used) or badc & pairs:
            first = first or "touches a failed element or a non-coupler"
            continue
        log = [bond_sites(k, L, M, N, swapped) for k in B.log]
        return qc, B.placed(swapped), used, log, dict(layout="fold" + ("-swapped" if swapped else ""), r0=r0, c0=c0,
                                                      passes=B.passes)
    raise G.Refused(f"no translation of the folded layout fits on {dev.name}; first reason: {first}")


def logical_from_log(L, M, N, log, dt, delta=1.0):
    """The same product of bond unitaries on the lattice qubits (site i = qubit i), from the Neel state."""
    from qiskit import QuantumCircuit
    from qiskit.circuit.library import UnitaryGate
    n = L * M * N
    qc = QuantumCircuit(n)
    for s in neel_sites(L, M, N):
        qc.x(s)
    U = UnitaryGate(bond_unitary(dt, delta))
    for a, b in log:
        qc.append(U, [a, b])
    return qc


def exact_from_log(L, M, N, log, dt, delta=1.0):
    """{str(site): exact <Z>} of the logged Trotter product (full statevector; up to about 24 sites)."""
    from qiskit.quantum_info import Statevector
    p = Statevector(logical_from_log(L, M, N, log, dt, delta)).probabilities()
    idx = np.arange(len(p))
    return {str(s): float(np.sum(p * (1 - 2 * ((idx >> s) & 1)))) for s in range(L * M * N)}


def staggered(zs, L, M, N):
    """Neel order parameter m_s = mean over sites of (-1)^(x+y+z) <Z_i> (1 in the Neel state as prepared: the odd
    sites are flipped, so (-1)^(x+y+z) <Z> = +1 on every site)."""
    return float(np.mean([(-1) ** (x + y + z) * zs[str(i)] for i, (x, y, z) in enumerate(G.sites(L, M, N))]))


def placed_check(qc, placed, used, L, M, N, log, dt, delta=1.0):
    """Without noise: max |<Z> placed - exact| over the sites, and max over the other used qubits of (1 - <Z>)
    (every bridge back in |0>). Statevector on the used qubits (18 for 4 x 2 x 2)."""
    from qiskit import QuantumCircuit
    from qiskit.quantum_info import Statevector
    m = {u: i for i, u in enumerate(used)}
    small = QuantumCircuit(len(used))
    for ins in qc.data:
        small.append(ins.operation, [m[qc.find_bit(q).index] for q in ins.qubits])
    p = Statevector(small).probabilities()
    idx = np.arange(len(p))
    z = {u: float(np.sum(p * (1 - 2 * ((idx >> m[u]) & 1)))) for u in used}
    ex = exact_from_log(L, M, N, log, dt, delta)
    site_err = max(abs(z[placed[s]] - ex[str(s)]) for s in placed)
    others = set(used) - set(placed.values())
    bridge_err = max((1 - z[u] for u in others), default=0.0)
    return site_err, bridge_err


# ---------------------------------------------------------------------------------------------------------------
# The line layout for 4 x 2 x 2 (2026-11-08; VS Claude's schedules, notes/heis_cz_2026-11-08, joined here with the
# carry idea and a merge at step boundaries). Lattice row y of both blocks z = 0, 1 shares one heavy-hex row
# (columns c0 .. c0 + 7): the eight sites (x, z) are interleaved along the line, and every bond inside the line (x- and
# z-bonds) rides on a swap as SWAP . U or is taken in place as U, so no swap is empty. The two lines (y = 0, 1) run the
# same schedule; a site at a bridge position takes its y-bond through the bridge (move onto the empty bridge, U, move
# back). Even steps run the schedule reversed (U is symmetric, so a reversed SWAP . U is again SWAP . U).
# Merge at step boundaries: when a y-bond's move back is followed by the next y-bond of the same bridge with no line
# operation on that position in between, the two moves cancel and the two U(dt) on the same pair are one U(2 dt)
# (exact: the same pair, U(dt)^2 = U(2 dt)); the log keeps both bonds, so the exact answer is unchanged.
# ---------------------------------------------------------------------------------------------------------------

_NAMES = ["0", "1", "2", "3", "0'", "1'", "2'", "3'"]   # x + 4 z (a prime marks block z = 1)
LINE_SCHEDULES = {
    # bridge line positions: (start arrangement, operations (kind, line position e: acts on e, e + 1))
    (1, 5): (["0'", "1", "0", "1'", "2'", "3", "2", "3'"],
             "SWAP.U(3,2)@5 ; SWAP.U(3,3')@6 ; U(1',2')@3 ; SWAP.U(2',2)@4 ; SWAP.U(2',3')@5 ; SWAP.U(1,0)@1 ; "
             "SWAP.U(1,1')@2 ; U(1,2)@3 ; SWAP.U(0',0)@0 ; SWAP.U(0',1')@1"),
    (3, 7): (["0'", "1", "2'", "0", "1'", "2", "3", "3'"],
             "U(2,3)@5 ; SWAP.U(3,3')@6 ; SWAP(2',0)@2 ; SWAP.U(2',1')@3 ; SWAP.U(2',2)@4 ; U(2',3')@5 ; "
             "SWAP.U(1,0)@1 ; SWAP.U(1,1')@2 ; SWAP.U(1,2)@3 ; SWAP.U(0',0)@0 ; SWAP.U(0',1')@1 ; SWAP(0',2)@2"),
}


def _parse_ops(text):
    import re
    out = []
    for o in text.split(";"):
        m = re.match(r"\s*(U|SWAP\.U|SWAP)\((\S+?),(\S+?)\)@(\d)", o)
        out.append((m.group(1), int(m.group(4))))
    return out


def _line_build(A, B, bridge, br, t, dt, delta, merge=True):
    """The 4 x 2 x 2 circuit on line labels A[0..7] (y = 0), B[0..7] (y = 1) and bridges {line position: label}.
    Returns (abstract operation list, start arrangement, end arrangement, log of site pairs)."""
    start_names, ops_text = LINE_SCHEDULES[tuple(br)]
    ops = _parse_ops(ops_text)
    idx = {s: i for i, s in enumerate(G.sites(4, 2, 2))}
    site = lambda name, y: idx[(name % 4, y, name // 4)]
    arr = [_NAMES.index(v) for v in start_names]
    start = list(arr)
    seq, log = [], []
    for step in range(t):
        steps_ops = ops if step % 2 == 0 else list(reversed(ops))
        ydone = set()

        def ybonds():
            for p in br:
                if arr[p] not in ydone:
                    seq.append(("y", p))
                    log.append((site(arr[p], 0), site(arr[p], 1)))
                    ydone.add(arr[p])
        ybonds()
        for kind, e in steps_ops:
            for y in (0, 1):
                s1, s2 = site(arr[e], y), site(arr[e + 1], y)
                if kind != "SWAP":
                    log.append((s1, s2))
            seq.append((kind, e))
            if kind != "U":
                arr[e], arr[e + 1] = arr[e + 1], arr[e]
            ybonds()
        if len(ydone) != 8:
            raise RuntimeError("a site missed its y-bond")
    # merge: consecutive y-bonds of one bridge with no line operation on that position in between
    out = []
    for op in seq:
        if merge and op[0] == "y":
            p = op[1]
            j = len(out) - 1
            while j >= 0 and not (out[j][0] in ("y", "yy") and out[j][1] == p) and \
                    not (out[j][0] in ("U", "SWAP.U", "SWAP") and out[j][1] in (p - 1, p)):
                j -= 1
            if j >= 0 and out[j][0] in ("y", "yy") and out[j][1] == p:
                out[j] = ("yy", p, (out[j][2] if out[j][0] == "yy" else 1) + 1)
                continue
        out.append(op if op[0] != "y" else ("y", op[1]))
    return out, start, arr, log


def _line_circuit(out, start, A, B, bridge, n_qubits, dt, delta):
    from qiskit import QuantumCircuit
    from qiskit.circuit.library import UnitaryGate
    idx = {s: i for i, s in enumerate(G.sites(4, 2, 2))}
    qc = QuantumCircuit(n_qubits)
    for y, line in ((0, A), (1, B)):
        for p in range(8):
            x, z = start[p] % 4, start[p] // 4
            if (x + y + z) % 2 == 1:
                qc.x(line[p])
    U = UnitaryGate(bond_unitary(dt, delta), label="heis")
    SU = UnitaryGate(SWAP @ bond_unitary(dt, delta), label="swap_heis")
    for op in out:
        kind, e = op[0], op[1]
        if kind in ("y", "yy"):
            k = 1 if kind == "y" else op[2]
            a, b, q = A[e], bridge[e], B[e]
            Uk = U if k == 1 else UnitaryGate(bond_unitary(k * dt, delta), label=f"heis_x{k}")
            qc.cx(a, b)
            qc.cx(b, a)
            qc.append(Uk, [b, q])
            qc.cx(b, a)
            qc.cx(a, b)
        else:
            for line in (A, B):
                if kind == "SWAP":
                    qc.swap(line[e], line[e + 1])
                else:
                    qc.append(U if kind == "U" else SU, [line[e], line[e + 1]])
    return qc


def physical_line(dev, t, dt, delta=1.0, avoid=(), merge=True):
    """4 x 2 x 2 on the line layout: the first translation (r0, c0) in psf-os's fold order whose two rows, eight
    columns and two bridges (at line positions 1, 5 or 3, 7) touch no failed element. Same return as `physical`."""
    avoid = {tuple(a) for a in avoid}
    adj = {}
    for a, b in dev.couplers:
        adj.setdefault(a, set()).add(b)
        adj.setdefault(b, set()).add(a)
    bad, badc = set(dev.failed_qubits), {frozenset(c) for c in dev.failed_couplers}
    cpl = {frozenset(c) for c in dev.couplers}
    first = None
    idx = {s: i for i, s in enumerate(G.sites(4, 2, 2))}
    for r0, c0 in dict.fromkeys((r, c) for _, r, c in G.fold_offsets(2, 2)):
        if (r0, c0) in avoid:
            continue
        if r0 + 2 > 8 or c0 + 8 > 16:
            continue
        bl = {c - c0: b for b, c in G.bridges(adj, r0, 2).get(0, []) if 0 <= c - c0 < 8}
        br = tuple(sorted(bl))
        if br not in LINE_SCHEDULES:
            first = first or f"bridges at line positions {br}"
            continue
        A = [20 * r0 + c0 + p for p in range(8)]
        B = [20 * (r0 + 1) + c0 + p for p in range(8)]
        out, start, end, log = _line_build(A, B, bl, br, t, dt, delta, merge=merge)
        qc = _line_circuit(out, start, A, B, bl, 20 * (r0 + 2) + 16, dt, delta)
        used = sorted({qc.find_bit(q).index for ins in qc.data for q in ins.qubits})
        pairs = {frozenset(qc.find_bit(q).index for q in ins.qubits) for ins in qc.data if len(ins.qubits) == 2}
        if qc.num_qubits > dev.num_qubits or pairs - cpl or bad & set(used) or badc & pairs:
            first = first or "touches a failed element or a non-coupler"
            continue
        placed = {}
        for y, line in ((0, A), (1, B)):
            for p in range(8):
                placed[idx[(end[p] % 4, y, end[p] // 4)]] = line[p]
        return qc, placed, used, log, dict(layout="line", r0=r0, c0=c0, bridges=list(br), merged=merge)
    raise G.Refused(f"no translation of the line layout fits on {dev.name}; first reason: {first}")
