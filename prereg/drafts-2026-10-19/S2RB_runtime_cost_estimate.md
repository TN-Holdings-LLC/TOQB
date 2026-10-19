# S2R2-B main run: GPU time and pod cost estimate (by formula), 2026-10-19

Workplace estimate from home's RTX 4070 timings (traj2, complex64). **Nothing was run.**

- H100 speed is **not measured**; it enters as a factor f ∈ {2, 3, 4}.
- The pod price is **not confirmed**; it enters as a variable p ($/GPU-hour).
- All figures are GPU-hours on one GPU running one process at a time, as the timings were taken. The effect of running
  several processes per GPU is not known (see §5).

## 1. Inputs (home, RTX 4070)

| cell | simulator, 68 circuits × 32 traj: s₆₈ | stand-in, 2 circuits × 100 shots: d₂ | compile, 68 circuits: k₆₈ |
|---|---|---|---|
| PSF L 8 | 0.73 s | 0.44 s | 0.30 s |
| Qiskit L 8 | 3.87 s | 0.34 s | 0.19 s |
| PSF L 16 | 1.10 s | 0.70 s | 0.65 s |
| Qiskit L 16 | 8.12 s | 0.63 s | 0.34 s |

## 2. Formulas

**One S2R2-B loop** (64 simulator circuits, 2 stand-in circuits, 2 simulator prediction circuits, 66 compiles):

    t_B = (64/68)·s₆₈ + d₂ + (2/68)·s₆₈ + (66/68)·k₆₈

- **Assumption:** the 2 prediction circuits use T = 32 like the gradient circuits (`[ ]` to confirm).

**One SPSA2 iteration** (2 stand-in circuits, 2 compiles):

    t_S = d₂ + (2/68)·k₆₈

**One evaluation** (P test points × 64 trajectories on the stand-in, plus P compiles), once per arm every 50 loops:

    t_E = P·64·r + (P/68)·k₆₈

The per-trajectory rate r of a large stand-in batch is not measured. It is bracketed by two rates:

- **Batched (lower bound):** r_lo = s₆₈ / (68·32), the simulator's batched rate. The stand-in adds channels (ZZ,
  over-rotation) but runs the same kind of batch.
- **Small batch (upper bound):** r_hi = d₂ / 200, the 2-circuit × 100-shot rate. This is inflated by poor GPU use on a
  tiny batch, if each shot is one trajectory (`[ ]` to confirm how shots map to trajectories).

**Per loop, both arms, with evaluation amortized over 50 loops:**

    t_loop = t_B + t_S + 2·t_E/50

**Total, RTX 4070 GPU-hours:**

    H₄₀₇₀ = S · N · Σ_cells t_loop / 3600          (S seeds, N loops per run, 4 cells)

**H100 and cost:**

    H_H100 = H₄₀₇₀ / f            cost = H_H100 · p        (f ∈ {2, 3, 4}; p = $/GPU-hour, unconfirmed)

## 3. Per-loop times (RTX 4070)

| cell | t_B (s) | t_S (s) | t_E, P = 500 (s) | t_E, P = 1,000 (s) | t_loop, P = 500 (s) | t_loop, P = 1,000 (s) | share of evaluation in t_loop (upper) |
|---|---|---|---|---|---|---|---|
| PSF L 8 | 1.44 | 0.45 | 12.9-72.6 | 25.9-145.2 | 2.4-4.8 | 2.9-7.7 | 61 % / 75 % |
| Qiskit L 8 | 4.28 | 0.35 | 55.8-58.3 | 111.6-116.6 | 6.9-7.0 | 9.1-9.3 | 34 % / 50 % |
| PSF L 16 | 2.40 | 0.72 | 21.0-116.8 | 41.9-233.6 | 4.0-7.8 | 4.8-12.5 | 60 % / 75 % |
| Qiskit L 16 | 8.84 | 0.64 | 103.3-121.9 | 206.6-243.8 | 13.6-14.4 | 17.8-19.2 | 34 % / 51 % |

How to read the table:

- Ranges are r_lo to r_hi.
- **Qiskit's evaluation range is narrow** because its two rates nearly coincide: the wide circuits make the batched
  rate slow, close to the small-batch one.
- **Inside t_B**, the simulator is 48 % of the time for PSF L 8 and 86 % for Qiskit L 16. Compile is 20 % for PSF L 8
  and 26 % for PSF L 16.

## 4. Totals

GPU-hours, low to high, as the evaluation rate goes from r_lo to r_hi:

| P | N (loops) | seeds S | RTX 4070 | H100, f = 2 | H100, f = 3 | H100, f = 4 |
|---|---|---|---|---|---|---|
| 500 | 2,000 | 100 | 1,490-1,880 | 750-940 | 500-630 | 370-470 |
| 500 | 2,000 | 200 | 2,980-3,770 | 1,490-1,880 | 990-1,260 | 750-940 |
| 500 | 5,000 | 100 | 3,730-4,710 | 1,860-2,350 | 1,240-1,570 | 930-1,180 |
| 500 | 5,000 | 200 | 7,450-9,420 | 3,730-4,710 | 2,490-3,140 | 1,860-2,350 |
| 1,000 | 2,000 | 100 | 1,920-2,710 | 960-1,350 | 640-900 | 480-680 |
| 1,000 | 2,000 | 200 | 3,840-5,410 | 1,920-2,710 | 1,280-1,800 | 960-1,350 |
| 1,000 | 5,000 | 100 | 4,800-6,760 | 2,400-3,380 | 1,600-2,250 | 1,200-1,690 |
| 1,000 | 5,000 | 200 | 9,600-13,520 | 4,800-6,760 | 3,200-4,510 | 2,400-3,380 |

- **Cost:** multiply an H100 column by p. For example, P = 1,000, N = 5,000, S = 200, f = 3 costs
  (3,200-4,510) × p dollars.
- **Wall-clock time** is GPU-hours divided by the number of GPUs used in parallel. The runs are independent, so they
  parallelise perfectly across GPUs.

## 5. What dominates

- **By cell** (P = 1,000, upper bound): Qiskit L 16 is about 40 % of the total, PSF L 16 26 %, Qiskit L 8 19 % and
  PSF L 8 16 %.
- **Within Qiskit cells:** the simulator gradient (64 circuits on 14 or more qubits) dominates.
- **Within PSF cells:** the evaluation dominates, 60-75 % of the time if the small-batch rate applies.
- **Evaluation overall:** 34-75 % of the time per loop depending on cell and P. Every 50 loops, both arms evaluate
  P × 64 stand-in trajectories.
- **SPSA2** is small per iteration, but its evaluation costs as much as S2R2-B's.
- **Biggest uncertainty:** the evaluation rate. It moves the total by up to 1.4 ×. One timing of a single evaluation
  per cell on the pod would settle it.

## 6. Ways to reduce it (listed only; each is the owner's decision, some change the design)

1. **Evaluate less often:** every 100 loops instead of 50 roughly halves the evaluation share. The AUC becomes coarser.
2. **Fewer test trajectories** (64 → 32) or fewer test points (1,000 → 500). Each roughly halves the evaluation; CE
   becomes noisier.
3. **Batch the evaluation:** evaluate both arms, or several seeds, in one large stand-in batch, so that the batched
   rate r_lo applies.
4. **Run several processes per GPU** (or CUDA MPS) so that small batches (the stand-in's 2 circuits, SPSA2) fill the
   GPU. The throughput gain is unmeasured.
5. **Overlap compile (CPU) with simulation (GPU)**, for example by pipelining the next loop's compile. Compile is 20-26 %
   of t_B in the PSF cells.
6. **Fewer seeds** (200 → 100) or fewer loops. Statistical power must be checked against p < 0.01.
7. **A stronger Qiskit setting** (X22 §4). If it narrows Qiskit's circuits, it lowers the dominant cost. Unmeasured.
8. **Measure the H100 factor f first** with the existing `bench_traj2` before buying hours.
