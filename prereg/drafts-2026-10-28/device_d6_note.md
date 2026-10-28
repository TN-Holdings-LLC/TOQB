# Device test D6 (owner's go of 2026-10-28: "カンニングなしで…キングストン…l16のn１３－２４シュミレータなしでガチンコ rule とじっぱと quiskit", "テストは今から"): the formula's ring, the zipper and Qiskit, none of them reading a quality number, on ibm_kingston at L = 16, n = 13-24, device only. Fixed by SHA-256 and CET time before the fetch

**Why.** In D5 part A (n = 20) Qiskit (level 2 on the Target) chose another 20-cycle by the day's error rates and tied
with the rule (+0.18, 1.6 SE), while the rule read no error rate. D6 gives every arm the same information: which
elements have failed (error >= 1 or no entry, `toqb.fold`'s rule) and nothing else.

- **Arms** (all template mode):
  - `fold:rule`: the ring by formula (bare, holes or pendants by n), as Paper 4.
  - `fold:zipcyc`: the zipper on the rule's own cycle qubits. It exists only for even n (14, 16, ..., 24); at odd n
    there is no zipper cell.
  - `qiskit:2:blind:template` (this commit): Qiskit 2.5.2, preset level 2, `seed_transpiler=0`. It is given only the
    working couplers (both directions; a coupler is dropped if it or either qubit has failed) and the standard basis
    names of the Target. No error rate and no duration reach it (`task_loop.blind_device`; tests/test_lam_device_blind.py).
- **Workload.** TOQB's ring classifier, L = 16, model 0 of `toqb.lam_device` (as flows G-K and D5), its first 64
  inputs, n = 13, 14, ..., 24 (12 values); 250 shots per circuit.
- **Device.** ibm_kingston. The Target is fetched at home just before the pod step and used only for its basis, its
  working couplers and the failed-element rule. If `submit` moves the job to another device, that is reported.
- **No simulator.** No twin (`lam_device build --twin none`). The noiseless reference per input is the direct
  statevector on the GPU (`TOQB_NOISELESS=cupy`). **Check (declared):** before the build, the GPU reference equals
  Qiskit's Statevector to 1e-9 for model 0 at n = 13, L = 16, on the first 4 inputs; else the run stops.
- **Job.** One job: 30 cells (12 rule, 6 zipper, 12 Qiskit) x 64 circuits x 250 shots;
  `assemble --max-seconds 300` (the time model gives 201.7 s). Dynamical decoupling and twirling off.
- **Measure.** Per cell, z_device ~ lam z_noiseless + delta over the 64 inputs (least squares; the slope's SE from the
  residuals).
- **Rule, per n.** d = lam_rule - lam_other on the device. **WIN** if d > 2 SE (SE = hypot of the two fits' SE),
  **LOSS** if d < -2 SE, else **TIE**. Two comparisons: rule against Qiskit (12 n) and rule against zipper (6 n).
- **Prediction (not a rule).**
  - **WIN against the zipper at all 6 even n.** Flow K and D5 part A: 1.44-1.81 times on the twin and 1.57 times on
    the device at n = 20.
  - **WIN against blind Qiskit at every n where Qiskit needs more two-qubit gates.** On the 2026-10-24 Target, blind
    Qiskit needs 1.2-3.2 times the rule's gates and 2.4-15 times its duration at every n except 20 and 24, where it
    finds the cycle (equal gates, 4.6-5.4 times the duration). **At n = 20 and 24, TIE or WIN; no claim.**
- **Reported beside it.** Per cell: two-qubit gates, duration, active qubits, the qubits used and the measured qubit;
  vanity (counts, duration) and essential (lam; shots as 1/lam^2) side by side; billed seconds; the calibration at
  submission.
- **Not claimed.** One job, one model, one device, one day; 250 shots leave about 0.05-0.1 SE per slope, so
  differences below about 0.15 are TIE; Qiskit at one level and one seed; Qiskit with calibration is a different
  test (D5 part A).
