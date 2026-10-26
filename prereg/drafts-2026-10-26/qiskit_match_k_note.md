# Flow I, test match 4 (owner's go of 2026-10-26 evening, "一晩覚悟でPODで"): Qiskit against the count rule and the zipper on the twin of ibm_kingston's 2026-10-24 calibration. Fixed by SHA-256 and CET time before the run

**Why.** Paper 4 (10.5281/zenodo.23665575) compares the count rule with the zipper only; a direct comparison with
Qiskit's own search was asked for. Flow D had Qiskit on the marrakesh snapshot at n = 9-19 (one model, cells above 20
active qubits skipped); here Qiskit runs on the twin that matched the device, with the four models of flow G, and with
room for 24 active qubits.

- **Device.** `file:<target.pkl>`, the Target of flow C and flow G (ibm_kingston, calibration 2026-10-24 15:26:59
  CEST), SHA-256 3b93913856d2f0b9bf97ac03f89c43457157735413b02d8722c82d31065b218d; the run stops if the file differs.
  Twin ("sim") only.
- **Arms.** `qiskit:2:target:template` (Qiskit 2.5.2, optimization level 2 on the Target, as in flow C, flow D and
  Paper 3); `fold:rule`; `psfai:template_zip` (PSF-Zero a25's zipper). L = 16, P = 24, T = 256, models 0-3 (seeds as
  in flow G), `--max-active 24`: a circuit with more than 24 active qubits is recorded as skipped ("exits").
- **Reuse of flow G.** `fold:rule` and the zipper at n = 13-18 are flow G's rows (results/flow-g-2026-10-26), not run
  again. **Check (declared):** the run first repeats both arms at n = 13, model 0; if either lam, q2 or us differs from
  flow G's row, the run stops and nothing is reused.
- **Order** (each part its own file; parts already finished are kept if the pod is stopped):
  1. Qiskit at n = 13, 14, 16, 18 (20, 20, 16, 22 active qubits by a compile on this Target);
  2. Qiskit at n = 15, 17 (24 active qubits each; the heaviest part; with it the match at n = 13-18 is complete);
  3. all three arms at n = 20 and 22 (Qiskit at n = 22 has 28 active qubits: it exits);
  4. all three arms at n = 24 (Qiskit 24 active qubits: it finds the 24-cycle, 384 two-qubit gates as the rule, over
     29.6 us against 5.6 us).
  Expected time on one H100, from flows D and G (about 140 s per cell at 20 active qubits, doubling per qubit; not
  measured above 20), plus the noiseless reference, which `fold_lam` computes on the CPU (Qiskit `Statevector`; 10 s
  per input at n = 20 and 114 s at n = 22 on a 2-core container): part 1 about 2 h, part 2 about 9 h, part 3 about 5 h,
  part 4 a day or more. Parts 3 and 4 will likely not finish in one night; the owner stops the pod when he decides.
  An n whose part did not finish with all four models is reported as not run; no verdict is drawn from part of an n.
- **Rule, per n** (as flow G). A model is a win for arm A over arm B if A's lam is larger on the twin, a loss if
  smaller. **WIN**: 3 or 4 wins of 4; **LOSS**: 3 or 4 losses; else **TIE**. Main verdicts: `fold:rule` against
  Qiskit at every n where both ran. Also given with the same rule: the zipper against Qiskit (every n where both ran)
  and `fold:rule` against the zipper (n = 20, 22, 24). A cell that errors counts as neither.
- **Prediction (not a rule).** `fold:rule` WIN against Qiskit at every n where both ran: on this Target Qiskit's circuits
  have 2.0-3.0 times the two-qubit gates and 5-10 times the duration at n = 13-18 (compile only, 2026-10-26). At n = 20 and 24,
  where Qiskit finds the device cycle itself (as many two-qubit gates as the rule) but schedules it over 25-30 us
  against 5.6 us, a WIN too, with a smaller margin. No prediction for the zipper against Qiskit.
- **Reported only.** Per n the four models' lam for each arm, counts, duration, active qubits; vanity (counts, duration)
  and essential (lam; shots as 1/lam^2) side by side; the time per cell.
- **Not claimed.** No device; one day's calibration of one device; random models; Qiskit at one optimization level and
  its default seed; Qiskit's circuits above 24 active qubits are not simulated, so where Qiskit exits nothing is said
  about its signal.
