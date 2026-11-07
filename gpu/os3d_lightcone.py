"""Exact <Z> per site of the 3D kicked Ising lattice (RZZ(-pi/2) on every edge, then RX(theta) on every site, t steps,
from |0...0>) by the light cone, for lattices too large for one statevector (2026-11-07, owner: "3D with 91 qubits").

Why it is exact: the first step's RZZ layer acts on |0...0> as a phase, so in the Heisenberg picture Z_i after t steps
is supported on the sites within graph distance t - 1 of i. Simulating that region with every gate inside it, for all
t steps, gives <Z_i> exactly (gates on edges leaving the region act on sites the operator never reaches in time).
`--check` compares with the full statevector (psf_os.grid3d.exact) on lattices of up to 24 sites, and with a region
one step wider.

usage: python gpu/os3d_lightcone.py M N OUT.json [--ts 1,2,3] [--theta 0.8] [--check]
"""
import argparse
import hashlib
import itertools
import json
import os
import sys

import numpy as np

L = 4


def sites(M, N):
    return list(itertools.product(range(L), range(M), range(N)))


def edges(M, N):
    idx = {s: i for i, s in enumerate(sites(M, N))}
    out = []
    for (x, y, z), i in idx.items():
        for d in ((1, 0, 0), (0, 1, 0), (0, 0, 1)):
            t = (x + d[0], y + d[1], z + d[2])
            if t in idx:
                out.append((i, idx[t]))
    return out


def region(M, N, i, r):
    s = sites(M, N)
    return [j for j in range(len(s)) if sum(abs(a - b) for a, b in zip(s[i], s[j])) <= r]


def z_in_region(M, N, i, t, theta, r):
    """<Z_i> after t steps, simulating only the sites within distance r of i (every gate inside that region)."""
    from qiskit import QuantumCircuit
    from qiskit_aer import AerSimulator
    from qiskit.quantum_info import Pauli
    reg = region(M, N, i, r)
    m = {q: k for k, q in enumerate(reg)}
    e = [(a, b) for a, b in edges(M, N) if a in m and b in m]
    qc = QuantumCircuit(len(reg))
    for _ in range(t):
        for a, b in e:
            qc.rzz(-np.pi / 2, m[a], m[b])
        for q in reg:
            qc.rx(theta, m[q])
    qc.save_expectation_value(Pauli("Z"), [m[i]], label="z")
    res = AerSimulator(method="statevector", precision="double").run(qc).result()
    return float(np.real(res.data(0)["z"])), len(reg)


def exact_lightcone(M, N, t, theta):
    """{str(site index): exact <Z>} in itertools.product order, as psf_os.grid3d.exact."""
    n = L * M * N
    if t == 1:
        return {str(i): float(np.cos(theta)) for i in range(n)}
    return {str(i): z_in_region(M, N, i, t, theta, t - 1)[0] for i in range(n)}


def check(theta):
    from psf_os import grid3d as G
    worst = 0.0
    for M, N in [(2, 2), (3, 2), (2, 3)]:
        for t in (1, 2, 3):
            full = G.exact(L, M, N, t, theta)
            lc = exact_lightcone(M, N, t, theta)
            d = max(abs(full[k] - lc[k]) for k in full)
            worst = max(worst, d)
            print(f"check 4x{M}x{N} t{t}: max |full - light cone| {d:.2e}", flush=True)
    for M, N in [(6, 3)]:
        for i in (0, 71):       # corners: the region one step wider stays small enough to simulate
            a, na = z_in_region(M, N, i, 3, theta, 2)
            b, nb = z_in_region(M, N, i, 3, theta, 3)
            worst = max(worst, abs(a - b))
            print(f"check 4x{M}x{N} t3 site {i}: radius 2 ({na} sites) {a:+.12f}, radius 3 ({nb} sites) {b:+.12f}",
                  flush=True)
    print("CHECK", "PASS" if worst < 1e-9 else "FAIL", f"(worst {worst:.2e})")
    return worst < 1e-9


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("M", type=int)
    ap.add_argument("N", type=int)
    ap.add_argument("out")
    ap.add_argument("--ts", default="1,2,3")
    ap.add_argument("--theta", type=float, default=0.8)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if os.path.exists(a.out):
        raise SystemExit(f"STOP: {a.out} exists")
    if a.check and not check(a.theta):
        raise SystemExit("STOP: the light cone does not match")
    out = {f"t{t}": exact_lightcone(a.M, a.N, int(t), a.theta) for t in a.ts.split(",")}
    with open(a.out, "w") as f:
        json.dump(out, f, indent=1, sort_keys=True)
    print("written", a.out, "sha256", hashlib.sha256(open(a.out, "rb").read()).hexdigest())
    sys.stdout.flush()


if __name__ == "__main__":
    main()
