# Long training with checkpoints, zipper against item 31 (report only; rule fixed in prereg/drafts-2026-10-23/zip_long_note.md, `376a709`)

H100 pod, 2026-10-23 02:00-05:49 CEST (6 runs, 16,000 loops, points 500-16,000); zip SHA-256
d6d23224d521da23a0a540f28456da12aae702c60cd7ac8686cfc3e111005ce3. All 6 runs valid. Scored at home
(`score_home.md`, `toqb.zip_long_score RUNS - ...`).

**Deviation, recorded.** The declared report included the undamped readout at every point. It was stopped at 06:33
CEST: the owner had dropped the undamped readout for future work that morning (02:16 CEST), and on this pod it ran at
11-14 minutes a point (2.5-3 h more; a day earlier, 1-2 minutes a point; cause not found). No undamp output was kept;
the score is without lam, delta and the undamped CE. The rule does not use them. Two of the six training runs
(item 31, teachers 11 and 12) also ran slower throughout (0.85 s a loop against about 0.5; cause not found).

**Check.** The 2,000-loop point equals yesterday's depth sweep's final parameters, bit for bit, in all 6 runs.

## The rule (16,000 loops; noiseless test CE per point, Wilcoxon, Holm over 3 teachers, alpha 0.01)

The zipper WINs in 3 of 3 teachers (gain +0.041 to +0.054; Holm p 3e-3 to 3e-7): **its gain persists.** It also WINs
at every other point except two TIEs at 1,000 loops (17 of 18 comparisons).

## What longer training does (reported, no claim)

| loops | noiseless test CE item 31 / zipper | stand-in acc, no shots: item 31 / zipper | with 250 shots: item 31 / zipper |
|---|---|---|---|
| 500 | 0.41-0.43 / 0.35-0.41 | 0.63-0.68 / 0.87-0.94 | 0.63-0.65 / 0.72-0.76 |
| 2,000 | 0.47-0.55 / 0.43-0.50 | 0.58-0.63 / 0.76-0.85 | 0.60-0.66 / 0.69-0.73 |
| 16,000 | 0.56-0.59 / 0.52-0.54 | 0.53-0.59 / 0.71-0.74 | 0.59-0.63 / 0.67-0.69 |

- Both arms get **worse** with more loops, on every measure, in every teacher: the best of the recorded points is the
  first, 500 loops. Design C's 2,000 loops are already past it.
- The noiseless train accuracy stays high (0.80-1.00) while the train CE rises: the models grow more extreme. One
  reading, not tested: design C's loss, mean (1 - y z) / 2, rewards a large |z| and does not penalise a confident
  wrong answer, so long training drives the outputs to extremes, which costs CE and, on unseen points, accuracy.
- Not chosen from it: no loop count is picked by these results (the declaration). Fewer loops, or a stopping rule that
  reads only the training loss, would need its own declaration on new teachers.
- Vanity: the zipper wins at 16,000 loops, 3 of 3. Essential: with 250 shots the zipper's accuracy is 0.67-0.69 at
  16,000 loops against 0.72-0.76 at 500; longer training is a loss for both arms, and the zipper's lead (+0.06 to
  +0.08 with shots) stays.
- Not claimed: one seed; the stand-in is TOQB's model of a 2026-10-13 calibration.
