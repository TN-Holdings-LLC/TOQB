"""Noiseless <Z> of qubit 0 for TOQB's ring classifier by a direct statevector, on numpy or cupy (2026-10-27).

`fold_lam` computes its noiseless reference with Qiskit's `Statevector` on the CPU, which takes minutes per input at
22-24 qubits. This module applies the same gates as `task_loop.model_circuit` (per layer: RY on every qubit, then RY
and RZ on every qubit, then the CZ ring; a final RY on every qubit) to a complex128 state with numpy or cupy, and
returns 1 - 2 P(qubit 0 = 1), Qiskit's qubit order (qubit q is bit q of the basis index).

    python -m toqb.noiseless_xp check [n ...]     compare with Qiskit's Statevector on random models (numpy and, if
                                                   TOQB_XP=cupy, cupy); prints the largest difference
"""
from __future__ import annotations

import os
import sys

import numpy as np


def _xp(name=None):
    name = name or os.environ.get("TOQB_XP", "numpy")
    if name == "cupy":
        import cupy
        return cupy
    return np


def z0(angles, n, L, xp=np):
    """<Z> of qubit 0 after the model with these angles (the order of `task_loop.angle_list`)."""
    a = np.asarray([float(v) for v in angles], dtype=np.float64)
    psi = xp.zeros(2 ** n, dtype=xp.complex128)
    psi[0] = 1.0
    it = iter(a)

    def one(m, q):  # 2x2 matrix m on qubit q: axis of bit q in a C-order (high, 2, low) view
        nonlocal psi
        v = psi.reshape(2 ** (n - 1 - q), 2, 2 ** q)
        a0, a1 = v[:, 0, :].copy(), v[:, 1, :].copy()
        v[:, 0, :] = m[0][0] * a0 + m[0][1] * a1
        v[:, 1, :] = m[1][0] * a0 + m[1][1] * a1

    def ry(t, q):
        c, s = np.cos(t / 2), np.sin(t / 2)
        one(((c, -s), (s, c)), q)

    def rz(t, q):
        v = psi.reshape(2 ** (n - 1 - q), 2, 2 ** q)
        v[:, 0, :] *= np.exp(-0.5j * t)
        v[:, 1, :] *= np.exp(0.5j * t)

    def cz(p, q):
        lo, hi = min(p, q), max(p, q)
        v = psi.reshape(2 ** (n - 1 - hi), 2, 2 ** (hi - lo - 1), 2, 2 ** lo)
        v[:, 1, :, 1, :] *= -1

    for _ in range(L):
        for q in range(n):
            ry(next(it), q)
        for q in range(n):
            ry(next(it), q)
            rz(next(it), q)
        for q in range(n):
            cz(q, (q + 1) % n)
    for q in range(n):
        ry(next(it), q)
    p = psi.reshape(2 ** (n - 1), 2)  # bit 0 is the last axis
    p1 = float(xp.sum(xp.abs(p[:, 1]) ** 2))
    return 1.0 - 2.0 * p1


def _check(ns):
    from qiskit.quantum_info import Statevector
    from toqb import task_loop as TL
    worst = 0.0
    names = ["numpy"] + (["cupy"] if os.environ.get("TOQB_XP") == "cupy" else [])
    for n in ns:
        for L in (2, 16):
            rng = np.random.default_rng(1000 * n + L)
            theta = rng.uniform(-1, 1, TL.n_params(n, L))
            for _ in range(3):
                x = rng.uniform(-1, 1, n)
                ang = TL.angle_list(theta, x, n, L, np.pi / 2)
                q = TL.model_circuit(ang, n, L).remove_final_measurements(inplace=False)
                ref = 1 - 2 * Statevector(q).probabilities([0])[1]
                for nm in names:
                    d = abs(z0(ang, n, L, _xp(nm)) - ref)
                    worst = max(worst, d)
                    print(f"n {n} L {L} {nm}: |diff| {d:.2e}", flush=True)
    print(f"largest |diff| {worst:.2e}", "PASS" if worst < 1e-9 else "FAIL")
    return 0 if worst < 1e-9 else 1


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "check":
        sys.exit(_check([int(v) for v in sys.argv[2:]] or [3, 5, 8, 12]))
    print(__doc__)
