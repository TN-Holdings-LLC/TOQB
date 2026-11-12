"""Design check for a 6-cycle device job (home, 2026-11-12; owner 09:58 JST "じゃあ６周で"): exact M(t) for K random
product states (left |1> with prob (1+m)/2, right with (1-m)/2), N qubits, fSim(pi/4, phi) brickwork, arms
A0 (phi 0), A1 (phi pi/2), A2 (phi pi/2 + period-3 RZ field H after each cycle); M(t) = sum over the right half of
(1 - <Z>)/2 minus its value at t = 0 (the transferred magnetization). Prints the sample mean and its spread,
the exponent over 3 -> 6, and the shot-noise error of the mean for S shots per circuit.
usage: python samples6.py N K M_BIAS SHOTS
"""
import sys
import time

import numpy as np
import quimb.tensor as qtn

from dw_scan import fsim

N, K, MB, SHOTS = int(sys.argv[1]), int(sys.argv[2]), float(sys.argv[3]), int(sys.argv[4])
CYC = 6
ARMS = {"A0": (0.0, 0.0), "A1": (np.pi / 2, 0.0), "A2": (np.pi / 2, 1.0)}


def rz(h):
    return np.diag([np.exp(-1j * h / 2), np.exp(1j * h / 2)])


def run(bits, phi, H):
    c = qtn.CircuitMPS(N, max_bond=4096, cutoff=1e-10)
    X = np.array([[0, 1], [1, 0]])
    for k, b in enumerate(bits):
        if b:
            c.apply_gate_raw(X, (k,))
    G = fsim(np.pi / 4, phi)
    pat = [H * (1, -1, 0)[k % 3] for k in range(N)]
    Z = np.diag([1.0, -1.0])
    out = []
    for _ in range(CYC):
        for par in (0, 1):
            for q in range(par, N - 1, 2):
                c.apply_gate_raw(G, (q, q + 1))
        if H:
            for k in range(N):
                c.apply_gate_raw(rz(pat[k]), (k,))
        z = np.array([float(np.real(c.psi.local_expectation(Z, k))) for k in range(N // 2, N)])
        out.append(z)
    return np.array(out)


rng = np.random.default_rng(11)
samples = [[int(rng.random() < ((1 + MB) / 2 if k < N // 2 else (1 - MB) / 2)) for k in range(N)] for _ in range(K)]
t0 = time.time()
for arm, (phi, H) in ARMS.items():
    Ms, var_shot = [], []
    for bits in samples:
        z = run(bits, phi, H)
        m0 = sum(bits[N // 2:])                         # number of |1> on the right at t = 0
        n1 = ((1 - z) / 2).sum(axis=1)                  # expected number of |1> on the right
        Ms.append(n1 - m0)
        var_shot.append(((1 - z ** 2) / 4).sum(axis=1))   # per-shot variance of the count (independent sites bound)
    Ms, var_shot = np.array(Ms), np.array(var_shot)
    mean = Ms.mean(axis=0)
    se_shot = np.sqrt(var_shot.mean(axis=0) / SHOTS / K)
    e36 = np.log(mean[5] / mean[2]) / np.log(2)
    e24 = np.log(mean[3] / mean[1]) / np.log(2)
    print(f"{arm}: M(t) mean " + " ".join(f"{x:.3f}" for x in mean) + f"  sample spread (t 6) {Ms[:, 5].std():.3f}"
          f"  shot error of the mean (t 3 / 6) {se_shot[2]:.4f} / {se_shot[5]:.4f}  exponent 2->4 {e24:.2f}, 3->6 {e36:.2f}"
          f"  ({time.time() - t0:.0f} s)", flush=True)
