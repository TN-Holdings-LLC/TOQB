# 3D prototype on a device: v3 fold against SABRE (2026-11-06, ibm_marrakesh; prereg/os3d_device_2026-11-06.md)

- One device (the night's daily-record device: queue 11:12 CET, marrakesh 0). Job dbmqhed8ft8s738vd70g, submitted
  11:15:21 CET, calibration 10:35 (at submit) / 11:06 CET (at run), 22 circuits, 4000 shots.
- Built at TOQB 579a9c3 before the submit: A at r0 1, c0 8 (fold); B SABRE seed 0; gates 83ca137c2878; answers
  SHA-256 6b2d068c... equal to the declaration. Qiskit 2.5.2, QISKIT_SABRE_ALL_THREADS unset.
- BEATS here is the code's definition (gpu/practice_score.judge): MSE below the better of "every <Z> = 0" and "every
  <Z> = 1" (the declaration's "all-1" means <Z> = 1).
- Neither arm used an endpoint of a failed coupler (the record's failed coupler 113-119 has both ends failed).
  calib_beside named no missing or non-operational element for any arm.

## Declared verdict

| t | R = MSE_A / MSE_B | verdict |
|---|---|---|
| 1 | 2.07 | **HURTS** |
| 2 | 3.17 | **HURTS** |
| 3 | 2.97 | **HURTS** |

v3 fold read the answer worse than SABRE at every depth on this device tonight.

## Per arm (beside)

| arm | READS | AGREES | BEATS | M / exact | retention | MSE / guess | CZ (layers) | floor | mirror |
|---|---|---|---|---|---|---|---|---|---|
| A t1 | READS | AGREES | BEATS | 0.653 / 0.697 | 0.937 | 0.0089 / 0.0920 | 116 (33) | 0.950 | 0.837 |
| B t1 | READS | DIFFERS | BEATS | 0.641 / 0.697 | 0.920 | 0.0043 / 0.0920 | 142 (64) | 0.975 | 0.772 |
| A t2 | READS | AGREES | BEATS | 0.428 / 0.425 | 1.007 | 0.0117 / 0.1841 | 232 (64) | 0.950 | 0.644 |
| B t2 | READS | AGREES | BEATS | 0.403 / 0.425 | 0.948 | 0.0037 / 0.1841 | 275 (106) | 0.966 | 0.538 |
| A t3 | READS | AGREES | BEATS | 0.341 / 0.321 | 1.061 | 0.0168 / 0.1241 | 348 (95) | 0.951 | 0.418 |
| B t3 | READS | AGREES | BEATS | 0.321 / 0.321 | 1.000 | 0.0057 / 0.1241 | 417 (168) | 0.979 | 0.314 |

Ring sentinel: DEAD. Calibration beside (submit = run): A worst CZ 0.052 at 48-49 (median 0.0031), worst readout
0.39 at q31; B worst CZ 0.0074-0.0082 at 106-107 / 107-108, worst readout 0.38 at q86 (not a site of B).

Both directions of the absolute criterion: A AGREES at every t while losing on MSE (the mean is right, single sites
are far off); B DIFFERS at t1 with the lower MSE.

## After the verdict (post hoc; not judged, chosen after seeing the data)

- A's error sits on two sites: the top two account for 66 / 85 / 87 % of A's MSE (B: 40 / 56 / 37 %). They are the
  sites read on q49 (floor 0.55; it carries coupler 48-49, CZ error 0.052 = 17 times A's median) and on q29. q29 and
  q49 are the two ends of bridge q38, the only bridge of block 0: the fold sends every y-bond of block 0 through
  29-38-49.
- Leaving out each arm's two worst sites: R 1.16 / 1.05 / 0.62. Leaving out q29 and q49 from A only: 1.04 / 0.53 /
  0.64. These are not verdicts.
- Reading: the fixed fold concentrates all y-bonds of a block on one bridge column, so one bad element there (flagged
  beforehand by the calibration beside) decides the comparison; SABRE spreads its errors. A's mirror is higher at
  every t (0.84 / 0.64 / 0.42 against 0.77 / 0.54 / 0.31), consistent with fewer CZ and layers. Why q29 reads too
  high (0.64 against 0.18 at t3, floor 1.0) is not known; a bridge that is not exactly |0> would turn bonds' sign,
  but this is untested.
- Next (to decide): the map-free rule that would avoid this is the next translation when a bridge column's floor
  is low; that is a calibration-free but data-dependent choice, so it needs a declaration of its own.
