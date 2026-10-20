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
