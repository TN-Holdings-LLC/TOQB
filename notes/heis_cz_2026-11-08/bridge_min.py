"""Fewest CZ to apply the Heisenberg bond U = exp(-i dt (XX+YY+ZZ)) between a and q that are only connected
through a bridge b that starts and ends in |0> (path a - b - q). Numerical: every CZ pattern of length k on the edges
(a,b), (b,q), single-qubit U3 everywhere between; best fidelity over random starts. Fidelity 1 = possible with k CZ."""
import itertools, sys
import numpy as np
from scipy.linalg import expm
from scipy.optimize import minimize

dt = float(sys.argv[1]) if len(sys.argv) > 1 else 0.05
X = np.array([[0, 1], [1, 0]], complex); Y = np.array([[0, -1j], [1j, 0]]); Z = np.diag([1, -1]).astype(complex)
U = expm(-1j * dt * (np.kron(X, X) + np.kron(Y, Y) + np.kron(Z, Z)))      # on (a, q)
I2 = np.eye(2)

def u3(t, p, l):
    return np.array([[np.cos(t / 2), -np.exp(1j * l) * np.sin(t / 2)],
                     [np.exp(1j * p) * np.sin(t / 2), np.exp(1j * (p + l)) * np.cos(t / 2)]])

def k3(A, B, C):            # qubit order (a, b, q)
    return np.kron(np.kron(A, B), C)

CZab = np.diag([1, 1, 1, 1, 1, 1, -1, -1]).astype(complex)       # a=1,b=1
CZbq = np.diag([1, 1, 1, -1, 1, 1, 1, -1]).astype(complex)       # b=1,q=1

def circuit(x, pat):
    V = np.eye(8, dtype=complex)
    x = x.reshape(-1, 9)
    for j, e in enumerate(pat):
        V = (CZab if e == 0 else CZbq) @ k3(u3(*x[j, :3]), u3(*x[j, 3:6]), u3(*x[j, 6:])) @ V
    return k3(u3(*x[-1, :3]), u3(*x[-1, 3:6]), u3(*x[-1, 6:])) @ V

idx0 = [0, 1, 4, 5]          # basis states with b = 0: (a, b, q) = (0,0,0),(0,0,1),(1,0,0),(1,0,1)

def infid(x, pat):
    V = circuit(x, pat)
    M = V[np.ix_(idx0, idx0)]          # <b=0| V |b=0> on (a, q)
    return 1 - abs(np.trace(U.conj().T @ M)) / 4

rng = np.random.default_rng(1)
starts = int(sys.argv[2]) if len(sys.argv) > 2 else 20
ks = [int(v) for v in sys.argv[3].split(",")] if len(sys.argv) > 3 else [5, 6, 7]

def best_for(pat):
    b = 1.0
    for _ in range(starts):
        x0 = rng.uniform(0, 2 * np.pi, 9 * (len(pat) + 1))
        r = minimize(infid, x0, args=(pat,), method="L-BFGS-B", options=dict(maxiter=3000))
        b = min(b, r.fun)
        if b < 1e-10:
            break
    return b

# sanity: the known 7-CZ construction (move a onto b: 2, bond on (b, q): 3, move back: 2)
print(f"dt {dt}: sanity, pattern ab ab bq bq bq ab ab -> {best_for((0, 0, 1, 1, 1, 0, 0)):.1e}", flush=True)
for k in ks:
    res = sorted((best_for(p), p) for p in itertools.product((0, 1), repeat=k)
                 if 0 in p and 1 in p)
    b, p = res[0]
    print(f"k = {k} CZ: best infidelity {b:.1e}  pattern {' '.join('ab' if e == 0 else 'bq' for e in p)}", flush=True)
