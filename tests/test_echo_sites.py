"""toqb.echo_sites: the per-site signal is 1 for a perfect echo, 0 for random bits, and its group means and SE."""
import numpy as np

from toqb import echo_sites as ES
from toqb import kising_charge as KC


def _perfect(n, N=1000):
    out = {}
    for i in KC.INPUTS:
        bits = [1 - b for b in KC.input_bits(i, n)]  # the echo returns the flipped input
        out[i] = {"".join(str(b) for b in reversed(bits)): N}
    return out


def test_perfect_and_random():
    n = 6
    a, se = ES.site_signal(_perfect(n), n)
    assert np.allclose(a, 1) and np.allclose(se, 0)
    rnd = {i: {format(k, "06b"): 10 for k in range(64)} for i in KC.INPUTS}
    a, se = ES.site_signal(rnd, n)
    assert np.allclose(a, 0) and np.all(se > 0)
    m, e = ES.group(np.array([0.2, 0.4, 0.6]), np.array([0.1, 0.1, 0.1]), [0, 2])
    assert abs(m - 0.4) < 1e-12 and abs(e - np.sqrt(0.02) / 2) < 1e-12
