# C r9 device day (2026-10-22): workplace post hoc notes for future work (2026-10-23, about 01:35 CEST)

**What this is.** Post hoc only, after the results; nothing here is a hypothesis test. It is computed from home's
files (`results/device-2026-10-22`: `raw_counts.json.gz`, `manifest.json`, `undamp.json`, `device/lam_posthoc.txt`,
`device/map_posthoc.txt`).

**Check of the reading.** The device's per-point z = P(clbit 0 = 0) − P(clbit 0 = 1) reproduces home's raw CE for
every cell (0.5716, 0.5867, 0.5087, 0.6613).

## 1. The twin's shape was right; its scale was wrong

Per point, the device z regressed on the twin's z (z_twin = 1 − 2 · twin_p1):

| cell | scale a | offset b | correlation | residual rms | shot-noise rms (250 shots) |
|---|---|---|---|---|---|
| PSF L 8 | 1.54 | +0.065 | 0.970 | 0.087 | 0.057 |
| PSF L 16 | 2.30 | +0.041 | 0.969 | 0.078 | 0.057 |
| Qiskit L 16 | 1.00 | +0.023 | 0.964 | 0.066 | 0.060 |
| Qiskit L 8 | 0.63 | +0.223 | **0.721** | **0.200** | 0.057 |

- In 3 of 4 cells the twin predicts which points get a large or a small answer almost exactly (correlation 0.96-0.97).
  The left-over is close to shot noise.
- What was wrong is two numbers per cell: a scale and an offset.
- Qiskit L 8 is the exception: its shape is broken too. Home found that its readout qubit 102 had degraded.

## 2. PSF's per-layer factor is constant, and about what the CZ drift predicts

**Per layer.** PSF's scale a is 1.54 at L 8 and 2.30 at L 16, which is 1.055 and 1.053 per layer: the same factor
per layer.

**CZ drift.** Home's calibration comparison gives a mean CZ error on PSF's couplers of 0.0077 at the snapshot and
0.0061 on the day. For depolarizing CZs, a signal is multiplied by about (1 − 4r/3) per CZ. With item 31's 28 CZ per
layer, the drift alone predicts:

| | per layer | L 8 | L 16 |
|---|---|---|---|
| predicted from the CZ drift | 1.062 | 1.62 | 2.62 |
| observed | 1.054 | 1.54 | 2.30 |

**Reading.** PSF's 2-2.7-fold under-statement is plausibly mostly the 9 days of calibration drift (an old map), not a
pessimistic noise model. This is a rough estimate.

**Not consistent for Qiskit L 16.** The mean CZ error over its 27 couplers rose slightly, yet a = 1.00. Its couplers
are not all used equally, so the mean may not be the right figure.

**Test.** Rebuild the twin on the day's calibration (`fetch_after.json`, Target SHA-256 c84ea703…) and refit λ on the
training inputs.

| outcome | meaning |
|---|---|
| λ_twin on the day's calibration ≈ the device's λ (PSF about 0.67-0.71) | the noise model is fine; only the map was old |
| λ_twin stays low | the noise model itself is pessimistic |

## 3. What knowing the device's (λ, δ) would have given

The device's λ and δ are home's `lam_posthoc`: fitted on the test inputs, against the noiseless output, without
labels. They are in-sample, so these figures are optimistic.

| cell | raw CE | undamped with the twin's λ (fixed beforehand) | undamped with the device's λ, δ | accuracy (device λ) |
|---|---|---|---|---|
| PSF L 8 | 0.509 | 0.504 | **0.425** | 0.85 |
| PSF L 16 | 0.572 | 0.797 | **0.517** | 0.73 |
| Qiskit L 16 | 0.587 | 0.524 | **0.514** | 0.73 |
| Qiskit L 8 | 0.661 | 0.691 | 0.789 (worse: its shape is broken) | 0.65 |

**Reading.**

- When the twin's shape is right, two numbers measured on the device turn the raw answers into much better ones.
- That supports home's next step: measure λ and δ on the device from the training inputs, label-free. Those are the
  clean version of these in-sample numbers.
- It also needs a guard. A cell whose answers do not follow the noiseless model (low correlation, as Qiskit L 8) must
  not be undamped. Example rule: undamp only if the device-vs-twin correlation on the training inputs is ≥ 0.9. Such a
  rule would be fixed before the run.

## 4. Consequences for the zipper (an estimate, unverified)

- The twin gave the zipper λ 0.17 at L 16 and 0.11 at L 20, hence 4.8 times the shots at L 20.
- If the twin under-states PSF's signal on the device by the same per-layer factor (about 1.05), the zipper's device
  λ at L 16 would be about 0.17 × 2.3 ≈ 0.39. The shot cost would then be about 6-7 times less than the twin's table.
- This is only a scaling of the twin. The device measurement in home's item 2 is what would show it.

## 5. Suggestions for the next pre-registration (for the owner to decide)

1. Measure (λ, δ) on the device for every cell from the 64 training inputs, label-free, before the test points are
   read.
2. A fixed correlation guard, as in §3.
3. The twin rebuilt on the day's calibration, beside the old one, as a report: map against model.
4. The zipper's cells included, so that its shot cost is measured on the device.
