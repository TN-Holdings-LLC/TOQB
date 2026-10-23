# Far teachers: formula placement (PSF-Zero's zipper) against search placement (Qiskit). Report only. DRAFT: rules proposed 2026-10-23, not yet fixed; the owner confirms them before the run, then this note is fixed by SHA-256 and CEST time

**Why.** The project's question is formula-built placement (PSF-Zero) against search (Qiskit), trained with design C0.
Today's diagnostics found that the earlier C tasks measured little learning: on the device day's task (teacher 4,
angle 0.3) the untrained model (theta = 0) is already 0.934 (L 16) and 0.940 (L 8) accurate noiseless, and the twin
training made both arms worse (L 16: PSF 0.762, Qiskit 0.730; L 8: 0.880, 0.787). The far teachers (angle 1.0) need
learning. The zipper is PSF-Zero's latest E5 ring schedule (psfbind ring r2, opt-in in a24); its far-teacher runs exist
(results/far-teacher-2026-10-23). This test adds the Qiskit arm on the same plans. It also gives the decision aid for
the remaining 1 minute of IBM time (owner, 2026-10-23 about 17:06 JST: a device run only if it can decide).

- **Task and runs.** The far-teacher plans unchanged: L 16, n 10, teachers 17, 18, 19 at angle 1.0 (gap 0.2, 64
  training and 500 test points), design C0 (seed 301, lr 0.4, 8 pairs, batch 4, 32 trajectories), 2,000 loops with a
  checkpoint at 500 (`toqb.s2rc_ckpt`), predicted and verified on the stand-in of `snapshot:marrakesh`; theta = 0
  through the arm (`toqb.theta0_eval`). New: the arm `qiskit:2:target:template` (Qiskit 2.5.2, level 2, the device's
  Target, seed_transpiler 0): 3 runs and 3 theta = 0 evaluations. The zipper (`psfai:template_zip`) is read from the
  far-teacher records; the score stops unless the test labels are identical. Script `gpu/far_qiskit.sh`, score
  `toqb.farq_score`.
- **Rule A (proposed; owner's main measure).** Accuracy without correction, shot-free: a test point is correct when
  the stand-in's exact P(1) is on the label's side. At 500 and at 2,000 loops, per teacher, zipper against Qiskit:
  exact McNemar on the 500 paired points; Holm over the 6; alpha 0.01. At a point, an arm is the more accurate if it
  WINs in at least 2 of 3 teachers (either direction is reported).
- **Rule B (proposed; replaces the far-teacher test's "gain" rule).** The trained model itself: its noiseless <Z> on
  the label's side, the same McNemar, Holm, 2 of 3. Reason: the far-teacher test's rule B (gain from theta = 0 in
  stand-in accuracy) assumed the readout offset cancels; with item 31 answering +1 on 84-94 % of balanced points it did
  not (teacher 19: +0.068 noiseless, -0.020 on the stand-in). B reads what was learned, free of the circuit's offset.
- **Decision aid for the device (proposed).** Per teacher and point, the power of one exact McNemar at alpha 0.01 in
  the stand-in's direction, with 300 and 500 test points drawn from the 500 and each answer from 250 shots of the
  stand-in's P(1) (2,000 repetitions, seed 20261024). Proposed threshold: a device declaration is written only if the
  power at 300 points is at least 0.8 for at least 2 of 3 teachers at one loop count; otherwise the minute is kept.
  The device is not the stand-in: the twin's scale was off by 1.5-2.3x for PSF on the device day (Qiskit 1.00).
- **Reported, without a claim.** Accuracy with 250 shots; the share of +1 answers; the stand-in and noiseless AUC and
  CE; twin-against-stand-in P(1) rmse; CZ count and duration; all at theta = 0, 500 and 2,000 loops. No undamped
  readout (owner, 2026-10-23). The workplace's predictions, written before any Qiskit result, are kept beside this note
  (`ftq_predictions_workplace_2026-10-23.md`) and checked afterwards; they are not rules.
- **Not done.** No loop count, teacher or threshold is chosen from results. Item 31 is not part of the comparison.
- **Seen before fixing.** The far-teacher results (zipper and item 31) and their post hoc readings; the device-day
  records. Nothing of the Qiskit arm on the far teachers.
- **Not claimed.** One seed; the stand-in is TOQB's model of a 2026-10-13 calibration; a stand-in result is never a
  device result.
- **Time and cost (estimate).** H100: fresh pod setup about 15 min; teacher data 4-8 min a job; Qiskit's circuit is
  longer (506 CZ, 48 us against the zipper's 336, 11.7 us), so training perhaps 30-50 min (6 jobs together); score
  about 15 min; about 1-1.5 h, about $4-6.

## For the owner to confirm before the run

1. Rule B as the trained model's noiseless accuracy (instead of the gain from theta = 0).
2. The device threshold: power at 300 points at least 0.8 in 2 of 3 teachers.
3. Zipper only against Qiskit (item 31 left out).
