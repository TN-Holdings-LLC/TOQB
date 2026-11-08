"""Fewest empty swaps on one 8-qubit row-line of the folded 4x2x2 layout, any start arrangement, with the y-bond
condition (every site stands on a bridge position BR at some moment). State = (arrangement, 10 bond bits, 8 visit
bits); visited set as a bitset (40320 x 2^18 bits = 1.3 GB). Prints one schedule.
usage: python ladder_bits.py 3,7 [maxcost]"""
import itertools, sys, time
import numpy as np

br = [int(v) for v in sys.argv[1].split(",")]
maxcost = int(sys.argv[2]) if len(sys.argv) > 2 else 3
edges = [(0, 1), (1, 2), (2, 3), (4, 5), (5, 6), (6, 7), (0, 4), (1, 5), (2, 6), (3, 7)]
names = ["0", "1", "2", "3", "0'", "1'", "2'", "3'"]
eid = {frozenset(e): i for i, e in enumerate(edges)}
perms = list(itertools.permutations(range(8)))
rank = {p: i for i, p in enumerate(perms)}
P = np.array(perms, dtype=np.int8)
T = np.zeros((len(perms), 7), dtype=np.int64)
B = np.full((len(perms), 7), -1, dtype=np.int64)
for i, p in enumerate(perms):
    for e in range(7):
        q = list(p); q[e], q[e + 1] = q[e + 1], q[e]
        T[i, e] = rank[tuple(q)]
        B[i, e] = eid.get(frozenset((p[e], p[e + 1])), -1)
NB = 18
VIS = np.zeros(len(perms), dtype=np.int64)
for pos in br:
    VIS |= 1 << (10 + P[:, pos].astype(np.int64))
FULL = (1 << NB) - 1
LOW = (1 << NB) - 1
bits = np.zeros((len(perms) << NB) >> 3, dtype=np.uint8)

def seen(k):
    return (bits[k >> 3] >> (k & 7)) & 1

def mark(k):
    np.bitwise_or.at(bits, k >> 3, (1 << (k & 7)).astype(np.uint8))

# history for reconstruction: list of (child, parent, op) arrays; op = 100*kind + e (kind 0 U, 1 SWAP.U, 2 SWAP)
hist = []
r = np.arange(len(perms), dtype=np.int64)
front = (r << NB) | VIS[r]
mark(front)
hist.append((front, np.full(len(front), -1, dtype=np.int64), np.full(len(front), -1, dtype=np.int16)))
t0 = time.time()

def expand_free(states):
    r = states >> NB; m = states & LOW
    ch, pa, op = [], [], []
    for e in range(7):
        b = B[r, e]
        ok = (b >= 0) & (((m >> np.maximum(b, 0)) & 1) == 0)
        rr, mm, ss = r[ok], m[ok] | (1 << b[ok]), states[ok]
        ch.append((rr << NB) | mm | VIS[rr]); pa.append(ss); op.append(np.full(len(ss), e, np.int16))
        rs = T[rr, e]
        ch.append((rs << NB) | mm | VIS[rs]); pa.append(ss); op.append(np.full(len(ss), 100 + e, np.int16))
    return np.concatenate(ch), np.concatenate(pa), np.concatenate(op)

def keep_new(ch, pa, op):
    ch, i = np.unique(ch, return_index=True)
    pa, op = pa[i], op[i]
    new = seen(ch) == 0
    ch, pa, op = ch[new], pa[new], op[new]
    mark(ch)
    return ch, pa, op

for cost in range(maxcost + 1):
    layer = [front]
    new = front
    while len(new):
        ch, pa, op = expand_free(new)
        new, pa, op = keep_new(ch, pa, op)
        hist.append((new, pa, op)); layer.append(new)
    allc = np.concatenate(layer)
    hit = allc[(allc & LOW) == FULL]
    print(f"cost {cost}: states this layer {len(allc)}; complete {len(hit)}  ({time.time() - t0:.0f} s)", flush=True)
    if len(hit):
        break
    r = allc >> NB; m = allc & LOW
    ch, pa, op = [], [], []
    for e in range(7):
        rs = T[r, e]
        ch.append((rs << NB) | m | VIS[rs]); pa.append(allc); op.append(np.full(len(allc), 200 + e, np.int16))
    front, pa, op = keep_new(np.concatenate(ch), np.concatenate(pa), np.concatenate(op))
    hist.append((front, pa, op))

if len(hit):
    # backtrack through hist (search each array for the child; arrays are sorted by np.unique)
    s = int(hit[0]); ops = []
    while True:
        found = False
        for ch, pa, op in hist:
            j = np.searchsorted(ch, s)
            if j < len(ch) and ch[j] == s:
                if pa[j] < 0:
                    found = None
                else:
                    o = int(op[j]); p_ = int(pa[j])
                    perm = perms[p_ >> NB]; e = o % 100; kind = o // 100
                    ops.append(f"{['U', 'SWAP.U', 'SWAP'][kind]}({names[perm[e]]},{names[perm[e + 1]]})@{e}")
                    s = p_; found = True
                break
        if found is not True:
            break
    print("start", [names[v] for v in perms[s >> NB]], " end", [names[v] for v in perms[int(hit[0]) >> NB]])
    print("ops:", " ; ".join(reversed(ops)))
