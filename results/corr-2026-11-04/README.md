# Correction test on ibm_fez, 2026-11-04: HELPS at all three theta_x; AGREES at 0.53 and 0.3, DIFFERS at 0.8 (over-corrects)

- **Declaration:** `prereg/drafts-2026-11-04/correction_note.md` (SHA-256 7ef2013d...2e541816, 11:44 CET, 01ae963).
- Queue 11:48 CET (marrakesh 2, fez 1, kingston 79) -> ibm_fez; fetch 11:48:53 CET (calibration 11:21:44; failed
  qubit 72, coupler (32, 33), outside the patch); copy (0, 0); psf-os 1250c90; 44 circuits (b14459c);
  job dblgrsm74qds73dqfbqg, sent 11:50:25 CET, DONE. Scored by `gpu/corr_score.py` (unchanged).

## Judged

| theta_x | gate decay / step (own mirror) | MSE ratio | verdict | after correction, diff t 1..9 | AGREES |
|---|---|---|---|---|---|
| 0.53 | 0.984 | 0.082 | HELPS | +0.007 ... +0.019 (max) | AGREES |
| 0.3 | 0.995 | 0.018 | HELPS | -0.016 ... +0.002 | AGREES |
| 0.8 | 0.957 | 0.403 | HELPS | +0.022 rising to +0.098 | DIFFERS (t 4: +0.052) |

Raw differences were -0.08 to -0.21 (0.53), -0.09 to -0.21 (0.3), -0.07 to -0.13 (0.8).

## Reported

- Floor alone: 0.148 / 0.039 / 0.308; gate alone: 0.260 / 0.365 / 0.237. Rule R dropped 27, 28 (as on fez this morning).
- Floor 0.916 (t 1) to 0.783 (t 10). Mean correction factor at t 9: 0.73 / 0.80 / 0.57 (noise grows by 1/factor).
- Corrected 2 SE 0.004-0.010: the remaining +0.01-0.02 at 0.53 is several SE, i.e. a small bias is left.
- At 0.8 the mirror decays faster than the square of the forward decay, so the gate step over-corrects; with
  0.53's mirror borrowed for 0.8 (post hoc this morning) it did not. The model holds at small and middle theta_x,
  not at 0.8.
- Tutorial (t 5, 7, 9): ours corrected |diff| 0.015, 0.000, 0.019 at 0.53 against their unmitigated gap 0.091, 0.139,
  0.180 (their mitigated result is a different method; not compared).
- Ring sentinel DEAD (fez's ring, as this morning); not part of the correction.
- Limits: the same device the rule was chosen on, 1 h 40 min later; one run.
