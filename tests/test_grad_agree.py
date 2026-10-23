"""toqb.grad_agree's projections on a stand-in twin: a uniform shrink gives cosine 1 and the shrink as the scale; a
bent output gives a lower cosine."""
import math

import numpy as np
import pytest

pytest.importorskip("qiskit")
from toqb import grad_agree as G  # noqa: E402
from toqb import s2r2 as S2  # noqa: E402
from toqb import task_loop as TL  # noqa: E402
from toqb import undamp as U  # noqa: E402


class FakeR:
    def __init__(self, task, f):
        self.task, self.f = task, f

    def compile(self, th, x):
        return (np.asarray(th), np.asarray(x))

    def z(self, model, cs, T, seed, crn=False):
        return np.array([self.f(U.ideal_z(th, [x], self.task)[0], x) for th, x in cs])


def _setup():
    task = dict(n=4, layers=2, enc=math.pi / 2, teacher_seed=3, teacher_angle=0.3, teacher_gap=0.2, n_train=8,
                n_test=8)
    X, y, _, _ = S2.teacher_data2(task)
    d = TL.n_params(4, 2)
    D = np.random.default_rng(1).choice([-1.0, 1.0], (16, d))
    theta = np.random.default_rng(2).uniform(-1, 1, d)
    return task, X, np.asarray(y, float), D, theta


def test_uniform_shrink_keeps_the_direction():
    task, X, y, D, theta = _setup()
    st, si = G.projections(FakeR(task, lambda z, x: 0.3 * z + 0.05), theta, X, y, task, D, 0.1, 1, 0, chunk=5)
    assert G.cos(st, si) == pytest.approx(1.0, abs=1e-12)
    assert np.linalg.norm(st) / np.linalg.norm(si) == pytest.approx(0.3, rel=1e-9)


def test_bent_output_lowers_the_cosine():
    task, X, y, D, theta = _setup()
    st, si = G.projections(FakeR(task, lambda z, x: 0.3 * z * (1 + x[0])), theta, X, y, task, D, 0.1, 1, 0)
    assert G.cos(st, si) < 0.99
