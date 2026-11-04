"""gpu/ising2d_answers.py (numpy path) equals psf_os.ising2d.answer_cone (Aer) and the t = 1 closed form cos(theta_x)."""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "gpu"))
import ising2d_answers as A  # noqa: E402

from psf_os import ising2d as I  # noqa: E402


def test_numpy_equals_aer_cones():
    r = A.run([2, 3], "numpy", "double")
    for t in (2, 3):
        for q, z in zip(I.QUBITS, r[str(t)]["z"]):
            assert abs(z - I.answer_cone(q, t)[0]) < 1e-10


def test_t1_closed_form():
    r = A.run([1], "numpy", "double")
    assert np.allclose(r["1"]["z"], np.cos(I.THETA_X), atol=1e-12)
