"""gpu/kim_answers.py (numpy backend) equals psf_os.kim's answers (Aer statevector cones) on a small heavy-hex piece."""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "gpu"))
import kim_answers as KA  # noqa: E402

from psf_os import kim as K  # noqa: E402

EDGES = sorted(tuple(sorted(e)) for e in [
    (0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 7), (7, 0),
    (4, 8), (8, 9), (9, 10), (10, 11), (11, 12), (12, 3), (0, 13)])
QUBITS = sorted({q for e in EDGES for q in e})


def test_numpy_cones_equal_kim_answers():
    lat = dict(qubits=QUBITS, edges=[list(e) for e in EDGES])
    for th in (0.4, 1.0, np.pi / 2):
        r = KA.run(lat, [th], [2, 4], "numpy", "double")
        for t in (2, 4):
            assert np.allclose(r[f"{th:.6f}"][str(t)]["z"], K.answers(QUBITS, EDGES, th, t)["z"], atol=1e-10)


def test_max_qubits_leaves_none():
    lat = dict(qubits=QUBITS, edges=[list(e) for e in EDGES])
    r = KA.run(lat, [0.4], [4], "numpy", "double", max_qubits=5)
    assert any(z is None for z in r[f"{0.4:.6f}"]["4"]["z"])
