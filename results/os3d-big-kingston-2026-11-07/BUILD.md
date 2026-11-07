# 4 x 6 x 3 again, on ibm_kingston (2026-11-07 daytime JST; prereg/os3d_big_kingston_2026-11-07.md)

- Declared at TOQB 795eb08, pushed before the fetch. Queue read 04:01 CET: marrakesh 2, fez 1, kingston 0.
- Built here from `ibm_kingston/dev/device.json` (fetched 04:01:16 CET; failed qubits 112, 113, 121, 146; couplers
  112-113, 121-122, 130-131, 145-146, 146-147): one qualifying translation, candidate 0 (r0 0, c0 0); 25 circuits,
  30.9 s by the model, gates c8742871856d, answers sha256 7d874e25... (k = 1, as sealed). Stabilizer check on this
  record: t = 1-3, deviation 0.

## Run

Job dbn99soqtr0c73acj9t0, submitted 04:03:13 CET (calibration at submit 03:49:42 CET), DONE by 04:05:04 CET;
dynamical decoupling and twirling off. Calibration beside (report only): worst CZ on the candidate 86-87, 0.048;
worst readout q31, 0.057.

## Declared rule and verdicts

Gate: **no healthy place, no 3D arm judged.** Candidate 0 (mirror t1 0.814): 4 sites below the mirror line, |1> floor
marks q7, q85, q87. Sentinel CLEAN.

| t | 2D patch (judged) |
|---|---|
| 1 | READS, AGREES, BEATS (M 0.687 / 0.697) |
| 2 | READS, AGREES, BEATS (0.665 / 0.673) |
| 3 | READS, AGREES, BEATS (0.557 / 0.573) |

## Beside (not judged)

| arm | MSE t1 / t2 / t3 | retention | CZ | verdicts beside |
|---|---|---|---|---|
| 3D candidate 0 | 0.0152 / 0.0117 / 0.0124 | 0.88 / 0.89 / 0.88 | 750 / 1500 / 2250 | READS, BEATS at t 1-3; AGREES at t 3 |
| 2D patch | 0.0005 / 0.0003 / 0.0011 | 0.99 / 0.99 / 0.97 | 16 / 32 / 48 | |

After the fact (not judged): the gate's lines are relative to the job's own readings (median - 5 MAD). With one
candidate of 87 qubits the lines are drawn from that candidate alone, so its own weakest qubits fall below them; on
both 4 x 6 x 3 runs today the gate refused (fez 2 candidates, kingston 1) while the arms read 0.78-0.81 (fez) and
0.88-0.89 (kingston) retention. The rule was confirmed at 16 sites with 4 candidates; at this size it refuses by
construction more than by the device. A size-aware line is a new rule (to be declared and confirmed before use).
