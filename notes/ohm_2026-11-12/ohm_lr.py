"""Where Ohm's law appears, desk study (a) of handover 11-11 item 0 (workplace, 2026-11-12; not declared, no device).

A pure domain wall does not give diffusion (home, notes/ohm_2026-11-11: easy-axis freezes). The textbook setting is a
weakly polarised wall at infinite temperature: rho = prod_y (1 + m s_y Z_y) / 2 with s_y = -1 on the left half and +1
on the right (the left leans to |1>). To first order in m the transferred magnetisation is exactly
    M(t) = sum_{x in R} (<n_x(t)> - <n_x(0)>) = m C(t),   C(t) = Tr(Z_L U(t)^dag Z_R U(t)) / 2^N
(Z_L, Z_R = sum of Z over each half; uses only that total Z is conserved). C(t) is computed by typicality from Haar
random states (statevector), checked at phi = 0 against free fermions: C(t) = sum_{x in R, y in L} |W_xy(t)|^2 with W
the single-particle matrix of the brickwork (as gpu/ff_xx.py). Finite m is checked by averaging random product states
(what a device would run) at a smaller N.

Floquet XXZ brickwork of fSim(theta, phi) (as notes/ohm_2026-11-11/dw_scan.py): even bonds then odd bonds = 1 cycle.
usage: python ohm_lr.py lr N CYCLES SAMPLES THETA PHI [PHI ...]
       python ohm_lr.py finite N CYCLES SAMPLES THETA M PHI [PHI ...]
       python ohm_lr.py cz THETA PHI [PHI ...]
       python ohm_lr.py field N CYCLES SAMPLES THETA PHI H [H ...]   (staggered field h after each cycle)
"""
import sys
import time

import numpy as np


def fsim(theta, phi):
    c, s = np.cos(theta), np.sin(theta)
    return np.array([[1, 0, 0, 0], [0, c, -1j * s, 0], [0, -1j * s, c, 0], [0, 0, 0, np.exp(-1j * phi)]])


def apply2(psi, G, q, n):
    """psi as (2,)*n with axis k = qubit k; G on (q, q+1), basis |a b> = |q, q+1>."""
    s = psi.reshape((2 ** q, 4, 2 ** (n - q - 2)))
    return np.einsum("ij,ajb->aib", G, s).reshape(-1)


def cycle(psi, G, n):
    for par in (0, 1):
        for q in range(par, n - 1, 2):
            psi = apply2(psi, G, q, n)
    return psi


def zsum(n, sites):
    """diagonal of sum_{k in sites} Z_k on the computational basis (qubit k = bit n-1-k of the index: axis order)."""
    idx = np.arange(2 ** n)
    d = np.zeros(2 ** n)
    for k in sites:
        d += 1 - 2 * ((idx >> (n - 1 - k)) & 1)
    return d


def stag_phase(n, h):
    """exp(-i h/2 sum_x (-1)^x Z_x) as a diagonal: a staggered field, applied after each cycle; it keeps total Z and
    breaks the circuit's integrability (h = 0: none)."""
    return np.exp(-0.5j * h * zsum_signed(n)) if h else None


def zsum_signed(n):
    idx = np.arange(2 ** n)
    d = np.zeros(2 ** n)
    for k in range(n):
        d += (-1) ** k * (1 - 2 * ((idx >> (n - 1 - k)) & 1))
    return d


def lr(n, cycles, samples, theta, phi, seed=0, h=0.0):
    rng = np.random.default_rng(seed)
    G = fsim(theta, phi)
    ph = stag_phase(n, h)
    zl, zr = zsum(n, range(n // 2)), zsum(n, range(n // 2, n))
    out = np.zeros((samples, cycles))
    for s in range(samples):
        a = rng.normal(size=2 ** n) + 1j * rng.normal(size=2 ** n)
        a /= np.linalg.norm(a)
        b = zl * a
        for t in range(cycles):
            a, b = cycle(a, G, n), cycle(b, G, n)
            if ph is not None:
                a, b = ph * a, ph * b
            out[s, t] = float(np.real(np.vdot(b, zr * a)))
    return out.mean(0), out.std(0) / np.sqrt(samples) if samples > 1 else np.zeros(cycles)


def free_c(n, cycles, theta):
    """C(t) at phi = 0 exactly: single-particle brickwork matrix W; C = sum_{x in R, y in L} |W_xy|^2."""
    g = np.array([[np.cos(theta), -1j * np.sin(theta)], [-1j * np.sin(theta), np.cos(theta)]])
    W = np.eye(n, dtype=complex)
    out = []
    for _ in range(cycles):
        for par in (0, 1):
            for q in range(par, n - 1, 2):
                W[[q, q + 1], :] = g @ W[[q, q + 1], :]
        out.append(float(np.sum(np.abs(W[n // 2:, : n // 2]) ** 2)))
    return np.array(out)


def finite(n, cycles, samples, theta, m, phi, seed=1):
    """M(t) for rho = prod (1 + m s_y Z_y)/2 by averaging random product states (each qubit |1> with probability
    (1 + m)/2 on the left, (1 - m)/2 on the right), as a device would: exact per sample, sampled over states."""
    rng = np.random.default_rng(seed)
    G = fsim(theta, phi)
    nr = zsum(n, range(n // 2, n))
    p1 = np.array([(1 + m) / 2] * (n // 2) + [(1 - m) / 2] * (n - n // 2))
    out = np.zeros((samples, cycles))
    for s in range(samples):
        bits = (rng.random(n) < p1).astype(int)
        psi = np.zeros(2 ** n, dtype=complex)
        psi[int("".join(map(str, bits)), 2)] = 1.0
        n0 = float(np.sum(bits[n // 2:]))
        for t in range(cycles):
            psi = cycle(psi, G, n)
            zr = float(np.sum(np.abs(psi) ** 2 * nr))
            out[s, t] = (n - n // 2 - zr) / 2 - n0
    return out.mean(0), out.std(0) / np.sqrt(samples)


def cz_count(theta, phi):
    from qiskit import QuantumCircuit, transpile
    from qiskit.circuit.library import UnitaryGate
    qc = QuantumCircuit(2)
    qc.append(UnitaryGate(fsim(theta, phi)[[0, 2, 1, 3]][:, [0, 2, 1, 3]]), [0, 1])   # qiskit little-endian
    t = transpile(qc, basis_gates=["cz", "rz", "sx", "x"], optimization_level=3, seed_transpiler=0)
    return t.count_ops().get("cz", 0)


def exponents(c):
    t = np.arange(1, len(c) + 1)
    pairs = [(a, 2 * a) for a in (1, 2, 4, 8, 16) if 2 * a <= len(c)]
    return {f"{a}-{b}": round(float(np.log(c[b - 1] / c[a - 1]) / np.log(b / a)), 3) for a, b in pairs}


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "lr":
        n, cycles, samples, theta = int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), float(sys.argv[5])
        if True:
            f = free_c(n, cycles, theta)
            print(f"N {n}: free fermions (phi 0) exact C(t): " + " ".join(f"{x:.4f}" for x in f), flush=True)
        for phi in map(float, sys.argv[6:]):
            t0 = time.time()
            c, e = lr(n, cycles, samples, theta, phi)
            print(f"N {n} theta {theta:.4f} phi {phi:.4f} (phi / 2 theta {phi / (2 * theta):.2f}), {samples} random "
                  f"states, {time.time() - t0:.0f} s", flush=True)
            print("  C(t): " + " ".join(f"{x:.4f}" for x in c))
            print("  +-:   " + " ".join(f"{x:.4f}" for x in e))
            if abs(phi) < 1e-12:
                print(f"  against free fermions: max |diff| {np.max(np.abs(c - f)):.1e}")
            print(f"  exponent over doubled times: {exponents(c)}", flush=True)
    elif mode == "finite":
        n, cycles, samples, theta, m = int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), float(sys.argv[5]), float(sys.argv[6])
        for phi in map(float, sys.argv[7:]):
            t0 = time.time()
            c, e = finite(n, cycles, samples, theta, m, phi)
            print(f"finite m {m}: N {n} phi {phi:.4f}, {samples} product states, {time.time() - t0:.0f} s", flush=True)
            print("  M(t)/m: " + " ".join(f"{x / m:.3f}" for x in c))
            print("  +-/m:   " + " ".join(f"{x / m:.3f}" for x in e))
            print(f"  exponent over doubled times: {exponents(c)}", flush=True)
    elif mode == "field":
        n, cycles, samples, theta, phi = int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), float(sys.argv[5]), float(sys.argv[6])
        for h in map(float, sys.argv[7:]):
            t0 = time.time()
            c, e = lr(n, cycles, samples, theta, phi, h=h)
            print(f"N {n} theta {theta:.4f} phi {phi:.4f} staggered field h {h}, {time.time() - t0:.0f} s", flush=True)
            print("  C(t): " + " ".join(f"{x:.4f}" for x in c))
            print(f"  exponent over doubled times: {exponents(c)}", flush=True)
    else:
        theta = float(sys.argv[2])
        for phi in map(float, sys.argv[3:]):
            print(f"fSim({theta:.4f}, {phi:.4f}): {cz_count(theta, phi)} CZ")
