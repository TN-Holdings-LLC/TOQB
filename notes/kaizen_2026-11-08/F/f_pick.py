"""F1: among many zero-empty-swap line schedules (bridges 1, 5), which one gives the fewest CZ at t = 4 after the
step-boundary merges (heis3d _line_build's y merge + rule A)? Enumerate schedules by depth-first search over bond
operations (U in place, SWAP.U) from every start arrangement, every site on a bridge position once; count CZ by
operation (3 per two-qubit block, 4 CX per y move pair + 3 per y block) and check the best with RuleCompiler and
heis3d.placed_check on the fez record."""
import itertools, sys, random
import heis3d as H
import line_merge as LM

BR = (1, 5)
edges = [(0, 1), (1, 2), (2, 3), (4, 5), (5, 6), (6, 7), (0, 4), (1, 5), (2, 6), (3, 7)]
eset = {frozenset(e) for e in edges}
limit = int(sys.argv[2]) if len(sys.argv) > 2 else 20000
found = []

def dfs(arr, done, vis, ops):
    if len(found) >= limit:
        return
    if len(done) == 10:
        if len(vis) == 8:
            found.append((tuple(start), list(ops)))
        return
    for e in range(7):
        pr = frozenset((arr[e], arr[e + 1]))
        if pr in eset and pr not in done:
            for kind in ("SWAP.U", "U"):
                a2 = list(arr)
                if kind == "SWAP.U":
                    a2[e], a2[e + 1] = a2[e + 1], a2[e]
                v2 = vis | {a2[p] for p in BR}
                # prune: sites still unvisited must be able to reach a bridge (cheap bound skipped)
                ops.append((kind, e)); dfs(a2, done | {pr}, v2, ops); ops.pop()

random.seed(1)
starts = list(itertools.permutations(range(8))); random.shuffle(starts)
for start in starts:
    dfs(list(start), frozenset(), {start[p] for p in BR}, [])
    if len(found) >= limit:
        break
print(f"schedules enumerated: {len(found)}")

def text(start, ops):
    return [H._NAMES[v] for v in start], " ; ".join(f"{k}(a,b)@{e}" for k, e in ops)

def cz_count(start, ops, t=4):
    H.LINE_SCHEDULES[BR] = text(start, ops)
    A = list(range(8)); B = list(range(8, 16)); bl = {1: 16, 5: 17}
    try:
        out, s0, end, log = H._line_build(A, B, bl, BR, t, 0.05, 1.0)
    except RuntimeError:
        return None
    n = 0
    for op in LM.merge(LM.to_L(out)):
        if op[0] in ("y", "yy"):
            n += 7
        else:
            n += 2 * 3        # both lines, one block (or swap) each
    return n

orig = H.LINE_SCHEDULES[BR]
scores = []
for st, ops in found:
    c = cz_count(st, ops)
    if c is not None:
        scores.append((c, st, ops))
scores.sort(key=lambda x: x[0])
H.LINE_SCHEDULES[BR] = orig
base = cz_count(tuple(H._NAMES.index(v) for v in orig[0]), H._parse_ops(orig[1]))
print(f"present schedule: {base} CZ at t4 by op count;  best of {len(scores)}: {scores[0][0]};  worst: {scores[-1][0]}")
from collections import Counter
print("distribution:", sorted(Counter(s[0] for s in scores).items())[:10])
best = scores[0]
print("best start", [H._NAMES[v] for v in best[1]], "ops", best[2])
import json
json.dump(dict(start=[H._NAMES[v] for v in best[1]], ops=best[2]), open("f_best.json", "w"))
# check with RuleCompiler on fez
from qiskit import QuantumCircuit
from psf_os import device as Dv, mirror2d as Mi
from psf_os.compile import RuleCompiler
dev = Dv.Device.load(sys.argv[1]); rc = RuleCompiler(dev)
for label, sched in (("present", orig), ("best", text(best[1], best[2]))):
    H.LINE_SCHEDULES[BR] = sched
    for t in (1, 2, 3, 4):
        qc, placed, used, log, where, ops = LM.physical_line_merged(dev, t, 0.05)
        used_now = sorted({qc.find_bit(q).index for ins in qc.data for q in ins.qubits})
        se, be = H.placed_check(qc, placed, used_now, 4, 2, 2, log, 0.05)
        f = QuantumCircuit(dev.num_qubits); f.compose(qc, qubits=list(range(qc.num_qubits)), inplace=True)
        print(f"{label:7} t {t}: RuleCompiler {Mi.cz_count(rc.pm.run(f))}  placed-exact {se:.1e}  bridge {be:.1e}")
