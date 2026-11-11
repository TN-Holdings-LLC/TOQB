"""Desk study (home, 2026-11-11 night; owner: "試して"): can a short brickwork circuit tell ballistic, superdiffusive
and diffusive spreading apart? Floquet XXZ brickwork of fSim(theta, phi) gates (even bonds, then odd bonds = one cycle)
on N qubits from a domain wall (left half |1>, right half |0>); per cycle the transferred magnetization
M(t) = sum over the right half of (1 - <Z>)/2, and the local exponent d ln M / d ln t between cycles.
Known regimes (integrable Floquet XXZ): phi < 2 theta easy-plane (ballistic, M ~ t), phi = 2 theta isotropic,
phi > 2 theta easy-axis (a pure domain wall freezes). Exact up to the MPS cap (quimb CircuitMPS, cutoff 1e-12).
usage: python dw_scan.py N CYCLES THETA PHI [PHI ...]
"""
import sys
import time

import numpy as np
import quimb.tensor as qtn


def fsim(theta, phi):
    c, s = np.cos(theta), np.sin(theta)
    return np.array([[1, 0, 0, 0], [0, c, -1j * s, 0], [0, -1j * s, c, 0], [0, 0, 0, np.exp(-1j * phi)]])


def run(n, cycles, theta, phi, chi=512):
    circ = qtn.CircuitMPS(n, max_bond=chi, cutoff=1e-12)
    X = np.array([[0, 1], [1, 0]])
    for q in range(n // 2):
        circ.apply_gate_raw(X, (q,))
    G = fsim(theta, phi)
    Z = np.diag([1.0, -1.0])
    ms = []
    for _ in range(cycles):
        for par in (0, 1):
            for q in range(par, n - 1, 2):
                circ.apply_gate_raw(G, (q, q + 1))
        z = np.array([float(np.real(circ.psi.local_expectation(Z, k))) for k in range(n // 2, n)])
        ms.append(float(np.sum((1 - z) / 2)))
    return np.array(ms), circ.psi.max_bond()


if __name__ == "__main__":
    n, cycles, theta = int(sys.argv[1]), int(sys.argv[2]), float(sys.argv[3])
    for phi in map(float, sys.argv[4:]):
        t0 = time.time()
        m, bond = run(n, cycles, theta, phi)
        t = np.arange(1, cycles + 1)
        loc = np.diff(np.log(m)) / np.diff(np.log(t))
        print(f"theta {theta:.4f} phi {phi:.4f} (phi / 2 theta = {phi / (2 * theta):.2f}) bond {bond} {time.time() - t0:.0f} s")
        print("  M(t):   " + " ".join(f"{x:.3f}" for x in m))
        print("  local exponent: " + " ".join(f"{x:.2f}" for x in loc))
