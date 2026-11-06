# 3D v3.1 on a device, with the 2D patch beside (2026-11-07, ibm_fez; prereg/os3d_v31_2026-11-07.md)

- Job dbn5m0lt7fqc73aivqa0, submitted 23:55:59 CET 11-06 (07:55 JST 11-07), 61 circuits, 4000 shots; built at TOQB
  3f95d9d (gates 716c8bdeafa7; answers sha256 0bce0dab..., k = 4, as sealed); psf-os 55167cf (plus the long-standing
  local additions in circuits.py and job.py, answer helpers not on these paths); qiskit 2.5.2, aer 0.18.0.
- Candidates (fixed order): 0 (r0 1, c0 0), 1 (1, 4), 2 (3, 0), 3 (3, 4).

## Declared rule and verdicts

All four candidates had marked qubits (0: q41, q43; 1: q27; 2: q63, 77, 83, 87; 3: q69, 77, 87), so the declared
fallback applied: the ranking over all ("probe passed none"). It chose **candidate 0** (weakest reading -0.210, the X
echo; the others -0.305 / -0.438 / -0.338). (The score file's `probe_passed_none: false` is a reporting error of the
scorer for rule "best", which looked only at `chosen`; the choice itself follows the declared rule. Fixed in the
scorer after this record.)

| t | 3D (candidate 0) | 2D patch |
|---|---|---|
| 1 | READS, DIFFERS, BEATS (M 0.577 / 0.697) | READS, AGREES, BEATS (M 0.695 / 0.697) |
| 2 | READS, DIFFERS, BEATS (0.341 / 0.425) | READS, AGREES, BEATS (0.676 / 0.673) |
| 3 | READS, DIFFERS, BEATS (0.251 / 0.321) | READS, AGREES, BEATS (0.575 / 0.573) |

## Beside

| arm | MSE t1 / t2 / t3 | retention | CZ (layers t1) | mirror t1 / t2 / t3 |
|---|---|---|---|---|
| 3D candidate 0 (judged) | 0.0309 / 0.0197 / 0.0225 | 0.83 / 0.80 / 0.78 | 108 (28) | 0.71 / 0.45 / 0.24 |
| 3D candidate 1 | 0.0317 / 0.0158 / 0.0219 | 0.82 / 0.80 / 0.76 | 108 | 0.71 / 0.44 / 0.23 |
| 3D candidate 2 | 0.0089 / 0.0055 / 0.0089 | 0.91 / 0.93 / 0.99 | 108 | 0.80 / 0.54 / 0.30 |
| 3D candidate 3 | 0.0064 / 0.0022 / 0.0060 | 0.91 / 0.95 / 0.95 | 108 | 0.84 / 0.64 / 0.43 |
| 2D patch | 0.0003 / 0.0005 / 0.0008 | 1.00 / 1.01 / 1.00 | 16 | 0.96 / 0.90 / 0.80 |

Price of the dimension (judged arms): CZ 6.75 times, retention 0.83 / 0.80 / 0.78 against 1.00. With the best
candidate after the fact (3, not judged): 0.91 / 0.95 / 0.95. The 2D patch used coupler 27-28 (calibration CZ error
0.123) and still read retention 1.00. Sentinel DEAD (fez, every day since 11-04).

Calibration beside (report only), worst CZ per candidate: 0: 0.026 (26-27), 1: 0.123 (27-28), 2: 0.056 (63-64), 3:
0.0047 (69-70).

## After the verdict (post hoc; not judged)

- The probes did not track the arms. At t = 3 depth the |1> floor (means -0.62 to -0.67, ideal -1) and the X echo
  (means 0.27 to 0.34, ideal +1; the echo has twice the skeleton's CZ) are washed out on every candidate, so the
  relative line marked qubits everywhere and the ranking by the weakest reading followed the noise of the deepest probe.
  Candidates 0 and 1 (rows 1-2) had the worst arms; their probe means were as good as or better than 2 and 3.
- What did order the candidates the same way as their errors: the arms' own mirror at t = 1 (0.84 > 0.80 > 0.71 =
  0.71; the MSE order is 3 < 2 < 0 ~ 1).
- So the probe depth was wrong for a device night (the simulator replay, with uniform noise, did not wash out like
  this). A next rule to declare and test before use: probes at t = 1 depth, and the ranking by the arm's own t = 1
  mirror (a check circuit of the same placement, not an answer).
