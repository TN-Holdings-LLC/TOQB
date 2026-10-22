"""Toy comparison (report only) of E5 against E4 on the S2R model in a fast numpy simulator.

The model: TOQB's data re-uploading classifier on a CZ ring (task_loop.model_circuit: per layer RY(enc x) on every
qubit, then RY RZ per qubit, then the CZ ring; final RY; read <Z> of qubit 0). Teacher-student data: a teacher of
the same model with angles uniform(-angle, angle), labels the sign of its <Z0>, points with |<Z0>| < gap dropped.

The "twin" here is a toy, not TOQB's: z = lam * z_ideal + delta (the global shrink, lam = 0.33 and delta = 0.05,
read off the device day's PSF L 8 twin), and each half's estimate carries independent Gaussian noise with the
trajectory variance (1 - z^2) / T_half. The test score is on the same toy device: raw CE from z, accuracy from its
sign; the noiseless accuracy and the undamped CE (z_u = (z - delta) / lam, clipped) are reported too. The same
draws are used for both methods (common random numbers by sweep, parameter and half).

Not TOQB's noise, not a device: it shows what the cross-fitting does to the statistics (noise and overfitting), not
how either method fares on hardware.

usage: python toy_e5.py N L SWEEPS TEACHERS OUT.json
"""
import json
import math
import sys
import time

import numpy as np

import e5 as E

N, L, SWEEPS = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3])
TEACHERS = [int(t) for t in sys.argv[4].split(",")]
OUT = sys.argv[5]
ENC, ANGLE, GAP = math.pi / 2, 1.0, 0.2
M_TRAIN, M_TEST, T = 64, 500, 32
LAM, DELTA = 0.33, 0.05
D = 2 * N * L + N

# ---------------------------------------------------------------------------------------------- simulator
dim = 2 ** N
bits = (np.arange(dim)[:, None] >> np.arange(N)[None, :]) & 1      # (dim, N): bit q of each basis index
z0_sign = 1.0 - 2.0 * bits[:, 0]
ring_phase = np.ones(dim)
for q in range(N):
    ring_phase *= np.where((bits[:, q] & bits[:, (q + 1) % N]) == 1, -1.0, 1.0)


def apply_ry(psi, q, th):
    """psi: (P, dim); th: scalar or (P,)."""
    P = psi.shape[0]
    s = psi.reshape(P, dim // (2 ** (q + 1)), 2, 2 ** q)
    c = np.cos(np.asarray(th) / 2).reshape(-1, 1, 1) if np.ndim(th) else np.cos(th / 2)
    sn = np.sin(np.asarray(th) / 2).reshape(-1, 1, 1) if np.ndim(th) else np.sin(th / 2)
    a0, a1 = s[:, :, 0, :], s[:, :, 1, :]
    n0 = c * a0 - sn * a1
    n1 = sn * a0 + c * a1
    return np.stack([n0, n1], axis=2).reshape(P, dim)


def apply_rz(psi, q, th):
    P = psi.shape[0]
    s = psi.reshape(P, dim // (2 ** (q + 1)), 2, 2 ** q)
    e0, e1 = np.exp(-0.5j * th), np.exp(0.5j * th)
    return np.stack([e0 * s[:, :, 0, :], e1 * s[:, :, 1, :]], axis=2).reshape(P, dim)


def z0(theta, X):
    """<Z0> of the model for parameters theta (D,) on points X (P, N)."""
    P = X.shape[0]
    psi = np.zeros((P, dim), complex)
    psi[:, 0] = 1.0
    k = 0
    for _ in range(L):
        for q in range(N):
            psi = apply_ry(psi, q, ENC * X[:, q])
        for q in range(N):
            psi = apply_ry(psi, q, theta[k])
            psi = apply_rz(psi, q, theta[k + 1])
            k += 2
        psi = psi * ring_phase[None, :]
    for q in range(N):
        psi = apply_ry(psi, q, theta[k + q])
    return (np.abs(psi) ** 2) @ z0_sign


def data(teacher_seed):
    rng = np.random.default_rng(teacher_seed)
    teacher = rng.uniform(-ANGLE, ANGLE, D)
    X, Y = [], []
    while len(X) < M_TRAIN + M_TEST:
        xs = rng.uniform(-1, 1, (256, N))
        zs = z0(teacher, xs)
        for x, z in zip(xs, zs):
            if abs(z) >= GAP and len(X) < M_TRAIN + M_TEST:
                X.append(x)
                Y.append(1.0 if z > 0 else -1.0)
    X, Y = np.array(X), np.array(Y)
    return X[:M_TRAIN], Y[:M_TRAIN], X[M_TRAIN:], Y[M_TRAIN:]


def noisy_halves(z_ideal_3, rng):
    """Two independent half estimates of the toy twin's z on the three shifted circuits: (3, P) -> 2 x (3, P)."""
    zt = LAM * z_ideal_3 + DELTA
    sd = np.sqrt(np.clip(1 - zt ** 2, 0, 1) / (T // 2))
    return [zt + rng.normal(0, 1, zt.shape) * sd for _ in range(2)]


def scores(theta, Xte, Yte):
    zi = z0(theta, Xte)
    z = LAM * zi + DELTA
    p = np.clip((1 + z) / 2, 1e-4, 1 - 1e-4)
    ce = float(np.mean(np.where(Yte > 0, -np.log(p), -np.log(1 - p))))
    zu = np.clip((z - DELTA) / LAM, -1, 1)
    pu = np.clip((1 + zu) / 2, 1e-4, 1 - 1e-4)
    ceu = float(np.mean(np.where(Yte > 0, -np.log(pu), -np.log(1 - pu))))
    return dict(ce=ce, acc=float(np.mean(np.sign(z) == Yte)), acc_noiseless=float(np.mean(np.sign(zi) == Yte)),
                ce_undamped=ceu)


def train(method, Xtr, Ytr, Xte, Yte, seed):
    th = np.zeros(D)
    A, B = E.folds(len(Ytr))
    out = [dict(sweep=0, **scores(th, Xte, Yte), moved=0)]
    for sw in range(SWEEPS):
        moved = 0
        claimed = 0.0
        for k in range(D):
            e = np.zeros(D)
            e[k] = math.pi / 2
            z3 = np.stack([z0(th - e, Xtr), z0(th, Xtr), z0(th + e, Xtr)])  # (3, m): -, 0, +
            if method == "E4":
                rng = np.random.default_rng([seed, sw, k, 0])
                h1, h2 = noisy_halves(z3, rng)
                hs = [E.sinusoid(h[0], h[1], h[2]) for h in (h1, h2)]
                u, info = E.e4_step(hs, Ytr)
            else:
                # the same total trajectories: each fold's points get their own two halves (independent seeds)
                rngA = np.random.default_rng([seed, sw, k, 1])
                rngB = np.random.default_rng([seed, sw, k, 2])
                a1, a2 = noisy_halves(z3[:, A], rngA)
                b1, b2 = noisy_halves(z3[:, B], rngB)
                hA = [E.sinusoid(h[0], h[1], h[2]) for h in (a1, a2)]
                hB = [E.sinusoid(h[0], h[1], h[2]) for h in (b1, b2)]
                u, info = E.e5_step(hA, hB, Ytr[A], Ytr[B])
            th[k] += u
            moved += int(info["moved"])
            claimed += info["claimed"] / (4 * len(Ytr))
        out.append(dict(sweep=sw + 1, **scores(th, Xte, Yte), moved=moved, claimed_brier=claimed))
        print(method, "sweep", sw + 1, {k: round(v, 4) if isinstance(v, float) else v for k, v in out[-1].items()},
              flush=True)
    return out


res = dict(N=N, L=L, sweeps=SWEEPS, lam=LAM, delta=DELTA, T=T, angle=ANGLE, teachers={})
t0 = time.time()
for ts in TEACHERS:
    Xtr, Ytr, Xte, Yte = data(ts)
    res["teachers"][ts] = {m: train(m, Xtr, Ytr, Xte, Yte, ts) for m in ("E4", "E5")}
    print("teacher", ts, "done", round(time.time() - t0), "s", flush=True)
json.dump(res, open(OUT, "w"), indent=1)
