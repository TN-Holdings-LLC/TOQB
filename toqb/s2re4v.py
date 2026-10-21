"""Design E4v (2026-10-21, W13): E4 with the step chosen on one part of the twin's trajectories and checked on another.

Why. E4 forms the Brier coefficients (P, Q, R, S) of one parameter from two independent halves of the trajectories,
so each coefficient is unbiased; it then takes u = the minimum of the estimated curve. The minimum of a noisy curve
is biased downwards (the winner's curse: min is concave, so E[min of the estimate] <= min of the truth), and the step
goes partly where the noise points. Over 170 or 330 parameters the claimed training gain becomes much larger than the
real one (home's finding, TOQB cbc00f5; the fruit match, F5).

What changes (and nothing else). The `traj` trajectories of every circuit are split into four independent quarters
(common random numbers within a quarter, as E4 does within a half):

- C_A = the unbiased coefficients from quarters 1 and 2 (one factor from each, `s2re.brier_coeffs_split`);
- C_B = the same from quarters 3 and 4, independent of C_A;
- u_A = the exact minimum of C_A's curve (`s2re.trig2_min`, the quartic in tan(u / 2));
- v = C_B's change at u_A: an unbiased estimate of the true change at u_A, because C_B does not depend on u_A;
- the parameter moves by u_A only if v < 0 (the check says the step helps); otherwise it stays.

No constant is chosen: the threshold is 0, the split is fixed, the order of parameters is E4's. The training cost per
circuit is the same `traj` trajectories as E4's, so the budget points (and W11's matching) are unchanged.

What it does not change. It still fits the 64 training points; it removes steps that only fit the twin's noise, not
the limit that 64 points put on what generalises.

`v` as recorded is chosen by its own sign, so the sum of accepted v's is itself optimistic. The realised change is
measured as in W12 (an exact twin evaluation), not taken from v.
"""
from __future__ import annotations

import math

import numpy as np

from toqb import s2re as E

QUARTERS = 4


def quarter_seed(base, sweep, d, k, q):
    """The trajectory seed of quarter q (0-3) for parameter k of sweep `sweep`. 11 > the largest offset 2 * 3 + 1, so
    seeds never repeat within a run."""
    if not 0 <= q < QUARTERS:
        raise ValueError(f"quarter {q} not in 0..{QUARTERS - 1}")
    return int(base) + 11 * (int(sweep) * int(d) + int(k)) + 2 * int(q) + 1


def delta_val(C, u):
    """The Brier sum's change from u = 0 to u, for coefficients C = (P, Q, R, S)."""
    P, Q, R, S = C
    return float(P * (math.cos(u) - 1) + Q * math.sin(u) + R * (math.cos(2 * u) - 1) + S * math.sin(2 * u))


def select_verify(hs, y):
    """hs: four quarter estimates (a, b, c) of every training point's sinusoid along one parameter; y: labels.
    Returns (u, verified, selected, accepted):
      u         the step taken (u_A if accepted, else 0.0);
      verified  v = C_B's change at u_A (unbiased for the true change at u_A), or 0.0 if not accepted;
      selected  C_A's own change at u_A (the curve the step was chosen on; optimistic), or 0.0 if not accepted;
      accepted  True if u_A != 0 and v < 0."""
    if len(hs) != QUARTERS:
        raise ValueError(f"need {QUARTERS} quarter estimates, got {len(hs)}")
    CA = E.brier_coeffs_split(hs[0], hs[1], y)
    CB = E.brier_coeffs_split(hs[2], hs[3], y)
    u, sel = E.trig2_min(*CA)
    if u == 0.0:
        return 0.0, 0.0, 0.0, False
    v = delta_val(CB, u)
    if v < 0:
        return float(u), v, float(sel), True
    return 0.0, 0.0, 0.0, False
