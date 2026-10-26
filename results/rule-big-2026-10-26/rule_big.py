"""fold:rule for n = 20-30 on snapshot:marrakesh: the choice, two-qubit gates per layer, and exactness on every clbit
by Clifford simulation (every rotation angle set to a random multiple of pi/2; 3 instances per (n, L))."""
import sys, time
sys.path.insert(0, "/tmp/claude-0/work/toqb"); sys.path.insert(0, "/tmp/claude-0/work/toqb/tests")
import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import StabilizerState
from test_fold import model
from toqb import s2r as S
from toqb.devices import get_device

def cliffordize(qc, rng):
    out = qc.copy_empty_like()
    for i in qc.data:
        op = i.operation
        if op.params:
            op = op.to_mutable(); op.params = [float(rng.integers(4)) * np.pi / 2 for _ in op.params]
        out.append(op, i.qubits, i.clbits)
    return out

def marg(c):
    s, meas = QuantumCircuit(c.num_qubits), {}
    for i in c.data:
        nm = i.operation.name
        if nm in ("barrier", "delay"):
            continue
        if nm == "measure":
            meas[c.find_bit(i.clbits[0]).index] = c.find_bit(i.qubits[0]).index; continue
        s.append(i.operation, [c.find_bit(q).index for q in i.qubits])
    st = StabilizerState(s)
    return [float(st.probabilities([meas[k]])[1]) for k in sorted(meas)]

dev = get_device("snapshot:marrakesh")
arm = S.Arm("fold:rule", dev)
for n in range(20, 31):
    for L in (2, 4):
        rng = np.random.default_rng(n * 10 + L)
        try:
            base = model(n, L, 10 * n + L)
            c0 = arm.compile(base)
        except Exception as e:
            print(n, L, "refused:", str(e)[:90]); break
        q2 = sum(1 for i in c0.data if len(i.qubits) == 2) / L
        act = len({c0.find_bit(q).index for i in c0.data for q in i.qubits})
        worst = 0.0
        for _ in range(3):
            qc = cliffordize(base, rng)
            c = arm.compile(qc)
            worst = max(worst, max(abs(a - b) for a, b in zip(marg(c), marg(qc))))
        print(n, L, arm.arm.stats["choice"], "m", arm.arm.stats["last"]["m"], "q2/layer", q2, "active", act, "clifford worst", worst, flush=True)
