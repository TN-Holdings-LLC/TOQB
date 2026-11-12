"""Desk estimate (not declared, no device): exact transfer W(t) across a wall in an L x M x N cubic lattice under the
fSim(pi/4, pi/2) cycle (bonds along x, y, z, each in even then odd order), weak-wall strings as gpu/ohm_answers.py
(left half x < L/2 |1> with probability (1 + m) / 2, right half (1 - m) / 2), each with its complement.
W(t) = mean over strings of (M_s - M_c) / 2, M = number of |1> on the right half minus at the start.
usage: python signal3d.py L M N K STEPS [seed]"""
import itertools
import sys

import numpy as np


def fsim(theta, phi):
    c, s = np.cos(theta), np.sin(theta)
    return np.array([[1, 0, 0, 0], [0, c, -1j * s, 0], [0, -1j * s, c, 0], [0, 0, 0, np.exp(-1j * phi)]],
                    dtype=np.complex64)


def bonds(L, M, N):
    idx = {s: i for i, s in enumerate(itertools.product(range(L), range(M), range(N)))}
    out = []
    for ax in range(3):
        for parity in (0, 1):
            for s, i in idx.items():
                if s[ax] % 2 != parity:
                    continue
                t = list(s)
                t[ax] += 1
                if tuple(t) in idx:
                    out.append((i, idx[tuple(t)]))
    return out, idx


def apply2(psi, n, G, a, b):
    """Apply the 4x4 gate G to qubits a, b (qubit q = axis q of the n-axis tensor)."""
    psi = np.moveaxis(psi, (a, b), (0, 1))
    sh = psi.shape
    psi = (G @ psi.reshape(4, -1)).reshape(sh)
    return np.moveaxis(psi, (0, 1), (a, b))


def z_all(psi, n):
    p = np.abs(psi) ** 2
    return np.array([p.sum(axis=tuple(k for k in range(n) if k != q)) @ np.array([1, -1]) for q in range(n)])


def run(L, M, N, bits, steps, G):
    n = L * M * N
    psi = np.zeros([2] * n, dtype=np.complex64)
    psi[tuple(bits)] = 1
    bl, _ = bonds(L, M, N)
    out = []
    for _ in range(steps):
        for a, b in bl:
            psi = apply2(psi, n, G, a, b)
        out.append(z_all(psi, n))
    return out


if __name__ == "__main__":
    L, M, N, K, steps = map(int, sys.argv[1:6])
    seed = int(sys.argv[6]) if len(sys.argv) > 6 else 20261112
    m = 0.5
    rng = np.random.default_rng(seed)
    sites = list(itertools.product(range(L), range(M), range(N)))
    right = [i for i, s in enumerate(sites) if s[0] >= L // 2]
    G = fsim(np.pi / 4, np.pi / 2)
    W = np.zeros(steps)
    Wmix = 0.0
    for k in range(K):
        s = [int(rng.random() < ((1 + m) / 2 if st[0] < L // 2 else (1 - m) / 2)) for st in sites]
        c = [1 - x for x in s]
        Ms = []
        for b in (s, c):
            m0 = sum(b[i] for i in right)
            zs = run(L, M, N, b, steps, G)
            Ms.append([((1 - z[right]) / 2).sum() - m0 for z in zs])
            Wmix += (len(right) / 2 - m0) * (1 if b is s else -1) / 2 / K
        W += (np.array(Ms[0]) - np.array(Ms[1])) / 2 / K
        print(f"string {k} done", flush=True)
    print("L M N", L, M, N, "right qubits", len(right), "cross-section", M * N)
    print("W_exact per step", " ".join(f"{w:.3f}" for w in W))
    print("W_mixed", round(Wmix, 3))
