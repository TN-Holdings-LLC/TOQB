# DRAFT (not fixed, not declared): how much signal the count rule keeps at n = 20, 22, 24 on the kingston day twin

Prepared 2026-10-27 (owner: "rule N20 22 24 は考えておく 一応用意はしておいて"). To be completed and fixed by SHA-256
and CET time before a run. Open points are marked **OPEN**.

**Why.** The count rule's lam is known up to n = 18 on the kingston day twin (flow G) and n = 19 on the marrakesh
snapshot (flow D). At n = 20-30 only its counts and Clifford correctness are known (results/rule-big-2026-10-26); the
error-product estimators failed (results/esp-check-2026-10-26), so lam there can only be simulated. Paper 4 states the
rule's choices up to n = 30.

- **Device.** `file:<target.pkl>`, the ibm_kingston Target of 2026-10-24 (data/targets/ibm_kingston_2026-10-24.pkl,
  SHA-256 3b939138…), twin ("sim") only, as flows G and I.
- **Arm.** `fold:rule` only (no zipper, no Qiskit: owner, 2026-10-27). On this Target: n = 20 the ring itself on a
  20-cycle (320 two-qubit gates, 5.6 us), n = 22 pendants on a 20-cycle (384, 9.2 us), n = 24 the ring itself on a
  24-cycle (384, 5.6 us); 20, 22, 24 active qubits (compile, 2026-10-26).
- **Run.** `python -m toqb.fold_lam OUT --n <n> --L 16 --P 24 --T 256 --models sim --arms fold:rule --max-active 24
  --models-seed 0 1 2 3 --device file:<target.pkl>`, one n after the other (20, 22, 24), a zip after each.
- **Expected time on one H100** (from flow I's measured cells: about 2.4-2.8 times per added active qubit; the
  noiseless reference on the CPU): n = 20 about 20 min, n = 22 about 3-4 h, n = 24 about 20 h. **OPEN:** whether to
  run n = 24; whether to move the noiseless reference to the GPU first (a change to `fold_lam`, to be checked equal to
  the CPU values at n <= 18 before use; it would cut n = 22 to about 1 h and n = 24 to about 8 h).
- **What is reported (no match, no WIN/LOSS: there is no second arm).** Per n the four models' lam, delta,
  correlation; counts, duration, active qubits; beside them the rule's lam at n = 13-18 (flow G) and, for scale, the
  zipper's at n = 18 (0.63-0.66). Shots for a fixed precision as 1/lam^2.
- **Prediction (not a rule).** **OPEN.** A proposal: at n = 20 and 24, where the ring sits on a cycle with no extra gate,
  lam at least that of n = 18 (0.61-0.68); at n = 22 (two pendants) between them.
- **Not claimed.** No device; one day's calibration of one device; random models; one placement per n.
