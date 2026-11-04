# P6 on ibm_marrakesh (the tutorial's device), 2026-11-04: READS but DIFFERS from step 1, further than on fez (-0.13 growing to -0.40); sentinel CLEAN; rule R HELPS

- **Declaration:** `prereg/drafts-2026-11-04/p6_marrakesh_note.md` (SHA-256 60fb7d01...0d267cef, 11:29 CET, 8ab43d1):
  P6's note with the device chosen by the owner.
- Fetch 11:30:24 CET (calibration 11:04:24 CET; failed (82, 83), (113, 119), qubits 82, 113, 119, 130); copy (0, 0)
  (the tutorial's qubits), nothing passed over; psf-os 61e9edd; 34 circuits (6c474a0); job dblgj9u74qds73dqf1s0, sent
  11:32 CET, DONE, 39 s billed. Scored by `gpu/p6_score.py` (unchanged).

## Judged

1. Sentinel **CLEAN**. 2. **READS** at theta_x 0.53, 0.3, 0.8. 3. **DIFFERS** at all three from t = 1.

| t | 1 | 3 | 5 | 7 | 9 |
|---|---|---|---|---|---|
| difference, marrakesh (0.53) | -0.131 | -0.213 | -0.275 | -0.336 | -0.398 |
| difference, fez (same job, 15 min earlier) | -0.077 | -0.135 | -0.159 | -0.210 | -0.201 |
| tutorial's unmitigated gap (marrakesh, their day) | | | 0.091 | 0.139 | 0.180 |

## Reported

- **Floor** (theta_x 0, ideal 1): 0.850, 0.797, 0.748 at t = 1, 5, 9 (fez: 0.919, 0.845, 0.798).
- **Rule R:** drops labels 29 (z0 0.11), 31 (0.09), 23 (0.38): their readout is nearly gone, and IBM marks none of
  them failed. MSE ratio 0.625, **HELPS**. 29 and 31 are the worst qubits at t = 5 at every theta_x.
- Divided by the floor, M at t = 5 is 0.652 against 0.795: the floor explains part of the miss, not most of it here.
- The ring sentinel reads CLEAN although the patch has three readout faults: the ring crosses the patch on 19 qubits
  and an echo does not test readout of the patch; the floor and the mirror are the checks that see them.
- Our difference at t = 5 is three times the tutorial's unmitigated gap on the same qubits of the same device. The
  tutorial's page does not say how its "noisy" value was obtained (readout handling, suppression, gate form); we do not
  compare beyond reporting it.
