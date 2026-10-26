"""Review 1 (workplace, independent): pend_circuit on synthetic cycles, every pendant subset.
Cycle qubits 0..m-1 in order, the pendant of cycle position p on qubit m + (rank of p). Checks, per case:
exactness on every clbit (statevector, up to the probabilities read per clbit, as tests/test_fold.p1_all), no
FoldRefused, two-qubit count == L * (n + k), every 2q gate on a physical edge (cycle edge or p-pendant edge).
usage: python r1_exhaustive.py TOQB_DIR MMAX"""
import itertools, sys
import numpy as np
sys.path.insert(0, sys.argv[1])
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector
from toqb import fold as F, task_loop as TL

def p1_all(c):
    act = sorted({c.find_bit(q).index for i in c.data for q in i.qubits if i.operation.name not in ("barrier", "delay")})
    idx = {q: k for k, q in enumerate(act)}
    s, meas = QuantumCircuit(len(act)), {}
    for i in c.data:
        if i.operation.name == "measure":
            meas[c.find_bit(i.clbits[0]).index] = idx[c.find_bit(i.qubits[0]).index]; continue
        s.append(i.operation, [idx[c.find_bit(q).index] for q in i.qubits])
    sv = Statevector(s)
    return [float(sv.probabilities([meas[k]])[1]) for k in sorted(meas)]

def model(n, L, seed):
    rng = np.random.default_rng(seed)
    return TL.model_circuit(TL.angle_list(rng.uniform(-1, 1, TL.n_params(n, L)), rng.uniform(-1, 1, n), n, L, np.pi / 2), n, L)

MMAX = int(sys.argv[2])
cases = bad = 0
worst = 0.0
for m in range(3, MMAX + 1):
    for k in range(0, m + 1):
        n = m + k
        if n > 13:
            continue
        for sub in itertools.combinations(range(m), k):
            pend = {p: m + j for j, p in enumerate(sub)}
            phys = {frozenset((i, (i + 1) % m)) for i in range(m)} | {frozenset((p, q)) for p, q in pend.items()}
            for L in (1, 2, 3):
                qc = model(n, L, 1000 * m + 10 * k + L)
                cases += 1
                try:
                    c, init, fin = F.pend_circuit(qc, list(range(m)), pend, m + k)
                except F.FoldRefused as e:
                    bad += 1; print("REFUSED", m, sub, L, e); continue
                two = [i for i in c.data if len(i.qubits) == 2 and i.operation.name != "barrier"]
                off = [i for i in two if frozenset(c.find_bit(q).index for q in i.qubits) not in phys]
                d = max(abs(a - b) for a, b in zip(p1_all(c), p1_all(qc)))
                worst = max(worst, d)
                if d > 1e-9 or len(two) != L * (n + k) or off:
                    bad += 1; print("FAIL", m, sub, L, "dist", d, "2q", len(two), "want", L * (n + k), "off-edge", len(off))
print(f"cases {cases}, failures {bad}, worst clbit distance {worst:.2e}")
