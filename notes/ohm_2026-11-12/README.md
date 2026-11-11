# Where Ohm's law appears: (a) a start that gives diffusion, (b) the device count (workplace, 2026-11-12; desk only)

Handover 11-11 item 0, continuing `notes/ohm_2026-11-11` (home: from a pure domain wall the brickwork is ballistic at
phi = 0, about t^(2/3) at the isotropic point, and frozen in the easy-axis regime; plain diffusion t^(1/2) never
appears). Not declared, no device. Script: `ohm_lr.py` (statevector, numpy); outputs in the `*.txt` beside it.

## (a) The start that gives diffusion: a weakly polarised wall

Start from a mixed wall rho = prod_y (1 + m s_y Z_y)/2 (left half leans to |1>, right half to |0>, polarisation m).
For small m the transferred magnetisation is exactly M(t) = m C(t) with C(t) = Tr(Z_L U^dag Z_R U) / 2^N (only total-Z
conservation is used), an infinite-temperature quantity. C(t) is computed by typicality from Haar-random states;
check: at phi = 0 it equals the free-fermion value sum_{x in R, y in L} |W_xy|^2 within the typicality error (N 20:
4.5e-3, two random states; N 14: 5e-2).

theta = pi/4, growth exponent d ln C / d ln t over doubled times (cycles; 1 cycle = 2 gate layers):

| phi (phi / 2 theta) | N 20: 2-4 / 4-8 / 8-16 | N 24: 2-4 / 4-8 / 8-16 | reading |
|---|---|---|---|
| 0 (0) | 1.004 / 1.002 / 0.946 (exact: C = t/2 until the edge) | exact 1.00 to t 16 | ballistic, no resistance |
| pi/4 (0.5) | 0.92 / 0.885 / 0.887 | | easy-plane: near ballistic |
| pi/2 (1, isotropic) | 0.76 / 0.737 / 0.626 | 0.767 / 0.734 / 0.702 | superdiffusive, towards 2/3 |
| 3pi/4 (1.5) | 0.631 / 0.57 / 0.512 | 0.636 / 0.57 / 0.565 | easy-axis: towards 1/2 |
| pi (2) | 0.585 / 0.592 / 0.507 | 0.588 / 0.59 / 0.566 | easy-axis: towards 1/2 (diffusion, Ohm) |

- So the Ohmic case is there: a weakly polarised wall in the easy-axis regime (phi > 2 theta), where the pure wall
  froze. The exponent falls slowly (0.59 at t 4-8, 0.57 at 8-16 for N 24); N 20 at 8-16 is already bent by the edges
  (compare N 24), so the late values need N >= 24.
- Breaking integrability with a staggered field h (after each cycle, keeps total Z) pulls the easy-plane point
  (phi = pi/4) down from 0.88 towards diffusion: 4-8 exponent 0.88 / 0.73 / 0.71 / 0.66 for h 0 / 0.5 / 1.0 / 1.5 (N 20;
  `field_N20.txt`). Slower than the easy-axis route; not needed for the question.
- How small must m be (`finite_N16.txt`: random product states, 400 per point, N 16, exact per state, which is what a
  device would run): at m 0.3 M/m follows C(t) within the sampling error (easy-axis and isotropic); at m 0.6 the
  easy-axis M/m is smaller (t 8: 1.23 against 1.68: the start of the freezing); m 1 is the pure wall (frozen; isotropic
  equals home's N 40 values to t 8). So m about 0.3 is in the linear (Ohmic) regime.

## (b) On the device

- CZ per fSim(pi/4, phi) (qiskit, CZ basis, optimisation 3): 2 at phi = 0; 3 at pi/4, pi/2, 3pi/4 and pi. On a line
  (no routing) one cycle is 2 gate layers: 4 CZ layers at phi = 0, 6 otherwise; N 40: 78 / 117 CZ per cycle.
- Tonight's limit (Hubbard 11-11: read at 48 CZ layers, not at 72): about 12 cycles at phi = 0 and 8 cycles for the
  others. At 8 cycles the exponents from t 4 to 8 are 1.00 / 0.73 / 0.59 (ballistic / isotropic / easy-axis): the three
  separate, but the easy-axis value is not yet 1/2. A device result should be compared with the exact M(t) (sealed),
  not read as an exponent.
- Exact answers at device size: every sample is a product state, so its M(t) is computable exactly per circuit by MPS
  at 40 qubits and 8 cycles (8 gates cross each cut, so the bond is at most 4^8 = 2^16; the Hubbard check at a similar
  depth needed 1722; the cost here is not measured), and at phi = 0 by free fermions at any size (<n_x> = sum over occupied y of |W_xy|^2,
  `gpu/ff_xx.py`). The declared answer is the average over the declared samples, not the linear-response C(t).
- Signal and noise (estimate): N 40, m 0.3, easy-axis, t 8: M = 0.3 x 1.7, about 0.5. Spread between states about 0.5
  per state at N 16 (larger at N 40) and shot spread about 2.2 per shot of the right half (20 qubits); 100 states x 100
  shots per time point give about +-0.06 at N 16's state spread. Circuits: one per state and time point (t 2, 4, 8: 300 circuits).
- Noise as flow: mixing raises M towards m N / 4 (3.0 at N 40, m 0.3), six times the signal; decay towards |0> also
  shifts M. Mirrored walls (left leaning to |0> in a twin set) reverse the decay's sign and cancel it in the mean; the
  mixing does not cancel. The phi = 0 arm (exact at any size) belongs in the same job, but the Hubbard ruler (11-11)
  did not track its partner, so it is a check beside, not a correction.

## Open (for home and the owner)

- Whether to declare: N 40, theta pi/4, phi 0 / pi/2 / pi, m 0.3, mirrored twin, t 2 / 4 / 8, 100 states each; the
  verdict as READS / AGREES against the sealed exact M(t) per arm, and the ordering of the three arms.
- Longer exact runs (N 28-32 linear response, or MPS of the mixed wall) to see the easy-axis exponent reach 1/2: heavy
  for the workplace (N 24 took 3.5 min per phi and cycle-16 run); VS if wanted.
