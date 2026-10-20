# P1: calibration update times and what changes between updates (2026-10-20, home, read-only)

Design C r6/r7 §5, step P1, with the owner's permission (2026-10-20). Run at home with the VPN off; no job, no QPU
time. `toqb.s2rc_device history` (12:22-12:25 CEST) and `drift` (12:30 CEST), TOQB `329f133` and `8e312b8`.

## History: 7 days, sampled every 2 h

| device | updates | gap median / min | update times (UTC) |
|---|---|---|---|
| ibm_marrakesh | 78 | 2.02 h / 0.62 h | about every odd hour, at :20-:50 (1:30, 3:30, 5:45, 7:40, 9:40, 11:20, ...) |
| ibm_fez | 76 | 2.06 h / 0.88 h | the same pattern |
| ibm_kingston | 86 | 2.00 h / 0.30 h | the same pattern |

History was served (0 failed samples). Updates closer than the 2 h sampling step can be missed, so these counts are
lower bounds.

## Drift: consecutive calibrations compared (`last_update_date` pairs, about 2.5 h apart)

| device | from -> to (CEST) | what changed |
|---|---|---|
| ibm_marrakesh | 09:41 -> 11:53 | T1 138/154 (median 21 %), T2 147/152 (29 %), readout 154/156 (47 %), sx 136/156 (19 %); cz 0/352 |
| ibm_marrakesh | 04:47 -> 09:41 | cz 2/352, **both crossing the failed rule (error >= 0.5)**; nothing else |
| ibm_fez | 08:53 -> 11:46 | **nothing** (a new timestamp with identical values) |
| ibm_fez | 07:08 -> 08:53 | readout 153/156 (median 24 %); nothing else |
| ibm_kingston | 09:41 -> 12:12 | readout 154/156 (27 %); nothing else |
| ibm_kingston | 06:50 -> 09:41 | readout 152/156 (26 %); nothing else |

Median and maximum are of |relative change| per element; the maxima reach several hundred to several thousand per
cent on single elements.

## Reading

- Design C's rule "the submission stops when the calibration timestamp differs from the fetched one" cannot be met:
  T0 to submission takes at least about 3.8 h (rehearsal and dry run of 2026-10-20), and the timestamp changes about
  every 2 h. r6/r7 §5 named this case for the owner.
- A new timestamp often changes little: readout errors only, or nothing at all. Two-qubit (cz) errors changed in one of
  the six pairs, and there two couplers crossed the failed rule. A check on failed elements at submission matters more
  than the timestamp.
