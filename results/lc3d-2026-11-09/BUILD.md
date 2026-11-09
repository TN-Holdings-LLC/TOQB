# Light cone on a device (prereg/lc3d_2026-11-09.md)

- Declared at TOQB 01ed41b, pushed before the fetch (12:35 CET 2026-11-09). Queue: marrakesh 11, fez 215,
  kingston 151 -> ibm_marrakesh. Record: as results/du91-2026-11-09 (failed 46, 73, 82, 113, 119, 130; coupler
  113-119).
- Job: candidates (1, 8), (3, 4), (5, 0) (odd rows, line 116-596 CZ) and (0, 0) (even row, 128-668); 148 circuits,
  168.2 s by the model; answers 1b8398af... equal the sealed table (e5540df2...).

## Run

Job dboq53gou4as73csglog, submitted 12:37 CET, queued, DONE by 14:51 CET. Sentinel DEAD. Scored by
`gpu/lc3d_score.py` (`ibm_marrakesh/scores.json`). Answers released in `answers/`.

Judged candidate 0 (r0 1, c0 8; mean t1 mirror 0.730). S = P(flip) - B(no flip) / exact, per distance:

| t | CZ | d0 | d1 | d2 | d3 | K (exact 1) | background (exact 0) | TVD of the shape |
|---|---|---|---|---|---|---|---|---|
| 1 | 116 | 0.736 / 0.961 | 0.037 / 0.038 | -0.010 / 0.001 | -0.008 / 0.000 | 0.76 | 2.32 | 0.025 |
| 2 | 212 | 0.550 / 0.854 | 0.079 / 0.138 | 0.041 / 0.007 | -0.020 / 0.000 | 0.65 | 2.15 | 0.056 |
| 3 | 308 | 0.411 / 0.696 | 0.191 / 0.266 | 0.025 / 0.036 | -0.004 / 0.002 | 0.61 | 2.88 | 0.049 |
| 4 | 404 | 0.269 / 0.523 | 0.223 / 0.379 | 0.064 / 0.089 | 0.012 / 0.008 | 0.57 | 3.10 | 0.053 |
| 5 | 500 | 0.176 / 0.353 | 0.237 / 0.440 | 0.034 / 0.180 | -0.005 / 0.026 | 0.44 | 3.62 | 0.144 |
| 6 | 596 | 0.100 / 0.218 | 0.228 / 0.438 | 0.103 / 0.279 | 0.004 / 0.063 | 0.43 | 3.88 | 0.102 |

Front (declared verdicts): d = 1 exact t1, measured t2 (FRONT DIFFERS; at t1 S = 0.037 against 0.038, not beyond
3 SE); d = 2 exact t3, measured t6 (FRONT DIFFERS); d = 3 exact t6, none (FRONT DIFFERS). The recorded prediction
(FRONT AGREES at d = 1 at most; d = 2, 3 DIFFERS) held at d = 2 and 3. The noise made 2.1 to 3.9 flipped spins (more than
the simulator's 1.1 to 3.7) and the excitation kept fell from 0.76 to 0.43.

Reported beside (declared as a number, not a verdict): the shape of the kept excitation over distance, S / K against
the exact distribution, has TVD 0.025-0.056 at t = 1-4 and 0.10-0.14 at t = 5, 6 at the judged place: the spread is
reproduced in shape while its amplitude shrinks; the declared arrival thresholds (S >= 0.03 and > 3 SE) are not met
in time because of the shrinking. S itself subtracts the no-flip arm's background, as declared.

Beside: candidate 1 TVD 0.03-0.14 to t = 5, 0.54 at t = 6; candidates 2 and 3 (floor or mirror lower) 0.15-0.61.
