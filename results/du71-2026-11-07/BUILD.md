# IBM's dual-unitary chain at N = 71, raw, through the user entrance (2026-11-07 night; prereg/du71_2026-11-07.md)

- Declared at TOQB bf0e37f, pushed before the fetch (f215e49..bf0e37f). Queue read 14:34:17 CET: marrakesh 0, fez 28,
  kingston 19; `gpu/daily_fetch.py` fetched marrakesh only (at most 10 pending). No shape qualifies on marrakesh
  (failed qubits 46, 73, 82, 113, 119, 130 on every copy; `fetch/marrakesh_device.json`), so by the declared rule the
  next by the queue: ibm_kingston, fetched by `psf-os fetch` at 14:35:25 CET.
- Built from that record: S1 at copy (0, 0), chain 0 .. 86 (rows 0-4), jobs A and B, 40 circuits and 47.6 s by the
  model each, CZ up to 1715, answers 07b6d574... (S1, as sealed).

## Run

Job A dbnij8c4148s73913t50 (submitted 14:37:35 CET), job B dbnijck4148s73913t90 (14:37:52 CET), A DONE by 14:40,
B by 14:42 CET. Calibration beside in each job folder (report only; worst CZ on the chain 85-86, 0.043). Sentinels
CLEAN (both jobs). Scored with `gpu/du51_score.py` (all depths, as declared).

## Verdicts

1. READS: MSE 0.0508 against mean square exact 0.6994.
2. Decay rate k against cos 2h, over t = 4-24 (every point above 3 SE):

| h | k | SE | cos 2h | k - cos 2h | verdict |
|---|---|---|---|---|---|
| 0.05 | 0.9948 | 0.0007 | 0.9950 | -0.0002 | AGREES |
| 0.10 | 0.9799 | 0.0008 | 0.9801 | -0.0002 | AGREES |
| 0.15 | 0.9570 | 0.0012 | 0.9553 | +0.0017 | AGREES |

3. Readable depth: 24 for every h (CZ 1715).

## Beside

On-cone <X_t>, t = 4 ... 24: h 0: 0.939 0.832 0.762 0.764 0.691 0.496 (exact 1); h 0.15: 0.832 0.592 0.387 0.374 0.275
0.164 (exact 0.833 ... 0.334). Off-cone largest |<X>| 0.077-0.128. Against N = 51 on the same device this afternoon:
the rates are closer to cos 2h at N = 71 (largest |k - cos 2h| 0.0017 against 0.0045). Answers released in `answers/`.
