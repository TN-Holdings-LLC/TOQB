# traj2 against CUDA-Q 0.15.1, 2026-10-19 (H100 pod, GPU otherwise idle)

`python -m toqb.check_cudaq` at TOQB fed598d, cudaq 0.15.1 (0.16.0 fails on general Kraus channels:
`results/cudaq-diag-2026-10-19/`), started detached 09:38 CEST, ended before 09:44 CEST. Output (warnings removed) in
`check_cudaq_0151.txt`.

**Agreement: PASS.** For both compilers, both depths and both noise models (twin "sim" and the stand-in), the two
engines' <Z> agree within 1.66 standard errors at most (gate: 4 se); the u3 mapping deviates by 3.1e-7.

**Timings on the same H100** (one measurement each; seconds):

| circuits | engine | PSF L 8 | Qiskit L 8 | PSF L 16 | Qiskit L 16 | Qiskit / PSF |
|---|---|---|---|---|---|---|
| 68 x 32 trajectories (a training step's shape) | traj2 | 0.41 | 0.80 | 0.59 | 1.70 | 2.0 / 2.9 |
| | CUDA-Q | 42.6 | 51.8 | 86.5 | 102.2 | 1.2 / 1.2 |
| 1 x 4096 trajectories | traj2 | 0.77 | 1.58 | 1.00 | 3.16 | 2.1 / 3.2 |
| | CUDA-Q | 0.75 | 1.83 | 1.40 | 3.72 | 2.4 / 2.7 |

**Readings (corrected the same evening; the first version blamed the 4-40 s first calls, which the timings do not
include):**

- The times are warm: the kernel is built once per plan and the check times after one warm-up call.
- The warm CUDA-Q cost per call, 68 x 32 time / 68, is 0.63 / 0.76 / 1.27 / 1.50 s (PSF L 8 / Qiskit L 8 / PSF L 16 /
  Qiskit L 16): 0.23-0.25 ms per inline noise operation of the plan in all four. A call costs about the same at 32
  trajectories as at 4,096 for PSF. So a fixed cost per call, proportional to the number of inline noise operations,
  dominates (inferred from four points; not profiled). Batched calls (broadcast) or gate-attached noise are the
  first candidates; neither was tried.
- 1 x 4,096 minus that fixed cost leaves an estimated simulation share of about 0.12 / 1.07 s (L 8, PSF / Qiskit) and
  0.13 / 2.22 s (L 16): rough (differences of single measurements). The Qiskit / PSF ratio of the whole 1 x 4,096 call
  (2.4-2.7 x) therefore measures mostly the per-call cost, not the simulation.
