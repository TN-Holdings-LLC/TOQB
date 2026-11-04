# DRAFT (not declared): P6 corrected by our own floor and mirror (owner's question of 2026-11-04 evening)

Motivation: the post-hoc reference `results/posthoc-correction-2026-11-04` (fez: MSE ratio 0.09-0.22). This test
asks whether the correction, fixed now, works on a new run. The rule below was chosen after seeing fez.

## Job (one job; device by the queue at fetch, pending jobs only; ties marrakesh, fez, kingston)

- Placement: `lattice2d` copy order, failed elements only, as in P6. psf-os unchanged in its circuit code.
- P6 at theta_x 0.53, 0.3, 0.8, t 1-9 (27). Floor theta_x 0 at t 1, 3, 5, 7, 9 (5; no extrapolation needed
  to depth 10: add t 10 if the builder allows, else F(10) = F(9)). Mirror of each theta_x at t 3, 5 (6), same copy,
  CZ exactly doubled. Ring sentinel. 4000 shots. Answers: the sealed P6 and bank answers.

## The correction (fixed)

1. Rule R (as P6) drops qubits. 2. F_q(t): the floor at t, linear between measured depths.
3. a_theta = median over kept qubits of mean_{t=3,5} [ 0.5 ln( clip(mirror_q(t) / max(F_q(2t), 0.05), 1e-3, 1) ) / t ].
4. z_corr = z / ( F_q(t) exp(a_theta t) ). SE scaled by the same factor.

## Judged (per theta_x)

1. **HELPS / NO EFFECT / HURTS:** MSE(z_corr, kept) / MSE(raw, all) at 0.8 / 1.25.
2. **AGREES** after correction: |M_corr - M_exact| <= 0.05 at every t (t 1-9).

## Reported

- The floor step alone and the gate step alone. Ratio of the mean correction factor (cost: noise grows by it).
- Tutorial comparison at t 5, 7, 9 (their unmitigated gap 0.091, 0.139, 0.180), not judged.

## Honest expectation

- The floor step is likely to help (both devices post hoc). The gate step is a model (decay of a mirror
  return taken as the square of the forward decay); it over-corrected theta_x 0.3 on fez when borrowed from 0.53.
- One run, one device: a pass says the correction can work, not that it always does.
