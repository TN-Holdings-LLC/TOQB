"""Review 2: structural check for larger n (no statevector). Replays pend_circuit's output: plain cz = CZ on the
ring nodes held; the 4-instruction block h(b), cx(b,a), cx(a,b), h(a) = CZ then SWAP. Per layer every ring edge
must get exactly one CZ, single-qubit layer gates must land on the qubit holding their ring node, and measurements
on the right qubit. Also the 2q count. Every pendant subset for m <= MMAX (n up to 2m-1), L = 3.
usage: python r2_structural.py TOQB_DIR MMAX"""
import itertools, sys
import numpy as np
sys.path.insert(0, sys.argv[1])
from toqb import fold as F, task_loop as TL

def check(m, sub, L):
    k = len(sub); n = m + k
    pend = {p: m + j for j, p in enumerate(sub)}
    qc = TL.model_circuit(TL.angle_list(np.linspace(-1, 1, TL.n_params(n, L)), np.linspace(-.5, .5, n), n, L, np.pi / 2), n, L)
    _, layers, final, meas = F.read_ring(qc)
    c, init, fin = F.pend_circuit(qc, list(range(m)), pend, m + k)
    holder = {q: i for i, q in enumerate(init)}         # device qubit -> ring node
    ins = [(i.operation, [c.find_bit(q).index for q in i.qubits], [c.find_bit(b).index for b in i.clbits]) for i in c.data]
    j, layer, done, ones = 0, 0, [], [[] for _ in range(n)]
    def close_layer():
        nonlocal done, ones, layer
        want = {frozenset((i, (i + 1) % n)) for i in range(n)}
        got = [frozenset(e) for e in done]
        assert sorted(map(sorted, got)) == sorted(map(sorted, want)), ("layer edges", layer)
        for i in range(n):
            assert [o.name for o in ones[i]] == [o.name for o in layers[layer][i]], ("1q ops", layer, i)
        done, ones, layer = [], [[] for _ in range(n)], layer + 1
    two = 0
    while j < len(ins):
        op, qs, cl = ins[j]
        if op.name == "h":
            b = qs[0]
            o1, o2, o3 = ins[j + 1], ins[j + 2], ins[j + 3]
            a = o1[1][1]
            assert o1[0].name == "cx" and o1[1] == [b, a] and o2[0].name == "cx" and o2[1] == [a, b] and o3[0].name == "h" and o3[1] == [a]
            done.append((holder[a], holder[b])); two += 2
            holder[a], holder[b] = holder[b], holder[a]
            j += 4; continue
        if op.name == "cz":
            done.append((holder[qs[0]], holder[qs[1]])); two += 1
        elif op.name == "measure":
            if done: close_layer()
            assert holder[qs[0]] == next(q for q, cc in meas if cc == cl[0]), "measure"
        elif len(qs) == 1:
            if len(done) == n: close_layer()
            if layer < len(layers):
                ones[holder[qs[0]]].append(op)
        j += 1
    if done: close_layer()
    assert layer == len(layers)
    assert two == L * (n + k), ("2q", two)

MMAX = int(sys.argv[2]); fails = cases = 0
for m in range(3, MMAX + 1):
    for k in range(0, m + 1):
        for sub in itertools.combinations(range(m), k):
            cases += 1
            try:
                check(m, sub, 3)
            except F.FoldRefused:
                fails += 1
                if k != m: print("REFUSED with k < m:", m, sub)
            except AssertionError as e:
                fails += 1; print("WRONG", m, sub, e)
print(f"cases {cases}, refused or wrong {fails} (all-pendant cases k = m: {MMAX - 2})")
