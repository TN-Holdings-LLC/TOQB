# Flow J, amendment 2 (owner, 2026-10-27 "GPUに移す"): n = 24 with the noiseless reference on the GPU. Fixed by SHA-256 and CET time before n = 24 runs; replaces amendment 1's run command

Everything as in amendment 1 (`6924d12`) except how the noiseless reference is computed for n = 24: by
`toqb.noiseless_xp` (a direct complex128 statevector of the same gates as `task_loop.model_circuit`) on cupy, through
`TOQB_NOISELESS=cupy` in `fold_lam`, instead of Qiskit's `Statevector` on the CPU. The noisy twin, the arm, the
models, the inputs and every other setting are unchanged; n = 20 and 22 keep the CPU reference already run.

- **Why.** At 24 qubits the CPU reference would take about 2-3 h a model (56 s an input at 22 qubits with numpy on a
  2-core container, 114 s with Qiskit), about half of n = 24's time.
- **Checks (declared), before n = 24, by `gpu/rule_lam_big_n24.sh`; the run stops if either fails:**
  1. `TOQB_XP=cupy python -m toqb.noiseless_xp check 3 5 8 12 13`: the direct statevector on numpy and on cupy equals
     Qiskit's `Statevector` within 1e-9 on 30 random cases (n = 3-13, L = 2 and 16). On the cloud container with
     numpy: largest difference 2.8e-15.
  2. Flow J's n = 20, model 0, again with `TOQB_NOISELESS=cupy`: lam, delta, corr, q2 and us equal to the row already
     run with the CPU reference (`n20.jsonl`), to the 5 decimals recorded. (On the container, n = 9, two models: equal.)
- **Run.** After flow J's first run has written "all done": `TARGET=… REF=<first run>/n20.jsonl OUT=<new folder> bash
  TOQB/gpu/rule_lam_big_n24.sh`.
- **Expected time on one H100:** the checks about 5 min; n = 24 about 8-10 h (about 2 h a model for the trajectories,
  from flow I's cells; the reference seconds).
- **Prediction (not a rule).** As in amendment 1: lam at least 0.61 on every model.
