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
