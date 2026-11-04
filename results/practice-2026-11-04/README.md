# Practice problems through the user entrance, ibm_marrakesh, 2026-11-04: RUNS; 22/22 READS, 19/22 AGREES, 19/22 BEATS, no correction

- **Declaration:** `prereg/drafts-2026-11-04/practice_note.md` (SHA-256 22474f14...b595ab, 12:44 CET, cfdb65c).
- `psf-os fetch` 13:30:11 CET (calibration 13:20:08; failed as this morning); `psf-os run2d` batch of 22 user circuits,
  all accepted, 70 circuits (5f612ab); job dblibpd8mdtc73d66v90, sent 13:32:35 CET, DONE. psf-os ac84182.
  Scored by `gpu/practice_score.py` (unchanged) from the entrance's own answer cards. **RUNS** (no hand step).

| problem | t | READS | AGREES (\|M - exact\| <= 0.05) | BEATS (trivial guess) |
|---|---|---|---|---|
| P4 b = pi/4 - 0.3 (33 q) | 2-16 | all | all (worst -0.031, t 16) | all |
| P4 b = pi/4 - 0.05 (33 q) | 2-16 | all | all (worst +0.024, t 2) | all |
| P5 theta 0.4 (151 q) | 2-8 | all | t 2 only (-0.046; then -0.06 to -0.07) | t 8 only |
| P5 theta 0.8 (151 q) | 2-8 | all | all (worst -0.048, t 8) | all |
| P5 theta 1.0 (151 q) | 2-8 | all | all (worst -0.010) | all |

## Reported

- P4 light-cone site (the one site carrying the signal at b = pi/4 - 0.05): 0.876 / 0.770 / 0.611 / 0.479 / 0.299
  against 0.897 / 0.808 / 0.641 / 0.509 / 0.408 at t 2 / 4 / 8 / 12 / 16: -0.02 to -0.03 up to t 12, -0.11 at t 16.
  P4 b = pi/4 - 0.05's AGREES on M is weak by itself (M is a mean of mostly near-zero sites); the site is the test.
- P5 theta 0.4: answers near 1, so the all-1 guess (MSE 0.004-0.011) is hard to beat with a loss of about 4-7 %.
- Floor 0.957-0.972 (this morning's P6 job on marrakesh: 0.850 at t 1). The device was in a better state at 13:30
  CET; this run does not separate the OS's part from the device's.
- Mirror means are far below the forward results' quality (P4 t 16: mirror 0.05 while the card agrees within 0.03):
  the mirror is a fault locator, not a measure of the forward error (as the correction test found).
- Mirror flags: P4 25 (t 2); P5 95, 100, 101, 36, 41; the worst P5 qubits include 94 and 100.
- CZ counts as the problems need after ac84182 (before it, twice as many).
- Sentinel CLEAN.
