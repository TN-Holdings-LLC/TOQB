# 4 x 4 x 3 (48 sites) over every qualifying place on a device, with the pre-run gate (2026-11-07 daytime JST;
prereg/os3d_mid_2026-11-07.md)

- Declared at TOQB 0fbbf44, pushed before the fetch. Queue read 04:17 CET: marrakesh 1, fez 0, kingston 5.
  4 x 4 x 3 places avoiding the failed elements: marrakesh none, fez 5, kingston 5 -> ibm_fez (fewest pending).
- Built here from `ibm_fez/dev/device.json` (failed qubits 72, 148; coupler 32-33): candidates 0-4 (r0 0-4, c0 0);
  73 circuits, 84.5 s by the model, gates 0071febb7344, answers sha256 346cc34a... (k = 5, as sealed). Stabilizer check
  on this record: all places, t = 1-3, deviation 0.

## Run

Job dbn9hdoqtr0c73acjkgg, submitted 04:19:16 CET (calibration at submit 03:48:55 CET), DONE by 04:21:08 CET.
Calibration beside (report only): worst CZ 27-28 (0.106) on candidates 0-1, 102-103 (0.086) on candidates 2-4.

## Declared rule and verdicts

Gate: **no healthy place, no 3D arm judged.** Every one of the five places had |1> floor marks (0: q5, 11, 27, 63;
1: q27, 63; 2: q63, 103; 3: q63, 103, 126; 4: q103, 126); candidates 2-4 also 4 low mirror sites each. Sentinel DEAD.
2D patch (judged): READS, AGREES, BEATS at t 1-3 (M 0.699 / 0.674 / 0.572 against 0.697 / 0.673 / 0.573).

## Beside (not judged)

| 3D candidate | MSE t1 / t2 / t3 | retention | verdicts beside |
|---|---|---|---|
| 0 (r0 0) | 0.0197 / 0.0107 / 0.0191 | 0.82 / 0.82 / 0.80 | READS, BEATS; DIFFERS |
| 1 (r0 1) | 0.0181 / 0.0100 / 0.0154 | 0.83 / 0.82 / 0.81 | READS, BEATS; DIFFERS |
| 2 (r0 2) | 0.0165 / 0.0090 / 0.0168 | 0.85 / 0.84 / 0.82 | READS, BEATS; DIFFERS |
| 3 (r0 3) | 0.0208 / 0.0119 / 0.0148 | 0.84 / 0.84 / 0.84 | READS, BEATS; DIFFERS |
| 4 (r0 4) | 0.0215 / 0.0126 / 0.0157 | 0.84 / 0.86 / 0.86 | READS, BEATS; AGREES at t 3 only |

After the fact: on fez every place of 4 x 4 x 3 (four heavy-hex rows tall) holds one of q27, q63,
q103, q126; all five arms read 0.80-0.86 and none agrees at t 1-2, in line with the refusal. The draft gate2 (not
declared) would also refuse all five (costs 0.030-0.057). Answers released in `answers/`.
