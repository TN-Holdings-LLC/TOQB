# Predictions before the run: Qiskit arm on far teachers 17-19, against the zipper (written 2026-10-23 10:11 CEST, before any result)

**What will run (home).**

- **Arm:** `qiskit:2:target:template`, the search-type compiler.
- **Conditions:** the same as today's far-teacher test: L 16, teachers 17-19 at angle 1.0, seed 301, 500 and 2,000
  loops, θ = 0 evaluated too.
- **Comparison:** against today's zipper runs (`psfai:template_zip`), on the same test points.
- **Truth tier:** the stand-in, a simulation. Results are never to be called device results.

**What this is.** Workplace predictions, written down before the data so that they can be checked afterwards. They are
not the run's declared rules.

## Inputs used (all from earlier records; none from the new run)

| | item 31 (PSF) | zipper (PSF) | Qiskit |
|---|---|---|---|
| CZ, L 16 | 448 | 336 | 506 |
| duration, L 16 | 18.0 µs | 11.7 µs | **48.2 µs** |
| twin λ / δ at L 16, near teacher (device-day records) | 0.268 / +0.046 | 0.158 / +0.015 (zip compare) | **0.496 / +0.087** |
| δ / λ (offset relative to signal) | 0.17 | 0.09-0.10 | **0.18** |
| twin's +1 share on the test set, L 16 near teacher | 0.91 | – | 0.80 |
| device day: device scale against the twin | 2.30 | – | **1.00** |

- **Qiskit's twin signal is the largest.** Its λ is about 3 times the zipper's, despite the most CZ and the longest
  duration. The likely reason is that its placement uses the calibration to pick better qubits; this is unconfirmed.
- **Qiskit's offset relative to its signal (0.18) is the same as item 31's**, about twice the zipper's.

## Predictions

Each has a check and a confidence (low below 60 %, medium 60-75 %, high above 75 %).

| # | prediction | check | confidence |
|---|---|---|---|
| P1 | Qiskit carries an offset like item 31's | +1 share of Qiskit ≥ 0.80 at θ = 0 and at both budgets | medium-high |
| P2 | As a result, raw shot-free accuracy is near chance at θ = 0 | Qiskit 0.50-0.60 at θ = 0 for all three teachers | medium |
| P3 | At 2,000 loops the zipper beats Qiskit on raw accuracy, in about the same pattern as against item 31 | zipper more accurate on ≥ 2 of 3 teachers (McNemar, Holm, α 0.01) | medium |
| P4 | The stand-in punishes Qiskit's 48 µs more than the twin predicted, through idle relaxation and static ZZ (10 kHz) | twin-vs-stand-in P(1) rmse for Qiskit clearly above the PSF arms' (about 0.01), e.g. ≥ 0.02 | medium; this rests on how the stand-in applies ZZ during idles, which I have not checked |
| P5 | Threshold-free (AUC), the zipper and Qiskit are close, with mixed signs across teachers | AUC difference within ±0.05 on ≥ 2 of 3 teachers at 2,000 loops | low-medium |
| P6 | What was learned (noiseless accuracy of the learned θ): no consistent winner between the zipper and Qiskit | the winner differs across teachers, or differences ≤ 0.03 | low; Qiskit's larger signal could give it the cleaner training signal, which would make Qiskit the better learner |
| P7 | With 250 shots, Qiskit loses less than the zipper relative to shot-free (its λ is larger) | (shot-free − with shots) is smaller for Qiskit than for the zipper on ≥ 2 of 3 teachers at 2,000 loops | medium-high |
| P8 | t17 stays hard for every arm | noiseless accuracy at 2,000 loops ≤ 0.66 for Qiskit as for both PSF arms | medium |

## What would change the picture

- **If P3 holds but P5 and P6 do not favour the zipper:** the raw-accuracy win against Qiskit is, as against item 31,
  mostly an offset effect. That is not evidence that formula beats search.
- **If Qiskit wins on AUC and on learned accuracy (P5 and P6 fail toward Qiskit):** search placement with
  calibration is buying a better training signal through larger λ. Formula-only placement would then need a
  calibration-free answer to signal size, not only fewer CZ.
- **If P4 fails** (the stand-in agrees with the twin for Qiskit): the 48 µs duration costs less than its length
  suggests, on this stand-in.

## Notes

- **The test points are shared.** The zipper's numbers come from today's runs. Because the plans are the same, the
  500 test points should be the same; the check is that the test labels are identical across the files.
- **Scope.** This comparison was not part of far_teacher_note.md. If home declares rules for it before scoring, those
  rules decide; these predictions are only checked against the outcome.
