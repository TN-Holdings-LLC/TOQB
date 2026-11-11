"""As inf_temp.py, with integrability broken while keeping total Z conserved (home, 2026-11-12): after each cycle a
Z rotation RZ(h_k) on qubit k with a fixed non-uniform pattern h_k = H * (1, -1, 0) repeating (period 3), or the odd
gate layer with a different phi. Purpose: does a chaotic chain reach the diffusive t^(1/2) sooner?
usage: python inf_temp_break.py N CYCLES THETA PHI_EVEN PHI_ODD H [--seed S]
"""
import sys
import time

import numpy as np

from inf_temp import apply2, fsim, zsum


def run(n, cycles, theta, phi_e, phi_o, h, seed):
    rng = np.random.default_rng(seed)
    a = (rng.normal(size=2 ** n) + 1j * rng.normal(size=2 ** n)).reshape((2,) * n)
    a /= np.linalg.norm(a)
    zl, zr = zsum(n, 0, n // 2), zsum(n, n // 2, n)
    b = zl * a
    ge, go = fsim(theta, phi_e), fsim(theta, phi_o)
    pat = [h * (1, -1, 0)[k % 3] for k in range(n)]
    ph = np.ones((2,) * n, dtype=complex)
    for k, hk in enumerate(pat):
        sh = [1] * n
        sh[k] = 2
        ph = ph * np.array([np.exp(-1j * hk / 2), np.exp(1j * hk / 2)]).reshape(sh)
    s = []
    for _ in range(cycles):
        for q in range(0, n - 1, 2):
            a, b = apply2(a, ge, q, n), apply2(b, ge, q, n)
        for q in range(1, n - 1, 2):
            a, b = apply2(a, go, q, n), apply2(b, go, q, n)
        a, b = ph * a, ph * b
        s.append(float(np.real(np.vdot(a, zr * b))) / 4)
    return np.array(s)


if __name__ == "__main__":
    n, cycles, theta, pe, po, h = int(sys.argv[1]), int(sys.argv[2]), *map(float, sys.argv[3:7])
    t0 = time.time()
    s = run(n, cycles, theta, pe, po, h, 1)
    dbl = [(k, np.log(s[2 * k - 1] / s[k - 1]) / np.log(2)) for k in range(1, cycles // 2 + 1)]
    print(f"N {n} theta {theta:.4f} phi_even {pe:.4f} phi_odd {po:.4f} H {h:.3f} {time.time() - t0:.0f} s")
    print("  S(t): " + " ".join(f"{x:.3f}" for x in s))
    print("  exponent over t -> 2t: " + " ".join(f"{k}->{2 * k}: {e:.2f}" for k, e in dbl))
