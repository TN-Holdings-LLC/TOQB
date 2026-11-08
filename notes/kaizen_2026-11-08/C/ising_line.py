"""Ising cost on one 8-qubit row-line of 4x2x2 (bridges at BR): RZZ(-pi/2) in place 1 CZ, SWAP.RZZ 2 CZ (psf-os
identity), empty SWAP 3 CZ; every bond once; every site on a bridge position once. Dial's algorithm (integer costs)
over (arrangement, 10 bond bits, 8 visit bits), visited bitset, any start arrangement. Prints the cheapest schedule.
usage: python ising_line.py 1,5"""
import itertools, sys, time
import numpy as np
br = [int(v) for v in sys.argv[1].split(",")]
COST = dict(U=1, SU=2, SW=3)
edges = [(0, 1), (1, 2), (2, 3), (4, 5), (5, 6), (6, 7), (0, 4), (1, 5), (2, 6), (3, 7)]
names = ["0", "1", "2", "3", "0'", "1'", "2'", "3'"]
eid = {frozenset(e): i for i, e in enumerate(edges)}
perms = list(itertools.permutations(range(8))); rank = {p: i for i, p in enumerate(perms)}
P = np.array(perms, dtype=np.int8)
T = np.zeros((len(perms), 7), np.int64); B = np.full((len(perms), 7), -1, np.int64)
for i, p in enumerate(perms):
    for e in range(7):
        q = list(p); q[e], q[e + 1] = q[e + 1], q[e]; T[i, e] = rank[tuple(q)]
        B[i, e] = eid.get(frozenset((p[e], p[e + 1])), -1)
NB = 18; LOW = (1 << NB) - 1; FULL = LOW
VIS = np.zeros(len(perms), np.int64)
for pos in br:
    VIS |= 1 << (10 + P[:, pos].astype(np.int64))
bits = np.zeros((len(perms) << NB) >> 3, np.uint8)
parent = {}
buckets = {0: [((np.arange(len(perms), dtype=np.int64) << NB) | VIS, np.full(len(perms), -1, np.int64), np.full(len(perms), -1, np.int16))]}
t0 = time.time()
c = 0
hist = []
while True:
    if c not in buckets:
        c += 1; continue
    ch = np.concatenate([b[0] for b in buckets[c]]); pa = np.concatenate([b[1] for b in buckets[c]])
    op = np.concatenate([b[2] for b in buckets[c]]); del buckets[c]
    ch, i = np.unique(ch, return_index=True); pa, op = pa[i], op[i]
    new = ((bits[ch >> 3] >> (ch & 7)) & 1) == 0
    ch, pa, op = ch[new], pa[new], op[new]
    np.bitwise_or.at(bits, ch >> 3, (1 << (ch & 7)).astype(np.uint8))
    hist.append((ch, pa, op))
    done = ch[(ch & LOW) == FULL]
    print(f"cost {c}: {len(ch)} states ({time.time() - t0:.0f} s)", flush=True)
    if len(done):
        break
    r = ch >> NB; m = ch & LOW
    for e in range(7):
        b = B[r, e]; ok = (b >= 0) & (((m >> np.maximum(b, 0)) & 1) == 0)
        rr, mm = r[ok], m[ok] | (1 << b[ok])
        buckets.setdefault(c + COST["U"], []).append(((rr << NB) | mm | VIS[rr], ch[ok], np.full(ok.sum(), e, np.int16)))
        rs = T[rr, e]
        buckets.setdefault(c + COST["SU"], []).append(((rs << NB) | mm | VIS[rs], ch[ok], np.full(ok.sum(), 100 + e, np.int16)))
        rs2 = T[r, e]
        buckets.setdefault(c + COST["SW"], []).append(((rs2 << NB) | m | VIS[rs2], ch, np.full(len(ch), 200 + e, np.int16)))
    c += 1
# backtrack
allh = [(h[0], h[1], h[2]) for h in hist]
s = int(done[0]); ops = []
while True:
    for ch, pa, op in allh:
        j = np.searchsorted(ch, s)
        if j < len(ch) and ch[j] == s:
            break
    if pa[j] < 0:
        break
    o = int(op[j]); p_ = int(pa[j]); perm = perms[p_ >> NB]; e = o % 100
    ops.append(f"{['U', 'SWAP.U', 'SWAP'][o // 100]}({names[perm[e]]},{names[perm[e + 1]]})@{e}")
    s = p_
print(f"cheapest Ising line cost per step: {c} CZ per line")
print("start", [names[v] for v in perms[s >> NB]])
print("ops:", " ; ".join(reversed(ops)))
