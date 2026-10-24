# Flow C (owner's plan of 2026-10-24): one minute on the device for the zipper and Qiskit, with the twin rebuilt on the day's calibration. Report only. The owner left the open points to Claude (2026-10-24 06:56 CEST); this note is fixed by SHA-256 and CEST time before any submission

**Why.** The zipper has never run on hardware, and on the device day the twin (snapshot of 2026-10-13) under-stated
PSF-Zero's signal by 1.5-2.3x while matching Qiskit's at L 16 (results/device-2026-10-22). Two questions, no
comparison of the arms (the far-teacher test's device threshold was not met, results/far-qiskit-2026-10-23):

1. Does the zipper's circuit behave on the device as the twin says: its scale, offset and correlation per point?
2. Is the twin's scale error the calibration's age: does a twin rebuilt from the day's calibration (fetched just
   before submission) predict the device's scale for both arms?

Owner, 2026-10-24: "the device may be used for correction". Used here only to rebuild the twin from the day's
calibration; no readout is corrected (the narrower reading, consistent with the decision of 2026-10-23 02:16).

- **Models.** No training. The far-teacher models after 2,000 loops: the zipper's (results/far-teacher-2026-10-23) and
  Qiskit's (results/far-qiskit-2026-10-23), teachers 17, 18, 19; the first 90 test points of each teacher (fixed
  order, labels balanced to within the draw). 2 arms x 3 teachers x 90 = 540 circuits, 250 shots each.
- **QPU time.** TOQB's model (0.036 s per circuit + 0.27 ms per shot + 3 s): 58.9 s, at most 60 s by `assemble
  --max-seconds 60`. The device day was billed 0.73 of the model (100 s against 137.6 s), so about 43 s expected.
  Only within the open plan's remaining minute; no paid time.
- **Steps (the device day).** [home, VPN off] `python -m toqb.s2rc_device fetch --backend ibm_marrakesh --out
  DAY/fetch`; [pod] for each of the 6 records `python -m toqb.device_reuse DAY/fetch RECORD RUNS --points 90` (the
  zipper by formula on a24, Qiskit by its level-2 search on the day's Target; twin predictions with the day's Target
  and with the snapshot), then `python -m toqb.s2rc_device assemble --fetch DAY/fetch --runs RUNS --out JOB
  --max-seconds 60` (ISA, failed elements, time); [home, VPN off] `submit --job JOB`, `result --job JOB`; anywhere
  `python -m toqb.flowc_score JOB RUNS flowc.md`. Checked end to end on a fake device without IBM
  (results/flow-c-procedure-2026-10-24).
- **Reported (no rule).** Per arm: the device's z against each twin's z per point (scale, offset, correlation,
  residual); the share of +1 answers; accuracy with the 250 shots against each twin's 99 % interval; the twin's scale
  error with the snapshot against with the day's calibration.
- **Not done.** No arm comparison is tested; no readout is corrected; nothing is chosen from the result.
- **Not claimed.** One job, one day, 90 points per teacher and arm.

## Choices (left to Claude by the owner, 2026-10-24 06:56 CEST)

1. 90 test points per teacher and arm (540 circuits): the most that fits the minute by TOQB's time model.
2. ibm_marrakesh: the device of the twin's and the stand-in's snapshot and of the device day.
3. The open plan's remaining minute only; if `assemble` predicts more than 60 s, or IBM reports less than a minute
   left, nothing is submitted.
4. The twin is rebuilt from the day's calibration; readouts are not corrected.
