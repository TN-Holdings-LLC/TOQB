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

**Readings:**

- One circuit, many trajectories: CUDA-Q and traj2 run at the same speed (0.75-1.4 x), and PSF's shorter circuits
  save the same factor on both engines (Qiskit / PSF 2.4-2.7 x on CUDA-Q, 2.1-3.2 x on traj2): the compression carries
  over to CUDA-Q.
- Many different circuits, few trajectories each (training): CUDA-Q is 50-150 x slower than traj2 and PSF's saving
  shrinks to 1.2 x. That is a per-circuit cost of this wrapper (`toqb.cudaq_engine`: one `cudaq.sample` call per
  circuit and trajectory batch; first calls 4-40 s), not a measured limit of CUDA-Q; batched or asynchronous
  submission was not tried.
