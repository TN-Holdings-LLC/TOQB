# Schwinger model on link qubits (VS Claude, 2026-11-10; not declared, no device)

Follows `notes/schwinger_scale_2026-11-10`. The circuit is `gpu/schwinger_link.py` (new file; gpu/schwinger.py is
unchanged) and its tests are in `tests/test_schwinger_link.py` (12 tests, made-up parameters). Full outputs are in
`out/`.

## The circuit

The gauge field is kept, with one qubit per link: the smallest truncation, with eps0 = 0. The links take the values
L in {0, -1} on odd links and {0, +1} on even links, which are the values a pair takes from the bare vacuum.

**Layout and interactions.** Sites and links alternate on one chain of 2N - 1 qubits, and every interaction is
between neighbours.
- The mass and the electric energy are one-qubit RZ gates (J L^2 = J (1 - Z_l) / 2).
- The hop s+_n R_n s-_{n+1} + h.c. is a three-body term on (site, link, site). It is written by formula with 8 CX,
  all between neighbours:
  - two CX from the link qubit, so that the two coupled basis states differ only on the link;
  - a doubly controlled RY as a Gray-code multiplexer (4 CX, 4 RY), conjugated by S;
  - the two CX again.

**Trotter order** (first order, dt 0.25): the diagonal layer, then the hops on odd links, then the hops on even links.

**Gauss's law.** Each hop commutes with Gauss's law. Inside Gauss's law the truncated model is the gauge-eliminated
H projected onto the configurations whose fields stay inside the kept values (P H P). The tests check this against
gpu/schwinger.hamiltonian.

## CZ per Trotter step (`out/cz_table.txt`)

| N | qubits | CZ per step | CZ per qubit | swap network: CZ per step | swap network: CZ per qubit |
|---|---|---|---|---|---|
| 6 | 11 | 40 | 3.64 | 45 | 8 |
| 8 | 15 | 56 | 3.73 | 84 | 10 |
| 10 | 19 | 72 | 3.79 | 135 | 14 |
| 12 | 23 | 88 | 3.83 | 198 | 16 |
| 14 | 27 | 104 | 3.85 | 273 | 20 |
| 16 | 31 | 120 | 3.87 | 360 | 22 |

The swap network's column is counted per site qubit. Its 3(N - 1) per qubit counts each gate on both of its qubits.

The link circuit needs 8(N - 1) CZ per step, which is 8(N - 1) / (2N - 1) per qubit. That number is below 4 for
every N and does not grow with N.

## The circuit itself (`out/circuit.txt`)

Two independent calculations were compared:
- the circuit's statevector (Aer above 20 qubits);
- the same Trotter product computed on the kept configurations only, as exp(-i dt P H_g P) for each group.

They match for N 6, 8 and 10 (M1-M3, 1, 2 and 4 steps) and for N 12 and 14 (M1, 1 and 2 steps; 23 and 27 qubits).
The largest difference is 7.8e-15. Gauss's law holds to 5e-16 (max over n of <G_n^2>).

## Truncation against Trotter error (`out/errors.txt`, `out/physics.txt`; N 6 and 8, M1-M3, t 0.25-2)

| N 8, M2 | t 0.5 | t 0.75 | t 1.0 | t 1.25 | t 2.0 |
|---|---|---|---|---|---|
| truncation, max abs(dZ) / abs(d nu) | 0.007 / 0.002 | 0.048 / 0.016 | 0.145 / 0.046 | 0.229 / 0.066 | 0.334 / 0.105 |
| link Trotter, max abs(dZ) / abs(d nu) | 0.027 / 0.002 | 0.071 / 0.002 | 0.131 / 0.016 | 0.182 / 0.035 | 0.128 / 0.044 |
| swap-network Trotter (for comparison) | 0.014 / 0.001 | 0.024 / 0.006 | 0.026 / 0.006 | 0.029 / 0.005 | 0.022 / 0.001 |

Meaning of the rows:
- **truncation:** the truncated exact answer, exp(-i P H P t), minus the full exact answer (gpu/schwinger.z_continuous);
- **link Trotter:** the link circuit minus the truncated exact answer;
- **swap-network Trotter:** gpu/schwinger's circuit minus the full exact answer.

## The truncation changes the physics, so the work stops here

- **No pair separates.** From the bare vacuum only neighbouring pairs are reachable: 13 configurations at N 6 and
  34 at N 8, against 20 and 70 in the full model. A pair cannot separate, because a field string longer than one
  link is outside {0, -1} / {0, +1}.
- **M1 and M3 become the same model.** Every reachable configuration has twice as many particles as non-zero links,
  so the diagonal energy per pair is J + 2m. That is 2 for M1 (J 1, m 0.5) and 2 for M3 (J 2, m 0). The truncated
  M1 and M3 agree to 6e-15, while in the full model they differ by up to 0.09 in <Z>. Martinez's comparison of J at
  m = 0 (M2 against M3) is still two different models after truncation, but M1 and M3 cannot be told apart.
- **The error is large where pair creation happens.** Up to t 0.5 the truncation error in nu is at most 0.002. From
  t 1 on it is 0.02-0.1, against a full-model nu of 0.13-0.63.
- **The link circuit's Trotter error is larger.** At dt 0.25 it is 2 to 7 times that of the swap network (up to 0.2
  in <Z>). The odd and even hops are split from each other and from the field.

As instructed, the work stops at the smallest truncation. Possible next steps (not done):
- two qubits per link, L in {-1, 0, +1} on every link, which allows a separated pair (3N - 2 qubits, N 8 = 22);
- a second-order Trotter step, or a smaller dt for the hop layers.
