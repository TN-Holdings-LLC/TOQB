# Flow B (owner's plan of 2026-10-24): the a24 switch on the GPU, the source of the readout offset, and a decaying step. Declared 2026-10-24: B1 a check, B2 a report, B3 one rule fixed before the run

Runs on the owner's PC (RTX 4070, 12 GB, WSL; measured 2.5-3.1 times slower than an H100 per job, results/
gpu-bench-rtx4070) or a pod; PSF-Zero arms only (Qiskit's 14-23 active qubits do not fit 12 GB well). TOQB at the
commit that fixes this note, PSF-Zero `1294780` or later, a24 front end (TOQB's default since `fb86f64`).

## B1. The a24 switch on the GPU (check, no claim)

`toqb.check_traj 4000` (complex64) with the a24 front end and `PSF_RUST_TEMPLATE=check`: the trajectory engine against
the exact density matrix for both arms; PASS needed before B2 and B3 run. Then one short design C run (L 16, teacher 17
at angle 1.0, 20 loops, no checkpoint) through `psfai:template_zip` and `psfai:template`, each twice: on a24 (the
default) and on a22 / c61 (set explicitly), with TOQB_FAST_PSF=1. The final parameters must be equal (the same circuits
and draws).

## B2. Where the readout offset comes from (report only, no rule)

Why: on the stand-in, item 31 and Qiskit answer +1 on 84-94 % of balanced points at theta = 0, the zipper on 74-83 %
(results/far-teacher-2026-10-23, far-qiskit-2026-10-23); the twin's offset is far smaller (delta +0.046 for item 31 at
L 16), and relaxation explains part of the twin's (0.046 to 0.028, results/lam-ablate-2026-10-22). The stand-in adds
three things to the snapshot's noise: T1 and T2 scaled per qubit (t12 0.3), a 1 % over-rotation of sx and x, and a
10 kHz static ZZ accumulated over the schedule.

`toqb.offset_ablate` on the far-teacher records (item 31 and the zipper, teachers 17-19): at theta = 0 and at 2,000
loops, on the stand-in as declared and with each addition switched off (no_zz, no_over, no_t12) and all three off
(plain): (lam, delta) against the noiseless model on the 64 training inputs (no labels), the share of +1 answers and
the shot-free accuracy on the 500 test points; the twin's (lam, delta) beside them. 1,024 trajectories. Read: which
addition, if any, makes the offset; nothing is chosen from it.

## B3. Does a decaying step stop long training from drifting? (one rule)

Why: with the constant step (design C, lr 0.4) both arms got worse from 500 to 16,000 loops on teachers near the start
(results/zip-long-2026-10-23); on far teachers accuracy still rose from 500 to 2,000 loops. Whether the constant step
drifts on a far teacher once the model has learned is open. A decaying step is the standard remedy and changes only a
formula.

- **Task.** L 16, n 10, teachers 20, 21, 22 at angle 1.0 (new; fixed before the run, not chosen by a result; their
  data checked only to be makeable: made in 630, 422 and 328 s on a CPU, test labels balanced; nothing else seen), gap 0.2, 64 training and 500 test points.
- **Runs.** The zipper (`psfai:template_zip`, a24) only. Design C (C0, seed 301, 8 pairs, batch 4, 32 trajectories,
  h 0.1, lr 0.4) for 4,000 loops with checkpoints at 500, 1,000 and 2,000 (`toqb.s2rc_ckpt`), twice per
  teacher: the constant step, and the decaying step lr_k = 0.4 ((A + 1) / (k + A))^0.602 with A = 1,000 (0.31 at
  500 loops, 0.21 at 2,000, 0.15 at 4,000). Both runs of a teacher share every random draw. 6 runs.
- **Rule.** At 4,000 loops, per teacher, the trained model's noiseless accuracy, decaying against constant: exact
  McNemar on the 500 paired test points, Holm over 3, alpha 0.01. The decaying step is the better if it WINs in at
  least 2 of 3 teachers (a LOSS in 2 of 3 is reported as the reverse).
- **Reported, without a claim.** The same at every checkpoint; the change from the best checkpoint to 4,000 loops per
  schedule; stand-in accuracy shot-free and with 250 shots; the share of +1 answers; the twin's curve.
- **Not done.** No loop count, A or teacher is chosen from results.
- **Not claimed.** One seed; the zipper only; the stand-in is TOQB's model of a 2026-10-13 calibration.

## Time (estimate, RTX 4070)

B1 about 15 min; B2 about 2-3 h (60 evaluations); B3 about 4-5 h (6 runs of 4,000 loops, 2-3 at a time). On the
owner's PC, no cost.

## Owner's decisions (2026-10-24 06:55 CEST)

1. B3's teachers 20, 21, 22 at angle 1.0.
2. 4,000 loops (not 8,000).
3. A = 1,000.
4. On the owner's PC (RTX 4070), no cost.
