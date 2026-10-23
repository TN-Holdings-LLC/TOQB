# Far-teacher test: does the zipper learn more than item 31 when the answer is far from the start? Report only, two rules fixed before the run (declared 2026-10-23)

**Why.** Post hoc on the long training (`results/zip-long-2026-10-23`, its theta = 0 diagnostic and the workplace's
Addenda 1-5): with teachers at angle 0.3 the untrained model (theta = 0) already scores 0.90-0.96 noiseless on two of
three teachers, so most of the zipper's lead there was readout; on the one teacher that needed learning (teacher 11,
0.66 at theta = 0) the zipper gained +0.24 in 500 loops (offset removed) against item 31's +0.02. One teacher is not a
claim. This test puts every teacher far from the start. Owner's choices of 2026-10-23 about 15:30 JST: rules at both
500 and 2,000 loops; accuracy and what training added as the two measures; L 16 only, 6 runs.

- **Task.** L 16, n 10, teachers 17, 18, 19 at teacher angle 1.0 (gap 0.2, 64 training and 500 test points). Fixed
  before the run; checked at home only that their data can be made (teacher 17: theta = 0 noiseless accuracy 0.574,
  teacher 18: 0.640; teacher 19: data made in 461 s, its theta = 0 accuracy not computed). No teacher was chosen by a result.
- **Runs.** Arms `psfai:template` (item 31; Rust template, check mode) and `psfai:template_zip` (the zipper): design C
  (C0, seed 301, lr 0.4, 8 pairs, batch 4, 32 trajectories) for 2,000 loops with a checkpoint at 500
  (`toqb.s2rc_ckpt`), predicted and verified on the stand-in of `snapshot:marrakesh`; and the untrained model through
  each arm (`toqb.theta0_eval`). 6 runs and 6 theta = 0 evaluations together. Script `gpu/far_teacher.sh`, score
  `toqb.far_score`.
- **Main measure (owner, 2026-10-23).** Accuracy without any correction: a test point is correct when the stand-in's
  exact P(1) is on the label's side (no shots).
- **Rule A.** At 500 and at 2,000 loops, per teacher, the zipper against item 31: exact McNemar on the 500 paired test
  points; Holm over the 6 comparisons; alpha 0.01; WIN = more points correct. At a point, the zipper is more accurate
  if it WINs in at least 2 of 3 teachers.
- **Rule B.** What training added: per test point g = correct(trained) - correct(theta = 0) for each arm, d = g(zipper)
  - g(item 31); two-sided Wilcoxon signed-rank on d; Holm over the 6; WIN if adjusted p < 0.01 and mean d > 0. At a
  point, the zipper learned more if it WINs in at least 2 of 3 teachers. (A circuit's readout offset is in both terms
  of g and largely cancels, so B reads learning rather than readout.)
- **Reported, without a claim.** Accuracy with the run's 250 shots; the share of +1 answers; the stand-in AUC and the
  noiseless AUC, accuracy and CE; all at theta = 0, 500 and 2,000 loops. No undamped readout (owner, 2026-10-23).
- **Not done.** No loop count, teacher or threshold is chosen from results; only the points above are compared.
- **Seen before fixing.** The long training and its diagnostics (teachers 11-13 at angle 0.3); the score's smoke test
  on them (A and B both 3 of 3 at 500 and 2,000 loops there, post hoc). Nothing of the far teachers beyond their
  theta = 0 noiseless accuracy.
- **Not claimed.** One seed; the stand-in is TOQB's model of a 2026-10-13 calibration.
- **Time and cost (estimate).** H100: teacher data about 4-5 min a teacher in every job, training about 25-35 min (12
  jobs together), score about 15 min; about 1 h with setup, about $4-5.
