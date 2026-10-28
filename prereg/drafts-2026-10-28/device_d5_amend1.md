# Device test D5, amendment 1 (owner, 2026-10-28: "実機テストには当て馬としてQUISKITもいれたら"; a short device job is outside the 10/27 no-Qiskit rule): Qiskit as a third arm in part A. Fixed by SHA-256 and CET time before D5's pod step; nothing of D5 had run

- **Added to part A:** `qiskit:2:target:template` (Qiskit 2.5.2, optimization level 2 on D3's fetched Target, its
  default seed; as flow I) on the same classifier (n = 20, L = 16, model 0, the same 64 inputs, 1000 shots). Its twin is
  computed if the compiled circuit has at most 24 active qubits (`lam_device build --twin auto`, this commit), else
  not (then only the device comparison is made).
- **Rule (added):** d = lam_rule - lam_qiskit on the device: **WIN** if d > 2 SE (hypot of the two fits' SE), **LOSS**
  if d < -2 SE, else **TIE**; Qiskit against its twin (if any): AGREE / BELOW / ABOVE within 2 SE.
- **Prediction (not a rule).** WIN against Qiskit. Basis: flow I (2026-10-24 twin) won at every n it ran (13-16, 18);
  at n = 20 Qiskit was compiled only, not simulated (it found the 20-cycle with the rule's two-qubit count but scheduled
  it over 25-30 us against 5.6 us), so the margin there is not known.
- **Job:** 7 cells x 64 = 448 circuits x 1000 shots; `assemble --max-seconds 200` (the time model gives 140.1 s).
- Everything else as device_d5_note.md (SHA-256 4d737d05…).
