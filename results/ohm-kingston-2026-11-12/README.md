# Ohm 6 cycles repeated on ibm_kingston, raw, 2026-11-12 (prereg/ohm_repeat_2026-11-12.md)

- Declaration 0483903 pushed 12:04:17 CET (reflog "update by push"); queue read 12:06:20 CET (marrakesh 0, fez 2,
  kingston 2). marrakesh first: the ring sentinel did not land on the user's ring (not buildable); fez excluded by the
  declaration -> ibm_kingston.
- Build: 508 circuits, 158.4 s by the model; CZ 234 / 468 (A0) and 351 / 702 (A1, A2), A1 and A2 equal in CZ and depth.
  circuits_sha256 771c3b0e... equal to the try-build whose pre-run check passed (`ibm_kingston/check_trybuild.txt`:
  168 circuits ALL PASS, worst 7.3e-8, 2197 s) -> the PASS carries over.
- Answers: the released fez file (5580b676...), by chain label 126e99ba... (as on fez).
- Job dbqqeh8k09pc73atn36g, submitted 12:47:02 CET, DONE; job files returned byte-identical; DD and twirling off.
- `job/circuits.qpy.gz` and `runs/*.qpy.gz` are gzipped (`gunzip` restores them byte for byte).

## Declared verdicts (`gpu/ohm_score.py`), with ibm_fez (same circuits, results/ohm-2026-11-12) beside

| arm | cycles | kingston: MSE of M / mean square | kingston | fez: MSE / mean square | fez |
|---|---|---|---|---|---|
| A0 free | 3 | 0.52 / 0.77 | DOES NOT READ | 1.80 / 0.77 | DOES NOT READ |
| A0 free | 6 | 0.98 / 2.61 | **READS** | 4.10 / 2.61 | DOES NOT READ |
| A1 isotropic | 3 | 0.76 / 0.52 | DOES NOT READ | 2.16 / 0.52 | DOES NOT READ |
| A1 isotropic | 6 | 1.63 / 1.19 | DOES NOT READ | 4.91 / 1.19 | DOES NOT READ |
| A2 + field | 3 | 0.73 / 0.40 | DOES NOT READ | 2.34 / 0.40 | DOES NOT READ |
| A2 + field | 6 | 1.53 / 0.67 | DOES NOT READ | 4.86 / 0.67 | DOES NOT READ |

AGREES (0.2 quanta): 0-2 of 28 everywhere. Per-qubit <Z>: READS in 28 / 28 circuits of every arm and cycle count.

## Prediction (written before the data)

- "No arm READS M at 3 or 6 cycles": **failed** (A0 at 6 cycles READS; the other five do not).
- "Every circuit's per-qubit <Z> READS": held.
- "The W exponents keep the exact ordering A0 > A1 > A2": held (0.737 / 0.608 / 0.510; exact 0.972 / 0.659 / 0.451;
  fez 0.758 / 0.625 / 0.519).
- "|p(A1) - p(A2)| <= 0.05 at each cycle count": held (0.004 and 0.018).

## Beside (not judged, never used to correct)

- Mixed share p = (W_device - W_exact) / (5.5 - W_exact): kingston 0.14 / 0.16 / 0.16 at 3 cycles and 0.22 / 0.26 /
  0.24 at 6 (A0 / A1 / A2); fez 0.26 / 0.28 / 0.28 and 0.46 / 0.45 / 0.43. Kingston moved W about half as far
  towards the mixed value; the exponents still sit near fez's (A2 again above its exact value, A1 slightly below).
- A0 at 6 cycles reads because its exact M is the largest (mean square 2.61) and its p the smallest; the arms with
  interaction carry smaller exact M.
- Drift D: -0.02 to -0.15. Floor 0.980-0.982; mirror 0.75 / 0.54 (A0), 0.66 / 0.39 (A1), 0.67 / 0.41 (A2) at 3 / 6
  cycles (fez 0.67 / 0.44, 0.57 / 0.29, 0.58 / 0.31). Sentinel CLEAN.

## Reproduce

`python reproduce.py ohm-kingston-2026-11-12`.
