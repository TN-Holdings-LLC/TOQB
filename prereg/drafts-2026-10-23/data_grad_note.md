# Data and gradient test: report only, two rules fixed before the run (declared 2026-10-23)

The workplace's proposal of 2026-10-23 (items 2 and 3 after the owner's decision of 02:16 CEST: no device-measured
correction, no undamped readout; results raw, accuracy the main measure; improvements on the formula side only), with
the owner's choices of about 09:25 JST: 64 and 256 training points (12 runs); rules fixed. Report only: nothing is
chosen from it; making the zipper the default for training, or more training points the task, are separate decisions.

**Questions.** (1) Is the 64-point training set the wall (does 256 do better)? (2) Does the zipper's gain survive
more data? (3) Does the twin's training gradient point where the noiseless model's does, more on the zipper's circuit
(where the twin's noise acts as one uniform shrink, `results/lam-ablate-2026-10-22`) than on item 31's?

- **Runs.** L 16 x new teachers 14, 15, 16 (angle 0.3, gap 0.2, 500 test points) x 256 or 64 training points x arms
  `psfai:template` (item 31) and `psfai:template_zip` (the zipper): 12 runs of design C (C0, seed 301, lr 0.4, 8 pairs,
  batch 4, 32 trajectories, 2,000 loops; `toqb.s2rc`) on `snapshot:marrakesh`, verified on its stand-in. The 64-point
  task takes the first 32 points per class of the 256-point task and the same 500 test points (`teacher_data2`'s new
  optional `test_after` = 128; without it nothing changes, checked: yesterday's labels reproduce). A training loop
  costs the same with either set (4 points a loop). Script `gpu/data_grad.sh`; score `toqb.data_grad_score`.
- **Gradient (report only).** `toqb.grad_agree` on each run, at theta = 0 and at the end: the loss's derivative along
  64 fixed Rademacher directions (h 0.1), on the first 64 training points, in the twin (32 trajectories, common random
  numbers, two independent seeds) and in the noiseless model; cos(twin, noiseless), cos(twin seed 1, twin seed 2) (the
  trajectory noise's own limit) and the norm ratio.
- **Main measure.** Accuracy without correction: a test point is correct when the stand-in's exact P(1) is on the
  label's side (no shots; the accuracy with the run's 250 shots is reported beside it).
- **Rule A (per arm).** 256 against 64 training points, per teacher: exact McNemar on the 500 paired test points, Holm
  over the 3 teachers, alpha 0.01; WIN = more points correct. The data was the wall for that arm if 256 WINs in at
  least 2 of 3 teachers.
- **Rule B.** At 256 training points, the zipper against item 31, the same test: the zipper's gain survives more data
  if it WINs in at least 2 of 3 teachers.
- **Reported, without a claim.** Rule B's comparison at 64 points; CE (no shots, with shots); the noiseless test and
  train CE; the gradient figures. The undamped readout is not used (owner, 2026-10-23).
- **Not claimed.** One seed; the stand-in is TOQB's model of a 2026-10-13 calibration. A gradient agreement on the
  twin says nothing yet about the device.
- **Running beside it.** The long training (`zip_long_note.md`) on another pod; nothing of it is seen before this
  note is fixed.
- **Time and cost (estimate).** H100: plans about 10 min (756 teacher points per class), training about 50-60 min (12
  runs, 6 at a time), gradients about 50 min; about 2 h, about $8-10.
