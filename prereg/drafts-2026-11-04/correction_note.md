# Declared: P6 corrected by our own floor and mirror (owner's go of 2026-11-04 11:44 CET)

Motivation: the post-hoc reference `results/posthoc-correction-2026-11-04` (fez: MSE ratio 0.09-0.22). This test
asks whether the correction, fixed here, works on a new run. The rule was chosen after seeing fez's data.

## Device and placement

- Device by the queue read right before the fetch, pending jobs only; ties in the order marrakesh, fez, kingston.
  If no copy qualifies on it, the next device in that order; if none qualifies, no job.
- Placement: `lattice2d` copy order (through `ising2d.place`), only the coupling graph and failed elements, as P6.
  No registry. psf-os 1250c90; builder `gpu/corr_device.py`; scorer `gpu/corr_score.py` (both fixed with this note).

## Job (one job, 4000 shots, no mitigation)

- P6 at theta_x 0.53, 0.3, 0.8, t 1-9 (27). Answers: sealed `results/p6-answers-2026-11-04`, `results/bank-2026-11-04`.
- Floor theta_x 0 at t 1, 3, 5, 6, 7, 9, 10 (7; 6 and 10 are the mirrors' depths).
- Mirror (U, barrier, U^dagger) of each theta_x at t 3, 5 (6); same copy; accepted only with CZ exactly doubled.
- Ring sentinel. 44 circuits; 52 s by the model on fake_kingston.

## The correction (fixed)

1. Rule R as P6: z0_q = mean floor at t 1, 5, 9; drop q if z0_q < median - max(5 x 1.4826 x MAD, 0.05).
2. F_q(t): the floor at t, linear between measured depths.
3. a_theta = median over kept q of mean_{t=3,5} [ 0.5 ln( clip(mirror_q(t) / max(F_q(2t), 0.05), 1e-3, 1) ) / t ].
4. z_corr = z / ( F_q(t) exp(a_theta t) ). SE scaled by the same factor.

## Judged (per theta_x)

1. **HELPS / NO EFFECT / HURTS:** MSE(z_corr, kept qubits) / MSE(raw, all) at 0.8 / 1.25.
2. **AGREES** after correction: |M_corr - M_exact| <= 0.05 at every t 1-9 (kept qubits with an answer).

## Reported (not judged)

- The floor step alone and the gate step alone (ratios); the gate decay per step; the mean correction factor per t
  (the noise grows by it); corrected 2 SE; sentinel; dropped qubits.
- Tutorial comparison at t 5, 7, 9 (their unmitigated gap 0.091, 0.139, 0.180).
- Scorer check before sending: on fez's data with OS2D's 0.53 mirror for every theta_x (post hoc), ratios 0.093 /
  0.105 / 0.213, AGREES / DIFFERS (0.3, +0.093 at t 9) / AGREES.

## Honest expectation

- The floor step likely helps (both devices post hoc). The gate step is a model (a mirror return's decay taken
  as the square of the forward decay); with each theta_x's own mirror the 0.3 over-correction may or may not shrink.
- One run, one device: a pass says the correction can work, not that it always does.
