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


def train(f, theta0, X, y):
    """Design E's whole training: one tangent evaluation and one formula."""
    f0, G = tangent(f, theta0, X)
    theta, tau = closed_form(f0, G, y, theta0)
    return dict(theta=theta, tau=tau, f0=f0, G=G, evaluations=len(X) * (2 * len(theta0) + 1))
