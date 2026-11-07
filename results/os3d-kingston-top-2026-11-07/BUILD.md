# ibm_kingston, rule "top" (stop removed): 4 x 4 x 3 and 4 x 6 x 3 from one record (2026-11-07 daytime JST;
prereg/os3d_mid_kingston_top_2026-11-07.md, prereg/os3d_big_kingston_top_2026-11-07.md)

- Pushes: b55f4a7 (4 x 4 x 3, rule top), then abb4ef1 (adds 4 x 6 x 3). A fetch `fetch2/` (04:30 CET) came after
  b55f4a7 but before abb4ef1 and is not used; a fetch at 04:28 CET came before b55f4a7 and is not used either.
  Used: `fetch3/` (queue read 04:32:58 CET: marrakesh 2, fez 0, kingston 1; kingston fetched 04:33:13 CET).
- Record: failed qubits 112, 113, 121, 146; couplers 112-113, 121-122, 130-131, 145-146, 146-147.
- 4 x 4 x 3 (`mid_4x4x3/`): candidates 0-4 (r0 0 c0 0, r0 0 c0 4, r0 1 c0 0, r0 1 c0 4, r0 2 c0 0); 73 circuits,
  84.5 s by the model, gates 6d4cfde9c210, answers 346cc34a... (k = 5, as sealed).
- 4 x 6 x 3 (`big_4x6x3/`): candidate 0 (r0 0, c0 0); 25 circuits, 30.9 s, gates c8742871856d (the same circuits as
  the 04:03 CET kingston job: same record of failures), answers 7d874e25... (k = 1, as sealed).
- Stabilizer check on this record: every place of both sizes, t = 1-3, deviation 0.

## Runs

4 x 4 x 3 job dbn9p2s4148s7390ik2g and 4 x 6 x 3 job dbn9p6oqtr0c73ack3f0, submitted one after the other
(04:35-04:36 CET), both DONE by 04:38 CET. Calibration beside in each folder (report only). Sentinel CLEAN on both.
Scored with the declared rule "top".

## 4 x 4 x 3: judged candidate 1 (r0 0, c0 4; own t1 mirror 0.859, the highest), flag "weak elements"

| t | 3D (candidate 1) | 2D patch |
|---|---|---|
| 1 | READS, DIFFERS, BEATS (M 0.642 / 0.697) | READS, AGREES, BEATS (0.680 / 0.697) |
| 2 | READS, AGREES, BEATS (0.416 / 0.440) | READS, AGREES, BEATS (0.658 / 0.673) |
| 3 | READS, AGREES, BEATS (0.295 / 0.312) | READS, AGREES, BEATS (0.551 / 0.573) |

Beside: retention of the five places (t1 / t2 / t3) and MSE sum: 1 (judged) 0.92 / 0.95 / 0.95, 0.0144; 0 0.91 / 0.91 /
0.91, 0.0177; 3 0.88 / 0.88 / 0.88, 0.0384; 2 0.87 / 0.87 / 0.86, 0.0411; 4 0.87 / 0.86 / 0.85, 0.0503. The judged place
has the smallest error of the five. The gate's flag on it: |1> floor marks q7, q53 (no low mirror site); the declared
gate alone would have refused it, and every other place too.

## 4 x 6 x 3: judged candidate 0 (the only place), flag "weak elements"

| t | 3D (candidate 0) | 2D patch |
|---|---|---|
| 1 | READS, DIFFERS, BEATS (M 0.611 / 0.697) | READS, AGREES, BEATS (0.687 / 0.697) |
| 2 | READS, DIFFERS, BEATS (0.393 / 0.445) | READS, AGREES, BEATS (0.656 / 0.673) |
| 3 | READS, AGREES, BEATS (0.272 / 0.316) | READS, AGREES, BEATS (0.557 / 0.573) |

Retention 0.88 / 0.88 / 0.86 (the same circuits at 04:03 CET, not judged then: 0.88 / 0.89 / 0.88).
