# 3D v3.1 at 4 x 6 x 3 (72 sites, 87 qubits) on a device with the pre-run gate (2026-11-07 daytime JST;
prereg/os3d_big_2026-11-07.md)

- Declared at TOQB 5de612d, pushed before the fetch (6f83d5e..5de612d). Queue read 03:44:14 CET: pending marrakesh 1,
  fez 1, kingston 6. 4 x 6 x 3 translations avoiding every failed element: marrakesh none, fez (0, 0) and (1, 0),
  kingston (0, 0) -> ibm_fez (fewest pending among those that qualify; tie with marrakesh, which does not qualify).
- Built here from `ibm_fez/dev/device.json` (failed qubits 72, 148; coupler 32-33): 37 circuits, 44.3 s by the model,
  gates 6d4a92075415, answers sha256 bd39df03... (k = 2, as sealed). Candidates 0 (r0 0, c0 0), 1 (r0 1, c0 0).
  CZ per arm 750 / 1500 / 2250 (layers 35 / 70 / 104). psf-os 55167cf (plus the long-standing local additions).

## Run

Job dbn9500ou4as73b434q0, submitted 03:52:46 CET (calibration at submit 03:20:32 CET), DONE by 03:54:28 CET;
dynamical decoupling and twirling off. Calibration beside: `ibm_fez/run/CALIB_BESIDE_*.json` (report only; worst CZ
on both candidates 27-28, 0.106; worst readout q83, 0.124). Scored with the declared rule "gate".

The draft scorer returned at a refusal without scoring the 2D arm, which the declaration judges in that case; fixed
before this record (reporting only: the choice, the lines and the verdicts are computed as declared).

## Declared rule and verdicts

Gate: **no healthy place, no 3D arm judged.** Candidate 1 (mirror t1 0.730) and candidate 0 (0.716): each had 6 sites
below the job's mirror line and |1> floor marks (0: q3, 5, 11, 27, 63, 103; 1: q27, 63, 103, 126). The two
translations overlap (rows 0-4 and 1-5) and share q27, q63, q103. Sentinel DEAD (fez, every day since 11-04).

| t | 2D patch (judged) |
|---|---|
| 1 | READS, AGREES, BEATS (M 0.696 / 0.697) |
| 2 | READS, AGREES, BEATS (0.669 / 0.673) |
| 3 | READS, AGREES, BEATS (0.573 / 0.573) |

## Beside (not judged)

| arm | MSE t1 / t2 / t3 | retention | CZ | verdicts beside |
|---|---|---|---|---|
| 3D candidate 0 | 0.0236 / 0.0137 / 0.0183 | 0.81 / 0.81 / 0.78 | 750 / 1500 / 2250 | READS, DIFFERS, BEATS at t 1-3 |
| 3D candidate 1 | 0.0261 / 0.0139 / 0.0169 | 0.81 / 0.80 / 0.78 | 750 / 1500 / 2250 | READS, DIFFERS, BEATS at t 1-3 |
| 2D patch | 0.0004 / 0.0007 / 0.0014 | 1.00 / 0.99 / 1.00 | 16 / 32 / 48 | |

After the fact (not judged): at 72 sites and up to 2250 CZ both 3D arms read and beat the trivial guess at every t,
and the retention barely falls with depth (0.81 to 0.78); neither agrees. The 4 x 2 x 2 arm the gate judged on
marrakesh today read 0.92 / 0.96 / 1.01. Answers released in `answers/` (answers sha256 bd39df03..., light-cone file
f261370d..., as sealed).
