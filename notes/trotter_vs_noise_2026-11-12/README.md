# Task C: Trotter error beside the device's error, 1D Hubbard U 4 (home, 2026-11-12; owner 10:49 JST)

The sealed answers of the 11-11 Hubbard runs are the values of the circuit as built (dt 0.25, first-order Trotter),
so the device verdicts carry no Trotter error. Here the two errors are set side by side.

- Device error = MSE of the device's per-qubit <Z> against the circuit's exact value (results/hubbard-2026-11-11,
  L 20, U 4).
- Trotter error = MSE of the circuit's exact value against the continuum (`trotter.py`, `coarse.py`: the same circuit
  at dt/2, dt/4, dt/8; continuum by Richardson from dt/4 and dt/8; quimb MPS, bond below the cap). Computed at L 8
  and 12; the two sizes agree within 25 %, so the per-site Trotter error is taken as size-independent here (L 20 not
  computed).

| J t | device steps (dt 0.25) | CZ layers | device error (L 20) | Trotter error dt 0.25 (L 8 / 12) | Trotter error dt 0.5 (L 8 / 12) | mean square of the answer |
|---|---|---|---|---|---|---|
| 0.5 | 2 | 24 | 0.0094 | 7.7e-4 (L 8) | - | 0.18 |
| 1.0 | 4 | 48 | 0.0080 | 9.5e-4 / 7.4e-4 | 2.6e-3 / 1.8e-3 (2 steps) | 0.046 (circuit), 0.06-0.08 (continuum, L 8-12) |
| 1.5 | 6 | 72 | 0.0141 | 2.4e-3 / 1.9e-3 | 1.5e-2 / 1.3e-2 (3 steps) | 0.022 (circuit), 0.04-0.05 (continuum) |

Reading (within these records only):
- At dt 0.25 the device's error is 5-12 times the Trotter error at every time. Smaller dt (more steps) would only add
  device error; the Trotter error is not what limits the reading today.
- Halving the depth (dt 0.5) raises the Trotter error 2.5 times at J t 1 (still 3-4 times below the device error at
  4 steps), but 6 times at J t 1.5, where it reaches about 30 % of the signal's mean square: J t 1.5 is not rescued
  by coarser steps.
- So the balance point lies between dt 0.25 and 0.5 at J t 1; the device's error at a fixed time and fewer steps was
  not measured (each time ran with one dt). A direct test: J t 1 with 2 steps (dt 0.5) and 4 steps (dt 0.25) in one
  job, both judged against the continuum value.
- Not used: the U = 0 ruler as a per-step noise gauge (11-11: it did not decay like U = 4 beyond 2 steps).
