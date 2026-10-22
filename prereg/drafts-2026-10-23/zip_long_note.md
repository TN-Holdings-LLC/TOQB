# Long training with checkpoints, the zipper against item 31: report only, one rule fixed before the run (declared 2026-10-23)

The workplace's proposal of 2026-10-23 (watch the training, not only its end), with the owner's choices of 2026-10-23
about 08:45 JST (01:45 CEST): L 16 only, 6 runs; yesterday's teachers 11, 12, 13; 64 training points (256 not now).
Report only: nothing is chosen from it and no device run follows from it.

**Questions.** (1) Does the zipper's better trained model (noiseless CE lower in 11 of 12 cells of the depth sweep,
`results/zip-depth-2026-10-22`) persist, shrink or grow with longer training? (2) Does either arm drift to a
noise-sensitive form (the twin's lam along the training)? (3) Where does the training stop improving with 64 training
points (noiseless train against test CE)?

- **Runs.** L 16 x teachers 11, 12, 13 (angle 0.3, gap 0.2, 64 training and 500 test points) x the arms
  `psfai:template` (item 31; Rust template, check mode) and `psfai:template_zip` (the zipper, TOQB's `ring_zip.py`):
  6 runs of design C (C0, seed 301, lr 0.4, 8 pairs, batch 4, 32 trajectories) for 16,000 loops with
  `toqb.s2rc_ckpt` (the same training draws as `toqb.s2rc`); points at 500, 1,000, 2,000, 4,000, 8,000 and 16,000
  loops, each predicted (T_pred 1,024, R 20,000) and verified on the stand-in of `snapshot:marrakesh`. Then
  `toqb.undamp_run` at every point. Script `gpu/zip_long.sh` (psf_compile c61 and AI front end a22 as yesterday; the
  zipper is not a24's), score `toqb.zip_long_score`.
- **The rule (the only test).** At 16,000 loops, per teacher: d_i = noiseless CE_i(item 31) - noiseless CE_i(zipper)
  on the 500 test points (the trained model's exact output, no noise); two-sided Wilcoxon signed-rank, Holm over the
  3 teachers, alpha 0.01, WIN if the adjusted p < 0.01 and mean d > 0. The zipper's gain **persists** if it WINs in
  at least 2 of the 3 teachers.
- **Reported, without a claim.** The same comparison at 500 to 8,000 loops (its course with the loops); per run and
  point: noiseless test and train CE and accuracy, the twin's lam and delta, the stand-in CE without shots (raw and
  undamped) and with the run's shots, the twin's CE on 100 test points along the training.
- **Not done.** No loop count is chosen by any result; only the points above are compared. Not 32,000 loops (a
  separate declaration if wanted).
- **Check stated now.** The 2,000-loop point uses the same plan up to the loop count as yesterday's depth sweep, so
  its parameters must equal those runs' final parameters bit for bit (`--prev`; reported, a difference is a fault to
  explain before reading the rest).
- **Seen before fixing.** Yesterday's depth sweep at 2,000 loops (these teachers); the score's smoke test on those
  runs (noiseless test / train CE at 2,000 loops: item 31 0.553 / 0.494, 0.465 / 0.424, 0.498 / 0.464; zipper 0.499 /
  0.358, 0.426 / 0.349, 0.460 / 0.385 for teachers 11-13). Nothing after 2,000 loops is known.
- **Not claimed.** One seed; the stand-in and the twin are TOQB's model of a 2026-10-13 calibration (on the device of
  2026-10-22 the twin's scale was off by 1.5-2.3 times, its per-point shape right).
- **Time and cost (estimate).** H100, the 6 runs together (PAR 6): about 3.5-4.5 h of training (yesterday a 2,000-loop
  L 16 run took 1,050-1,310 s with 4 together), then about 20-30 min of undamping (36 points); about $15-20.
