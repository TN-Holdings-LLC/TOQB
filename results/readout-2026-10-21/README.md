# The readout, two small tests (2026-10-21, home, cloud CPU; exploratory, nothing fixed, nothing scored by W8 / W11)

Question (owner, 2026-10-21): fix E, fix C, or carry E's strength into C? W12 part 1 showed a ceiling shared by C0 and
E4 (64 training points) and E4's optimism after sweep 1, so the optimiser is not where the room is. These tests look
at the readout instead: the answer p = (1 + z) / 2 of <Z0>.

## Test 1: a readout calibrated on the training labels (p = sigmoid(a z + b), exact maximum likelihood on the 64
training points), noiseless (`cal_noiseless.py`, `calibrated_noiseless.jsonl`)

| arm, point | test CE raw -> calibrated | test accuracy raw -> calibrated |
|---|---|---|
| Z | 0.6946 -> 0.5243 | 0.654 -> 0.707 |
| C0 25.5 % | 0.5120 -> 0.6064 | 0.747 -> 0.777 |
| C0 100 % | 0.4984 -> 0.5225 | 0.758 -> 0.774 |
| E4 25.5 % | 0.5202 -> 0.5308 | 0.730 -> 0.761 |
| E4 76.5 % | 0.5446 -> 0.6056 | 0.695 -> 0.725 |

Reading: it hurts CE for every trained model. A model fitted to the 64 points separates them, so the calibration fitted
on the same points is overconfident (C0 at 25.5 %: slope a 702). It only helps theta = 0. Rejected.

## Test 2: label-free undamping (`undamp.py`, `undamp_diag.jsonl`)

The twin's noise shrinks and shifts <Z0>: z_noisy ~ lam z + delta. With (lam, delta) known, the answer is
p = (1 + (z_noisy - delta) / lam) / 2. Diagnostic here: (lam, delta) fitted by least squares between the stand-in's
test outputs (records) and exact noiseless outputs on the same inputs, **without labels**; the labels only score.

| arm, point | lam / delta | stand-in CE -> undamped (noiseless) | accuracy -> undamped |
|---|---|---|---|
| Z | 0.391 / 0.050 | 0.6432 -> 0.8257 (0.6946) | 0.643 -> 0.660 |
| C0 25.5 % | 0.432 / 0.040 | 0.5928 -> 0.5469 (0.5120) | 0.723 -> 0.758 |
| C0 100 % | 0.463 / 0.042 | 0.5823 -> 0.5269 (0.4984) | 0.734 -> 0.757 |
| E4 25.5 % | 0.423 / 0.034 | 0.5991 -> 0.5282 (0.5202) | 0.721 -> 0.764 |
| E4 76.5 % | 0.441 / 0.043 | 0.6020 -> 0.5366 (0.5446) | 0.686 -> 0.736 |

Reading:
- For trained models the noise costs 0.06 to 0.08 in CE (stand-in against noiseless), and undamping recovers most of it
  (0.04 to 0.07), plus 0.02 to 0.05 in accuracy from removing the shift. That is larger than any E4-against-C0
  difference seen today (about 0.01 to 0.02).
- For theta = 0 it is worse: its noiseless answer is itself badly calibrated, and undamping restores that.
- Limits: (lam, delta) were fitted on the stand-in's test outputs, which a real run does not have. The honest version
  takes them from the twin alone on the training inputs (the twin and the stand-in agree within P(1) rms 0.01), or by
  formula from the noise model. Rescaling an expectation value by a known noise factor is a known error-mitigation
  idea (not checked by search today), not new.

## Test 3: the honest version, the twin alone (`honest_undamp.py`, `honest_undamp.jsonl`)

(lam, delta) from the twin alone: its outputs on the 64 training inputs (64 trajectories, seed predict.seed + 5)
against exact noiseless outputs on the same inputs; no labels and no stand-in in the fit. Applied to the stand-in's
recorded test outputs. Fruit match, 9 runs per arm and point (cloud CPU, about 110 s per parameter set).

| arm, point | lam / delta | stand-in CE raw -> undamped | accuracy | CE better in |
|---|---|---|---|---|
| Z | 0.379 / 0.054 | 0.6432 -> 0.8487 | 0.643 -> 0.663 | 4 / 9 |
| C0 25.5 % | 0.416 / 0.048 | 0.5928 -> 0.5432 | 0.723 -> 0.758 | 6 / 9 |
| C0 100 % | 0.437 / 0.050 | 0.5823 -> 0.5291 | 0.734 -> 0.757 | 6 / 9 |
| E4 25.5 % | 0.408 / 0.042 | 0.5991 -> 0.5226 | 0.721 -> 0.766 | 8 / 9 |
| E4 76.5 % | 0.426 / 0.051 | 0.6020 -> 0.5356 | 0.686 -> 0.738 | 8 / 9 |

By angle (trained models): at 0.3 and 1.0 undamping helps every arm (CE -0.06 to -0.15, accuracy up to +0.08); at 2.0
it helps E4 slightly and hurts C0 (CE 0.610 -> 0.629 at 100 %, 0.649 -> 0.715 at 25.5 %); theta = 0 is hurt at 1.0 and
2.0. Undamping restores the noiseless model's own confidence: it helps where the noiseless answers are good and hurts
where they are confidently wrong.

Reading: the twin-only, label-free undamping matches the diagnostic (test 2): on average it recovers 0.05 to 0.08 in
CE and 0.02 to 0.05 in accuracy for trained models, more than any optimiser difference seen today. It is not uniform:
it can hurt a poor model. The E4-against-C0 order after undamping is not read here (not a pre-registered comparison).

## Test 4: both compiler arms (`undamp_arms.py`, `undamp_arms_L8.jsonl`; the rehearsal of 2026-10-20, L 8, angle 0.3)

The same twin-only undamping on PSF's and Qiskit's (level 2, Target) runs, each arm trained on its own twin. Cloud
CPU: PSF about 110 s per run, Qiskit about 2,720 s per run (deeper circuits on 14 qubits); Qiskit seed 203 did not
finish within the 2-hour job limit and is missing. Scores below: the stand-in's exact P(1) redrawn as 1,000 shots per
point, 200 times (mean).

| run | lam | CE raw -> undamped | accuracy raw -> undamped |
|---|---|---|---|
| PSF 201 | 0.38 | 0.569 -> 0.436 | 0.752 -> 0.809 |
| PSF 202 | 0.40 | 0.567 -> 0.436 | 0.758 -> 0.808 |
| PSF 203 | 0.41 | 0.574 -> 0.461 | 0.709 -> 0.764 |
| Qiskit 201 | 0.60 | 0.537 -> 0.457 | 0.710 -> 0.759 |
| Qiskit 202 | 0.61 | 0.533 -> 0.458 | 0.712 -> 0.765 |

Reading: raw, Qiskit is better in CE by about 0.035 (more signal survives its noise: lam 0.61 against 0.40); undamped,
PSF is better by about 0.010 in CE and 0.03 in accuracy. Compiler figures from the same records: PSF's circuits are
2.4 times shorter (10.4 against 25.2 us), with 9 % fewer two-qubit gates (224 against 247) on 10 qubits instead of 14,
yet keep less signal on this stand-in. Two or three runs per arm, one easy teacher, post hoc: not a claim.
