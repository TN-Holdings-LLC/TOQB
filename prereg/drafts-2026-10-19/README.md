# Drafts of 2026-10-19 (not fixed; nothing here is a pre-registration yet)

Written at the workplace on 2026-10-19 (CEST) from the owner's decisions and the home session's notes; design text
and formula estimates only, nothing was run there. Kept as written; corrections found since are listed below and go
into the next revision, not into these files.

| file | what it is |
|---|---|
| `X22_preregistration_skeleton.md` | engine x compiler (2 x 2) test, CUDA-Q + PSF-Zero: claim form (Pareto within the tested range, not "the only solution"), noise-model gate N1-N4, engine fairness, the Qiskit setting, log-scale interaction |
| `S2RB_preregistration_skeleton.md` | S2R2-B (owner's decision B): GPU simulator learning with stand-in records vs SPSA2 |
| `S2RB_runtime_cost_estimate.md` | GPU hours of the S2R2-B main run, by formula from RTX 4070 timings |
| `qpu_cost_check_gradcos.md`, `mc_gradcos.py` | check of the hardware cost of decision A (gradient agreement on a real device) and a Monte Carlo of the estimator |

**Corrections and new facts since (2026-10-19, pod pilot on an H100, partial):**

- H100 / RTX 4070 speed of `traj2` (68 circuits x 32 trajectories): PSF L 8 2.3 x, Qiskit L 8 4.8 x, PSF L 16 1.9 x,
  Qiskit L 16 5.0 x. On the H100 the PSF / Qiskit gap at L 16 is 2.8 x (7.4 x on the RTX 4070): ten qubits do not
  fill an H100 (per-step launch and host time dominate), fourteen do.
- The evaluation batches all test points of one structure (template compiles), so the batched rate r_lo applies in
  the runtime estimate.
- Gradient agreement, simulator vs stand-in (`toqb.gradcos`, 24 directions, 8 points, T = 256, student means 5 / 6):
  PSF L 8 1.00 / 1.00, PSF L 16 0.97 / 0.99, Qiskit L 8 0.80 / 0.85, Qiskit L 16 0.87 / 0.97; the stand-in's gradient
  over the simulator's: PSF 0.74-0.79, Qiskit L 8 0.34-0.50, Qiskit L 16 0.81. With K = 24 a true 0.9 reads as
  0.81-0.96, so: PSF about 1, Qiskit about 0.85-0.9.
- CUDA-Q 0.16.0 runs on the pod (target nvidia). Its first contact used a simplified noise model, so its times are not
  yet comparable; `toqb.check_cudaq` (the N1-N4 gate) is the next step.
