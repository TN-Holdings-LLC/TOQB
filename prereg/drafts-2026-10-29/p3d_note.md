# P3D: the check of the Paper 3 diagnosis (DRAFT by the workplace, 2026-10-29; owner's go pending). Noiseless classical simulation only. Nothing here is a device result. To be fixed by SHA-256 and CET time before the run

## 1. Why

The diagnosis (psf-zero `docs/findings/paper3-learning-failure-diagnosis-2026-10-29.md`) claims three causes for
"training lowered accuracy" in Paper 3. It ruled out a barren plateau and the device's noise.

1. **Random walk.** Design C's update is dominated by its own estimator's randomness and random-walks away from a good
   start.
2. **Multiplicative noise.** That randomness scales with the gradient, so a larger λ only lengthens the walk.
3. **Too few points.** At L = 16, 64 training points cannot fix 330 parameters.

This test checks causes 1 and 3 directly.

- **Cause 2's identity is not run here.** With outputs λf, C's step is exactly λ times its noiseless step, so a larger λ
  is a larger learning rate. This is exact and is checked by a unit test (`test_g_is_the_expectation_of_c_and_damping_
  is_a_learning_rate`), not by a run.
- **Its positive side belongs to Paper 5's device test, not here.** That positive side is "with additive shot noise,
  a larger λ helps".

## 2. Fixed (nothing is chosen after a result; nothing is tuned)

**Code.** `toqb/p3d.py`, `gpu/p3d.sh`, `tests/test_p3d.py` at the commit that adds this file. Outputs are exact
noiseless ⟨Z_0⟩ of TOQB's ring classifier (`toqb.task_loop`).

**Where every value comes from.** Each is taken from the records or from a count:

- **Design C's settings:** the device day's plan.
- **Task A:** the device day's task.
- **Task C's teachers:** the far-teacher test of 2026-10-23.
- **N = 330:** the parameter count d at L = 16.
- **E's 2 sweeps:** C's evaluation budget. E uses 2 × 3 × 330 × 64 = 126,720 outputs, against C's
  2,000 × 16 × 4 = 128,000.
- **G's lr and step count:** equal to C's, by definition of G.

| item | value |
|---|---|
| Task A (Part A) | n 10, L 16, enc π/2, teacher_seed 4, teacher_angle 0.3, gap 0.2, 64 training / 500 test points (`s2r2.teacher_data2`): the device day's task |
| Task C (Part C) | n 10, L 16, enc π/2, teacher_seed 17, 18, 19, teacher_angle 1.0, gap 0.2, N_train 64 and 330, 500 test points, test_after 165, so that both N share one test set and N = 64's points are a subset of N = 330's |
| Arm Z | θ = 0 (no training) |
| Arm C | design C's update exactly as `toqb.s2rc` (8 ±1 directions, antithetic, batch 4, h 0.1, lr 0.4, 2,000 loops, from 0, loss mean((1 − y f)/2), the same random-number sequence), outputs exact. Seeds 301 (the device day's), 302, 303. Part A only |
| Arm G | the exact gradient of the same loss over all training points, lr 0.4, 2,000 steps, from 0 (adjoint method). G's step is the expectation of C's step (to O(h²)); only the estimator's randomness differs |
| Arm E | design E4 (`s2re.train_e4`): exact per-parameter Brier minimum, fixed order, 2 sweeps, from 0 |
| Accuracy | noiseless test accuracy, sign(⟨Z_0⟩) = label; ⟨Z_0⟩ = 0 counts as wrong. One SE ≈ 0.011 at 0.93 and 0.022 at 0.6 (500 points) |
| Paired test | one-sided exact McNemar over the 500 test points; Holm over the family named in each rule; α = 0.01 |
| Path measures | \|Δθ\| = \|θ_final − 0\|; walk = lr·√Σ_k \|g_k\|²; straight = lr·Σ_k \|g_k\| (as in the diagnosis) |

## 3. Procedure checks (gates: a failure stops the run, and nothing is scored)

**Gates in the script:**

- **A0a.** The fast simulator equals `exact_batch.z0_batch` within 1e-10. Its adjoint gradient equals the
  parameter-shift rule within 1e-10, at n 10, L 16 (`p3d check`). The unit tests must also pass.
- **A0b.** Arm Z on Task A gives home's recorded θ = 0 accuracy, 0.934 (`device-2026-10-22/theta0_home`).
- **C0.** Task C's two N share the identical test set, and N = 64's training points are a subset of N = 330's. Checked
  by a unit test, and again by the scorer.

**Already done before this draft, and reported:**

- **Reproduction.** On the 2026-10-20 noiseless record (L 8, teacher 4, angle 0.3, seed 201), `p3d.train_c` gives test
  accuracy 0.754 and CE 0.501. That equals the record (0.754 / 0.501), and θ = 0 gives 0.948, also equal. That task is
  not used below.
- **A0a ran:** largest differences 1.6e-15 (outputs) and 1.1e-15 (gradients).

## 4. Predictions and rules (fixed now)

### Part A: cause 1, on Task A

| id | prediction | rule |
|---|---|---|
| A1 | C ends below θ = 0, for every seed | McNemar C worse than Z, per seed; Holm over the 3 seeds. HOLDS if all 3 reject; FAILS if none; PARTLY otherwise. Expected size: 0.75-0.88 (records: 0.754 noiseless at L 8, 0.762 twin-trained at L 16) |
| A2 | G does not decline, and beats C | acc_G ≥ acc_Z − 0.02, **and** McNemar C worse than G for every seed (Holm over 3) |
| A3 | E does not decline | acc_E ≥ acc_Z − 0.02 |
| A4 | the mechanism | for every C seed: 0.6 ≤ \|Δθ\| / walk ≤ 1.2 and straight / \|Δθ\| ≥ 20; for G: straight / \|Δθ\| ≤ 3 |

### Part C: cause 3, on Task C

| id | prediction | rule |
|---|---|---|
| C1 (primary for E; reported for G) | more points help | McNemar N = 64 worse than N = 330, per teacher; Holm over the 3 teachers. HOLDS if at least 2 reject |
| C2 (descriptive) | the train − test gap shrinks with N | count of teachers with a smaller gap at N = 330 |

## 5. How the outcomes will be read (written before the run)

| outcome | reading |
|---|---|
| A1, A2, A4 hold | cause 1 confirmed: the decline is C's estimator randomness, a random walk; the same expected step without it does not decline |
| A1 holds, A2 fails (G also declines) | cause 1 is wrong or incomplete: the loss and learning rate themselves (linear loss, fixed lr, 330 parameters on 64 points) cause the decline. If A3 holds, F4 (a proper loss) or F1's solver is the fix, not the estimator alone |
| A1 fails (noiseless C does not decline at L 16) | the recorded L 16 decline (0.762) needed the twin's noise: the diagnosis is incomplete at L 16 |
| A4 fails for C only | C declined, but not by a walk of the predicted shape: the mechanism is mis-stated |
| C1 holds | cause 3 confirmed: at L 16 the point count limits generalisation |
| C1 fails, training accuracy at N = 330 high | the far teacher at L 16 is not learnable from 330 points either: look again at the circuit form (fact 2) |
| C1 fails, training accuracy at N = 330 low | the trainer cannot fit at L 16 (an optimisation limit), and cause 3 is not tested |

Every result is reported as it is, including failures.

## 6. Run

**Command** (from the parent of TOQB):

    OUT=<new folder> PAR=<cores> bash TOQB/gpu/p3d.sh

- **Runs.** 21: A_Z, then 20 runs in parallel, longest first.
- **Needs.** numpy, scipy and pytest. No GPU, no Qiskit, no device.
- **Measured costs, one CPU thread (workplace):**
  - C: about 4-5 min per seed;
  - G at N 64: about 13 min;
  - G at N 330: about 90 min each;
  - E at N 330: about 11 min;
  - E at N 64: about 2 min.
- **Wall time:** with PAR ≥ 8, about 1.5 h (bound by one G at N 330); with PAR 2, about 3 h.
- **Rehearsal.** `P3D_SMOKE=1` runs the same procedure on a tiny model (n 4, L 2, 20 loops). It is never scored as a
  result.
- **Scoring.** `python -m toqb.p3d score <OUT>/runs` writes `p3d_score.md` and `.json` with the verdicts of section 4.

## 7. Limits

- **Simulation only.** Noiseless classical simulation; no twin, no stand-in, no device.
- **Small samples.** One task for Part A (with 3 C seeds); three teachers for Part C.
- **G's learning rate is C's**, not tuned for G. A2 tests "the same expected step without randomness", not the best
  gradient method.
- **Path measures are proxies.** Distances in parameter space stand in for distances between functions; accuracy is
  the decisive measure.
- **N = 330 at L 16 is one choice of "N ≥ d".** It shows whether more points help, not how many are enough.
