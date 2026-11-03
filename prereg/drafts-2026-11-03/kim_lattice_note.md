# P5 stage B: the kicked Ising model on ibm_kingston's whole lattice (the form of IBM's 2023 utility experiment), t <= 5, exact answers, no error mitigation (home, 2026-11-03)

**Why.** P4 (1D chain) read exact answers up to N = 33, t = 16. The next step is 2D: the device's own heavy-hex
lattice, in the form of IBM's 2023 utility experiment (Kim et al., Nature 618, 500; 127 qubits, error mitigation by
zero-noise extrapolation). Stage B is the part with exact answers for every qubit; the depths without them come later,
each in its own note.

**The problem** (`psf_os/kim.py`, psf-os 7faa7ab). The lattice: every working coupler of the fetched device record between working
qubits, with the registry's masked couplers removed, its largest connected part. |0...0> in; each step RZZ(-pi/2) on
every lattice edge (one CZ each, 3 colour layers), then RX(theta) on every lattice qubit; Z readout of every lattice
qubit. theta = 0, 0.4, 0.8, 1.0, pi/2; t = 0..5 (CZ: t x edges, 815 at t = 5 on the dry run's lattice).

**Answers** (`gpu/kim_lattice.py`, CPU, computed from the same fetch right after the job is built and before it is
sent; SHA-256 recorded in `build.json` and in the commit that records the build): theta = 0: 1 everywhere;
theta = pi/2: Clifford, stabilizer simulation of the whole lattice (0 everywhere for t >= 1); other theta: each qubit's
causal cone (the ball of radius t - 1 and the edges inside it; at most 19 qubits at t = 5), statevector. Checked in
tests/test_kim.py on a 14-qubit heavy-hex piece: cone = whole lattice (1e-10, t <= 4), the radius t - 2 is wrong (the
argument is tight), stabilizer = statevector at pi/2. Dry run (fetch of 03:22 CET): the compiled circuit at
theta 0.8, t = 2 on a noiseless MPS simulator gives M = 0.641 against 0.639 exact.

Exact magnetisation M (mean of <Z_q>) on the dry run's lattice (151 qubits, 163 edges):

| theta | t = 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|
| 0.4 | 0.921 | 0.928 | 0.901 | 0.948 | 0.903 |
| 0.8 | 0.697 | 0.639 | 0.532 | 0.526 | 0.464 |
| 1.0 | 0.540 | 0.419 | 0.299 | 0.254 | 0.196 |

**The job** (`gpu/kim_lattice.py`): one job, the lattice after the registry's mask (`results/coverage-days-2026-11-02-day3/list_after.json`;
no new scan), 5 records x 6 circuits, then the sentinel (echo D = 24 on the n = 40 ring), 4000 shots, options off,
"stay", `psf-os submit`; 41 s by the time model. Dry run: accepted (every CZ count = t x edges, every lattice qubit
measured). No standard job: the mask removes one coupler of 164 ((85, 86)); the OS-against-standard comparison was
made in 1D.

## Judged (theta = 0.4, 0.8, 1.0)

1. **Sentinel:** CLEAN expected; otherwise reported with its sites.
2. **Raw, every qubit:** over all lattice qubits and t = 1..5, the mean squared error of <Z_q> against the answer,
   against the answer's mean square: READS if at most half of it, else DOES NOT READ.
3. **Magnetisation, raw:** AGREES if |M_measured - M_exact| <= 0.05 at every t = 1..5, else DIFFERS.
4. **Magnetisation, normalised:** each <Z_q> divided by the same qubit's measured <Z_q> at theta = 0 and the same t;
   AGREES if within 0.05 of M_exact at every t, else DIFFERS. (theta = 0 keeps every qubit in |0>: it sees readout
   and bit-flip errors, not dephasing, so this is a partial correction; reported as such.)
   - READS and AGREES (raw) at all three theta: *psf-os reads the utility-form circuit on the whole lattice without
     error mitigation, to depth 5.*
   - READS and AGREES only normalised: *the answer is read up to the readout and bit-flip part of the noise.*

## Reported, not judged

M at theta = 0 (decay from 1) and at pi/2 (exact 0: any bias); per-qubit errors at t = 5 and the five worst qubits;
billed time.

**Stop.** One run of the job. Stage C (t = 6-8: exact answers for some qubits only, pod) and stage D (t = 20, no exact
answer) need their own notes.
