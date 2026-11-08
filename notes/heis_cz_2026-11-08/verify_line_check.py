"""Build the 4x2x2 Heisenberg circuit with a line schedule found by ladder_bits.py on the 18-qubit fold region
(two 8-qubit row-lines A (y = 0) and B (y = 1), bridges at line positions BR), alternate forward / reversed steps,
count CZ after synthesis, and compare the placed <Z> with the exact Trotter product of the logged bond order.
usage: python verify_line.py 1,5 "<start>" "<ops>" [t_max] [dt]"""
import sys, re
import numpy as np
from scipy.linalg import expm
from qiskit import QuantumCircuit, transpile
from qiskit.circuit.library import UnitaryGate
from qiskit.quantum_info import Statevector

br = [int(v) for v in sys.argv[1].split(",")]
names = ["0", "1", "2", "3", "0'", "1'", "2'", "3'"]
start = [names.index(v) for v in eval(sys.argv[2])]
ops = []
for o in sys.argv[3].split(";"):
    m = re.match(r"\s*(U|SWAP\.U|SWAP)\((\S+?),(\S+?)\)@(\d)", o)
    ops.append((m.group(1), int(m.group(4))))
tmax = int(sys.argv[4]) if len(sys.argv) > 4 else 4
dt = float(sys.argv[5]) if len(sys.argv) > 5 else 0.05
X = np.array([[0, 1], [1, 0]], complex); Y = np.array([[0, -1j], [1j, 0]]); Z = np.diag([1, -1]).astype(complex)
SW = np.eye(4)[[0, 2, 1, 3]]
Ub = expm(-1j * dt * (np.kron(X, X) + np.kron(Y, Y) + np.kron(Z, Z)))
U, SU = UnitaryGate(Ub, label="heis"), UnitaryGate(SW @ Ub, label="swap_heis")
A = list(range(8)); Bq = list(range(8, 16)); bridge = {p: 16 + i for i, p in enumerate(br)}

def site(name, y):            # lattice site index: (x, y, z) -> x + 4 y + 8 z
    x, z = name % 4, name // 4
    return x + 4 * y + 8 * z

def neighbours(s1, s2):
    a = np.array([s1 % 4, (s1 // 4) % 2, s1 // 8]); b = np.array([s2 % 4, (s2 // 4) % 2, s2 // 8])
    return abs(a - b).sum() == 1

def build(t):
    qc = QuantumCircuit(18)
    arr = list(start)
    for y in (0, 1):
        for p in range(8):
            s = site(arr[p], y)
            if (s % 4 + (s // 4) % 2 + s // 8) % 2 == 1:
                qc.x((A if y == 0 else Bq)[p])
    log = []
    for step in range(t):
        seq = ops if step % 2 == 0 else list(reversed(ops))
        ydone = set()

        def ybonds():
            for p in br:
                if arr[p] not in ydone:
                    a, b, q = A[p], bridge[p], Bq[p]
                    qc.cx(a, b); qc.cx(b, a); qc.append(U, [b, q]); qc.cx(b, a); qc.cx(a, b)
                    log.append((site(arr[p], 0), site(arr[p], 1))); ydone.add(arr[p])
        ybonds()
        for kind, e in seq:
            for line, y in ((A, 0), (Bq, 1)):
                s1, s2 = site(arr[e], y), site(arr[e + 1], y)
                if kind == "SWAP":
                    qc.swap(line[e], line[e + 1])
                else:
                    assert neighbours(s1, s2), (kind, e, s1, s2)
                    qc.append(U if kind == "U" else SU, [line[e], line[e + 1]])
                    log.append((s1, s2))
            if kind != "U":
                arr[e], arr[e + 1] = arr[e + 1], arr[e]
            ybonds()
        assert len(ydone) == 8, ydone
    return qc, arr, log

for t in range(1, tmax + 1):
    qc, arr, log = build(t)
    assert len(log) == 28 * t and len({frozenset(b) for b in log[-28:]}) == 28
    tq = transpile(qc, basis_gates=["cz", "rz", "sx", "x"], optimization_level=int(__import__("os").environ.get("OPT", "1")))
    cz = tq.count_ops().get("cz", 0)
    # the compiled circuit itself against the uncompiled one (state fidelity; layout fixed: no coupling map)
    fid = abs(np.vdot(Statevector(qc).data, Statevector(tq).data)) ** 2
    # placed <Z>
    p = Statevector(qc).probabilities(); idx = np.arange(len(p))
    zq = lambda q: float(np.sum(p * (1 - 2 * ((idx >> q) & 1))))
    placed = {}
    for y, line in ((0, A), (1, Bq)):
        for pos in range(8):
            placed[site(arr[pos], y)] = zq(line[pos])
    bridge_err = max(1 - zq(b) for b in bridge.values())
    # exact from the log
    lq = QuantumCircuit(16)
    for s in range(16):
        if (s % 4 + (s // 4) % 2 + s // 8) % 2 == 1:
            lq.x(s)
    for a_, b_ in log:
        lq.append(U, [a_, b_])
    pl = Statevector(lq).probabilities(); il = np.arange(len(pl))
    ex = {s: float(np.sum(pl * (1 - 2 * ((il >> s) & 1)))) for s in range(16)}
    err = max(abs(placed[s] - ex[s]) for s in range(16))
    ms = np.mean([(-1) ** (s % 4 + (s // 4) % 2 + s // 8) * ex[s] for s in range(16)])
    print(f"t {t}: CZ {cz} ({cz // t} per step)  max|placed - exact| {err:.1e}  bridges back to |0>: {bridge_err:.1e}"
          f"  exact m_s {ms:.4f}  compiled-vs-built fidelity {fid:.12f}")
