# Post-hoc (not declared): correcting P6 with our own floor and mirror, 2026-11-04

Reference values only. The exact answers were visible while these were computed; five variants were tried
(floor global / per qubit, gate per qubit / median, with and without rule R). Nothing here is a verdict.

- **Floor** (readout of |0>): z / F_q(t), F from the job's theta_x 0 cells (t 1, 5, 9; linear in between).
- **Gate** (fez only: the OS2D mirror at theta_x 0.53, t 3, 5, same copy, 2 min later):
  G(t) = exp(a t), a from 0.5 ln(mirror_q(t) / F_q(2t)); per qubit or the median (per step 0.985 on fez).
- Rule R as declared for P6.

| fez, MSE ratio to raw | 0.53 | 0.3 | 0.8 |
|---|---|---|---|
| rule R only | 0.58 | 0.50 | 0.65 |
| floor per qubit + R | 0.15 | 0.04 | 0.32 |
| floor + gate (median) + R | 0.09 | 0.09 | 0.22 |

- fez theta_x 0.53, floor + gate (median) + R: difference at t 1, 3, 5, 7, 9 = +0.006, +0.008, +0.020, -0.000,
  +0.013 (raw -0.077 to -0.201). theta_x 0.3 over-corrects (+0.04 to +0.08): the mirror was at 0.53 only.
- marrakesh (no mirror): floor per qubit + R ratio 0.34 / 0.17 / 0.47; the gap left grows to -0.24 at t 9.
  Per-qubit floor without rule R fails there (theta_x 0.8 ratio 3.7: dividing by the dead readout of 29 and 31).
- Files: `posthoc_floor.py`, `posthoc_mirror.py` (run from the TOQB root with psf-os 61e9edd), `output.txt`.
