# Flow J (owner's go of 2026-10-27): how much signal the count rule keeps at n = 20 and 22 on the kingston day twin, rule only. Fixed by SHA-256 and CET time before the run

From the draft rule_lam_big_draft.md (`f0d8963`) with the owner's choices of 2026-10-27: n = 20 and 22 only (n = 24
later, if at all); the noiseless reference stays on the CPU (no change to `fold_lam`); the prediction below is written.

**Why.** The count rule's lam is known up to n = 18 on the kingston day twin (flow G) and n = 19 on the marrakesh
snapshot (flow D). At n = 20-30 only its counts and Clifford correctness are known (results/rule-big-2026-10-26); the
error-product estimators failed (results/esp-check-2026-10-26), so lam there can only be simulated.

- **Device.** `file:<target.pkl>`, the ibm_kingston Target of 2026-10-24 (data/targets/ibm_kingston_2026-10-24.pkl,
  SHA-256 3b93913856d2f0b9bf97ac03f89c43457157735413b02d8722c82d31065b218d; the run stops if it differs), twin ("sim")
  only, as flows G and I.
- **Arm.** `fold:rule` only (no zipper, no Qiskit: owner, 2026-10-27). On this Target: n = 20 the ring itself on a
  20-cycle (320 two-qubit gates, 5.6 us, 20 active qubits), n = 22 pendants on a 20-cycle (384, 9.2 us, 22 active
  qubits) (compile, 2026-10-26).
- **Run.** `TARGET=… OUT=… NS="20 22" NOTE=prereg/drafts-2026-10-27/rule_lam_big_note.md bash TOQB/gpu/rule_lam_big.sh`:
  for each n, `python -m toqb.fold_lam OUT/n<n>.jsonl --n <n> --L 16 --P 24 --T 256 --models sim --arms fold:rule
  --max-active 24 --models-seed 0 1 2 3 --device file:<target.pkl>`, n = 20 first, a zip after each n.
- **Expected time on one H100:** n = 20 about 30 min, n = 22 about 3 h (from flow I's measured cells; the noiseless
  reference on the CPU takes most of n = 22).
- **What is reported (no match, no WIN/LOSS: there is no second arm).** Per n the four models' lam with its standard
  error, delta, correlation; counts, duration, active qubits; beside them the rule's lam at n = 13-18 (flow G) and the
  zipper's at n = 18 (0.63-0.66); shots for a fixed precision as 1/lam^2.
- **Prediction (not a rule).** n = 20 (the ring on a cycle, no extra gate): lam at least 0.61 (the lowest of the rule's
  at n = 18) on every model. n = 22 (two pendants, 22 qubits): lam between 0.50 and n = 20's largest on every model.
- **Not claimed.** No device; one day's calibration of one device; random models; one placement per n.
