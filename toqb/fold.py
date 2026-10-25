"""The hole schedule as a TOQB arm (2026-10-25; analysis arm, not a PSF-Zero compiler): `fold:template`.

The owner's idea of 2026-10-25 ("fold the map a few big times"; results/fold-holes-2026-10-25): a CZ ring of n
logical qubits is laid on a heavy-hex cycle of m >= n qubits, the outline of a fixed shape of cells chosen by formula
(`fold_place` below; no search, no error value decides; failed elements are not used); the m - n spare qubits
("holes") start in |0>. Per ring layer: CZ on every ring edge already adjacent on the cycle, in rounds of disjoint
pairs; for each run of holes, the ring node before it moves across (CX a->hole, CX hole->a per hole: a's state moves
and its old site becomes |0>), then CZ across. n + 2(m - n) two-qubit gates per layer when the holes are apart.

Template mode, as `qiskit:L:target:template`: the input's angles become parameters, the hole schedule is built and
transpiled once per structure (optimisation level 1, the layout fixed, no routing), and each call binds the angles.
Reads TOQB's ring classifier (layers of single-qubit gates, each followed by the n CZs of one ring 0-1-...-n-1-0, then
single-qubit gates and measurements); anything else raises `FoldRefused`.
"""
from __future__ import annotations

from collections import defaultdict

FOLD_VERSION = "toqb fold 2026-10-26.1 (hole schedule on a formula-placed heavy-hex cycle; pend: ring nodes hung off a shorter cycle)"


class FoldRefused(RuntimeError):
    pass


# ------------------------------------------------------------------------------------------------ placement

def lattice(edges, nq):
    """Heavy-hex read off the coupling graph: bridges (two neighbours, indices not consecutive), rows (components
    without the bridges), and per row pair its bridges (upper qubit, bridge, lower qubit) left to right."""
    nb = defaultdict(set)
    for a, b in edges:
        nb[a].add(b)
        nb[b].add(a)
    bridges = {q for q in range(nq) if len(nb[q]) == 2 and all(abs(x - q) > 1 for x in nb[q])}
    row_of, nrows = {}, 0
    for q in range(nq):
        if q in bridges or q in row_of or not nb[q]:
            continue
        stack = [q]
        row_of[q] = nrows
        while stack:
            u = stack.pop()
            for v in nb[u]:
                if v not in bridges and v not in row_of:
                    row_of[v] = nrows
                    stack.append(v)
        nrows += 1
    pairs = defaultdict(list)
    for b in bridges:
        u, v = sorted(nb[b], key=lambda x: row_of.get(x, -1))
        if u in row_of and v in row_of and row_of[u] != row_of[v]:
            pairs[(row_of[u], row_of[v])].append((u, b, v))
    for k in pairs:
        pairs[k].sort()
    return pairs


def _cell_edges(rp, j, pairs):
    (u1, b1, v1), (u2, b2, v2) = pairs[rp][j], pairs[rp][j + 1]
    e = set()
    for a in range(min(u1, u2), max(u1, u2)):
        e.add((a, a + 1))
    for a in range(min(v1, v2), max(v1, v2)):
        e.add((a, a + 1))
    for x, y in ((u1, b1), (b1, v1), (u2, b2), (b2, v2)):
        e.add((min(x, y), max(x, y)))
    return e


def _as_cycle(e):
    nb = defaultdict(list)
    for a, b in e:
        nb[a].append(b)
        nb[b].append(a)
    if not nb or any(len(v) != 2 for v in nb.values()):
        return None
    start = min(nb)
    cyc, prev, cur = [start], None, start
    while True:
        nxt = nb[cur][0] if nb[cur][0] != prev else nb[cur][1]
        if nxt == start:
            break
        cyc.append(nxt)
        prev, cur = cur, nxt
    return cyc if len(cyc) == len(nb) else None


def shapes(pairs):
    """Outlines of k cells side by side in a row pair (8k + 4 qubits), and of k cells plus k2 side by side in the next
    row pair down when the outline is one cycle (24, 32, 36, ...): [(length, name, qubits in cycle order)], in the
    fixed order (row pairs top to bottom, cells left to right)."""
    out, keys = [], sorted(pairs)
    for rp in keys:
        nc = len(pairs[rp]) - 1
        for k in range(1, nc + 1):
            for j in range(nc - k + 1):
                e = set()
                for c in range(j, j + k):
                    e ^= _cell_edges(rp, c, pairs)
                cyc = _as_cycle(e)
                if cyc:
                    out.append((len(cyc), ("row", rp, j, k), cyc))
                for rb in (kk for kk in keys if kk[0] == rp[1]):
                    nb2 = len(pairs[rb]) - 1
                    for k2 in range(1, nb2 + 1):
                        for c in range(nb2 - k2 + 1):
                            e2 = set(e)
                            for cc in range(c, c + k2):
                                e2 ^= _cell_edges(rb, cc, pairs)
                            cyc2 = _as_cycle(e2)
                            if cyc and cyc2:
                                out.append((len(cyc2), ("row+row", rp, j, k, rb, c, k2), cyc2))
    return out


def fold_place(target, n):
    """(m, shape name, cycle qubits) for a ring of n on `target`, or None: the shortest outline of m >= n qubits, the
    first in the fixed order whose qubits (sx) and couplers (cz) all work (error < 1)."""
    def bad(name, qa):
        p = target[name].get(qa) if name in target.operation_names else None
        return p is None or (p.error is not None and p.error >= 1)
    edges = {tuple(sorted(qa)) for qa in target["cz"] if qa is not None and not bad("cz", qa)}
    cands = shapes(lattice(edges, target.num_qubits))
    for m in sorted({c[0] for c in cands}):
        if m < n:
            continue
        for length, name, cyc in cands:
            if length != m:
                continue
            if any(bad("sx", (q,)) or bad("measure", (q,)) for q in cyc):
                continue
            if all(tuple(sorted((cyc[i], cyc[(i + 1) % m]))) in edges for i in range(m)):
                return m, name, cyc
    return None


# ------------------------------------------------------------------------------------------------ schedule

def spread_holes(n, m):
    """Cycle position -> ring index (None for a hole): the m - n holes spread evenly."""
    h = m - n
    at = {round((k + 0.5) * m / h) % m for k in range(h)} if h else set()
    while len(at) < h:
        at.add(max(set(range(m)) - at))
    occ, q = [], 0
    for p in range(m):
        if p in at:
            occ.append(None)
        else:
            occ.append(q)
            q += 1
    return occ


def read_ring(qc):
    """TOQB's ring classifier as (n, layers: per layer the single-qubit instructions per qubit, final ones, measures);
    FoldRefused for anything else."""
    n = qc.num_qubits
    ring = {frozenset((i, (i + 1) % n)) for i in range(n)}
    layers, cur, seen, meas = [], [[] for _ in range(n)], set(), []
    for ins in qc.data:
        nm = ins.operation.name
        qs = [qc.find_bit(q).index for q in ins.qubits]
        if nm == "cz":
            e = frozenset(qs)
            if e not in ring or e in seen:
                raise FoldRefused("not a CZ ring in layers")
            seen.add(e)
            if len(seen) == n:
                layers.append(cur)
                cur, seen = [[] for _ in range(n)], set()
        elif nm == "measure":
            meas.append((qs[0], qc.find_bit(ins.clbits[0]).index))
        elif nm == "barrier":
            continue
        elif len(qs) == 1 and not seen:
            if meas:
                raise FoldRefused("a gate after a measurement")
            cur[qs[0]].append(ins.operation)
        else:
            raise FoldRefused(f"{nm} on {qs} inside a ring layer")
    if seen:
        raise FoldRefused("an incomplete ring layer")
    return n, layers, cur, meas


def hole_circuit(qc, cyc, nq):
    """The hole schedule of `qc` on the cycle `cyc` (device qubits in cycle order) of an nq-qubit device:
    (circuit, initial device qubit of each ring index, final one)."""
    from qiskit import QuantumCircuit
    n, layers, final, meas = read_ring(qc)
    m = len(cyc)
    occ = spread_holes(n, m)
    start = {r: cyc[p] for p, r in enumerate(occ) if r is not None}
    out = QuantumCircuit(nq, qc.num_clbits)
    for layer in layers:
        pos = {r: p for p, r in enumerate(occ) if r is not None}
        for r in range(n):
            for op in layer[r]:
                out.append(op, [cyc[pos[r]]])
        edges = [p for p in range(m) if occ[p] is not None and occ[(p + 1) % m] is not None
                 and ((occ[p] + 1) % n == occ[(p + 1) % m] or (occ[(p + 1) % m] + 1) % n == occ[p])]
        rounds = []
        for p in edges:  # commuting CZs in rounds of disjoint pairs, so the schedule is not one long chain
            for rd in rounds:
                if all({p, (p + 1) % m}.isdisjoint({q, (q + 1) % m}) for q in rd):
                    rd.append(p)
                    break
            else:
                rounds.append([p])
        for rd in rounds:
            for p in rd:
                out.cz(cyc[p], cyc[(p + 1) % m])
        for p in [p for p in range(m) if occ[p] is None and occ[(p - 1) % m] is not None]:
            cur, pb = (p - 1) % m, (p + 1) % m
            while occ[pb] is None:
                pb = (pb + 1) % m
            while occ[(cur + 1) % m] is None:
                nx = (cur + 1) % m
                out.cx(cyc[cur], cyc[nx])
                out.cx(cyc[nx], cyc[cur])
                occ[nx], occ[cur] = occ[cur], None
                cur = nx
            out.cz(cyc[cur], cyc[pb])
    pos = {r: p for p, r in enumerate(occ) if r is not None}
    for r in range(n):
        for op in final[r]:
            out.append(op, [cyc[pos[r]]])
    for q, c in meas:
        out.measure(cyc[pos[q]], c)
    return out, [start[r] for r in range(n)], [cyc[pos[r]] for r in range(n)]


# ------------------------------------------------------------------------------------------------ pend (2026-10-26)
# The ring on the longest formula-placed cycle of m <= n qubits, its n - m extra nodes hung off the cycle on outside
# neighbours ("pendants"); per layer each pendant node trades places with its cycle node by one CZ+SWAP block (two
# two-qubit gates): n + (n - m) two-qubit gates per layer. Analysis arm `fold:pend`, not a PSF-Zero compiler.

def _working(target, name, qa):
    p = target[name].get(qa) if name in target.operation_names else None
    return p is not None and (p.error is None or p.error < 1)


def pend_place(target, n, packed=False):
    """(m, shape name, cycle qubits, {cycle position: pendant qubit}) for a ring of n on `target`, or None: the
    longest cycle of m <= n qubits (the shapes and order of `fold_place`) whose qubits and couplers all work and which
    has n - m cycle nodes with a working outside neighbour; pendants spread evenly over those nodes in cycle order,
    each node's smallest working outside neighbour not used before (packed=True: the first n - m such nodes)."""
    edges = {tuple(sorted(qa)) for qa in target["cz"] if qa is not None and _working(target, "cz", qa)}
    nb = defaultdict(set)
    for a, b in edges:
        nb[a].add(b)
        nb[b].add(a)
    ok = lambda q: _working(target, "sx", (q,)) and _working(target, "measure", (q,))  # noqa: E731
    cands = shapes(lattice(edges, target.num_qubits))
    for m in sorted({c[0] for c in cands}, reverse=True):
        if m > n:
            continue
        k = n - m
        for length, name, cyc in cands:
            if length != m or not all(ok(q) for q in cyc):
                continue
            if not all(tuple(sorted((cyc[i], cyc[(i + 1) % m]))) in edges for i in range(m)):
                continue
            inside, used, spots = set(cyc), set(), []
            for p, q in enumerate(cyc):
                outs = sorted(x for x in nb[q] if x not in inside and ok(x))
                if outs:
                    spots.append((p, outs))
            if len(spots) < k:
                continue
            pick = spots[:k] if packed else ([spots[(j * len(spots)) // k] for j in range(k)] if k else [])
            pend = {}
            for p, outs in pick:
                free = [x for x in outs if x not in used]
                if not free:
                    break
                pend[p] = free[0]
                used.add(free[0])
            if len(pend) == k:
                return m, name, cyc, pend
    return None


def pend_circuit(qc, cyc, pend, nq):
    """The pendant schedule of `qc` on the cycle `cyc` with pendants {cycle position: device qubit}:
    (circuit, initial device qubit of each ring index, final one)."""
    from qiskit import QuantumCircuit
    n, layers, final, meas = read_ring(qc)
    m = len(cyc)
    oc, op, r = [None] * m, {}, 0
    for p in range(m):
        oc[p] = r
        r += 1
        if p in pend:
            op[p] = r
            r += 1
    if r != n:
        raise FoldRefused(f"pend: {m} + {len(pend)} places for {n} ring nodes")

    def where():
        w = {v: cyc[p] for p, v in enumerate(oc)}
        w.update({v: pend[p] for p, v in op.items()})
        return w

    start = where()
    out = QuantumCircuit(nq, qc.num_clbits)
    for layer in layers:
        w = where()
        for i in range(n):
            for o in layer[i]:
                out.append(o, [w[i]])
        need = {frozenset((i, (i + 1) % n)) for i in range(n)}
        while need:
            progress = False
            rounds = []
            for p in range(m):  # plain CZ on ring edges between neighbouring cycle nodes
                e = frozenset((oc[p], oc[(p + 1) % m]))
                if e in need:
                    for rd in rounds:
                        if all({p, (p + 1) % m}.isdisjoint({q, (q + 1) % m}) for q in rd):
                            rd.append(p)
                            break
                    else:
                        rounds.append([p])
                    need.discard(e)
            for rd in rounds:
                for p in rd:
                    out.cz(cyc[p], cyc[(p + 1) % m])
                progress = True
            for p in sorted(op):  # a CZ+SWAP block where the cycle node's other ring edge is done
                u, v = oc[p], op[p]
                e = frozenset((u, v))
                other = frozenset((u, (u - 1) % n)) if (u + 1) % n == v else frozenset((u, (u + 1) % n))
                if e in need and other not in need:
                    a, b = cyc[p], pend[p]
                    out.h(b)  # CZ then SWAP on (a, b) = H(b), CX(b, a), CX(a, b), H(a)
                    out.cx(b, a)
                    out.cx(a, b)
                    out.h(a)
                    oc[p], op[p] = v, u
                    need.discard(e)
                    progress = True
            if not progress:
                raise FoldRefused("pend: no schedule step left")
    w = where()
    for i in range(n):
        for o in final[i]:
            out.append(o, [w[i]])
    for q, c in meas:
        out.measure(w[q], c)
    return out, [start[i] for i in range(n)], [w[i] for i in range(n)]


# ------------------------------------------------------------------------------------------------ the arm

class FoldLoop:
    """`fold:template`: the hole schedule; `fold:pend` (2026-10-26): the pendant schedule, pendants spread; each built
    and transpiled once per structure, the angles bound per call. Variants (2026-10-26): `fold:pendpack`, pendants on
    the first cycle nodes that have one; `fold:pendbind`, pendants spread, the angles bound before transpiling (level
    1), so that runs of single-qubit gates are merged per call."""

    def __init__(self, mode="template"):
        if mode not in ("template", "pend", "pendpack", "pendbind"):
            raise ValueError("fold: the modes are template (holes), pend, pendpack and pendbind (pendants)")
        self.mode, self.name = mode, f"fold:{mode}"
        self.stats = dict(template_builds=0, refused=0)

    def version(self):
        import qiskit
        return f"{FOLD_VERSION}; qiskit {qiskit.__version__}"

    def setup(self, target):
        from qiskit.transpiler import generate_preset_pass_manager
        self.target = target
        self.pm = generate_preset_pass_manager(1, target=target, initial_layout=list(range(target.num_qubits)),
                                               routing_method="none", seed_transpiler=0)
        self._cache = {}

    def _template(self, qc):
        from qiskit.circuit import ParameterVector
        values = [float(p) for i in qc.data for p in i.operation.params]
        pv = ParameterVector("v", len(values))
        par = qc.copy_empty_like()
        k = 0
        for ins in qc.data:
            op = ins.operation
            if op.params:
                op = op.to_mutable()
                op.params = [pv[k + j] for j in range(len(op.params))]
                k += len(op.params)
            par.append(op, ins.qubits, ins.clbits)
        if self.mode.startswith("pend"):
            placed = pend_place(self.target, qc.num_qubits, packed=self.mode == "pendpack")
            if placed is None:
                self.stats["refused"] += 1
                raise FoldRefused(f"pend: no cycle of <= {qc.num_qubits} qubits with enough pendants by the formula")
            m, shape, cyc, pend = placed
            hc, init, fin = pend_circuit(par, cyc, pend, self.target.num_qubits)
        else:
            placed = fold_place(self.target, qc.num_qubits)
            if placed is None:
                self.stats["refused"] += 1
                raise FoldRefused(f"no cycle of >= {qc.num_qubits} qubits by the formula")
            m, shape, cyc = placed
            hc, init, fin = hole_circuit(par, cyc, self.target.num_qubits)
        tq = self.pm.run(hc)
        self.stats["template_builds"] += 1
        self.stats["last"] = dict(m=m, shape=str(shape))
        order = [pv[j] for j in range(len(values))]
        return tq, order, init, fin

    def compile_circuit(self, qc):
        from toqb.task_loop import _qiskit_sig
        if self.mode == "pendbind":
            n = qc.num_qubits
            if n not in self._cache:
                placed = pend_place(self.target, n)
                if placed is None:
                    self.stats["refused"] += 1
                    raise FoldRefused(f"pend: no cycle of <= {n} qubits with enough pendants by the formula")
                self._cache[n] = placed
            m, shape, cyc, pend = self._cache[n]
            hc, init, fin = pend_circuit(qc, cyc, pend, self.target.num_qubits)
            out = self.pm.run(hc)
            self.stats["last"] = dict(m=m, shape=str(shape))
            out.metadata = dict(toqb_initial=list(init), toqb_final=list(fin))
            return out
        sig = _qiskit_sig(qc)
        if sig not in self._cache:
            self._cache[sig] = self._template(qc)
        tq, order, init, fin = self._cache[sig]
        values = [float(p) for i in qc.data for p in i.operation.params]
        present = set(tq.parameters)
        out = tq.assign_parameters({p: v for p, v in zip(order, values) if p in present})
        out.metadata = dict(toqb_initial=list(init), toqb_final=list(fin))
        return out
