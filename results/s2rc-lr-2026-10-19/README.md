# Design C, learning-rate comparison, 2026-10-19 (tuning seeds 101-102; not scored)

Pod: one H100; `gpu/s2rc_rehearsal.sh` at TOQB 1588e51 with SEEDS="101 102", LOOPS=500, P=200, SHOTS=1000, PAR=4 for
each of lr 0.2, 0.4 and 0.8, all three at once (12 runs on the GPU); 13:31-16:30 JST (06:31-09:30 CEST). The twin and
the compilers use the stand-in's published calibration (`snapshot:marrakesh`); the "device" is the stand-in.
`summary.txt` holds the three summaries as printed; the raw records stay on the pod.

**Per cell, mean of the two seeds** (stand-in CE and accuracy of one simulated job of 200 points x 1000 shots; rms of
twin P(1) - stand-in P(1) over the 200 points; "in" = stand-in CE inside the twin's 99 % interval, shots and the
twin's own Monte Carlo error):

| lr | cell | stand-in CE | accuracy | P(1) rms | in |
|---|---|---|---|---|---|
| 0.2 | PSF L 8 | 0.590 | 0.659 | 0.009 | 2/2 |
| 0.2 | Qiskit L 8 | 0.547 | 0.712 | 0.039 | 0/2 |
| 0.2 | PSF L 16 | 0.659 | 0.600 | 0.006 | 2/2 |
| 0.2 | Qiskit L 16 | 0.617 | 0.579 | 0.012 | 2/2 |
| 0.4 | PSF L 8 | 0.581 | 0.690 | 0.009 | 2/2 |
| 0.4 | Qiskit L 8 | 0.535 | 0.722 | 0.047 | 0/2 |
| 0.4 | PSF L 16 | 0.640 | 0.601 | 0.008 | 2/2 |
| 0.4 | Qiskit L 16 | 0.613 | 0.564 | 0.017 | 1/2 |
| 0.8 | PSF L 8 | 0.578 | 0.722 | 0.010 | 2/2 |
| 0.8 | Qiskit L 8 | 0.555 | 0.639 | 0.051 | 0/2 |
| 0.8 | PSF L 16 | 0.638 | 0.594 | 0.008 | 2/2 |
| 0.8 | Qiskit L 16 | 0.613 | 0.581 | 0.016 | 2/2 |

**Mean stand-in CE over the four cells:** lr 0.2 0.6032, lr 0.4 **0.5922**, lr 0.8 0.5957. lr 0.4 is chosen for the
rehearsal (lowest mean, inside the grid; PSF alone would take 0.8 by 0.001-0.003, Qiskit L 8 takes 0.4 by 0.02).

**Readings (two tuning seeds, 500 loops; not a test):**

- The twin predicts PSF's circuits far better: P(1) rms 0.006-0.010 against 0.012-0.051 for Qiskit (4-5 x at L 8);
  PSF's stand-in CE fell inside the interval in 12 of 12 runs, Qiskit's in 5 of 12 (0 of 6 at L 8). The direction of
  design C's H2, and of the gradient agreement of the morning (PSF cos about 1, Qiskit 0.85-0.9).
- But Qiskit's circuits reach the lower stand-in CE: 0.535-0.555 against 0.578-0.590 at L 8, 0.613-0.617 against
  0.638-0.659 at L 16; their twin CE also starts lower (L 8 seed 102: 0.50 against 0.58). Compiled against the
  Marrakesh calibration, Qiskit level 2 places the circuit by the calibrated error rates; PSF's template places the
  ring by the coupling map alone (the likely cause; not checked). Under the FakeFez twin of the S2R2-B pilot the order
  was the other way round.
- Accuracy at L 16 is 0.56-0.62: with P = 200 a cell needs 0.605 for the first Holm step of design C's H1, so P = 500
  (0.564) or pooled models would be needed for H1 at L 16.
