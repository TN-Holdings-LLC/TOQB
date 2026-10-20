# Design C rehearsal on the stand-in (2026-10-20; simulation only, not scored)

**Record fixed** at home on 2026-10-20, 09:45 CEST: the pod's zip `s2rc_rehearsal.zip` (written 09:29 CEST) has
SHA-256 `d93dc912365e71bedefb4b31b015e627e98b0292537d0d4e554e8794fa5b389c`. Its contents are in
`s2rc_rehearsal_1/`, unchanged except `jobs.txt`, where the pod's folder is written `<pod>/`.

**Run.** `gpu/s2rc_rehearsal.sh` at TOQB `5a6981e`, psf-zero `7a827829`; one H100 80 GB, 224 CPUs, PAR 6; seeds
201-203; lr 0.4; 2,000 loops; P = 500; N = 1,000; T_pred = 1,024; R = 20,000. 04:07:09-09:29:24 CEST (5 h 22 min).
The twin is built from the stand-in's published calibration (`snapshot:marrakesh`); the "device" is the stage-0
stand-in (`t12` 0.3, `over` 0.01, `zz_hz` 10 kHz, seed 20261017). Design C r7 §6.

## (a) Procedure check: passed

All 12 runs are valid; every record of §4-§5 exists (with the stand-in in place of the device); both prediction
intervals were produced; the stand-in's CE and accuracy are computed by the prediction's code path; H1 and H2 ran.
No fault, so no rerun.

## (b) Record (not a gate)

| run | train h | run h | correct / 500 (strict) | H1 p | predicted CE [99 %, twin + shots] | stand-in CE | inside: twin + shots / shots only | accuracy pred / stand-in | CE gap | P(1) rms |
|---|---|---|---|---|---|---|---|---|---|---|
| PSF L 8 s201 | 0.77 | 0.89 | 378 | 8.5e-32 | 0.5646 [0.5601, 0.5691] | 0.5688 | yes / no | 0.760 / 0.763 | +0.0042 | 0.0116 |
| PSF L 8 s202 | 0.78 | 0.88 | 380 | 8.6e-33 | 0.5675 [0.5630, 0.5721] | 0.5664 | yes / yes | 0.747 / 0.765 | −0.0012 | 0.0105 |
| PSF L 8 s203 | 0.73 | 0.88 | 352 | 1.6e-20 | 0.5740 [0.5695, 0.5786] | 0.5716 | yes / yes | 0.709 / 0.706 | −0.0025 | 0.0103 |
| Qiskit L 8 s201 | 1.87 | 2.74 | 356 | 4.6e-22 | 0.5237 [0.5194, 0.5280] | 0.5359 | no / no | 0.748 / 0.716 | +0.0122 | 0.0531 |
| Qiskit L 8 s202 | 1.88 | 2.75 | 358 | 7.4e-23 | 0.5187 [0.5144, 0.5232] | 0.5318 | no / no | 0.751 / 0.718 | +0.0132 | 0.0494 |
| Qiskit L 8 s203 | 1.59 | 1.85 | 349 | 2.1e-19 | 0.5159 [0.5114, 0.5202] | 0.5237 | no / no | 0.738 / 0.701 | +0.0078 | 0.0414 |
| PSF L 16 s201 | 1.49 | 1.72 | 303 | 1.2e-06 | 0.6313 [0.6264, 0.6363] | 0.6318 | yes / yes | 0.602 / 0.611 | +0.0004 | 0.0088 |
| PSF L 16 s202 | 1.49 | 1.73 | 294 | 4.8e-05 | 0.6385 [0.6336, 0.6434] | 0.6371 | yes / yes | 0.590 / 0.594 | −0.0014 | 0.0085 |
| PSF L 16 s203 | 1.49 | 1.71 | 297 | 1.5e-05 | 0.6384 [0.6336, 0.6433] | 0.6339 | yes / no | 0.586 / 0.597 | −0.0045 | 0.0082 |
| Qiskit L 16 s201 | 3.14 | 4.72 | 301 | 2.9e-06 | 0.5910 [0.5863, 0.5957] | 0.6019 | no / no | 0.609 / 0.606 | +0.0109 | 0.0331 |
| Qiskit L 16 s202 | 3.05 | 4.63 | 306 | 3.1e-07 | 0.5997 [0.5949, 0.6046] | 0.6078 | no / no | 0.601 / 0.615 | +0.0081 | 0.0262 |
| Qiskit L 16 s203 | 3.13 | 4.72 | 297 | 1.5e-05 | 0.6086 [0.6039, 0.6134] | 0.6102 | yes / yes | 0.588 / 0.599 | +0.0016 | 0.0135 |

- **H1** (Holm over the 4 cells, per seed): every cell below 0.01 for every seed; the largest adjusted p is 4.8e-05
  (PSF L 16, seed 202).
- **R1** (stand-in CE inside the twin + shots interval): PSF 6 of 6, Qiskit 1 of 6. Both Qiskit misses at L 16 and all
  three at L 8 lie above the interval: the stand-in is worse than the twin predicted.
- **H2** (the twin's P(1) error, PSF against Qiskit; here against the stand-in's exact P(1), averaged over the 3
  seeds per point; one-sided Wilcoxon over 500 points, Holm over 2 depths): L 8 mean difference 0.0208, Qiskit worse at
  421 of 500 points, p 4.3e-58; L 16 0.0072, 405 of 500, p 4.7e-43. On a device the error carries shot noise of about
  0.5/√250 = 0.032 per point, larger than these differences.
- **Vanity:** on the stand-in, every cell is far above chance and the twin's interval held for every PSF run.
- **Essential:** the stand-in differs from the twin on purpose (T1/T2 scaled, over-rotation, ZZ crosstalk), so these
  deviations are expected and do not move to the device. Qiskit reaches the lower CE on the twin and on the stand-in,
  but the twin predicts its circuits worse: Qiskit's placement reads the calibration, PSF's does not (C r7 §9). No
  device data.

## Times (C r7 §5)

- **W_r** = the largest Qiskit L 16 run time, training plus prediction, measured here with the stand-in's
  verification included (the record does not separate them): **17,004 s = 4.72 h**. It exceeds 4.4 h, so the replacement
  rule sets the device day's **time limit to W_r + 1.6 h = 6.32 h**.
- Qiskit L 16: training 3.05-3.14 h, then prediction and verification 1.6 h (`times.eval` 5,839-5,893 s), with 6 runs
  sharing the GPU. Qiskit L 8 s203, which ran with fewer neighbours at the end, needed 1,028 s for the same step against
  3,217-3,228 s for its sisters. The device day runs 4 runs and no verification, so both parts should be shorter; not
  measured.

## The learning curve (C r7 §8b), checked

The curve's last value equals the CE of the predicted P(1) on the first 100 test points (all of class +1) to within
the curve's own Monte Carlo error, for all 12 runs (for example Qiskit L 16 s201: curve 0.4422, first 100 points
0.4440). The gap between the curve and the predicted CE is therefore the one-class subset, as C r7 §8b said.

## Layer 4, stand-in tier (`layer4_standin/`; TOQB v0.2 prototype, not a claim)

`toqb.predscore from-s2rc`, `from-rehearsal` and the score, per run. The measurement kind is `exact-no-shots` (the
stand-in's exact P(1); per-point shots were not stored), so the scores are per shot. Every score carries the warnings
"truth tier stand-in", "exact truth without shots", the upper-bound note on the twin's Monte Carlo error, and that the
order of prediction and truth cannot be read from the record's times (one run made both). None is claimable.

| cell (mean of seeds 201-203) | Bernoulli score over chance, nats per shot per point | 99 % coverage of the twin's error, class +1 / −1 | P(1) rms |
|---|---|---|---|
| PSF L 8 | 0.0326 | 0.992 / 0.995 | 0.0108 |
| Qiskit L 8 | 0.0668 | 0.884 / 0.683 | 0.0480 |
| PSF L 16 | 0.0148 | 0.991 / 1.000 | 0.0085 |
| Qiskit L 16 | 0.0451 | 0.955 / 0.920 | 0.0242 |

Reading: the score over chance mixes how far the model is from ½ (Qiskit's lower CE) with how well the twin hits, so
Qiskit scores higher over chance while its coverage is lower. The coverage per class shows the twin's misses on
Qiskit's circuits sit mostly in class −1 at L 8. Comparing twins needs a reference prediction on the same truth
(`toqb.reftwin`, from the device day on).
