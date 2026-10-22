"""Lower bound / optimum of the CZ count of one layer of an n-qubit CZ ring on a line of n qubits (analysis only).

Per layer every ring edge gets exactly one CZ while its two qubits are adjacent on the line. Moves on adjacent
positions: CZ (an undone ring edge; 1 CZ), CZ+SWAP on an undone ring edge (2 CZ: the pair is locally iSWAP), plain
SWAP (3 CZ). Cost counted here: the extra over n (CZ+SWAP +1, SWAP +3). Start layout: any layout of minimum total
ring length (every cut of the line crossed exactly twice), up to symmetry; the end layout is free (the next layer
runs the schedule backwards, as N2 does). IDA* with the admissible bound ceil(Phi / 2), Phi = sum over undone ring
edges of (line distance - 1): a CZ+SWAP changes Phi by at most 2, a SWAP by at most 4 (4 per 3 cost < 2 per 1).
"""
import itertools
import sys


def start_layouts(n):
    """Layouts with every cut crossed exactly twice: ring node 0 leftmost, the two arcs from 0 to the far node m go
    left to right, interleaved (2^(n-2) interleavings; up to the reflection of the ring)."""
    out = set()
    for m in range(1, n):
        top = list(range(0, m + 1))          # 0, 1, ..., m
        bot = [0] + list(range(n - 1, m - 1, -1))  # 0, n-1, ..., m
        a, b = top[1:-1], bot[1:-1]
        for mask in itertools.combinations(range(len(a) + len(b)), len(a)):
            seq, ia, ib = [0], 0, 0
            for k in range(len(a) + len(b)):
                if k in mask:
                    seq.append(a[ia]); ia += 1
                else:
                    seq.append(b[ib]); ib += 1
            seq.append(m)
            out.add(tuple(seq))
    return sorted(out)


def solve(n, limit=40):
    edges = [(i, (i + 1) % n) for i in range(n)]
    eid = {}
    for k, (a, b) in enumerate(edges):
        eid[(a, b)] = eid[(b, a)] = k
    nbr = [[(i - 1) % n, (i + 1) % n] for i in range(n)]
    full = (1 << n) - 1

    def phi(pos, done):
        s = 0
        for k, (a, b) in enumerate(edges):
            if not done >> k & 1:
                s += abs(pos[a] - pos[b]) - 1
        return s

    best = [None]

    def dfs(line, pos, done, g, bound, path, seen):
        h = (phi(pos, done) + 1) // 2
        if g + h > bound:
            return g + h
        if done == full:
            best[0] = list(path)
            return -1
        key = (line, done)
        if seen.get(key, 1 << 30) <= g:
            return 1 << 30
        seen[key] = g
        nxt = 1 << 30
        # free CZs first: an undone adjacent ring edge with a CZ only never hurts (commuting), but we keep the
        # option of CZ+SWAP on it, so both branches are searched
        for p in range(n - 1):
            x, y = line[p], line[p + 1]
            k = eid.get((x, y))
            cands = []
            if k is not None and not done >> k & 1:
                cands.append(("cz", 0, done | 1 << k, False))
                cands.append(("czswap", 1, done | 1 << k, True))
            cands.append(("swap", 3, done, True))
            for name, c, nd, sw in cands:
                if sw:
                    nl = list(line); nl[p], nl[p + 1] = y, x; nl = tuple(nl)
                    np_ = list(pos); np_[x], np_[y] = p + 1, p; np_ = tuple(np_)
                else:
                    nl, np_ = line, pos
                path.append((name, p, x, y))
                r = dfs(nl, np_, nd, g + c, bound, path, seen)
                path.pop()
                if r == -1:
                    return -1
                nxt = min(nxt, r)
        return nxt

    results = []
    for lay in start_layouts(n):
        pos = [0] * n
        for p, q in enumerate(lay):
            pos[q] = p
        bound = (phi(tuple(pos), 0) + 1) // 2
        while bound <= limit:
            best[0] = None
            r = dfs(lay, tuple(pos), 0, 0, bound, [], {})
            if r == -1:
                results.append((bound, lay, best[0]))
                break
            bound = r
        limit = min(limit, results[-1][0]) if results else limit
    results.sort(key=lambda t: t[0])
    return results


if __name__ == "__main__":
    n = int(sys.argv[1])
    res = solve(n)
    print("n", n, "optimal extra", res[0][0], "CZ per layer", n + res[0][0])
    b, lay, path = res[0]
    print("start", lay)
    for st in path:
        print("  ", st)
