"""<Z_0> of the data re-uploading ring model (toqb.task_loop's model) without noise, for many angle lists at once:
numpy state vectors in a batch. Equal to `task_loop.exact_z0` (tested); used to run designs C and E noiselessly at
full size in seconds instead of minutes."""
from __future__ import annotations

import numpy as np

from toqb import task_loop as TL


def z0_batch(angle_lists, n, L):
    """angle_lists: (B, A) in `task_loop.angle_list`'s order. Returns (B,) <Z_0>."""
    A = np.asarray(angle_lists, float)
    B = A.shape[0]
    psi = np.zeros((B, 2 ** n), dtype=complex)
    psi[:, 0] = 1
    b = np.arange(2 ** n)
    ring = np.ones(2 ** n)
    for q in range(n):
        ring *= np.where(((b >> q) & 1) & ((b >> ((q + 1) % n)) & 1), -1, 1)
    kinds = TL.gate_kinds(n, L)
    # qubit of each gate, in angle_list's order
    qubits = []
    for _ in range(L):
        qubits += list(range(n))
        for q in range(n):
            qubits += [q, q]
    qubits += list(range(n))
    col = 0
    gate_in_layer = 3 * n
    for li in range(L + 1):
        count = n if li == L else gate_in_layer
        for j in range(count):
            kind, q, a = kinds[col], qubits[col], A[:, col]
            t = psi.reshape(B, 2 ** (n - 1 - q), 2, 2 ** q)
            if kind == "ry":
                c, s = np.cos(a / 2)[:, None, None], np.sin(a / 2)[:, None, None]
                t0, t1 = t[:, :, 0, :], t[:, :, 1, :]
                t = np.stack([c * t0 - s * t1, s * t0 + c * t1], axis=2)
            else:
                ph0, ph1 = np.exp(-0.5j * a)[:, None, None], np.exp(0.5j * a)[:, None, None]
                t = np.stack([ph0 * t[:, :, 0, :], ph1 * t[:, :, 1, :]], axis=2)
            psi = t.reshape(B, 2 ** n)
            col += 1
        if li < L:
            psi = psi * ring[None, :]
    zsign = np.where(b & 1, -1.0, 1.0)
    return (np.abs(psi) ** 2) @ zsign
