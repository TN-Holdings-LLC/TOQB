"""Design E's formula: the parameter-shift tangent is exact for single-rotation parameters, and on a model that is
linear in its parameters the closed form fits the requested outputs exactly. Numpy only."""
import math

import numpy as np

from toqb import s2re as E


def _model(theta, x):
    # a toy "circuit": a product of cosines, each parameter entering as one rotation angle (cos(a + theta_k))
    return float(np.prod([math.cos(a + t) for a, t in zip(x, theta)]))


def test_parameter_shift_is_exact():
    rng = np.random.default_rng(1)
    X = rng.uniform(-1, 1, (5, 3))
    th = rng.uniform(-0.5, 0.5, 3)
    f0, G = E.tangent(_model, th, X)
    eps = 1e-6
    for k in range(3):
        e = np.zeros(3)
        e[k] = eps
        num = [(_model(th + e, x) - _model(th - e, x)) / (2 * eps) for x in X]
        assert np.allclose(G[:, k], num, atol=1e-8)


def test_closed_form_fits_a_linear_model_exactly():
    rng = np.random.default_rng(2)
    G = rng.normal(size=(4, 9))
    f0 = rng.normal(size=4) * 0.1
    y = np.array([1, -1, 1, -1])
    theta, tau = E.closed_form(f0, G, y, np.zeros(9))
    assert np.allclose(f0 + G @ theta, y * tau)
    # minimum norm: no component outside the row space of G
    P = np.linalg.pinv(G) @ G
    assert np.allclose(P @ theta, theta)


def test_brier_min_is_the_global_minimum():
    rng = np.random.default_rng(3)
    U = np.linspace(-np.pi, np.pi, 200001)
    for trial in range(200):
        m = int(rng.integers(1, 9))
        a, b, c = rng.normal(size=(3, m)) * rng.uniform(0.01, 1, 3)[:, None]
        y = rng.choice([-1.0, 1.0], m)
        u, v = E.brier_min(a, b, c, y)
        grid = ((a[None] + np.cos(U)[:, None] * b[None] + np.sin(U)[:, None] * c[None] - y[None]) ** 2).sum(axis=1)
        direct = float(((a + b * np.cos(u) + c * np.sin(u) - y) ** 2).sum())
        assert abs(direct - v) <= 1e-9 * max(1.0, abs(v))
        assert v <= grid.min() + 1e-9


def test_sinusoid_is_exact_for_one_rotation():
    x = np.array([0.3, -0.7, 1.1])
    th = np.array([0.2, -0.4, 0.9])
    k = 1
    vals = []
    for s in (-math.pi / 2, 0.0, math.pi / 2, 0.83):
        t = th.copy()
        t[k] += s
        vals.append(_model(t, x))
    a, b, c = E.sinusoid(vals[0], vals[1], vals[2])
    assert abs(a + b * math.cos(0.83) + c * math.sin(0.83) - vals[3]) < 1e-12


def test_train_e4_never_raises_the_loss():
    rng = np.random.default_rng(4)
    X = rng.uniform(-1, 1, (12, 3))
    y = np.where(rng.uniform(size=12) > 0.5, 1.0, -1.0)
    fv = lambda th: np.array([_model(th, x) for x in X])
    fv.y = y
    th, hist = E.train_e4(fv, np.zeros(3), 3)
    assert all(h2 <= h1 + 1e-12 for h1, h2 in zip(hist, hist[1:]))
    assert abs(hist[-1] - float(np.mean(((fv(th) - y) / 2) ** 2))) < 1e-12
