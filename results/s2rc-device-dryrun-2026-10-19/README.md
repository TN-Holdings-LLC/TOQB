# Design C device path: procedure check on the home GPU, 2026-10-19 (not scored)

`gpu/s2rc_device_dryrun.sh` at TOQB f1c2ebf on the home PC (RTX 4070, WSL; `TOQB_TRAJ_MEM_GB=2`), 13:31-14:20 CEST,
with option A's sizes: P_8 150, P_16 500, N 250, M 1, seed 299, 20 loops (the models are not trained: the procedure
is what is checked). No IBM connection: the Target is FakeFez's, and the "device" is a noiseless Qiskit Aer run of
the assembled circuits. Output as printed (paths shortened to `<home>/`).

**Every step ran to the end:**

| step | start (CEST) | result |
|---|---|---|
| fetch (FakeFez's Target saved to a file) | 13:31:20 | done |
| plans | 13:31:23 | done |
| train and predict, 4 runs in parallel, QPY export | 13:31:23 | all valid; wall time PSF L 8 114 s, PSF L 16 584 s, Qiskit L 8 1,020 s, Qiskit L 16 2,691 s |
| assemble (hashes, ISA and failed elements, QPU-time limit) | 14:16:55 | 4 cells, 1,300 circuits x 250 shots, modelled QPU time 137.6 s (limit 150 s) |
| submit, LOCAL (noiseless Aer) | 14:17:23 | done |
| score | 14:19:54 | `score.md` written |
| end | 14:19:55 | `== DONE: <home>/s2rc_dry/s2rc_device_dryrun.zip` |

**Score as printed (not evidence about anything: untrained models, and a noiseless "device" against a twin with
FakeFez's noise):**

| cell | P | correct (strict) | H1 p (Holm) | CE (pred) | in 99 % (twin+shots / shots) | acc (pred) | mean dev (shot floor) |
|---|---|---|---|---|---|---|---|
| L16 PSF | 500 | 272 | 0.035 | 0.6795 (0.6664) | no / no | 0.556 (0.588) | 0.0382 (0.0251) |
| L16 Qiskit | 500 | 277 | 0.035 | 0.6740 (0.6637) | no / no | 0.568 (0.596) | 0.0402 (0.0251) |
| L8 PSF | 150 | 90 | 0.035 | 0.6683 (0.6620) | yes / yes | 0.610 (0.588) | 0.0319 (0.0235) |
| L8 Qiskit | 150 | 89 | 0.035 | 0.6722 (0.6705) | yes / yes | 0.597 (0.565) | 0.0403 (0.0237) |

H2 as printed: L 8 mean d +0.0084, Wilcoxon p (Holm) 0.0061; L 16 +0.0020, 0.225.

**Readings:**

- **Procedure check (a) of C r4 section 6: passed for the device path,** at the job's real size: plans, training with
  export, assemble with every check, submission (locally), scoring, Holm over cells and depths.
- **The printed tests mean nothing here, by construction:** the "device" has no noise and the twin has FakeFez's, so
  the twin overpredicts noise, more for the wider Qiskit circuits; that alone makes Qiskit's deviation larger (the
  L 8 "H2 confirmed") and puts L 16 outside the intervals. It shows that R1 and H2 react; it is not a result.
- **Time on the device day:** on the 4070, Qiskit L 16 took 45 min for 20 loops plus the prediction of 500 points x
  1,024 trajectories; the prediction dominates at 20 loops. Training (2,000 loops) is estimated at about 4.2 h for
  Qiskit L 16 on the H100 (C r3 section 5); the H100's prediction time is not measured.
- Assemble took 28 s and the local run 2.5 min for 1,300 circuits.
