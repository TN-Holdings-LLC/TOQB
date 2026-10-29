"""Tests of toqb.p3d (the Paper 3 diagnosis check)."""
import math

import numpy as np

from toqb import exact_batch as EB
from toqb import p3d as P
from toqb import task_loop as TL


def test_fast_simulator_matches_z0_batch_and_exact_z0():
    for n, L in ((3, 2), (5, 4), (6, 3)):
        rng = np.random.default_rng(n * 10 + L)
        M = P.Model(n, L)
        th = rng.uniform(-math.pi, math.pi, M.d)
        X = rng.uniform(-1, 1, (5, n))
        A = np.array([TL.angle_list(th, x, n, L, P.ENC) for x in X])
        assert np.max(np.abs(M.f(th, X) - EB.z0_batch(A, n, L))) < 1e-12
        assert abs(M.f(th, X[:1])[0] - TL.exact_z0(A[0], n, L)) < 1e-12


def test_adjoint_gradient_equals_parameter_shift_every_parameter():
    n, L = 4, 3
    rng = np.random.default_rng(3)
    M = P.Model(n, L)
    th = rng.uniform(-2, 2, M.d)
    X = rng.uniform(-1, 1, (3, n))
    f, J = M.grad(th, X)
    assert np.max(np.abs(f - M.f(th, X))) < 1e-13
    for k in range(M.d):
        e = np.zeros(M.d)
        e[k] = math.pi / 2
        assert np.max(np.abs((M.f(th + e, X) - M.f(th - e, X)) / 2 - J[:, k])) < 1e-12


def test_train_c_follows_s2rc_update_and_random_sequence():
    """Two loops by hand, with s2rc's exact sequence of draws, against train_c."""
    n, L = 3, 2
    M = P.Model(n, L)
    rng = np.random.default_rng(0)
    Xtr = rng.uniform(-1, 1, (8, n))
    ytr = np.array([1.0, -1.0] * 4)
    p = dict(P.TRAIN_C, loops=2)
    th, gn = P.train_c(M, Xtr, ytr, 5, p)
    r = np.random.default_rng(5)
    m = r.uniform(-p["init"], p["init"], M.d)
    for _ in range(2):
        idx = r.choice(len(Xtr), p["sim_batch"], replace=False)
        D = r.choice([-1.0, 1.0], (p["pairs"], M.d))
        zs = np.array([[TL.exact_z0(TL.angle_list(c, Xtr[i], n, L, P.ENC), n, L) for i in idx]
                       for c in np.vstack([m + p["h"] * D, m - p["h"] * D])])
        ls = ((1 - zs * ytr[idx][None, :]) / 2).mean(axis=1)
        K = p["pairs"]
        g = (((ls[:K] - ls[K:]) / (2 * p["h"]))[:, None] * D).mean(axis=0)
        m = m - p["lr"] * g
    assert np.max(np.abs(th - m)) < 1e-12


def test_g_is_the_expectation_of_c_and_damping_is_a_learning_rate():
    """G's gradient is the mean of C's loss gradient; and with outputs lambda * f, C's step is exactly lambda times
    the noiseless step (the identity behind cause 2: a larger lambda only rescales the learning rate)."""
    n, L = 3, 2
    M = P.Model(n, L)
    rng = np.random.default_rng(1)
    th = rng.uniform(-1, 1, M.d)
    X = rng.uniform(-1, 1, (6, n))
    y = np.array([1.0, -1.0] * 3)
    _, J = M.grad(th, X)
    gG = -(y[:, None] * J).mean(axis=0) / 2
    h = 1e-5
    num = np.array([(np.mean((1 - y * M.f(th + h * e, X)) / 2) - np.mean((1 - y * M.f(th - h * e, X)) / 2)) / (2 * h)
                    for e in np.eye(M.d)])
    assert np.max(np.abs(num - gG)) < 1e-8
    D = rng.choice([-1.0, 1.0], (8, M.d))
    for lam in (0.268, 0.496):
        def step(scale):
            zp = np.stack([scale * M.f(th + 0.1 * dk, X) for dk in D])
            zm = np.stack([scale * M.f(th - 0.1 * dk, X) for dk in D])
            lp, lm = ((1 - zp * y) / 2).mean(axis=1), ((1 - zm * y) / 2).mean(axis=1)
            return (((lp - lm) / 0.2)[:, None] * D).mean(axis=0)
        assert np.max(np.abs(step(lam) - lam * step(1.0))) < 1e-14


def test_train_g_descends_and_e_runs():
    n, L = 3, 2
    M = P.Model(n, L)
    rng = np.random.default_rng(2)
    X = rng.uniform(-1, 1, (10, n))
    y = np.sign(M.f(rng.uniform(-0.5, 0.5, M.d), X))
    loss = lambda t: np.mean((1 - y * M.f(t, X)) / 2)
    th, gn = P.train_g(M, X, y, dict(lr=0.4, steps=30))
    assert loss(th) < loss(np.zeros(M.d)) and len(gn) == 30
    th, hist = P.train_e(M, X, y, dict(sweeps=1))
    assert hist[-1] <= hist[0]


def test_task_c_shares_test_set_and_nests_training():
    a, b = P.data(dict(P.task_c(17, 64), layers=2, n=4)), P.data(dict(P.task_c(17, 330), layers=2, n=4))
    assert np.array_equal(a[2], b[2]) and np.array_equal(a[3], b[3])
    big = {tuple(np.round(x, 12)) for x in b[0]}
    assert all(tuple(np.round(x, 12)) in big for x in a[0])


def test_score_and_mcnemar():
    bo, ao, p = P.mcnemar_worse([0, 0, 0, 1, 1], [1, 1, 1, 1, 0])
    assert (bo, ao) == (3, 1) and 0 < p < 1
    assert P.holm([0.001, 0.2, 0.003]) == [True, False, True]
