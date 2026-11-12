"""Design check for the 6-cycle device job, workplace version of samples6.py (2026-11-12; home's instruction of 02:05 CET,
step 1). Same circuits and arms as samples6.py (fSim(pi/4, phi) brickwork, N qubits, random product states with bias m;
A0 phi 0, A1 phi pi/2, A2 phi pi/2 + period-3 RZ field H (1, -1, 0) after each cycle), plus:
  - A0 against free fermions per bit string (<n_x> = sum over occupied y of |W_xy|^2);
  - the per-shot variance of the right-half count measured by sampling the MPS (V_SAMPLE strings, 400 shots each), beside
    the independent-site bound of samples6.py (sum of p(1-p));
  - the shot error of the exponent 3 -> 6 per arm, and of the difference A1 - A2 (independent circuits):
    d e = (1 / ln 2) sqrt((dM6 / M6)^2 + (dM3 / M3)^2), dM = sqrt(var / (K S));
  - the spread of the exponent over bit-string resamples (bootstrap, 2000), for information (the device is compared with
    the exact values of the same strings, so this spread is not part of the device's error).
Only the 3 and 6 cycle points are kept. The bit strings here (seed 11, as samples6.py) are design samples, not the
declared ones.
usage: python samples6w.py N K M_BIAS SHOTS [SHOTS ...]
"""
import sys
import time

import numpy as np
import quimb.tensor as qtn

from dw_scan import fsim

N, K, MB = int(sys.argv[1]), int(sys.argv[2]), float(sys.argv[3])
SHOTS = [int(s) for s in sys.argv[4:]]
CYC, V_SAMPLE, V_SHOTS = 6, 5, 400
ARMS = {"A0": (0.0, 0.0), "A1": (np.pi / 2, 0.0), "A2": (np.pi / 2, 1.0)}


def rz(h):
    return np.diag([np.exp(-1j * h / 2), np.exp(1j * h / 2)])


def run(bits, phi, H, sample=0, seed=0):
    c = qtn.CircuitMPS(N, max_bond=4096, cutoff=1e-10)
    X = np.array([[0, 1], [1, 0]])
    for k, b in enumerate(bits):
        if b:
            c.apply_gate_raw(X, (k,))
    G = fsim(np.pi / 4, phi)
    pat = [H * (1, -1, 0)[k % 3] for k in range(N)]
    Z = np.diag([1.0, -1.0])
    z_out, var_out, bond = {}, {}, 0
    for t in range(1, CYC + 1):
        for par in (0, 1):
            for q in range(par, N - 1, 2):
                c.apply_gate_raw(G, (q, q + 1))
        if H:
            for k in range(N):
                c.apply_gate_raw(rz(pat[k]), (k,))
        if t in (3, 6):
            z_out[t] = np.array([float(np.real(c.psi.local_expectation(Z, k))) for k in range(N // 2, N)])
            bond = max(bond, c.psi.max_bond())
            if sample:
                cnt = [sum(cfg[N // 2:]) for cfg, _ in c.psi.sample(sample, seed=seed + t)]
                var_out[t] = float(np.var(cnt, ddof=1))
    return z_out, var_out, bond


def free_z(bits, t):
    g = np.array([[np.cos(np.pi / 4), -1j * np.sin(np.pi / 4)], [-1j * np.sin(np.pi / 4), np.cos(np.pi / 4)]])
    W = np.eye(N, dtype=complex)
    for _ in range(t):
        for par in (0, 1):
            for q in range(par, N - 1, 2):
                W[[q, q + 1], :] = g @ W[[q, q + 1], :]
    occ = [k for k, b in enumerate(bits) if b]
    n = np.sum(np.abs(W[:, occ]) ** 2, axis=1)
    return 1 - 2 * n[N // 2:]


rng = np.random.default_rng(11)
samples = [[int(rng.random() < ((1 + MB) / 2 if k < N // 2 else (1 - MB) / 2)) for k in range(N)] for _ in range(K)]
t0 = time.time()
res = {}
for arm, (phi, H) in ARMS.items():
    M, vb, vs, bonds, ff = {3: [], 6: []}, {3: [], 6: []}, {3: [], 6: []}, [], 0.0
    for i, bits in enumerate(samples):
        z, var, bond = run(bits, phi, H, sample=V_SHOTS if i < V_SAMPLE else 0, seed=100 * i)
        bonds.append(bond)
        m0 = sum(bits[N // 2:])
        for t in (3, 6):
            M[t].append(float(((1 - z[t]) / 2).sum() - m0))
            vb[t].append(float(((1 - z[t] ** 2) / 4).sum()))
            if t in var:
                vs[t].append(var[t])
            if arm == "A0":
                ff = max(ff, float(np.max(np.abs(z[t] - free_z(bits, t)))))
    res[arm] = dict(M={t: np.array(v) for t, v in M.items()}, vb={t: np.mean(v) for t, v in vb.items()},
                    vs={t: np.mean(v) for t, v in vs.items()}, bond=max(bonds), ff=ff)
    r = res[arm]
    print(f"{arm} (phi {phi:.4f}, H {H}): bond max {r['bond']}; M mean t3 {r['M'][3].mean():.3f}, t6 {r['M'][6].mean():.3f}; "
          f"exponent 3->6 {np.log2(r['M'][6].mean() / r['M'][3].mean()):.3f}; per-shot variance t3 / t6: bound "
          f"{r['vb'][3]:.2f} / {r['vb'][6]:.2f}, sampled {r['vs'][3]:.2f} / {r['vs'][6]:.2f}"
          + (f"; free fermions max |dZ| {ff:.1e}" if arm == "A0" else "") + f"  ({time.time() - t0:.0f} s)", flush=True)

boot = np.random.default_rng(5)
idx = boot.integers(0, K, size=(2000, K))
for S in SHOTS:
    line = [f"shots {S}:"]
    de = {}
    for arm, r in res.items():
        m3, m6 = r["M"][3].mean(), r["M"][6].mean()
        v3, v6 = max(r["vb"][3], r["vs"][3]), max(r["vb"][6], r["vs"][6])
        d3, d6 = np.sqrt(v3 / (K * S)), np.sqrt(v6 / (K * S))
        de[arm] = np.sqrt((d6 / m6) ** 2 + (d3 / m3) ** 2) / np.log(2)
        bs = np.log2(r["M"][6][idx].mean(1) / r["M"][3][idx].mean(1))
        line.append(f"{arm} exponent shot error {de[arm]:.3f} (string resample spread {bs.std():.3f})")
    e1 = np.log2(res["A1"]["M"][6].mean() / res["A1"]["M"][3].mean())
    e2 = np.log2(res["A2"]["M"][6].mean() / res["A2"]["M"][3].mean())
    dd = np.hypot(de["A1"], de["A2"])
    line.append(f"A1 - A2 = {e1 - e2:.3f} +- {dd:.3f} (ratio {(e1 - e2) / dd:.1f}; criterion >= 3)")
    print("; ".join(line), flush=True)
