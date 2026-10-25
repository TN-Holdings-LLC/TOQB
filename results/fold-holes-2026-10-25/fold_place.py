"""Formula placement of a heavy-hex cycle (analysis prototype, 2026-10-25; no search over mappings).

The device's heavy-hex is read off its coupling graph: a *bridge* is a qubit with two neighbours whose indices are
not consecutive (they lie in different rows); the *rows* are the components left when bridges are removed; a *cell*
is the rectangle between two consecutive bridges joining the same two rows (12 qubits). Cycles are outlines of
fixed shapes of cells:
  row(k):    k cells side by side in one row pair                         8k + 4 qubits (12, 20, 28, 36, ...)
  row+row:   row(k) plus k2 cells side by side in the next row pair down, when the outline is one cycle
             (row(2) + 1 under its junction: 24; row(3) + 1: 32; ...)
The cycle for a ring of n is the shortest available length m >= n; among the shapes of that length the first, in a
fixed order (row pairs top to bottom, cells left to right), all of whose qubits and couplers work."""
from collections import defaultdict


def lattice(edges, nq):
    nb = defaultdict(set)
    for a, b in edges:
        nb[a].add(b); nb[b].add(a)
    bridges = {q for q in range(nq) if len(nb[q]) == 2 and all(abs(x - q) > 1 for x in nb[q])}
    # rows: components of the graph without bridges
    row_of, rows = {}, []
    for q in range(nq):
        if q in bridges or q in row_of or not nb[q]:
            continue
        comp, stack = [], [q]
        row_of[q] = len(rows)
        while stack:
            u = stack.pop(); comp.append(u)
            for v in nb[u]:
                if v not in bridges and v not in row_of:
                    row_of[v] = len(rows); stack.append(v)
        rows.append(sorted(comp))
    # bridges per row pair, ordered left to right by their upper row's qubit
    pairs = defaultdict(list)
    for b in bridges:
        u, v = sorted(nb[b], key=lambda x: row_of[x])
        pairs[(row_of[u], row_of[v])].append((u, b, v))
    for k in pairs:
        pairs[k].sort()
    return nb, rows, row_of, pairs


def cell_edges(r_pair, j, pairs):
    """Edges of cell j of a row pair: upper row from u1 to u2, bridge b2, lower row v2 back to v1, bridge b1."""
    (u1, b1, v1), (u2, b2, v2) = pairs[r_pair][j], pairs[r_pair][j + 1]
    E = set()
    for a in range(min(u1, u2), max(u1, u2)):
        E.add((a, a + 1))
    for a in range(min(v1, v2), max(v1, v2)):
        E.add((a, a + 1))
    for x, y in ((u1, b1), (b1, v1), (u2, b2), (b2, v2)):
        E.add(tuple(sorted((x, y))))
    return E


def as_cycle(E):
    """The ordered qubits of E if E is one simple cycle, else None."""
    nb = defaultdict(list)
    for a, b in E:
        nb[a].append(b); nb[b].append(a)
    if any(len(v) != 2 for v in nb.values()):
        return None
    start = min(nb)
    cyc, prev, cur = [start], None, start
    while True:
        nxt = nb[cur][0] if nb[cur][0] != prev else nb[cur][1]
        if nxt == start:
            break
        cyc.append(nxt); prev, cur = cur, nxt
    return cyc if len(cyc) == len(nb) else None


def shapes(pairs):
    """Every shape of the two families, in the fixed order, as (length, qubits in cycle order)."""
    out = []
    keys = sorted(pairs)
    for rp in keys:
        ncell = len(pairs[rp]) - 1
        for k in range(1, ncell + 1):
            for j in range(0, ncell - k + 1):
                E = set()
                for c in range(j, j + k):
                    E ^= cell_edges(rp, c, pairs)
                cyc = as_cycle(E)
                if cyc:
                    out.append((len(cyc), ("row", rp, j, k), cyc))
                # one more cell in the next row pair down, under a junction of this row
                below = [kk for kk in keys if kk[0] == rp[1]]
                for rb in below:
                    nb2 = len(pairs[rb]) - 1
                    for k2 in range(1, nb2 + 1):
                        for c in range(0, nb2 - k2 + 1):
                            E2 = set(E)
                            for cc in range(c, c + k2):
                                E2 ^= cell_edges(rb, cc, pairs)
                            cyc2 = as_cycle(E2)
                            if cyc2 and cyc:
                                out.append((len(cyc2), ("row+row", rp, j, k, rb, c, k2), cyc2))
    return out


def place_cycle(edges, nq, n, works=lambda q: True, works_edge=lambda a, b: True):
    nb, rows, row_of, pairs = lattice(edges, nq)
    cands = shapes(pairs)
    for m in sorted({c[0] for c in cands}):
        if m < n:
            continue
        for length, name, cyc in cands:
            if length != m:
                continue
            if all(works(q) for q in cyc) and all(works_edge(cyc[i], cyc[(i + 1) % m]) for i in range(m)):
                return m, name, cyc
    return None


if __name__ == "__main__":
    from qiskit_ibm_runtime import fake_provider
    for d in ("FakeMarrakesh", "FakeKingston", "FakeFez", "FakeTorino"):
        cm = getattr(fake_provider, d)().coupling_map
        E = {tuple(sorted(e)) for e in cm.get_edges()}
        _, rows, _, pairs = lattice(E, cm.size())
        lens = sorted({c[0] for c in shapes(pairs)})
        ok = all(all(tuple(sorted((c[2][i], c[2][(i + 1) % len(c[2])]))) in E for i in range(len(c[2])))
                 for c in shapes(pairs))
        print(d, "rows", len(rows), "row pairs", len(pairs), "cycle lengths", lens[:12], "all on couplers:", ok)
        for n in (9, 14, 19, 21, 23, 30, 36, 37):
            r = place_cycle(E, cm.size(), n)
            print("  n", n, "->", "none (no shape long enough)" if r is None else f"m {r[0]} {r[1]}")
