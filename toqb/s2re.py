"""Design E (exploratory, 2026-10-20): train the model by a formula, with no search, no random draws and no
learning rate.

The model's output for parameters theta near a point theta0 is, to first order,

    f(theta; x) = f0(x) + g(x) . (theta - theta0),    g_k(x) = d f / d theta_k at theta0.

Every trainable angle of the model is a single RY or RZ rotation, so g_k(x) is exact by the parameter-shift rule:
g_k(x) = (f(theta0 + pi/2 e_k; x) - f(theta0 - pi/2 e_k; x)) / 2. With the training points' values f0 (m), their
features G (m x d) and labels y in {+1, -1}, the parameters are the minimum-norm solution of the linear system that
asks every training point for the output y * tau:

    theta* = theta0 + pinv(G) (y tau - f0),       tau = rms(f0)    (the outputs' own scale at theta0; no tuning).

With m < d the system is underdetermined and pinv picks the smallest change from theta0; nothing is chosen by trying
alternatives. `f` can be any evaluator of the model's <Z0>: the exact noiseless one here, or a twin.
"""
from __future__ import annotations

import math

import numpy as np


def tangent(f, theta0, X):
    """f0 (m) and G (m x d) at theta0 for the points X, by the parameter-shift rule (2 d + 1 evaluations per point)."""
    theta0 = np.asarray(theta0, float)
    d = len(theta0)
    f0 = np.array([f(theta0, x) for x in X])
    G = np.zeros((len(X), d))
    for k in range(d):
        e = np.zeros(d)
        e[k] = math.pi / 2
        G[:, k] = [(f(theta0 + e, x) - f(theta0 - e, x)) / 2 for x in X]
    return f0, G


def closed_form(f0, G, y, theta0):
    """theta* = theta0 + pinv(G) (y tau - f0), tau = rms(f0). Returns theta* and tau."""
    tau = float(np.sqrt(np.mean(np.asarray(f0) ** 2)))
    return np.asarray(theta0, float) + np.linalg.pinv(G) @ (np.asarray(y, float) * tau - np.asarray(f0)), tau


def sinusoid(fm, f0, fp):
    """a, b, c of f(u) = a + b cos u + c sin u from the values at u = -pi/2, 0, +pi/2 (exact for one rotation)."""
    fm, f0, fp = (np.asarray(v, float) for v in (fm, f0, fp))
    a = (fp + fm) / 2
    return a, f0 - a, (fp - fm) / 2


def brier_coeffs(a, b, c, y):
    """sum_i (a_i + b_i cos u + c_i sin u - y_i)^2 = K + P cos u + Q sin u + R cos 2u + S sin 2u: (K, P, Q, R, S)."""
    r = np.asarray(a, float) - np.asarray(y, float)
    b, c = np.asarray(b, float), np.asarray(c, float)
    K = float(np.sum(r * r) + (np.sum(b * b) + np.sum(c * c)) / 2)
    return K, 2 * float(np.sum(r * b)), 2 * float(np.sum(r * c)), float(np.sum(b * b) - np.sum(c * c)) / 2, float(np.sum(b * c))


def trig2_min(P, Q, R, S):
    """The exact global minimum over u of P cos u + Q sin u + R cos 2u + S sin 2u (a trigonometric polynomial of
    degree 2; any constant is irrelevant). Its stationary points, with t = tan(u / 2), are the real roots of the quartic
        (2S - Q) t^4 + (8R - 2P) t^3 - 12 S t^2 - (2P + 8R) t + (Q + 2S) = 0,
    plus u = pi (t at infinity). The roots are the eigenvalues of the quartic's companion matrix (np.roots); u = 0 is
    always a candidate, so the minimum is never above the value at u = 0. A parameter whose coefficients are all below
1e-12 does not move the loss and stays (u = 0). No grid, no search.
    Returns (u in (-pi, pi], the value minus the value at u = 0)."""
    val = lambda u: P * math.cos(u) + Q * math.sin(u) + R * math.cos(2 * u) + S * math.sin(2 * u)
    coef = np.array([2 * S - Q, 8 * R - 2 * P, -12 * S, -(2 * P + 8 * R), Q + 2 * S], float)
    cand = [0.0, math.pi]
    big = np.abs(coef).max()
    if big <= 1e-12:
        return 0.0, 0.0  # the parameter does not move the loss (to rounding): it stays where it is
    if big > 0:
        nz = np.flatnonzero(np.abs(coef) > 1e-14 * big)
        if len(coef) - nz[0] > 1:
            for t in np.roots(coef[nz[0]:]):
                if abs(t.imag) <= 1e-9 * max(1.0, abs(t.real)):
                    cand.append(2 * math.atan(t.real))
    u = min(cand, key=val)
    return u, val(u) - val(0.0)


def brier_min(a, b, c, y):
    """The exact global minimum over u of sum_i (f_i(u) - y_i)^2 with f_i(u) = a_i + b_i cos u + c_i sin u: the sum is
    K + P cos u + Q sin u + R cos 2u + S sin 2u (brier_coeffs), minimised by trig2_min.
    Returns (u in (-pi, pi], the minimum value)."""
    K, P, Q, R, S = brier_coeffs(a, b, c, y)
    u, _ = trig2_min(P, Q, R, S)
    return u, K + P * math.cos(u) + Q * math.sin(u) + R * math.cos(2 * u) + S * math.sin(2 * u)


def brier_coeffs_split(h1, h2, y):
    """(P, Q, R, S) of the Brier sum from two independent noisy estimates h1 = (a, b, c) and h2 of the same sinusoids
    (two halves of the twin's trajectories). Every product takes one factor from each half, so each coefficient is an
    unbiased estimate of the noiseless one (a product of two estimates from one half would carry the variance)."""
    a1, b1, c1 = (np.asarray(v, float) for v in h1)
    a2, b2, c2 = (np.asarray(v, float) for v in h2)
    y = np.asarray(y, float)
    r1, r2 = a1 - y, a2 - y
    return (float(np.sum(r1 * b2 + r2 * b1)), float(np.sum(r1 * c2 + r2 * c1)),
            float(np.sum(b1 * b2) - np.sum(c1 * c2)) / 2, float(np.sum(b1 * c2 + b2 * c1)) / 2)


def train_e4(fv, theta0, sweeps):
    """Design E4: per parameter in fixed order, the exact sinusoid of every training output (fv(theta) returns the
    vector of outputs) and the exact Brier minimum along it (brier_min). fv must close over the labels' points; the
    labels are passed through fv.y. Returns theta and the history of the training Brier loss (one value per sweep)."""
    th = np.asarray(theta0, float).copy()
    d = len(th)
    f0 = np.asarray(fv(th), float)
    y = np.asarray(fv.y, float)
    hist = [float(np.mean(((f0 - y) / 2) ** 2))]
    for _ in range(sweeps):
        for k in range(d):
            e = np.zeros(d)
            e[k] = math.pi / 2
            a, b, c = sinusoid(fv(th - e), f0, fv(th + e))
            u, _ = brier_min(a, b, c, y)
            fn = a + b * math.cos(u) + c * math.sin(u)
            if np.sum((fn - y) ** 2) <= np.sum((f0 - y) ** 2):
                th[k] += u
                f0 = fn
        hist.append(float(np.mean(((f0 - y) / 2) ** 2)))
    return th, hist


def train(f, theta0, X, y):
    """Design E's whole training: one tangent evaluation and one formula."""
    f0, G = tangent(f, theta0, X)
    theta, tau = closed_form(f0, G, y, theta0)
    return dict(theta=theta, tau=tau, f0=f0, G=G, evaluations=len(X) * (2 * len(theta0) + 1))
