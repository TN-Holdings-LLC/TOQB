"""Design E5 (prototype, workplace, 2026-10-22): E4's exact per-parameter solve, cross-fitted over the training points.

What E4 taught (the fruit match and W12):
- E4's step is the exact minimum of the estimated training Brier along one parameter. It overshoots: the step follows
  the twin's noise (the winner's curse) and the 64 training points' quirks (overfitting with 170-330 parameters), so
  the test CE stalls or rises after the first sweep, while C0's small SPSA steps act as a brake.
- A brake with a constant (a learning rate, a penalty, an early stop at k sweeps) is a tuned constant. E5 adds one with
  no constant: a step is taken only when it helps points it was not chosen on.

The step for parameter k (everything else is E4's):
- The training points are split by a fixed rule into fold A (even index) and fold B (odd index).
- For each fold f, two independent halves of the twin's trajectories give unbiased Brier coefficients C_f (E4's
  split-half products). The two folds use independent random numbers.
- u_A = argmin of C_A's curve, u_B = argmin of C_B's (the exact quartic, `s2re.trig2_min`).
- The cross-fitted gain is v = dL_B(u_A) + dL_A(u_B). Each term is unbiased for the out-of-fold change of a step
  chosen on the other fold.
- If v < 0, the parameter moves by u* = argmin of (C_A + C_B), E4's own step on all points. Otherwise it stays.

Threshold 0, fixed folds, E4's order and cost: 3 x d x m circuits x traj trajectories per sweep. A parameter whose
improvement does not carry across the folds stops moving by itself, so training stops when it stops generalising,
with no early-stopping constant.
"""
from __future__ import annotations

import math

import numpy as np

# E4's formulas (toqb.s2re), copied so that the prototype runs alone; identical to s2re's.


def sinusoid(fm, f0, fp):
    fm, f0, fp = (np.asarray(v, float) for v in (fm, f0, fp))
    a = (fp + fm) / 2
    return a, f0 - a, (fp - fm) / 2


def brier_coeffs_split(h1, h2, y):
    a1, b1, c1 = (np.asarray(v, float) for v in h1)
    a2, b2, c2 = (np.asarray(v, float) for v in h2)
    y = np.asarray(y, float)
    r1, r2 = a1 - y, a2 - y
    return (float(np.sum(r1 * b2 + r2 * b1)), float(np.sum(r1 * c2 + r2 * c1)),
            float(np.sum(b1 * b2) - np.sum(c1 * c2)) / 2, float(np.sum(b1 * c2 + b2 * c1)) / 2)


def trig2_min(P, Q, R, S):
    val = lambda u: P * math.cos(u) + Q * math.sin(u) + R * math.cos(2 * u) + S * math.sin(2 * u)
    coef = np.array([2 * S - Q, 8 * R - 2 * P, -12 * S, -(2 * P + 8 * R), Q + 2 * S], float)
    cand = [0.0, math.pi]
    big = np.abs(coef).max()
    if big <= 1e-12:
        return 0.0, 0.0
    nz = np.flatnonzero(np.abs(coef) > 1e-14 * big)
    if len(coef) - nz[0] > 1:
        for t in np.roots(coef[nz[0]:]):
            if abs(t.imag) <= 1e-9 * max(1.0, abs(t.real)):
                cand.append(2 * math.atan(t.real))
    u = min(cand, key=val)
    return u, val(u) - val(0.0)


def delta_val(C, u):
    P, Q, R, S = C
    return float(P * (math.cos(u) - 1) + Q * math.sin(u) + R * (math.cos(2 * u) - 1) + S * math.sin(2 * u))


def folds(m):
    """Fixed rule: fold A = even indices, fold B = odd indices of the training points."""
    idx = np.arange(m)
    return idx[idx % 2 == 0], idx[idx % 2 == 1]


def e5_step(hA, hB, yA, yB):
    """hA = (half 1, half 2) sinusoid estimates (a, b, c) on fold A's points, hB likewise on fold B's (independent).
    Returns (u, info): u = argmin(C_A + C_B) if the cross-fitted gain v < 0, else 0."""
    CA = brier_coeffs_split(hA[0], hA[1], yA)
    CB = brier_coeffs_split(hB[0], hB[1], yB)
    uA, _ = trig2_min(*CA)
    uB, _ = trig2_min(*CB)
    v = delta_val(CB, uA) + delta_val(CA, uB)
    C = tuple(x + y for x, y in zip(CA, CB))
    us, dv = trig2_min(*C)
    if v < 0 and us != 0.0:
        return us, dict(v=v, claimed=dv, moved=True)
    return 0.0, dict(v=v, claimed=0.0, moved=False)


def e4_step(h, y):
    """E4's step on all points (for comparison): u = argmin of the split-half coefficients."""
    C = brier_coeffs_split(h[0], h[1], y)
    u, dv = trig2_min(*C)
    return u, dict(claimed=dv, moved=u != 0.0)
