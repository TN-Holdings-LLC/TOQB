# Owner principle, recorded 2026-10-21

Recorded from the owner's message to the workplace session (2026-10-21), after the C-against-E battle of 2026-10-20
(`results/s2re-battle-2026-10-20/`). Workplace note, copied as received; home additions below the line.

## The principle

- Lanes do not matter, as in swimming or sprinting: there is no need to take lane 4, because real strength wins from
  lane 1.
- No clever tricks. Compete with the formula alone.
- Tricks come from not believing in the formula, and they only feed normalcy bias.
- No compromise for a vague kind of stability.

## What it means for the work (workplace reading)

1. Placement and calibration are lanes.
   - PSF-Zero is not given calibration-aware placement, a control arm or a hand-picked device in order to win.
   - Qiskit's calibration-aware placement is recorded as its own choice (consult B, option 1).
   - If PSF loses under that, the loss is reported.
2. Starting points and tuning are not the method.
   - A gain from a better start (theta = 0) or from a tuned learning rate is reported as such, never as the method's
     win.
   - Methods are compared from the same start, at the same cost (circuit evaluations x trajectories).
3. Formulas, not searches. Where a step can be solved in closed form, it is. Example: E4's one-dimensional Brier
   minimum, through the roots of a quartic in tan(u/2), instead of a grid with a parabola polish.
4. No stabilising devices.
   - Results are reported raw, including losses and ties, with vanity and essential figures side by side.
   - Procedures that exist only to make a run look smooth (for example two staggered pipelines) are not proposed.
5. What is honest is not a trick. These keep the race meaningful rather than easing it:
   - a theta = 0 control;
   - a teacher difficulty set by a rule before training;
   - bias correction of noisy estimates;
   - equal-cost comparison.

## State of the evidence at the time of the note (stand-in tier and noiseless runs only)

- PSF does not yet beat Qiskit on absolute CE on the stand-in: Qiskit chooses its lane from the calibration.
- PSF's twin predicts its circuits better (the direction of H2).
- E4-Brier against C is a tie on one seed and one teacher, noiseless.

---

## Home, 2026-10-21

- Item 3 is done: `toqb.s2re.brier_min` solves the one-dimensional Brier minimum exactly. Along one parameter the
  training loss is K + P cos u + Q sin u + R cos 2u + S sin 2u; its stationary points are the real roots of
  (2S - Q) t^4 + (8R - 2P) t^3 - 12 S t^2 - (2P + 8R) t + (Q + 2S) = 0 with t = tan(u/2), plus u = pi. The roots
  are taken as the eigenvalues of the companion matrix (`np.roots`): the closed form in exact arithmetic (Ferrari),
  numerically by a 4 x 4 eigenproblem. Tested: on 200 random instances the value is never above a 200,001-point grid
  minimum (tolerance 1e-9). `toqb.s2re.train_e4` sweeps it over the parameters; the training loss never rises (test).
- Item 2 is applied from this round on: C0 (C's update from theta = 0) against E4 from theta = 0, at C0's budget of
  128,000 circuit evaluations (2,000 loops x 16 candidates x 4 points); E4 takes the whole sweeps that fit.
- Item 5, teacher difficulty: the rounds of 2026-10-21 keep teacher_angle 1.0 (the value of 2026-10-20, where
  theta = 0 scores 0.596 on teacher_seed 4). A rule fixed before training (for example "the angle at which theta = 0
  scores below a set accuracy on the training points") is a design decision left to the owner.
