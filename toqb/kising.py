"""Kicked transverse-field Ising ring at J = pi/4 on TOQB's ring schedule, with an exact noiseless answer at any n
(2026-10-28; the workplace's direction (A) of paper5_direction_2026-10-28, its free-fermion checks ff_check.py and
ff_general.py reproduced at home before this module was written):

    python -m toqb.kising OUT.jsonl --n 20 --L 8 16 24 50 100 [--h 0.6] [--P 24] [--T 256] [--seeds 0 1 2 3]
                                    [--arms fold:rule] [--device file:<target.pkl>] [--max-active 24]

One Floquet step is CZ on every ring edge, then Z, then RX(2h) on every qubit; it equals
exp(-i h sum X) exp(+i pi/4 sum ZZ) up to a phase, a free-fermion (Jordan-Wigner) evolution. Inputs are X-basis product
states |s> (s_j = +1 for |+>, -1 for |->). The quantity is <X_0> after L steps, computed exactly in O(n^3) by the
Majorana covariance (`x0_exact`), so no statevector is needed at any n.

The circuit is written in the angle order of `task_loop.model_circuit` (per layer: RY on every qubit; RY, RZ on every
qubit; the CZ ring; a final RY), so every TOQB arm compiles it as it compiles the classifier:
  - one step U = RX(2h) Z = e^{i a} RZ(phi) RY(theta) RZ(lam) (ZYZ); RZ(lam) commutes with the CZ ring before it, so it
    moves into the block before that ring;
  - layer 1: RY(s_j pi/2) (the input), RZ(lam); layers 2..L: RY(theta), RZ(phi + lam); final: RY(-pi/2) (X to Z);
  - the last step is not applied: U^dagger X U = -X for U = RX(2h) Z, so the measured <Z_0> is -<X_0> after L steps
    (`sign_of_readout` = -1; tests/test_kising.py checks the circuit against Qiskit's Statevector).
Each row: one (n, L, h, arm, seed) with P random inputs and T trajectories on the twin ("sim"); least squares
z ~ lam z_noiseless + delta as in `fold_lam`. The output file must not exist.
"""
from __future__ import annotations

import json
import os
import sys
import time

import numpy as np
from scipy.linalg import expm

SIGN_OF_READOUT = -1


def step_euler(h):
    """(theta, phi, lam) with RX(2h) Z = e^{i a} RZ(phi) RY(theta) RZ(lam)."""
    from qiskit.synthesis import OneQubitEulerDecomposer
    rx = np.array([[np.cos(h), -1j * np.sin(h)], [-1j * np.sin(h), np.cos(h)]])
    u = rx @ np.diag([1.0, -1.0])
    theta, phi, lam = OneQubitEulerDecomposer("ZYZ").angles(u)
    return float(theta), float(phi), float(lam)


def angles(s, n, L, h):
    """The `task_loop.model_circuit` angle list for input signs s (length n), depth L, field h."""
    theta, phi, lam = step_euler(h)
    a = []
    for k in range(L):
        if k == 0:
            a += [s[q] * np.pi / 2 for q in range(n)]
            for _ in range(n):
                a += [0.0, lam]
        else:
            a += [theta] * n
            for _ in range(n):
                a += [0.0, phi + (lam if k < L - 1 else 0.0)]
    a += [-np.pi / 2] * n
    return a


def circuit(s, n, L, h):
    from toqb import task_loop as TL
    return TL.model_circuit(angles(s, n, L, h), n, L)


def _step_map(n, h, parity, J=np.pi / 4):
    """The one-step orthogonal map on 2n Majoranas (as ff_general.step_map of the workplace)."""
    m = 2 * n
    GX, GZ = np.zeros((m, m)), np.zeros((m, m))
    for j in range(n):
        GX[2 * j, 2 * j + 1], GX[2 * j + 1, 2 * j] = 2 * h, -2 * h
    for j in range(n - 1):
        GZ[2 * j + 1, 2 * j + 2], GZ[2 * j + 2, 2 * j + 1] = -2 * J, 2 * J
    GZ[0, m - 1], GZ[m - 1, 0] = -2 * J * parity, 2 * J * parity
    return expm(GX) @ expm(GZ)


def x_exact(s, n, Ls, h):
    """{L: <X_j> for all j} after L full steps from the X-basis product state s; exact, free fermions."""
    s = np.asarray(s, dtype=float)
    M, m = _step_map(n, h, int(np.prod(s))), 2 * n
    C = np.zeros((m, m))
    for j in range(n):  # <X_j> = s_j enters as the (2j, 2j+1) covariance with the JW sign c_X = -1
        C[2 * j, 2 * j + 1], C[2 * j + 1, 2 * j] = -s[j], s[j]
    out, O, t = {}, np.eye(m), 0
    for L in sorted(Ls):
        O = np.linalg.matrix_power(M, L - t) @ O
        t = L
        Ct = O @ C @ O.T
        out[L] = np.array([-Ct[2 * j, 2 * j + 1] for j in range(n)])
    return out


def _weights(n):
    """Pauli weight of the string i g_k g_l (W) and of P i g_k g_l with P = prod X (WP), Jordan-Wigner in the X basis."""
    m = 2 * n
    W, WP = np.zeros((m, m), int), np.zeros((m, m), int)
    for k in range(m):
        for l in range(m):
            if k == l:
                continue
            j, jp = sorted((k // 2, l // 2))
            W[k, l] = jp - j + 1
            WP[k, l] = n - W[k, l] + 2 if j != jp else n - 1
    return W, WP


def x0_noisy(s, n, Ls, h, p, J=np.pi / 4):
    """{L: <X_0>} after L steps, each followed by depolarizing noise of probability p on every qubit; exact for this
    Pauli noise at any n (the workplace's noisy_ff.py, 2026-10-28: bilinears and P * bilinears are single Pauli strings,
    so the channel rescales them, and the step keeps their span; one recursion per parity sector). p = 0 gives
    x_exact's value."""
    s = np.asarray(s)
    par, m = int(np.prod(s)), 2 * n
    Mp, Mm = _step_map(n, h, +1, J), _step_map(n, h, -1, J)
    W, WP = _weights(n)
    f = 1 - 4 * p / 3
    D, DP = f ** W, f ** WP
    cx = -1.0  # X_j = cx * (i/2)[g_2j, g_2j+1] in this convention (x_exact's sign)
    A = np.zeros((m, m))
    A[0, 1], A[1, 0] = cx, -cx
    B = np.zeros((m, m))
    C = np.zeros((m, m))
    for j in range(n):
        C[2 * j, 2 * j + 1], C[2 * j + 1, 2 * j] = s[j] * cx, -s[j] * cx
    out, a, b, t = {}, A, B, 0
    for L in sorted(Ls):
        for _ in range(L - t):
            a, b = a * D, b * DP
            sp, sm = Mp @ (a + b) @ Mp.T, Mm @ (a - b) @ Mm.T
            a, b = (sp + sm) / 2, (sp - sm) / 2
        t = L
        out[L] = float(0.5 * np.sum((a + par * b) * C))
    return out


def z_noiseless(s, n, L, h):
    """The noiseless <Z_0> the circuit of `circuit(s, n, L, h)` measures."""
    return SIGN_OF_READOUT * float(x_exact(s, n, [L], h)[L][0])


def main(argv):
    argv = list(argv)
    if not argv or argv[0].startswith("--"):
        print(__doc__)
        return 1
    out = argv.pop(0)
    if os.path.exists(out):
        print(f"STOP: {out} exists: an output is never overwritten", file=sys.stderr)
        return 2
    opts = {"--n": ["20"], "--L": ["8"], "--h": ["0.6"], "--P": ["24"], "--T": ["256"], "--seeds": ["0"],
            "--arms": ["fold:rule"], "--device": ["snapshot:marrakesh"], "--max-active": ["24"]}
    key = None
    for a in argv:
        if a in opts:
            key, opts[a] = a, []
        else:
            opts[key].append(a)
    from toqb import s2r2 as S2
    from toqb.fold_lam import active
    P, T, maxa, h = int(opts["--P"][0]), int(opts["--T"][0]), int(opts["--max-active"][0]), float(opts["--h"][0])
    for n in [int(v) for v in opts["--n"]]:
        for L in [int(v) for v in opts["--L"]]:
            for sd in [int(v) for v in opts["--seeds"]]:
                rng = np.random.default_rng(8_000_000 + 1000 * n + L + 100000 * sd)
                ins = [rng.choice([1, -1], n) for _ in range(P)]
                zl = np.array([z_noiseless(s, n, L, h) for s in ins])
                for arm in opts["--arms"]:
                    base = dict(n=n, L=L, h=h, arm=arm, P=P, T=T, seed=sd, kind="kising",
                                sd_noiseless=round(float(zl.std(ddof=1)), 5))
                    if opts["--device"][0] != "snapshot:marrakesh":
                        base["device"] = opts["--device"][0].split("/")[-1]
                    plan = dict(name="kising-lam", device=opts["--device"][0], verify=False,
                                task=dict(n=n, layers=L, enc=float(np.pi / 2)),
                                predict=dict(traj=T, seed=1), standin=dict(t12=0.3, over=0.01, zz_hz=1e4,
                                                                           seed=20261017))
                    try:
                        R = S2.Runner(plan, arm)
                        cs = [R.arm.compile(circuit(s, n, L, h)) for s in ins]
                        d, q2 = R.arm.duration(cs[0], (n, L))
                        base.update(q2=int(q2), us=round(d * 1e6, 3), active=active(cs[0]), version=R.arm.version())
                        if base["active"] > maxa:
                            row = dict(base, skipped=f"{base['active']} active qubits > {maxa}")
                        else:
                            t1 = time.time()
                            z = np.asarray(R.z("sim", cs, T, 7), dtype=float)
                            lam, delta = np.polyfit(zl, z, 1)
                            row = dict(base, lam=round(float(lam), 5), delta=round(float(delta), 5),
                                       corr=round(float(np.corrcoef(zl, z)[0, 1]), 5),
                                       rms=round(float(np.sqrt(np.mean((z - lam * zl - delta) ** 2))), 5),
                                       s=round(time.time() - t1, 1))
                    except Exception as exc:  # recorded, not hidden
                        row = dict(base, error=f"{type(exc).__name__}: {exc}"[:300])
                    with open(out, "a", encoding="utf-8") as f:
                        f.write(json.dumps(row) + "\n")
                    print(json.dumps(row), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
