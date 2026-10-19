# S2R2-B main run: GPU time and pod cost estimate (r2, H100 measured), 2026-10-19

Workplace estimate by formula from the H100 pod pilot's timings (traj2, complex64). **Nothing was run here.**

- The pod price is **not confirmed**; it enters as a variable p ($/GPU-hour).
- Figures are GPU-hours with one process per GPU, as the timings were taken.
- **r2 replaces r1's RTX 4070 basis and its H100 factor f.**
  - The measured H100 / RTX 4070 speed-ups of the simulator were PSF L 8 2.3 ×, Qiskit L 8 4.8 ×, PSF L 16 1.9 × and
    Qiskit L 16 5.0 ×.
  - Evaluation uses the batched rate r_lo: the pilot confirmed that evaluation computes circuits of one shape together.

## 1. Inputs (H100 pilot)

| cell | simulator, 68 circuits × 32 traj: s₆₈ | stand-in, 2 circuits × 100 shots: d₂ | compile, 68 circuits: k₆₈ |
|---|---|---|---|
| PSF L 8 | 0.32 s | 0.13 s | 0.26 s |
| Qiskit L 8 | 0.81 s | 0.14 s | 0.17 s |
| PSF L 16 | 0.58 s | 0.25 s | 0.62 s |
| Qiskit L 16 | 1.61 s | 0.28 s | 0.31 s |

## 2. Formulas (as r1; evaluation at the batched rate)

    t_B    = (64/68)·s₆₈ + d₂ + (2/68)·s₆₈ + (66/68)·k₆₈         one S2R2-B loop
    t_S    = d₂ + (2/68)·k₆₈                                      one SPSA2 iteration
    t_E    = P·64·s₆₈/(68·32) + (P/68)·k₆₈                        one evaluation (P test points × 64 traj), per arm
    t_loop = t_B + t_S + 2·t_E/50                                 both arms, evaluation every 50 loops
    H      = S · N · Σ_cells t_loop / 3600                        GPU-hours (S seeds, N loops, 4 cells)
    cost   = H · p

- **Assumption (unchanged from r1):** the 2 prediction circuits use T = 32 (`[ ]` to confirm).

## 3. Per-loop times (H100)

| cell | t_B (s) | of which: simulator / stand-in / compile | t_S (s) | t_E, P = 500 | t_E, P = 1,000 | t_loop, P = 500 | t_loop, P = 1,000 | evaluation share (P = 500 / 1,000) |
|---|---|---|---|---|---|---|---|---|
| PSF L 8 | 0.69 | 0.31 / 0.13 / 0.25 | 0.14 | 6.6 s | 13.2 s | 1.10 s | 1.36 s | 24 % / 39 % |
| Qiskit L 8 | 1.09 | 0.79 / 0.14 / 0.17 | 0.15 | 13.2 s | 26.3 s | 1.76 s | 2.29 s | 30 % / 46 % |
| PSF L 16 | 1.42 | 0.56 / 0.25 / 0.60 | 0.27 | 13.1 s | 26.2 s | 2.21 s | 2.73 s | 24 % / 38 % |
| Qiskit L 16 | 2.14 | 1.56 / 0.28 / 0.30 | 0.29 | 26.0 s | 51.9 s | 3.47 s | 4.51 s | 30 % / 46 % |

- The simulator column includes the 2 prediction circuits.
- The sum of t_loop over the 4 cells is 8.5 s (P = 500) or 10.9 s (P = 1,000).

## 4. Totals (H100 GPU-hours; multiply by p for the cost)

| P | N (loops) | S = 100 seeds | S = 200 seeds |
|---|---|---|---|
| 500 | 2,000 | 474 | 948 |
| 500 | 5,000 | 1,185 | 2,371 |
| 1,000 | 2,000 | 605 | 1,210 |
| 1,000 | 5,000 | 1,512 | 3,025 |

- **Cost:** H · p. For example, P = 1,000, N = 5,000, S = 200 costs 3,025 · p dollars.
- **Wall-clock time** is H divided by the number of GPUs used in parallel (the runs are independent).
- **Compared with r1's RTX 4070 basis** (9,600-13,520 GPU-hours for the same case): the H100 total is 3.2-4.5 × smaller.

## 5. What dominates on the H100

- **By cell:** Qiskit L 16 41 %, PSF L 16 25-26 %, Qiskit L 8 21 %, PSF L 8 12-13 % (P = 500 / 1,000).
- **Evaluation:** 24-46 % of the time per loop (r1 had up to 75 %, because of the small-batch rate).
- **Compile (CPU) now matters in the PSF cells.** It is 36 % of t_B for PSF L 8 and 43 % for PSF L 16, because the H100
  speeds up only the GPU part. Compile time is nearly the same on both machines (PSF L 16: 0.65 s against 0.62 s).
- **The simulator gap narrows on the H100.** Qiskit / PSF simulator time was 5.3 × at L 8 and 7.4 × at L 16 on the
  RTX 4070. On the H100 it is 2.5 × and 2.8 ×. Ten qubits do not fill an H100, so PSF's narrower circuits gain less
  from the bigger GPU.

## 6. Ways to reduce it (listed only; each is the owner's decision, some change the design)

1. **Overlap compile (CPU) with simulation (GPU):** compile the next loop's circuits while the GPU simulates. This is
   largest for the PSF cells (up to 43 % of t_B).
2. **Run several processes per GPU** (or CUDA MPS). A 10-qubit simulation leaves most of an H100 idle, so two or more
   runs per GPU may share it with little slow-down. The throughput gain is unmeasured.
3. **Evaluate less often** (every 100 loops) or with fewer test trajectories (64 → 32). The evaluation share
   roughly halves; the AUC becomes coarser or noisier.
4. **Fewer seeds** (200 → 100) or fewer loops, after a power check against p < 0.01.
5. **A stronger Qiskit setting** (X22 §4) may narrow Qiskit's circuits and lower the dominant cell. Unmeasured.
6. **Measure one full loop and one evaluation per cell** on the pod, to replace the component-sum estimate here.
