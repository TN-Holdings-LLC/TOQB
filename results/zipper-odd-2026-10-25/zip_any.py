"""The zipper ring schedule for every n >= 4, even (as TOQB toqb/ring_zip.py) and odd (2026-10-25; analysis).

Odd n: the same start order; round B is a CZ + SWAP at the left end only, round C has (n - 3)/2 SWAPs:
CZ per layer n + 1 + 3 (n - 3)/2 = (5n - 7)/2, the least found by exact search for n = 5, 7, 9 (all states) and by
IDA* from every minimum-length start for n = 5-11 (TOQB results/zipper-bound-2026-10-24).
"""


def ring_rounds_zip_any(n):
    if n < 4:
        raise RuntimeError("zipper: n must be >= 4")
    top = list(range(1, n)); bot = list(range(n - 1, 0, -1))
    order, used, t, b, from_top = [0], {0}, 0, 0, True
    while len(order) < n:
        src = top if from_top else bot
        k = 0
        while k < 2 and len(order) < n:
            i = t if from_top else b
            while src[i] in used:
                i += 1
            order.append(src[i]); used.add(src[i])
            if from_top: t = i + 1
            else: b = i + 1
            k += 1
        from_top = not from_top
    occ = list(order)
    edges = {(min(i, (i + 1) % n), max(i, (i + 1) % n)) for i in range(n)}

    def take(p):
        a, b_ = occ[p], occ[p + 1]
        e = (min(a, b_), max(a, b_))
        if e not in edges:
            raise RuntimeError(f"zipper: positions ({p}, {p + 1}) hold {a}, {b_}, not a ring edge")
        edges.discard(e)
        return (a, b_)

    rounds = []
    odd = list(range(1, n - 1, 2))                       # (1,2), (3,4), ...  [n even: up to (n-3,n-2); n odd: (n-2,n-1)]
    rounds.append(([take(p) for p in odd], []))          # A
    ends = [0, n - 2] if n % 2 == 0 else [0]
    czb = [take(p) for p in ends]
    rounds.append((czb, [(p, p + 1) for p in ends]))     # B
    for p in ends:
        occ[p], occ[p + 1] = occ[p + 1], occ[p]
    mid = [(p, p + 1) for p in range(2, n - 3 + (n % 2), 2)]
    if mid:
        rounds.append(([], mid))                         # C
        for p, p1 in mid:
            occ[p], occ[p1] = occ[p1], occ[p]
    rounds.append(([take(p) for p in odd], []))          # D
    if edges:
        raise RuntimeError(f"zipper: edges left {sorted(edges)}")
    return order, rounds


if __name__ == "__main__":
    import sys
    from qiskit import QuantumCircuit
    from qiskit.quantum_info import Clifford
    for n in range(4, int(sys.argv[1]) + 1):
        order, rounds = ring_rounds_zip_any(n)
        # build one layer on the line (line position p holds ring index occ[p]) and count CZ with merging
        occ = list(order); qc = QuantumCircuit(n); ncz = 0
        for czs, swaps in rounds:
            sw = {p for p, _ in swaps}
            where = {q: i for i, q in enumerate(occ)}
            for a, b in czs:
                p, p1 = sorted((where[a], where[b]))
                assert p1 == p + 1
                qc.cz(p, p1)
                if p in sw:
                    qc.swap(p, p1); ncz += 2; sw.discard(p)        # merged block: 2 CZ
                else:
                    ncz += 1
            for p in sorted(sw):
                qc.swap(p, p + 1); ncz += 3
            for p, p1 in swaps:
                occ[p], occ[p1] = occ[p1], occ[p]
        # forward layer then the same rounds backwards must equal two copies of the ring's CZ layer (identity)
        # and the forward layer alone must equal (ring CZ layer on the start order) followed by the permutation.
        ref = QuantumCircuit(n)
        start = {q: i for i, q in enumerate(order)}
        for i in range(n):
            ref.cz(start[i], start[(i + 1) % n])
        end = {q: i for i, q in enumerate(occ)}
        perm = QuantumCircuit(n)
        # move each ring index from its start position to its end position
        from qiskit.circuit.library import PermutationGate
        pattern = [0] * n
        for q in range(n):
            pattern[start[q]] = end[q]
        perm.append(PermutationGate(pattern), range(n))
        ok = Clifford(qc) == Clifford(ref.compose(perm))
        two = qc.compose(qc.reverse_ops())
        ok2 = Clifford(two) == Clifford(QuantumCircuit(n))
        target = (5 * n - 8) // 2 if n % 2 == 0 else (5 * n - 7) // 2
        print(f"n {n:2d}: CZ per layer {ncz} (target {target}) layer = ring CZ + permutation: {ok}; "
              f"forward then backward = identity: {ok2}; start {order}")
