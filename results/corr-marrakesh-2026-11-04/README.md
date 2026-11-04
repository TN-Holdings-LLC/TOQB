# Correction test on ibm_marrakesh, 2026-11-04: HELPS at all three theta_x, but AGREES only at 0.8; at 0.53 and 0.3 a gap of -0.13 to -0.15 is left at t 9

- **Declaration:** `prereg/drafts-2026-11-04/correction_marrakesh_note.md` (SHA-256 3946456b...f86f1d391, 11:55 CET,
  a56933f), otherwise `correction_note.md`. Fetch 11:56:28 CET (calibration 11:40:29); copy (0, 0); 44 circuits
  (b5cdc0f); job dblgv8pkbkrc73cnn6qg, sent 11:57:39 CET, DONE. Scored by `gpu/corr_score.py` (unchanged).

## Judged

| theta_x | gate / step | MSE ratio | verdict | corrected diff t 1..9 | AGREES |
|---|---|---|---|---|---|
| 0.53 | 0.983 | 0.189 | HELPS | +0.011 ... -0.150 (t 9) | DIFFERS (t 5: -0.060) |
| 0.3 | 0.995 | 0.105 | HELPS | +0.003 ... -0.130 (t 9) | DIFFERS (t 6: -0.056) |
| 0.8 | 0.952 | 0.161 | HELPS | +0.039 ... -0.023 | AGREES |

Raw t 9: -0.360 / -0.341 / -0.204 (fez an hour earlier: -0.197 / -0.189 / -0.114).

## Reported

- marrakesh minus fez: gate decay per step -0.0006 / -0.0005 / -0.0049 (the mirrors see almost the same gate loss);
  MSE ratio 0.189 vs 0.082, 0.105 vs 0.018, 0.161 vs 0.403.
- So the forward signal on marrakesh loses far more than its mirror shows. A mirror cancels coherent errors
  (e.g. static ZZ, over-rotation) that the forward circuit keeps; this is a hypothesis, not tested here.
- 0.8 AGREES most likely because two errors cancel (the mirror model over-corrects at 0.8, as on fez, and the
  loss the mirror misses pulls the other way); it is not evidence that the correction works at 0.8.
- Rule R dropped 23, 31, 48, 49 (this morning 23, 29, 31): readout faults moved within 30 minutes to an hour.
- Floor 0.872 (t 1) to 0.768 (t 10). Sentinel CLEAN.
