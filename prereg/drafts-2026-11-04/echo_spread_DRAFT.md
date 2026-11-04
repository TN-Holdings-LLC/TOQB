# DRAFT (not declared): how far a local kick spreads on the 2D patch, measured with the OS's own mirror (workplace, 2026-11-04)

Status: a draft for home and the owner. No builder yet (the pieces exist: `ising2d`, `lattice2d`, `mirror2d`). Counts
below are of the patch's geometry only.

**Prior work, stated first.** Inserting a local operator between U and U^dagger and reading where the signal changes is
the out-of-time-order correlator (OTOC) measurement; Google ran it on superconducting devices (2021, and the 2025
"Quantum Echoes" work). What is new here is not the observable but the setting: the patch is placed without the
calibration map (`lattice2d.place`), and the circuit is the same mirror the OS already uses as a sentinel, so the
measurement doubles as a check of the OS's own instrument.

## The circuits (one job, on the P6 copy chosen by P6's rules)

For t = 1..T (T fixed below), with U = the P6 circuit of t steps (RX 0.53, RZ 0.1, RZZ 1.0 as 2 CZ):

| cell | circuit | ideal <Z_q> |
|---|---|---|
| echo | U, barrier, X on the centre qubit c, barrier, U^dagger | F_q(t) = <0| X_c(t) Z_q X_c(t) |0> with X_c(t) = U^dagger X_c U (an OTOC); 1 outside the kicked region, below 1 inside |
| no-kick control | U, barrier, U^dagger (the mirror sentinel) | 1 everywhere |
| floor | U with every non-diagonal single-qubit gate removed | 1 everywhere |

**Why the no-kick control is in the same job** (home's point): without it, a drop caused by noise cannot be told from a
drop caused by the kick's spread. The quantity read is the kick's own effect, per qubit:
D_q(t) = (no-kick <Z_q>) - (echo <Z_q>), against the exact 1 - F_q(t).

c = qubit 26 of the tutorial's labels (the patch's centre: smallest eccentricity, 7 hops to the farthest qubit).
Acceptance: the echo and the control each have exactly twice U's CZ count (barriers at both joins).

## Exact answers: how far they reach (counted first, as asked)

X_c(t) lives in the ball of radius t around c (each step adds at most one hop: a ZZ turns X into Y and puts only Z on the
neighbour, which commutes with the step's other ZZ layers). Gates outside that ball cancel between U and U^dagger, so
F_q(t) for every q is a statevector of the ball of radius t + 1 around c:

| t | ball(c, t): where F_q can differ from 1 | region simulated: ball(c, t + 1) |
|---|---|---|
| 1 | 3 | 7 |
| 2 | 7 | 11 |
| 3 | 11 | 19 |
| 4 | 19 | 27 |
| 5 | 27 | 33 |
| 6 | 33 | 35 (the whole patch) |
| 7 | 35 (the whole patch) | 35 |

So t <= 3 runs on a laptop (19 qubits), t = 4 on a CPU at 27 qubits, t = 5 at 33 qubits on the pod (about 69 GB in single precision, as P6's t = 6..9),
t = 6, 7 is the whole patch (35 qubits: 2^35 amplitudes, about 0.27 TB in single precision and 0.55 TB in double,
beyond one GPU; another method or a reduced region would be needed, so nothing is promised there). Proposed: T = 5 (all answers on CPU and pod), with t = 6, 7 as reported cells only if the pod
can answer them before the run.

## Judged (proposed)

1. **Sentinel and acceptance:** the ring sentinel CLEAN expected; echo and control CZ counts exact.
2. **The kick spreads (Q1):** the radius R(t) of the kicked region, defined as the largest hop distance from c at which
   the mean D_q over that shell exceeds 3 x its shot-noise SE, grows with t (R(t+1) >= R(t) for every t <= T, and
   R(T) > R(1)).
3. **At the right speed (Q2):** on the shells where the exact 1 - F_q(t) is at least 0.05, the measured shell means D
   agree with the exact ones within 0.05 (the P5/P6 line) at every t <= T; reported with 2 SE (the answer card).

## Reported, not judged

The per-qubit maps of D_q(t) and 1 - F_q(t) (the "contour map" of the spread, drawn on the lattice, not interpolated);
the no-kick control per qubit (the mirror sentinel's flags); the floor; the device chosen and the copy.

## Cost

T = 5: 5 echo + 5 control + 2 floor (t = 1, 5) + 4 sentinel = 16 circuits, about 21 s by the time model at 4000 shots.
