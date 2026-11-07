# IBM's dual-unitary chain at N = 51, raw, through the user entrance (2026-11-07; prereg/du51_2026-11-07.md)

- Declared at TOQB 0855899, pushed before the fetch (a253ef9..0855899). Queue read 11:14:43 CET: marrakesh 0, fez 1,
  kingston 0. Shapes: marrakesh none qualifies (not used), kingston S1 at copy (0, 0) -> ibm_kingston (pending 0;
  marrakesh, first in the tie order, does not qualify).
- Built here from `ibm_kingston/dev/device.json` (failed qubits 112, 113, 121, 146; couplers 112-113, 121-122,
  130-131, 145-146, 146-147): chain on rows 0-3 (qubits 0..75), jobs A (h 0, 0.05) and B (h 0.1, 0.15), 40 circuits
  and 47.6 s by the model each, CZ up to 1225 (t = 24), answers sha256 0db4c7eb... (S1, as sealed).

## Run

Job A dbnfljdt7fqc73ajisig (submitted 11:17:47 CET), job B dbnflnk4148s7390vi20 (11:18:04 CET), both DONE by
11:20:51 CET; dynamical decoupling and twirling off. Calibration beside in each job folder (report only; worst CZ on
the chain 10-11, 0.010; worst readout q53, 0.051). Sentinels CLEAN (both jobs). Scored with `gpu/du51_score.py`
(all depths, as declared).

## Verdicts (section 4)

1. READS: MSE 0.0403 against mean square exact 0.6994 (half: 0.350).
2. Decay rate k against cos 2h, over t = 4-24 (every point above 3 SE):

| h | k | SE | cos 2h | k - cos 2h | verdict |
|---|---|---|---|---|---|
| 0.05 | 0.9950 | 0.0006 | 0.9950 | +0.0000 | AGREES |
| 0.10 | 0.9821 | 0.0008 | 0.9801 | +0.0020 | AGREES |
| 0.15 | 0.9598 | 0.0011 | 0.9553 | +0.0045 | AGREES (tolerance 0.005) |

3. Readable depth: 24 for every h (the deepest point asked; CZ 1225).

## Beside

On-cone <X_t>, t = 4 / 8 / 12 / 16 / 20 / 24 (exact in brackets):
- h 0: 0.921 0.819 0.764 0.785 0.670 0.632 (1)
- h 0.05: 0.912 0.825 0.745 0.724 0.573 0.522 (0.980 ... 0.887)
- h 0.10: 0.898 0.734 0.613 0.568 0.448 0.378 (0.923 ... 0.617)
- h 0.15: 0.820 0.606 0.452 0.397 0.267 0.220 (0.833 ... 0.334)
Off-cone largest |<X>| per point 0.050-0.107. Raw, no mitigation: the h = 0 column is the device's own loss
(0.92 at t = 4 to 0.63 at t = 24); the rate is read as the ratio to it, as declared. The h = 0.15 rate sits 0.0045 above
cos 2h, inside the 0.005 tolerance. Answers released in `answers/` (sha256 0db4c7eb..., as sealed).
