"""Tests of toqb.qelm (the search-free classifier prototype). The slow light-cone check is `python -m toqb.qelm check`."""
import numpy as np

from toqb import qelm as Q


def test_features_match_qiskit_basis_circuits():
    from qiskit.quantum_info import Statevector
    n, L = 4, 2
    X = np.random.default_rng(1).uniform(-1, 1, (2, n))
    F = Q.features_noiseless(X, n, L, batch=2)
    for i, x in enumerate(X):
        for bi, bs in enumerate(Q.BASES):
            sv = Statevector(Q.circuit(x, bs, n, L).remove_final_measurements(inplace=False))
            for q in range(n):
                assert abs(1 - 2 * sv.probabilities([q])[1] - F[i, bi * n + q]) < 1e-12


def test_ols_is_invariant_to_per_feature_affine_maps():
    rng = np.random.default_rng(2)
    F, T = rng.normal(size=(40, 6)), rng.normal(size=(15, 6))
    y = np.sign(rng.normal(size=40))
    a, b = rng.normal(size=6), rng.uniform(0.1, 1.0, size=6)
    z1 = Q.ols_predict(Q.ols_fit(F, y), T)
    z2 = Q.ols_predict(Q.ols_fit(a + b * F, y), a + b * T)
    assert np.max(np.abs(z1 - z2)) < 1e-10


def test_device_features_layout_and_subsample():
    n, P, S = 3, 2, 10
    k1 = np.arange(P * 3 * n).reshape(P * 3, n) % (S + 1)
    F = Q.device_features(k1, S, n)
    assert F.shape == (P, 3 * n)
    assert F[1, n + 2] == 1 - 2 * k1[1 * 3 + 1, 2] / S  # point 1, basis Y, qubit 2
    k = np.array([[0, 5, 10]])
    sub = Q.subsample(k, 10, 4, 0)
    assert sub[0, 0] == 0 and sub[0, 2] == 4 and 0 <= sub[0, 1] <= 4


def test_affine_fit_recovers_damping_and_offset():
    rng = np.random.default_rng(3)
    F0 = rng.uniform(-1, 1, (50, 4))
    a, lam = np.array([0.1, -0.05, 0.0, 0.02]), np.array([0.8, 0.5, 0.3, 0.9])
    a2, l2 = Q.affine_fit(a + lam * F0, F0)
    assert np.allclose(a2, a) and np.allclose(l2, lam)


def test_data_split_is_fixed_and_scaled():
    Xtr, ytr, Xte, yte = Q.data()
    assert Xtr.shape == (Q.N_TRAIN, Q.N) and Xte.shape == (Q.N_TEST, Q.N)
    assert Xtr.min() >= -1 and Xtr.max() <= 1 and set(np.unique(ytr)) <= {-1.0, 1.0}
    assert np.array_equal(Q.data()[0], Xtr)


def test_depth_formula_is_the_argmax_of_the_lambda_squared_gap():
    a, b = 56.5, 26.4
    Ls = np.linspace(0.1, 100, 200001)
    gap = np.exp(-2 * Ls / a) - np.exp(-2 * Ls / b)
    assert abs(Ls[np.argmax(gap)] - Q.depth_formula(a, b)) < 1e-3
    assert round(Q.depth_formula(56.5, 26.4)) == Q.A_L == 19


def test_teacher_task_labels_and_margin():
    T = Q.teacher_task(n=4, L=2, pool=520)
    s = (T["F"] - T["mu"]) @ T["w"]
    assert np.all(np.sign(s) == T["y"]) and np.all(np.abs(s) >= T["gamma"])
    assert T["F"].shape == (Q.N_TRAIN + Q.N_TEST, 12) and T["kept"] >= Q.N_TRAIN + Q.N_TEST
