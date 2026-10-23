# Data and gradient test (report only; rules fixed in prereg/drafts-2026-10-23/data_grad_note.md, `3c1ba20`)

H100 pod, 2026-10-23 02:34-04:00 CEST; `score.md` as written on the pod; zip SHA-256
98ccbdd5fc6be4512a5886a4f8b6fea386e8b397be83c73ffb30dd7d65b9afea. All 12 runs valid. Checked mid-run (workplace's
question): the 64- and 256-point runs differ in their parameters (max |difference| 1.56 and 1.42 for teacher 14) and
share the test labels; their predicted CE agreed to 3e-5 by chance.

## The rules (accuracy without correction: stand-in exact P(1), no shots; McNemar, Holm over 3 teachers, alpha 0.01)

- **A. Was 64 points the wall?** No, for either arm: 256 points WIN in 1 of 3 teachers for item 31, 0 of 3 for the
  zipper.
- **B. Does the zipper's gain survive more data?** YES, 3 of 3 (at 256 points: 0.804 / 0.610, 0.830 / 0.644, 0.818 /
  0.652; Holm p 4e-17 to 3e-13). At 64 points (reported) also 3 of 3.

## Vanity and essential

- Vanity: accuracy without shots, zipper 0.79-0.83 against item 31's 0.57-0.65 (+0.17 to +0.22).
- Essential: with the run's 250 shots the zipper's accuracy falls to 0.69-0.74 (its signal is shrunk more, so shots
  flip more answers); item 31's stays 0.61-0.64. Still +0.05 to +0.10 for the zipper in all 6 cells. Its CE is worse
  (0.640-0.651 against 0.620-0.641 with shots): right side more often, less confident.
- More data narrows the noiseless train-test gap (e.g. zipper teacher 14: train 0.298 / test 0.434 at 64 points, 0.422 /
  0.438 at 256) without lowering the test CE much: the limit is not the number of training points.

## Gradient agreement (report only)

- Raw cos(twin, noiseless), mean over 6 runs: zipper 0.907 at the start, 0.722 at the end; item 31 0.768 and 0.554.
- The trajectory noise is large (cos between two twin seeds -0.13 to 0.83), so the raw cosines are lowered by noise and
  are not comparable across arms as they stand.
- **Post hoc (not declared):** dividing by the noise's expected attenuation (sqrt(2r / (1 + r)), r the twin-twin
  cosine; one run with r < 0 left out) gives medians: zipper 1.04 at the start and 0.97 at the end, item 31 0.92 and
  0.70. Values above 1 show the correction itself is noisy. Read as: on the zipper's circuit the twin's gradient points
  where the noiseless one does, within noise; on item 31's it bends, more after training. Consistent with the
  uniform-shrink reading; a declared test with more trajectories would be needed to claim it.
- The gradient's scale (twin / noiseless) is 0.08-0.24, about the twin's lam.
- Not claimed: one seed, the stand-in is TOQB's model of a 2026-10-13 calibration.
