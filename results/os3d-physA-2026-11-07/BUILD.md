# 3D physics part A on a device (2026-11-07 evening JST; prereg/os3d_physA_2026-11-07.md)

- Declared at TOQB f616b93, pushed before the fetch (f02b902..87f2333). Queue read 12:03:19 CET: marrakesh 4, fez 0,
  kingston 0. 4 x 4 x 3 places: marrakesh none, fez 5, kingston 5 -> ibm_fez (fewest pending, tie order before
  kingston). Record: failed qubits 72, 148; coupler 32-33.
- Job 1 `j1_4x4x3/`: 5 places (r0 0-4, c0 0), 181 circuits, 205.0 s by the model, gates 66ff2143268c, answers
  60d9745f... (k = 5, as sealed).
- Job 2 `j2_4x2x2/`: 4 places ((1, 0), (1, 4), (3, 0), (3, 4)), 286 circuits, 322.2 s, gates a03e481ad438, answers
  cb619cee... (k = 4, as sealed).
- Stabilizer check on this record (theta = pi/2): both sizes, every place, t = 1-3, deviation 0.

## Runs

Job 1 dbngdb0ou4as73b4icfg, job 2 dbngdlgqtr0c73ad2ab0, submitted 12:08-12:09 CET, both DONE by 12:20 CET.
Calibration beside in each job folder (report only). Sentinels DEAD (fez, as every day since 11-04).
Scored with the declared rule "top": `j1_4x4x3/scores.json`, `j2_4x2x2/scores.json`.

## Job 1, 4 x 4 x 3: judged candidate 1 (r0 1; own t1 mirror the highest), flag "weak elements"

| theta | t | 3D M / exact | retention | 3D verdict | 2D verdict (retention) |
|---|---|---|---|---|---|
| 0.4 | 1 / 2 / 3 | 0.729/0.921, 0.638/0.811, 0.534/0.729 | 0.79 / 0.79 / 0.73 | READS, DIFFERS (BEATS at t3 only) | READS AGREES BEATS (0.99 / 0.99 / 0.99) |
| 0.6 | 1 / 2 / 3 | 0.659/0.825, 0.503/0.628, 0.393/0.512 | 0.80 / 0.80 / 0.77 | READS, DIFFERS (BEATS at t2, t3) | READS AGREES BEATS (1.00 / 0.99 / 0.99) |
| 0.8 | 1 / 2 / 3 | 0.556/0.697, 0.367/0.440, 0.255/0.312 | 0.80 / 0.83 / 0.82 | READS, DIFFERS, BEATS | READS AGREES BEATS (1.00 / 1.00 / 1.01) |

Bulk (4 sites) against surface (44), mean <Z> measured / exact, beside:

| theta | t | bulk | surface | bulk - surface, measured / exact |
|---|---|---|---|---|
| 0.4 | 2 | 0.682 / 0.941 | 0.634 / 0.799 | +0.048 / +0.142 |
| 0.4 | 3 | 0.586 / 0.856 | 0.530 / 0.718 | +0.056 / +0.138 |
| 0.6 | 2 | 0.554 / 0.782 | 0.498 / 0.614 | +0.056 / +0.168 |
| 0.6 | 3 | 0.425 / 0.623 | 0.390 / 0.502 | +0.035 / +0.121 |
| 0.8 | 2 | 0.402 / 0.544 | 0.364 / 0.430 | +0.038 / +0.114 |
| 0.8 | 3 | 0.262 / 0.358 | 0.255 / 0.308 | +0.007 / +0.050 |

At t = 1 bulk and surface share the exact value (cos theta). From t = 2 on the exact bulk magnetization stays above the
surface; the measured bulk is above the surface at every (theta, t >= 2), at about a third of the exact gap.

## Job 2, 4 x 2 x 2: judged candidate 3 (r0 3, c0 4), flag "healthy"

| theta | retention t = 1 ... 6 | verdicts |
|---|---|---|
| 0.4 | 0.90 0.88 0.86 0.86 0.86 0.83 | READS at every t; DIFFERS; BEATS from t = 2 |
| 0.6 | 0.90 0.90 0.88 0.85 0.78 0.66 | READS; DIFFERS; BEATS |
| 0.8 | 0.90 0.92 0.93 0.76 0.63 0.55 | READS; AGREES at t = 2, 3; BEATS |

2D patch: READS, AGREES, BEATS at every theta and t = 1-6 (retention 0.97-1.01).
"DOES NOT BEAT" at small theta and t = 1 (3D): there every site has the same exact value, so the trivial guess is
already exact. Answers released in `answers/` (as sealed).
