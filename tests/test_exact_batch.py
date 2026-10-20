"""The batched exact simulator equals task_loop.exact_z0. Numpy only."""
import numpy as np

from toqb import exact_batch as EB
from toqb import task_loop as TL


def test_batch_equals_exact_z0():
    rng = np.random.default_rng(3)
    for L in (1, 3):
        d = TL.n_params(10, L)
        As = [TL.angle_list(rng.uniform(-2, 2, d), rng.uniform(-1, 1, 10), 10, L, 1.5707963267948966) for _ in range(4)]
        ref = np.array([TL.exact_z0(a, 10, L) for a in As])
        assert np.max(np.abs(EB.z0_batch(As, 10, L) - ref)) < 1e-12
