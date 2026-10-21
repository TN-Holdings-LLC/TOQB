"""The undamped readout (2026-10-21): design E's idea (solve by formula from what the model knows, no search) applied
to the answer of a model trained by design C.

The twin's noise shrinks and shifts the expectation value the classifier reads: on the same inputs,

    z_noisy ~ lam * z_ideal + delta,

where z_ideal is the noiseless <Z0> of the logical circuit and z_noisy the twin's (gate noise, relaxation, readout).
(lam, delta) are fitted by least squares between the twin and the exact noiseless model on the TRAINING INPUTS, with
no labels and no device or stand-in data. The noise sits in the dependent variable, so the slope is unbiased with few
trajectories. The answer is then

    z_u = clip((z - delta) / lam, -1, 1),      p(label +1) = (1 + z_u) / 2,

the clip being the physical range of an expectation value (no constant is chosen). For a model whose noiseless answers
are good this restores most of what the noise costs in CE; for a model whose noiseless answers are confidently wrong it
restores that too (results/readout-2026-10-21). Rescaling an expectation value by a known noise factor is a known
error-mitigation idea, not new.
"""
from __future__ import annotations

import numpy as np

from toqb import s2r2 as S2
from toqb import task_loop as TL
from toqb.s2rc import _scores


class Stop(Exception):
    pass


def fit(z_noisy, z_ideal):
    """(lam, delta, rms residual) of z_noisy ~ lam z_ideal + delta by least squares. lam must be positive."""
    z_noisy, z_ideal = np.asarray(z_noisy, float), np.asarray(z_ideal, float)
    if z_noisy.shape != z_ideal.shape or z_noisy.size < 3:
        raise Stop("fit needs two equal-length vectors of at least 3 values")
    if np.ptp(z_ideal) <= 1e-12:
        raise Stop("the ideal outputs are constant: the shrink cannot be fitted")
    lam, delta = np.polyfit(z_ideal, z_noisy, 1)
    if not lam > 0:
        raise Stop(f"the fitted shrink is not positive (lam = {lam:.4f})")
    rms = float(np.sqrt(np.mean((z_noisy - (lam * z_ideal + delta)) ** 2)))
    return float(lam), float(delta), rms


def apply(z, lam, delta):
    """The undamped expectation value, clipped to [-1, 1]."""
    return np.clip((np.asarray(z, float) - delta) / lam, -1.0, 1.0)


def ideal_z(theta, X, task):
    """Exact noiseless <Z0> of the model at theta for the inputs X (toqb.task_loop.exact_z0)."""
    n, L, enc = task["n"], task["layers"], task["enc"]
    return np.array([TL.exact_z0(TL.angle_list(theta, x, n, L, enc), n, L) for x in X])


def estimate(R, theta, X, task, traj, seed):
    """(lam, delta, rms) from the twin of runner R (its arm and model) and the exact noiseless model, on inputs X."""
    zt = R.z("sim", [R.compile(theta, x) for x in X], traj, seed)
    return fit(zt, ideal_z(theta, X, task))


def predict_job_undamped(p1, y, shots, reps, level, seed, lam, delta, traj=None):
    """toqb.s2rc.predict_job with the undamped readout: the same draws (same seed and order), each simulated job's
    <Z> undamped before it is scored. With lam = 1 and delta = 0 it equals predict_job up to the clip."""
    rng = np.random.default_rng(seed)
    P1 = np.broadcast_to(np.asarray(p1, dtype=float), (reps, len(p1)))
    if traj:
        P1 = np.clip(P1 + rng.standard_normal(P1.shape) * np.sqrt(P1 * (1 - P1) / traj), 0.0, 1.0)
    k = rng.binomial(shots, P1)
    zs = apply(1 - 2 * k / shots, lam, delta)
    ce = np.array([S2._ce(z, y) for z in zs])
    acc = np.mean(np.where(zs == 0, 0.5, (np.sign(zs) == y[None, :]).astype(float)), axis=1)
    lo, hi = (1 - level) / 2 * 100, (1 + level) / 2 * 100
    return dict(ce_mean=float(ce.mean()), ce_interval=[float(np.percentile(ce, lo)), float(np.percentile(ce, hi))],
                acc_mean=float(acc.mean()), acc_interval=[float(np.percentile(acc, lo)), float(np.percentile(acc, hi))],
                ce_exact=S2._ce(apply(1 - 2 * np.asarray(p1), lam, delta), y), reps=reps, level=level, shots=shots,
                lam=lam, delta=delta)


def score(z, y, lam, delta):
    """(CE, accuracy) of measured <Z> values with the undamped readout, as toqb.s2rc._scores."""
    return _scores(apply(z, lam, delta), np.asarray(y))
