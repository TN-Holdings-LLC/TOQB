"""Desk study (home, 2026-11-12; owner 08:31 JST): spreading from a weakly polarised wall (infinite temperature, linear
response), same Floquet XXZ brickwork of fSim(theta, phi) as dw_scan.py. Exact statevector on N qubits with quantum
typicality: with one Haar-random |psi>, S(t) = <psi| U^-t Z_R U^t Z_L |psi> / 4 (Z_L, Z_R: total Z of the left and
right halves) equals the transferred magnetization per unit of wall polarisation up to an error ~ 2^(-N/2).
Expected (integrable Floquet XXZ at infinite temperature): phi < 2 theta ballistic (S ~ t), phi = 2 theta
superdiffusive (t^(2/3)), phi > 2 theta diffusive (t^(1/2), the Ohmic case).
usage: python inf_temp.py N CYCLES THETA PHI [PHI ...] [--seed S]
"""
import sys
import time

import numpy as np


def fsim(theta, phi):
    c, s = np.cos(theta), np.sin(theta)
    return np.array([[1, 0, 0, 0], [0, c, -1j * s, 0], [0, -1j * s, c, 0], [0, 0, 0, np.exp(-1j * phi)]])


def apply2(psi, G, q, n):
    """psi: shape (2,)*n; G on qubits (q, q + 1) (qubit 0 = axis 0)."""
    psi = np.moveaxis(psi, (q, q + 1), (0, 1))
    sh = psi.shape
    psi = (G @ psi.reshape(4, -1)).reshape(sh)
    return np.moveaxis(psi, (0, 1), (q, q + 1))


def zsum(n, lo, hi):
    """Diagonal of sum_{k in [lo, hi)} Z_k as an array of shape (2,)*n."""
    d = np.zeros((2,) * n)
    for k in range(lo, hi):
        sh = [1] * n
        sh[k] = 2
        d = d + np.array([1.0, -1.0]).reshape(sh)
    return d


def run(n, cycles, theta, phi, seed):
    rng = np.random.default_rng(seed)
    a = (rng.normal(size=2 ** n) + 1j * rng.normal(size=2 ** n)).reshape((2,) * n)
    a /= np.linalg.norm(a)
    zl, zr = zsum(n, 0, n // 2), zsum(n, n // 2, n)
    b = zl * a
    G = fsim(theta, phi)
    s = []
    for _ in range(cycles):
        for par in (0, 1):
            for q in range(par, n - 1, 2):
                a = apply2(a, G, q, n)
                b = apply2(b, G, q, n)
        s.append(float(np.real(np.vdot(a, zr * b))) / 4)
    return np.array(s)


if __name__ == "__main__":
    args = [x for x in sys.argv[1:] if not x.startswith("--")]
    seed = int(sys.argv[sys.argv.index("--seed") + 1]) if "--seed" in sys.argv else 1
    if "--seed" in sys.argv:
        args.remove(str(seed))
    n, cycles, theta = int(args[0]), int(args[1]), float(args[2])
    for phi in map(float, args[3:]):
        t0 = time.time()
        s = run(n, cycles, theta, phi, seed)
        t = np.arange(1, cycles + 1)
        dbl = [(k, np.log(s[2 * k - 1] / s[k - 1]) / np.log(2)) for k in range(1, cycles // 2 + 1)]
        print(f"N {n} theta {theta:.4f} phi {phi:.4f} (phi / 2 theta = {phi / (2 * theta):.2f}) seed {seed} {time.time() - t0:.0f} s")
        print("  S(t): " + " ".join(f"{x:.3f}" for x in s))
        print("  exponent over t -> 2t: " + " ".join(f"{k}->{2 * k}: {e:.2f}" for k, e in dbl))
