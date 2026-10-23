"""teacher_data2's optional test_after (2026-10-23): unchanged without it; a shared test set and nested training sets
with it."""
import math

import numpy as np
import pytest

pytest.importorskip("qiskit")
from toqb import s2r2 as S2  # noqa: E402


def _task(**kw):
    t = dict(n=6, layers=2, enc=math.pi / 2, teacher_seed=14, teacher_angle=0.3, teacher_gap=0.2, n_train=16,
             n_test=40)
    t.update(kw)
    return t


def test_unchanged_without_it():
    a = S2.teacher_data2(_task())
    b = S2.teacher_data2(_task(test_after=None))
    for x, y in zip(a, b):
        assert np.array_equal(x, y)


def test_shared_test_set_and_nested_training():
    big = S2.teacher_data2(_task(n_train=64))
    small = S2.teacher_data2(_task(n_train=16, test_after=32))
    assert np.array_equal(big[2], small[2]) and np.array_equal(big[3], small[3])
    rows = {tuple(r) for r in big[0]}
    assert all(tuple(r) in rows for r in small[0])
    assert len(small[0]) == 16 and len(small[2]) == 40
