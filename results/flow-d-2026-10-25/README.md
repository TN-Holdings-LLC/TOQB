# Flow D, 2026-10-25: how much signal the hole schedule keeps, against the zipper and Qiskit (report only, no rule)

Declared in prereg/drafts-2026-10-25/fold_lam_note.md (SHA-256 06e80a2d…, `76ea393`) and amendment 1
(fold_lam_amend1.md, `3c89ed4`: Qiskit's limit 20 active qubits instead of 24, since 24 would have taken more than a
day). H100 pod, `snapshot:marrakesh`, toqb `76ea393`, psf-zero `fab3602` (a25, psfbind r3); 12:35-14:59 CET.
fold_lam.zip SHA-256 782b57497bb2db9e255dbb37d1a725b654c0e668eead0d0e0eebdd31acb64900.

`toqb.fold_lam`: per (n, L) one random model of TOQB's ring classifier and 24 random inputs, the same for every arm;
<Z> of clbit 0 with 256 trajectories on the twin ("sim") and the stand-in ("dev"); z ~ lam z_noiseless + delta.
Files: `L8.jsonl` (the first run: L = 8, n = 9-13 every arm, n = 14 fold and zipper), `L8b.jsonl` (after the amendment:
L = 8, n = 14-19; n = 14's fold and zipper lines are equal to L8.jsonl's, checked), `L16.jsonl`, the logs, `times.txt`.

**lam, twin / stand-in** (holes: m - n, the spare qubits of the hole schedule's cycle; skip: Qiskit's circuit had more
than 20 active qubits)

| n | holes | L = 8: fold | zipper | Qiskit | L = 16: fold | zipper | Qiskit |
|---|---|---|---|---|---|---|---|
| 9 | 3 | 0.64 / 0.66 | 0.38 / 0.36 | 0.52 / 0.53 | 0.26 / 0.26 | 0.11 / 0.15 | 0.32 / 0.26 |
| 10 | 2 | 0.71 / 0.75 | 0.41 / 0.40 | 0.66 / 0.55 | 0.51 / 0.50 | 0.10 / 0.11 | 0.10 / 0.05 |
| 11 | 1 | 0.82 / 0.81 | 0.38 / 0.38 | 0.41 / 0.38 | 0.70 / 0.71 | 0.15 / 0.10 | 0.08 / 0.02 |
| 13 | 7 | 0.60 / 0.57 | 0.58 / 0.58 | 0.32 / 0.30 | 0.12 / 0.07 | 0.27 / 0.25 | 0.26 / 0.06 |
| 14 | 6 | 0.73 / 0.72 | 0.52 / 0.52 | skip (24) | 0.11 / 0.19 | 0.19 / 0.17 | 0.40 / 0.25 |
| 15 | 5 | 0.68 / 0.66 | 0.71 / 0.73 | 0.75 / 0.72 | 0.26 / 0.32 | 0.30 / 0.31 | skip (24) |
| 16 | 4 | 0.72 / 0.70 | 0.54 / 0.55 | skip (23) | 0.40 / 0.43 | 0.33 / 0.33 | 0.10 / 0.12 |
| 17 | 3 | 0.85 / 0.86 | 0.65 / 0.65 | skip (25) | 0.49 / 0.47 | 0.21 / 0.21 | skip (24) |
| 18 | 2 | 0.81 / 0.82 | 0.61 / 0.58 | 0.25 / 0.27 | 0.56 / 0.51 | 0.30 / 0.34 | skip (22) |
| 19 | 1 | 0.89 / 0.89 | 0.65 / 0.62 | skip (23) | 0.65 / 0.61 | 0.26 / 0.31 | skip (32) |

**Two-qubit gates and duration (us), fold / zipper / Qiskit:** L = 8: 104-218 / 152-352 / 144-503; 4.9-6.4 / 7.2 /
15.9-49.3. L = 16: 208-434 / 304-704 / 297-968; 6.9-10.1 / 11.7 / 29.9-99.9 (per cell in the jsonl files).

**Read (no rule, nothing chosen from it).**

- **Vanity:** the hole schedule has the fewest two-qubit gates and the shortest duration in every cell.
- **What a device user needs (on TOQB's models, not a device):** with 1-4 holes (n = 9-11, 16-19) the hole schedule
  keeps the most signal in every cell but one (n = 9, L = 16: Qiskit 0.32 / 0.26 against 0.26 / 0.26): 1.3-2.2 times
  the zipper's at L = 8 and 1.2-7 times at L = 16 (n = 10, 11: 4.7-7). With 6-7 holes (n = 13, 14) it keeps the least
  at L = 16 (0.07-0.19); with 5 (n = 15) the arms are close. So the number of holes decides, and it is known from n by formula: the hole
  schedule for a cycle a few qubits longer than the ring, the zipper otherwise. Why many holes hurt is not checked
  (one reading: a hole not exactly |0> carries its error along each move, and 6-7 holes move every layer).
- Qiskit varies most with n (L = 16: 0.40 at n = 14, 0.02-0.12 at n = 10, 11, 16) and could be run only where its
  circuit had at most 20 active qubits.
- At L = 16 lam is small (often 0.1-0.3): with 24 inputs and 256 trajectories a difference of 0.1 there is within
  the estimate's spread. One random model per cell; one seed.

**Not claimed.** No device; the twin and the stand-in are TOQB's models of a 2026-10-13 calibration; the hole
schedule's and Qiskit's single-qubit runs are not merged, the zipper's are.
