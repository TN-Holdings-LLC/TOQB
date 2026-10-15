"""Classical reference models for TOQB's loop task (numpy only): the bar a quantum model is read against.

They are trained on the same training points and scored on the same test points as the loop's arms. They are not
participants and are not tuned to the task. Each has one fixed configuration and one seed, as below.

  logistic        logistic regression on x, gradient descent (5000 steps, rate 0.5, L2 1e-3)
  logistic_quad   the same on x, x^2 and the pairwise products x_i x_j
  mlp32           one hidden layer of 32 tanh units, full-batch gradient descent (5000 steps, rate 0.3, seed 0)
  knn5            5 nearest neighbours (Euclidean), majority vote

Recorded per model: test accuracy, the time to train and predict (one thread), and the energy that time takes at the
plan's assumed CPU power (`energy.cpu_w`, a range): an estimate, not a measurement.
"""
from __future__ import annotations

import time

import numpy as np


def _logistic(Xtr, ytr, Xte, quad=False):
    def feats(X):
        cols = [X]
        if quad:
            n = X.shape[1]
            cols += [X ** 2, np.array([X[:, i] * X[:, j] for i in range(n) for j in range(i + 1, n)]).T]
        return np.hstack(cols + [np.ones((len(X), 1))])
    A, B = feats(Xtr), feats(Xte)
    w = np.zeros(A.shape[1])
    t = (ytr > 0).astype(float)
    for _ in range(5000):
        p = 1 / (1 + np.exp(-A @ w))
        w -= 0.5 * (A.T @ (p - t) / len(t) + 1e-3 * w)
    return np.where(B @ w > 0, 1.0, -1.0)


def _mlp(Xtr, ytr, Xte, hidden=32, seed=0):
    rng = np.random.default_rng(seed)
    W1, b1 = rng.normal(0, 1, (Xtr.shape[1], hidden)), np.zeros(hidden)
    W2, b2 = rng.normal(0, 0.1, hidden), 0.0
    t = (ytr > 0).astype(float)
    for _ in range(5000):
        H = np.tanh(Xtr @ W1 + b1)
        g = (1 / (1 + np.exp(-(H @ W2 + b2))) - t) / len(t)
        gH = np.outer(g, W2) * (1 - H ** 2)
        W2, b2 = W2 - 0.3 * (H.T @ g), b2 - 0.3 * g.sum()
        W1, b1 = W1 - 0.3 * (Xtr.T @ gH), b1 - 0.3 * gH.sum(0)
    return np.where(np.tanh(Xte @ W1 + b1) @ W2 + b2 > 0, 1.0, -1.0)


def _knn(Xtr, ytr, Xte, k=5):
    d = ((Xte[:, None, :] - Xtr[None, :, :]) ** 2).sum(-1)
    return np.where(ytr[np.argsort(d, 1)[:, :k]].sum(1) > 0, 1.0, -1.0)


MODELS = {
    "logistic": lambda a, b, c: _logistic(a, b, c),
    "logistic_quad": lambda a, b, c: _logistic(a, b, c, quad=True),
    "mlp32": lambda a, b, c: _mlp(a, b, c),
    "knn5": lambda a, b, c: _knn(a, b, c),
}


def run_classical(plan):
    """The classical reference record of a loop plan."""
    from toqb.task_loop import _cest_now, teacher_data
    Xtr, ytr, Xte, yte = teacher_data(plan["task"])
    rows = []
    for name, fn in MODELS.items():
        s = time.perf_counter()
        pred = fn(Xtr, ytr, Xte)
        t = time.perf_counter() - s
        rows.append(dict(model=name, accuracy=float(np.mean(pred == yte)), seconds=t))
    return dict(kind="classical reference", started=_cest_now(), numpy=np.__version__, models=rows)
