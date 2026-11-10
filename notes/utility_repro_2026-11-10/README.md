# Reproducing IBM's 2023 utility experiment raw: what fits on Heron (home, 2026-11-10; no device)

Target: Kim et al., Nature 618, 500 (2023), ibm_kyiv (Eagle, 127 qubits, heavy-hex): U = [R_ZZ(theta_J) R_X(theta_h)]^t,
theta_J = -pi/2 (one CNOT per ZZ), start |0...0>, three CNOT layers per step; theta_h swept over [0, pi/2]
(the later SPD paper uses k pi/32, k = 0..16). Observables (from the Nature paper, as read on 2026-11-10):
- Fig. 2: <Z_106> at 4 steps (theta_h sweep) and the magnetization to 20 steps at theta_h = 0.
- Fig. 3: magnetization and a weight-10 observable (X 13, 29, 31; Y 9, 30; Z 8, 12, 17, 28, 32) at 5 steps
  (exact by light-cone and depth reduction in the paper); a weight-17 observable (X 37, 41, 52, 56, 57, 58, 62, 79;
  Y 75; Z 38, 40, 42, 63, 72, 80, 90, 91) at 5 steps (MPS-exact in the paper).
- Fig. 4: the weight-17 observable with Y and Z exchanged on its Y/Z sites after 5 steps and a final R_X layer;
  <Z_62> at 20 steps (exact only at theta_h = 0).
IBM's numbers were error-mitigated (ZNE); here everything would be raw.

TOQB already ran the same form on a Heron's own lattice (P5, 2026-11-03, `results/kim-lattice-2026-11-03`,
`kim-cd-2026-11-03`, `kim-e-2026-11-03`): whole lattice to t = 8 with exact answers, t = 20 recorded without one.

## Does the Eagle graph fit on Heron?

- Eagle's 127 qubits / 144 couplers embed in Heron r2's 156 / 176 in exactly two ways (mirror images)
  (rustworkx VF2, `embed.py`).
- On the 11-08 records every embedding uses failed elements on every device (fewest: fez 2, kingston 6,
  marrakesh 7). So the whole Eagle problem cannot be run as published.

## But the 5-step observables only see their light cone

All ZZ rotations commute, so after t steps an observable depends only on the gates within t hops of its support.
Cones on the Eagle graph: Z_106 at 4 steps 17 qubits; weight-10 at 5 steps 37; weight-17 at 5 steps 68; Z_62 at
20 steps all 127. With the gates on failed elements left out (outside the cone they change nothing), an observable
whose cone avoids every failed element has exactly IBM's ideal value. On the 11-08 records:

| device | embedding | failed elements (Eagle indices) | Z106 (4) | w10 (5) | w17 (5, and Fig. 4a) | Z62 (20) |
|---|---|---|---|---|---|---|
| fez | 0 | q 59; e (20, 21) | clear | clear | hit | hit |
| fez | 1 | q 48, 119; e (11, 12) | clear | hit | clear | hit |
| kingston | 0 | q 96, 97, 126; e (96, 97), (116, 117), (125, 126) | hit | clear | hit | hit |
| kingston | 1 | q 86, 87, 94, 117; 5 couplers | hit | clear | hit | hit |
| marrakesh | 0, 1 | 6 qubits, 1 coupler | hit | hit | hit | hit |

So Fig. 2's Z_106, Fig. 3's weight-10 and the weight-17 observables (Fig. 3 and 4a) are reproducible exactly on
some device-days; Z_62 at 20 steps is not (its cone is the whole device), unless a day has no failed element there.

## What a declaration would need (not written)

- A fixed rule: the device and embedding are the first (queue order, then embedding 0, 1) whose cone for the
  observable avoids every failed mark; the observable is not run on a day where none does.
- Exact answers: Z_106 (17-qubit cone) by statevector; weight-10 (37 qubits) and weight-17 (68) need the paper's
  light-cone-and-depth reduction or an exact MPS / Pauli propagation, on a pod; theta_h = 0 and pi/2 by the
  stabilizer method at any depth.
- Raw expectation: a weight-10 product loses signal roughly as the product of ten single-site retentions, so it is
  the hardest raw test; the shots needed follow from the mirrors.
