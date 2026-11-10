# A second ruler exact at any size: the Trotterised XX chain (home, 2026-11-10; prototype, not declared)

Owner's direction (2026-11-10): the OS's central applications are quantum dynamics (spin models, lattice gauge); more
problems whose exact answer is known at any size, after the dual-unitary chain (N = 91).

`gpu/ff_xx.py`: Neel start, brickwork of G(theta) = exp(-i theta (XX + YY) / 2) on even then odd bonds. Every G is a
matchgate, so the Trotter circuit itself maps the Jordan-Wigner fermions linearly: <Z_i> exact at any N from an
N x N matrix (free fermions). G costs 2 CZ (Qiskit's XXPlusYYGate(2 theta) decomposed into cz / rz / sx / x).

Check (`python gpu/ff_xx.py check`): the gate against the matrix 4e-15; <Z_i> against Qiskit's statevector for
N 4-14, 1-6 steps, theta 0.2 and 0.6: worst 3.8e-14.

What it adds to the dual-unitary ruler: not Clifford at any angle, and the imbalance I = (1/N) sum (-1)^i <Z_i>
changes sign with the steps (Bessel-like), so noise, which pulls it to 0, cannot imitate it.

Exact imbalance at N = 91 (CZ 180 per step):

| theta | 1 | 2 | 3 | 4 | 6 | 8 | 10 | 12 | 16 |
|---|---|---|---|---|---|---|---|---|---|
| 0.15 | +0.914 | +0.677 | +0.351 | +0.018 | -0.374 | -0.231 | +0.153 | +0.301 | -0.190 |
| 0.25 | +0.773 | +0.247 | -0.223 | -0.359 | +0.172 | +0.201 | -0.209 | +0.067 | -0.138 |
| 0.40 | +0.490 | -0.235 | -0.155 | +0.306 | -0.124 | +0.246 | -0.094 | +0.218 | +0.199 |

12 steps at N = 91 are 2,160 CZ, about the dual-unitary chain's readable depth on marrakesh (t 24, 2,205 CZ).
Next, before any declaration: placement on a chain (shape or rule C, as du91), a light-cone noiseless check of the
compiled circuit (the cone of a site after 12 steps is at most 26 qubits), the owner's choice of theta and steps.

## Correction and the Clifford ruler (home, later on 2026-11-10)

- **Correction:** the cone of a site grows by two sites per step on each side (two layers per step), so after 12
  steps it is up to 49 qubits, not 26 as written above; a statevector check of the cone reaches about 6 steps.
- **The ruler:** at theta = pi/2, G is iSWAP-dagger (Clifford) and every <Z_i> is exactly +-1 at every step (the
  Neel pattern moves deterministically), the analogue of the dual-unitary h = 0 ruler. `gpu/ff_xx.py` writes it in
  a Clifford-only form (Sdg Sdg, H, CX, CX, H; two CZ), checked against the matrix and the statevector.

## Try-build on the fez record of 11-08 (`gpu/ffxx_build.py`; not a run)

- Rule C places 91 sites (as du91); CZ exactly 180 per step (720 / 1,440 / 2,160 at 4 / 8 / 12 steps); one job of 22
  circuits, 27.6 s by the model (thetas pi/2 and 0.25, steps 4, 8, 12).
- theta = pi/2, compiled for the device, at full size on Aer's stabilizer method (200 shots): all 91 bits equal the
  exact +-1 in every shot at 4, 8 and 12 steps.
- theta = 0.25, 4 steps, compiled: every one of the 91 sites by its backward light cone (at most 16 qubits) on a
  statevector: worst |z - exact| 6.7e-15.
- Open for the owner before any declaration: thetas, steps, the device; the answers would be sealed by chain index.
