# Declared: the light cone of one flipped spin in a 3D Heisenberg lattice (4 x 2 x 2), raw
(owner 2026-11-08 21:25 JST "進めて", on the proposal to measure how information spreads in the 3D lattice; for the
next run when the queues allow)

Declared before any device record of this run is fetched. A change after this commit is a new declared file.

## Problem

16 sites (x, y, z) in 4 x 2 x 2, the XXX bond U = exp(-i 0.05 (XX + YY + ZZ)) on every lattice edge, in the bond order
of the line layout with rule A (`gpu/heis3d.py` physical_line; `prereg/os3d_heisE_2026-11-08.md`), t = 1-6 steps.
Start: every spin up (|0>) except the one at site (1, 0, 0), flipped. XXX conserves the number of flipped spins, so
the exact state stays one excitation spread over the lattice; the all-up state itself is an eigenstate (exact <Z> = +1
everywhere). Exact probability of the excitation at Manhattan distance d from the source, t = 1-6 (sums over sites):

| t | d0 | d1 | d2 | d3 | d4 |
|---|---|---|---|---|---|
| 1 | 0.961 | 0.038 | 0.001 | 0.000 | 0.000 |
| 2 | 0.854 | 0.138 | 0.007 | 0.000 | 0.000 |
| 3 | 0.696 | 0.266 | 0.036 | 0.002 | 0.000 |
| 4 | 0.523 | 0.379 | 0.089 | 0.008 | 0.000 |
| 5 | 0.353 | 0.440 | 0.180 | 0.026 | 0.001 |
| 6 | 0.218 | 0.438 | 0.279 | 0.063 | 0.002 |

(4, 6, 4, 1 sites at d = 1, 2, 3, 4.) A step of 0.05 is kept on purpose: at 0.25 one step already carries the
excitation three sites along the layout's bond order, which is the circuit's order, not a speed.

## Job

`gpu/lc3d_build.py DEV OUT ANS --dt 0.05 --ts 1,2,3,4,5,6 --source 1,0,0 --k 4`: every line translation that fits, in
its fixed order, up to 4 candidates; at each, the flip arm and the no-flip arm (the background noise makes) at
t = 1-6, each with its floor and mirror; one ring sentinel; 4000 shots. On the 11-07 fez record: 148 circuits, 168.2 s
by the model; CZ 116 / 212 / 308 / 404 / 500 / 596 (t = 1-6, odd rows). Code at the declaring commit.

## Device

Of ibm_marrakesh, ibm_fez, ibm_kingston (`gpu/daily_fetch.py`), the fewest pending jobs (ties: that order) among
those where at least one line translation fits. None: "not run".

## Choice and verdicts (`gpu/lc3d_score.py OUT ANS`)

- Place: rule "top" over the mean of the candidate's two t = 1 mirrors (flip and no flip).
- Occupation n_i = (1 - <Z_i>) / 2; P(d, t) its sum over distance d in the flip arm, B(d, t) the same in the no-flip
  arm; S = P - B; SE from the cards' per-site SE, sites taken as independent.
- Per judged t and d <= 3: AGREES if |S - P_ex| <= 0.05; ARRIVED if S >= 0.03 and S > 3 SE.
- Front, d = 1, 2, 3: exact arrival t1, t3, t6 (first t with P_ex >= 0.03); measured arrival the first t with
  ARRIVED; FRONT AGREES if equal (both "none" counts as equal), else FRONT DIFFERS.
- Reported as numbers: the excitation kept K(t) = sum_d S(d, t) (exact 1), the background total sum_d B(d, t) (exact 0),
  and the shape TVD(t) = 1/2 sum_d |S / K - P_ex|.
- Every candidate beside; the sentinel as recorded.

## Simulator estimate (reference only, not a verdict)

SIMULATOR_ESTIMATE

## Answers (sealed now)

Exact <Z> per site for the flip and no-flip arms of every translation the line layout can choose (18 on a fault-free
Heron r2), t = 1-6: table sha256 e5540df21fc3945fdf3c370c11fc6f66d3247ba2bb29263f8986b7107b8116e6. The builder's
answers must equal the table's entries for its candidates (checked after the build); the table is committed after
the verdicts.

## Pre-run checks

Placed against exact with the flip, t = 1, 2 (18 qubits, full statevector): to 1.2e-15. The whole try-built job
(11-07 fez record) run noiselessly: every front arrival as exact (t1, t3, t6) at all four places; K = 1.000, background 0.

## Limits

16 sites, one excitation (its exact answer is a 16 x 16 problem, classically trivial: the test measures the device,
not a hard problem); one device, one run; no advantage claimed.
