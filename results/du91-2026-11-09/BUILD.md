# Dual-unitary chain at N = 91 on a device (prereg/du91_2026-11-09.md)

- Declared at TOQB fd88a28 (pushed with 514b98e before the fetch). Queue read 11:59 CET 2026-11-09: marrakesh 0,
  fez 218, kingston 157 -> ibm_marrakesh. Record: failed qubits 46, 73, 82, 113, 119, 130; coupler 113-119.
- No shape qualifies; rule C places the chain: start (+1, row 0, column 0), 1665 steps, first start, suspect on.
- Jobs A (h 0, 0.05) and B (h 0.1, 0.15): 40 circuits each, 47.6 s by the model each, CZ up to 2205; answers
  e90f825e... equal the sealed index table (441c9c1a...) written on the chain's labels.
- Pre-run check on this build: the compiled h = 0 circuits of job A by the stabilizer method at full size: |<X>| = 1.000
  on the light-cone site at t = 4-24, the site the sealed answers name.

## Run

Jobs dbopknc4148s739tdie0 (A) and dbopkps4148s739tdii0 (B), submitted 12:03 CET, DONE by 12:05 CET. Sentinels: A DEAD,
B CLEAN. Scored by `gpu/du51_score.py` (scores.json). Answers released in `answers/` (the run's and the index table).

| | N = 51 (11-07, kingston) | N = 71 (11-07, kingston) | **N = 91 (11-09, marrakesh, rule C)** | cos 2h |
|---|---|---|---|---|
| k, h = 0.05 | 0.9950 (0.0006) | 0.9948 (0.0007) | **0.9956 (0.0006)** | 0.9950 |
| k, h = 0.10 | 0.9821 (0.0008) | 0.9799 (0.0008) | **0.9821 (0.0008)** | 0.9801 |
| k, h = 0.15 | 0.9598 (0.0011) | 0.9570 (0.0012) | **0.9590 (0.0011)** | 0.9553 |
| verdicts | AGREES x 3 | AGREES x 3 | **AGREES x 3** | |
| READS (MSE / mean square) | 0.0403 / 0.699 | 0.0508 / 0.699 | **0.0393 / 0.699** | |
| readable depth | 24 | 24 | **24 (every h)** | |
| most CZ | 1225 | 1715 | **2205** | |

The largest distance to cos 2h at N = 91 is 0.0037 (h = 0.15), inside the declared tolerance max(2 SE, 0.005). The h = 0
ruler falls from 0.895 (t = 4) to 0.651 (t = 24). Off the cone the mean |<X>| is 0.043, but two labels read large
values at every point: 85 (mean |<X>| 0.59) and 83 (0.45), chain indices 65 and 63, next to failed qubits 82 and 73;
they are off every judged light-cone site (indices 4-24) and are reported as they are.
