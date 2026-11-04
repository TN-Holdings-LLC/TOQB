# Practice problems through the user entrance on ibm_fez, 2026-11-04: RUNS; 22/22 READS, 18/22 AGREES, 20/22 BEATS; the same pattern as marrakesh

- **Declaration:** `prereg/drafts-2026-11-04/practice_fez_note.md` (SHA-256 6d886d38...60db00fc, 13:52 CET, 69f99d7),
  otherwise `practice_note.md`. `psf-os fetch` 13:55:31 CET (calibration 13:36:35; failed 72, (32, 33)); run2d batch
  of 22 accepted (P4 moved by the entrance to copy (4, 0), P5 on (0, 0)); job dblin89kbkrc73cnpcbg, sent 13:57:04 CET,
  DONE. Scored by `gpu/practice_score.py` (unchanged). **RUNS.**

| problem | AGREES (fez) | worst diff fez | worst diff marrakesh (13:32 CET) |
|---|---|---|---|
| P4 b = pi/4 - 0.3 | t 2-12 (t 16 DIFFERS) | -0.060 (t 16) | -0.031 |
| P4 b = pi/4 - 0.05 | all | -0.018 | +0.024 |
| P5 theta 0.4 | t 2 only | -0.061 | -0.070 |
| P5 theta 0.8 | all | -0.023 | -0.048 |
| P5 theta 1.0 | all | +0.015 | -0.010 |

BEATS: all but P5 theta 0.4 at t 4, 6. READS: all.

## Reported

- P5 theta 0.4 misses by -0.04 to -0.07 on both devices, the same size: a systematic loss (floor 0.96 on both), not
  one device's fault. The all-1 guess is hard to beat there.
- P4 light-cone site at b = pi/4 - 0.05: 0.836 / 0.749 / 0.565 / 0.392 / 0.297 against 0.897 / 0.808 / 0.641 / 0.509 /
  0.408 (fez is lower than marrakesh at t 8, 12: -0.08, -0.12).
- Floor 0.957-0.964 (marrakesh 0.957-0.972). Sentinel DEAD (fez's ring, as all day; not part of the judgements).
- Two devices, 25 minutes apart, both in a good state; the day-to-day spread is still not measured.
