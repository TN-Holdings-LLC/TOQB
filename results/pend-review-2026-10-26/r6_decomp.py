"""Review 6: (a) the block H(b), CX(b,a), CX(a,b), H(a) equals CZ then SWAP (exactly, including global phase);
(b) does CZ.SWAP have a 2-CZ decomposition whose hub-side (qubit a) outer single-qubit gates are diagonal (so that
they commute with the hub's plain CZs and merge into the layer gates)? Numerical least squares, 300 restarts per
case; a residual near 0 means yes. Analysis only, nothing here is used at compile time."""
import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator
from scipy.optimize import least_squares
ref = QuantumCircuit(2); ref.cz(0, 1); ref.swap(0, 1)
for a, b in ((0, 1), (1, 0)):
    d = QuantumCircuit(2); d.h(b); d.cx(b, a); d.cx(a, b); d.h(a)
    print(f"(a) block on (a, b) = ({a}, {b}) equals CZ then SWAP exactly:", np.allclose(Operator(d).data, Operator(ref).data))
CZ = np.diag([1, 1, 1, -1]).astype(complex)
SW = np.array([[1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0], [0, 0, 0, 1]], complex)
target = SW @ CZ
def u3(t, p, l):
    return np.array([[np.cos(t / 2), -np.exp(1j * l) * np.sin(t / 2)], [np.exp(1j * p) * np.sin(t / 2), np.exp(1j * (p + l)) * np.cos(t / 2)]])
def rz(x): return np.diag([np.exp(-0.5j * x), np.exp(0.5j * x)])
def fit(df, dl):
    def build(x):
        i = 0
        A1 = rz(x[i]) if df else u3(*x[i:i + 3]); i += 1 if df else 3
        A3 = rz(x[i]) if dl else u3(*x[i:i + 3]); i += 1 if dl else 3
        B1, A2, B2, B3 = (u3(*x[i + 3 * j:i + 3 + 3 * j]) for j in range(4))
        return np.kron(A3, B3) @ CZ @ np.kron(A2, B2) @ CZ @ np.kron(A1, B1)
    nx = (1 if df else 3) + (1 if dl else 3) + 12
    def res(x):
        U = build(x); ph = np.vdot(target.ravel(), U.ravel()); ph = ph / abs(ph)
        d = (U - ph * target).ravel(); return np.concatenate([d.real, d.imag])
    rng = np.random.default_rng(1); best = None
    for _ in range(300):
        r = least_squares(res, rng.uniform(-np.pi, np.pi, nx))
        if best is None or r.cost < best.cost: best = r
        if r.cost < 1e-20: break
    return best.cost
for df, dl in ((True, True), (True, False), (False, True), (False, False)):
    print(f"(b) hub gate before the block diagonal={df}, after={dl}: best residual {fit(df, dl):.2e}")
