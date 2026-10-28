# Device test D5, part A (2026-10-28): the formula's ring, the zipper on the same qubits, and Qiskit, on ibm_kingston

- **Declarations:** `prereg/drafts-2026-10-28/device_d5_note.md` (4d737d05…) and three amendments:
  - 1 (3b83d226…): Qiskit added;
  - 2 (9794d89c…): Qiskit on the device only, no twin;
  - 3 (f5cabe69…): only part A today, as its own job; parts B and C not run.
- **Workload:** TOQB's ring classifier, n = 20, L = 16, model 0 (as flows J and K), 64 inputs × 1000 shots per arm.
- **Fetch:** D3's, calibration 11:36:52 CET, Target 4c3a43e9….
- **Pod:**
  - The first run (TOQB 7148f53) built the rule cell. It was stopped for amendment 2.
  - `gpu/device_d5b.sh` (d760f74) built the zipper and Qiskit cells.
  - `gpu/device_d5_part.sh A` (9c99889) assembled job A. Manifest 14:07:59 CET, SHA-256 097be827…; time model 61.8 s.
- **Job:** `dbgvbb4dgr2s73csbpjg`.
  - Submitted 14:16:23 CET; ran 14:16:31 to 14:17:54.
  - Calibration at submission: 13:17:09 CET, newer than the twin's 11:36:52.
  - **55 s billed.** Dynamical decoupling and twirling off.
- **Scoring:** `lam_device score` at TOQB 9c99889 (the home checkout, 55642f1, stopped at the twin-less Qiskit cell).
  Its partial file is kept as `job_A/lam_score_partial_home.json`. The zip as received is `d5A_result.zip`, SHA-256
  bad7662c….

## Result

| arm | 2Q gates | duration | active qubits | device lam | twin lam (11:36:52) | against twin |
|---|---|---|---|---|---|---|
| fold:rule (the bare ring on the 20-cycle) | 320 | 5.6 µs | 20 | **0.943 ± 0.044** (corr 0.94) | 0.857 ± 0.010 | AGREE (0.087 ≤ 0.089) |
| fold:zipcyc (zipper, same 20 qubits) | 736 | 10.6 µs | 20 | **0.600 ± 0.044** (corr 0.87) | 0.651 ± 0.028 | AGREE (0.051 ≤ 0.088) |
| Qiskit level 2 (D3's Target) | 320 | 25.0 µs | 20 | **0.765 ± 0.099** (corr 0.70) | not simulated | – |

| comparison (device) | d | SE | d / SE | verdict | prediction |
|---|---|---|---|---|---|
| rule − zipper | +0.343 | 0.062 | 5.5 | **WIN** | WIN: held |
| rule − Qiskit | +0.178 | 0.108 | 1.6 | **TIE** | WIN: did not hold |

- **Vanity:**
  - The rule kept 1.57 times the zipper's signal on the device. The twin said 1.32.
  - The rule kept 1.23 times Qiskit's signal, with the same gate count and 4.4 times less duration.
- **Essential:**
  - Shots for a fixed precision as 1/lam²: rule 1.12, Qiskit 1.71, zipper 2.78. So the zipper needs about 2.5 times
    the rule's shots, and Qiskit about 1.5 times (Qiskit's figure is uncertain).
  - Qiskit's slope has twice the others' SE: its outputs scatter more (corr 0.70).
- **First device evidence of Paper 4's central comparison.** On the same qubits, with the same classifier and inputs,
  only the schedule changed, and the formula's ring kept clearly more than the zipper. One job, one model, one day.

## Not established

- **Whether the rule beats Qiskit on the device.** The difference was +0.18, but within 2 SE. A decisive test needs
  about 3 times the shots, or more models.
- **Why the rule came out above its twin and the zipper below.** Both are within 2 SE. The calibration also changed
  between the twin (11:36:52) and the run (13:17:09).
