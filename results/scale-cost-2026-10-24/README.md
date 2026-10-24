# Circuit cost against size: item 31, the zipper and Qiskit (compile only; report, no claim; 2026-10-24)

Flow A of the owner's plan of 2026-10-24 (preparation for the scale test of formula against search). One model
circuit of TOQB's ring classifier per (n, L) with random angles, compiled by each arm for the `snapshot:marrakesh`
Target; no simulation. `python -m toqb.scale_cost scale_cost.json --n 10 12 14 16 --L 16 24 32` (toqb `c6655d1` plus
`toqb/scale_cost.py`; psf-zero `1294780`, a22 / c61 front end; Qiskit 2.5.2). Cloud container, no GPU.

| n | L | item 31: CZ / us / active | zipper: CZ / us / active | Qiskit: CZ / us / active | Qiskit / zipper: CZ, duration |
|---|---|---|---|---|---|
| 10 | 16 | 448 / 18.0 / 10 | 336 / 11.7 / 10 | 506 / 48.2 / 14 | 1.51, 4.1 |
| 10 | 24 | 672 / 25.7 / 10 | 504 / 16.1 / 10 | 649 / 57.7 / 21 | 1.29, 3.6 |
| 10 | 32 | 896 / 33.3 / 10 | 672 / 20.5 / 10 | 1027 / 93.6 / 14 | 1.53, 4.6 |
| 12 | 16 | 192 / 6.1 / 12 | 192 / 6.1 / 12 | 192 / 17.2 / 12 | 1.00, 2.8 |
| 12 | 24 | 288 / 7.7 / 12 | 288 / 7.7 / 12 | 288 / 24.4 / 12 | 1.00, 3.1 |
| 12 | 32 | 384 / 9.4 / 12 | 384 / 9.4 / 12 | 384 / 31.6 / 12 | 1.00, 3.4 |
| 14 | 16 | 656 / 18.0 / 14 | 496 / 11.7 / 14 | 530 / 52.3 / 20 | 1.07, 4.5 |
| 14 | 24 | 984 / 25.7 / 14 | 744 / 16.1 / 14 | 1334 / 138.2 / 14 | 1.79, 8.6 |
| 14 | 32 | 1312 / 33.3 / 14 | 992 / 20.5 / 14 | 1135 / 105.8 / 21 | 1.14, 5.2 |
| 16 | 16 | 784 / 18.0 / 16 | 576 / 11.7 / 16 | 968 / 99.9 / 16 | 1.68, 8.6 |
| 16 | 24 | 1176 / 25.7 / 16 | 864 / 16.1 / 16 | 1511 / 157.2 / 16 | 1.75, 9.8 |
| 16 | 32 | 1568 / 33.3 / 16 | 1152 / 20.5 / 16 | 1864 / 168.6 / 23 | 1.62, 8.2 |

- n = 12: the ring embeds on the device (a 12-cycle), so all three use exactly n CZ per layer; Qiskit's circuit is
  still 2.8-3.4 times longer (cause not looked at).
- Elsewhere the zipper keeps 5n/2 - 4 CZ per layer and a duration that does not grow with n (its rounds run in
  parallel); Qiskit's duration is 3.6-4.6 times the zipper's at n = 10 and 4.5-9.8 times at n = 14-16, uses up to 23
  active qubits, and is not monotone in L (n = 14: 138 us at L 24, 106 at L 32): a search's result, not a formula's.
- For the simulation: Qiskit's 14-23 active qubits make its trajectories 2^4 to 2^7 times larger than the zipper's
  10-16 at the same n. One circuit per cell, one random model; durations are the Target's schedule.
