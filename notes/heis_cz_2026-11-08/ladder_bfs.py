"""One heavy-hex row of the folded 4 x 2 x 2 layout holds two lattice rows (blocks z = 0, 1; block 1 mirrored) on a
line of 8 qubits. Lattice bonds on that line: the x-chains 0-1-2-3 and 0'-1'-2'-3' and the z-rungs k-k'.
Operations on neighbouring qubits, each 3 CZ: U (a bond, no move), SWAP.U (a bond riding on the swap), SWAP (empty).
Every bond once per step. 0-1 BFS: fewest empty swaps to do all 10 bonds, from the start arrangement to any end.
Option --stay-blocks forbids swaps across the junction (the present scheme: sites stay in their blocks).
Option --bridge P1,P2: every site must also stand on one of these line positions at some moment (y-bond through the
bridge), as an extra 8 bits."""
import itertools, sys
import numpy as np

stay = "--stay-blocks" in sys.argv
bridge = None
for a in sys.argv:
    if a.startswith("--bridge="):
        bridge = [int(v) for v in a.split("=")[1].split(",")]
n = 8
edges = [(0, 1), (1, 2), (2, 3), (4, 5), (5, 6), (6, 7), (0, 4), (1, 5), (2, 6), (3, 7)]
eid = {frozenset(e): i for i, e in enumerate(edges)}
start = (0, 1, 2, 3, 7, 6, 5, 4)
perms = list(itertools.permutations(range(n)))
rank = {p: i for i, p in enumerate(perms)}
P = np.array(perms, dtype=np.int8)
T = np.zeros((len(perms), n - 1), dtype=np.int32)
B = np.full((len(perms), n - 1), -1, dtype=np.int16)
for i, p in enumerate(perms):
    for e in range(n - 1):
        q = list(p); q[e], q[e + 1] = q[e + 1], q[e]
        T[i, e] = rank[tuple(q)]
        B[i, e] = eid.get(frozenset((p[e], p[e + 1])), -1)
nb = 10 + (8 if bridge else 0)
full = (1 << nb) - 1
# bridge bits: site s on a bridge position -> bit 10 + s
if bridge:
    BR = np.zeros(len(perms), dtype=np.int64)
    for pos in bridge:
        BR |= (1 << (10 + P[:, pos].astype(np.int64)))
nstate = len(perms) << nb
dist = np.full(nstate, -1, dtype=np.int8)

def key(r, m):
    return (r.astype(np.int64) << nb) | m

def addbr(r, m):
    return m | BR[r] if bridge else m

r0 = np.arange(len(perms)) if '--all-starts' in sys.argv else np.array([rank[start]])
m0 = addbr(r0, np.zeros(len(r0), dtype=np.int64))
front = key(r0, m0); dist[front] = 0
cost = 0
while True:
    # closure under free moves (bond ops) at this cost
    new = front
    while len(new):
        r = (new >> nb).astype(np.int64); m = new & ((1 << nb) - 1)
        out = []
        for e in range(n - 1):
            b = B[r, e].astype(np.int64)
            ok = (b >= 0) & (((m >> np.maximum(b, 0)) & 1) == 0)
            if stay:
                ok &= (e != 3)       # positions 3-4 are the junction: a bond there is allowed, a swap is not
            rr, mm = r[ok], m[ok] | (1 << b[ok])
            out.append(key(rr, addbr(rr, mm)))          # U, no move
            if True:
                okm = (b >= 0) & (((m >> np.maximum(b, 0)) & 1) == 0)
                if stay:
                    okm &= (e != 3)
                rs, ms = T[r[okm], e], m[okm] | (1 << b[okm])
                out.append(key(rs, addbr(rs, ms)))      # SWAP.U
        # junction bond without swap when stay (allowed above only if e != 3) -> add it back
        if stay:
            e = 3
            b = B[r, e].astype(np.int64)
            ok = (b >= 0) & (((m >> np.maximum(b, 0)) & 1) == 0)
            rr, mm = r[ok], m[ok] | (1 << b[ok])
            out.append(key(rr, addbr(rr, mm)))
        cand = np.unique(np.concatenate(out)) if out else np.array([], dtype=np.int64)
        cand = cand[dist[cand] < 0]
        dist[cand] = cost
        front = np.concatenate([front, cand]); new = cand
    done = front[(front & ((1 << nb) - 1)) == full]
    if len(done):
        ends = [tuple(int(v) for v in P[k >> nb]) for k in done[:4]]
        print(f"fewest empty swaps per step on one row-line: {cost}  ({len(done)} end states; e.g. {ends})")
        break
    # one empty swap
    r = (front >> nb).astype(np.int64); m = front & ((1 << nb) - 1)
    out = []
    for e in range(n - 1):
        if stay and e == 3:
            continue
        rs = T[r, e]
        out.append(key(rs, addbr(rs, m)))
    cand = np.unique(np.concatenate(out)); cand = cand[dist[cand] < 0]
    cost += 1; dist[cand] = cost; front = cand
    print(f"cost {cost}: {len(front)} states", flush=True)
