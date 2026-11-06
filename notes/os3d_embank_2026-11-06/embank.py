"""Design study (owner 2026-11-06 23:15 JST: "盛り土" - spread the load instead of one bridge). Static layouts of the
4 x 2 x 2 lattice on Heron r2 where no data moves: every bond is a parity chain through empty qubits
(CX ... CX, RZZ, CX ... CX: 2 (d - 1) + 1 CZ for a path of d edges whose inner qubits are empty and |0>).
For a layout (site -> qubit) this computes, by shortest paths through empty qubits on the coupling graph (an
evaluator of a fixed layout, not a placement search): CZ per step, the longest bond, and the load of every qubit
(how many bonds pass through it), against v3.1 (108 CZ per step; bridge q38 carried every y-bond of its block)."""
import collections
import itertools


def heron_edges():
    e = set()
    for r in range(8):
        for c in range(15):
            e.add((20 * r + c, 20 * r + c + 1))
    for r in range(7):
        cols = (3, 7, 11, 15) if r % 2 == 0 else (1, 5, 9, 13)
        for k, c in enumerate(cols):
            b = 20 * r + 16 + k
            e.add((20 * r + c, b))
            e.add((b, 20 * (r + 1) + c))
    return e


def lattice(L=4, M=2, N=2):
    s = list(itertools.product(range(L), range(M), range(N)))
    idx = {v: i for i, v in enumerate(s)}
    E = []
    for (x, y, z), i in idx.items():
        for d in ((1, 0, 0), (0, 1, 0), (0, 0, 1)):
            t = (x + d[0], y + d[1], z + d[2])
            if t in idx:
                E.append((i, idx[t]))
    return s, E


def evaluate(place, edges=None):
    """place: {site index: qubit}. Returns (CZ per step, max path, load per qubit, unreachable bonds)."""
    edges = edges or heron_edges()
    adj = collections.defaultdict(set)
    for a, b in edges:
        adj[a].add(b)
        adj[b].add(a)
    data = set(place.values())
    s, E = lattice()
    cz, longest, load, bad = 0, 0, collections.Counter(), []
    for i, j in E:
        a, b = place[i], place[j]
        prev = {a: None}
        q = collections.deque([a])
        while q:
            u = q.popleft()
            if u == b:
                break
            for w in sorted(adj[u]):
                if w not in prev and (w == b or w not in data):
                    prev[w] = u
                    q.append(w)
        if b not in prev:
            bad.append((i, j))
            continue
        path = [b]
        while prev[path[-1]] is not None:
            path.append(prev[path[-1]])
        d = len(path) - 1
        cz += 2 * (d - 1) + 1
        longest = max(longest, d)
        for u in path[1:-1]:
            load[u] += 1
    return cz, longest, load, bad
