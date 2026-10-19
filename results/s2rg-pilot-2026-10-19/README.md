# S2R2-B pilot, 2026-10-19 (tuning only, not scored)

Pod: one H100 80 GB, 64 CPUs; `gpu/s2rg_pilot.sh` at TOQB c9ee8f8 (code as in the bundle of that commit), PSF-Zero
1d3fa8b5; start 02:30:09 CEST, end 05:49:08 CEST. Seeds 101 and 102 (outside every pre-registered range); n = 10,
both compilers, L = 8 and 16; budget $100 of stand-in time per run (459-488 loops of 2 circuits x 100 shots); 48 runs,
six at a time. The raw records (`s2rg_pilot.zip`) stay on the pod; the console output is kept here
(`setup_bench_probe_gradcos.txt`: environment, check_traj2, bench_traj2, the first CUDA-Q probe and the gradient
agreement; `progress_and_summary.txt`: every run and the summary).

**AUC of the stand-in's CE over the budget (lower is better), mean of the two seeds:**

| | S2R2-B lr 0.05 | 0.1 | 0.2 | SPSA2 a 0.2 | 0.5 | 1.0 |
|---|---|---|---|---|---|---|
| PSF L 8 | 0.613 | 0.589 | **0.571** | 0.644 | **0.630** | 0.641 |
| Qiskit L 8 | 0.631 | 0.617 | **0.605** | 0.648 | 0.637 | **0.636** |
| PSF L 16 | 0.663 | 0.652 | **0.632** | **0.673** | 0.676 | 0.684 |
| Qiskit L 16 | 0.667 | 0.659 | **0.644** | **0.672** | 0.674 | 0.682 |

- S2R2-B (simulator learning) is below SPSA2 (stand-in only) in every cell, at its best setting by 0.059 / 0.031 /
  0.040 / 0.029 (PSF L 8 / Qiskit L 8 / PSF L 16 / Qiskit L 16).
- Under S2R2-B, PSF is below Qiskit in all four (seed, depth) pairs at every learning rate; at lr 0.2 by 0.035 (L 8)
  and 0.011 (L 16) on average.
- lr 0.2, the largest tried, is best in every cell: the grid's edge. A larger rate may be better still.
- Wall time per run (six runs sharing the GPU): S2R2-B 10 / 31 / 19 / 61 min (PSF L 8 / Qiskit L 8 / PSF L 16 /
  Qiskit L 16), SPSA2 2 / 8 / 4 / 15 min.
- Gradient agreement, simulator vs stand-in (cos, student means 5 / 6): PSF L 8 1.00 / 1.00, PSF L 16 0.97 / 0.99,
  Qiskit L 8 0.80 / 0.85, Qiskit L 16 0.87 / 0.97.
