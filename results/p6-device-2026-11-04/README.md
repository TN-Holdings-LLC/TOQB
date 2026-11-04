# P6 on ibm_fez, 2026-11-04: the Qedma tutorial's 2D Ising problem without error mitigation: READS but DIFFERS from step 1 (-0.08, growing to -0.21); sentinel DEAD; rule R HELPS

- **Declaration:** `prereg/drafts-2026-11-04/p6_device_note.md` (SHA-256 d97af6a6...4fa5e6b3), fixed 02:44 CET, TOQB 5040056.
- **Device by queue** (11:13:55 CET): ibm_marrakesh 1, ibm_fez 0, ibm_kingston 85 -> ibm_fez. Fetch 11:14:55 CET
  (calibration 10:58:19 CET; failed (32, 33), qubit 72; no registry). Copy (0, 0), nothing passed over. Built with
  psf-os 61e9edd as declared (d229642); 34 circuits (theta_x 0.53 t 1-9, floor t 1, 5, 9, bank 0.3 and 0.8 t 1-9,
  sentinel); job dblgced8mdtc73d64e8g, sent 11:17:29 CET, DONE, 38 s billed. Scored by `gpu/p6_score.py`.

## Judged

1. **Sentinel:** DEAD (ring through the patch on 20 qubits).
2. **READS** at theta_x 0.53, 0.3, 0.8 (MSE 0.041, 0.044, 0.021 against half the answer's mean square 0.34, 0.45, 0.13).
3. **AGREES: no, DIFFERS at all three, from t = 1**:

| t | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
|---|---|---|---|---|---|---|---|---|---|
| M measured (0.53) | 0.786 | 0.741 | 0.739 | 0.688 | 0.636 | 0.604 | 0.576 | 0.563 | 0.568 |
| M exact | 0.863 | 0.842 | 0.874 | 0.836 | 0.795 | 0.792 | 0.787 | 0.775 | 0.768 |
| difference (2 SE) | -0.077 (0.003) | -0.101 | -0.135 | -0.148 | -0.159 | -0.188 | -0.210 | -0.212 | -0.201 (0.005) |

## Reported

- **Against the tutorial's unmitigated values** (marrakesh, gate implementation unknown): |difference| at t = 5, 7, 9:
  ours 0.159, 0.210, 0.201 against theirs 0.091, 0.139, 0.180. On this day's fez we are further from the answer.
- **Answer card:** every difference is 47-98 SE: bias, not chance. The floor (theta_x 0, ideal 1) is 0.919, 0.845,
  0.798 at t = 1, 5, 9: the device loses Z even when no gate rotates it. Divided by the floor, M at t = 5 is 0.753
  (exact 0.795) and at t = 9 about 0.71 (0.768): the floor explains most of the miss (reported, not a verdict).
- **Rule R (sub-analysis fixed in advance):** line 0.666; drops labels 27 (z0 0.30) and 28 (0.37) (physical 27, 28):
  MSE ratio 0.579, **HELPS**. The two are the worst qubits at t = 5 at every theta_x.
- Bank cells: theta_x 0.3 misses by -0.087 to -0.206, theta_x 0.8 by -0.063 to -0.147, the same pattern.
- **The queue rule chose the device with the empty queue, which on this day had a low floor.** Recorded as a
  observation about the rule (an empty queue does not mean a good device), not as a reason to read a map.
