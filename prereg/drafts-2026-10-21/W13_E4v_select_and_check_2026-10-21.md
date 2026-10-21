# W13. E4v: choose the step on one part of the trajectories and check it on another (2026-10-21)

**Status.** Written at the workplace on 2026-10-21 at about 09:30 CEST, after the fruit match was scored. It is step
2 of the plan the owner approved:

1. the cause check (W12);
2. one improved E4, fixed in advance, on fresh teachers, scored by the frozen W11 scorer;
3. no further version either way.

The owner chose option A, "select and check". The code was syntax-checked only; home runs the tests. **Fix this file
and the code by SHA-256 before the first E4v record is read.**

**A correction first.** The workplace's earlier option (b), "shrink the step by the signal-to-noise ratio", does
nothing in the form proposed. Shrinking all four Brier coefficients (P, Q, R, S) by one factor leaves the minimum u
where it was. A real damping in u needs a chosen constant, which was option B, and the owner did not take it.

## 1. The method

E4 is unchanged except at the step of each parameter. The `traj` trajectories of every circuit are split into four
independent quarters, with common random numbers within a quarter, as E4 does within a half.

| | E4 (the fruit match) | E4v |
|---|---|---|
| estimates of each sinusoid | 2 halves of traj / 2 | 4 quarters of traj / 4 |
| coefficients | C = split(half 1, half 2), unbiased | C_A = split(q1, q2), C_B = split(q3, q4), unbiased and independent |
| step | u = argmin of C's curve | u_A = argmin of C_A's curve (the same exact quartic) |
| taken if | always (u = 0 is a candidate) | **only if v = C_B's change at u_A is < 0** |
| cost per sweep | 3 · d · m · traj | the same |

**Why it helps.** The minimum of a noisy curve is biased downwards (the winner's curse). v comes from trajectories
that played no part in choosing u_A, so given u_A it is unbiased for the true change. A step is taken only when an
independent estimate says it helps. Steps that only follow the twin's noise are then mostly refused.

**What it does not fix.** The training points are still the same 64. The ceiling that 64 points put on
generalisation (W12, reading R1) is untouched. Each choice also uses fewer trajectories than E4's (16 rather than 32),
so u_A is noisier than E4's u.

**Expectation, stated before the run.** At best E4v ties C0 at L 8, because C0 itself stalls after 510 loops. This is
an expectation, not a result.

**Records.**

- Kind "s2re4", so the frozen W11 scorer counts E4v as its E4 role unchanged.
- New fields: `variant` = "e4v", `quarter_traj`, `n_params`, `accepted_per_sweep` and `brier_change_selected_per_sweep`.
- `brier_change_per_sweep` holds the checked changes v of the accepted steps. These are chosen by their own sign, so
  their sum is optimistic too. The realised change is measured as in W12.

## 2. The match, fixed now

| item | value |
|---|---|
| tasks | **fresh teachers 10, 11, 12** × angles 0.3, 1.0, 2.0 × L 8 (9 tasks). Teachers 7-9 have been seen and are not reused |
| arms | Z (s2re4, sweeps 0); C0 (`toqb.s2rc_ckpt`, seed 201, init 0, loops 2,000, checkpoints 510 / 1,020 / 1,530); E4v (s2re4, traj 32, sweeps "budget" (3 at L 8), checkpoints, twin seed = teacher seed, `"variant": "e4v"`) |
| everything else | as the fruit match's plans: task fields, predict block, stand-in, device snapshot, PSF arm; only the teacher seed, the predict seed derived from it as before, and the variant change |
| scoring | `toqb/match_score_fruit.py`, **SHA-256 29a152d1…, unchanged**, on a directory holding only these runs |
| headline | W11's F1: per group (angle, L), Holm over groups; "won in the fruit zone" at a group = E4v vs C0 WIN and E4v vs Z WIN at f_min (sweep 1 = loop 510) |
| after | **no further version, whatever the result.** 0 of 3 groups: "no early advantage for E4 at L 8 on this stand-in, in two versions (E4, E4v)". 1 or more groups: the groups are reported as they came, and any next step is a new owner decision |

**Reported only:**

- F2 to F5, as W11.
- E4v's accepted share per sweep.
- W12's realised / claimed ratio, measured on the E4v runs.

## 3. Points for the owner to decide

| # | question | options | recommendation |
|---|---|---|---|
| 1 | F3 seeds for E4v | (a) add C0 202 / 203 and E4v twin seeds 1010 / 2010 on (1.0, L 8, teacher 10): 4 runs, about +30 min; (b) none | (a): E4v's seed spread is unknown, and a TIE or WIN cannot be read without it |
| 2 | plain E4 on teachers 10-12, for attribution | (a) 9 runs in a separate directory, scored separately by the same frozen scorer, reported beside E4v, never a headline: about +1 h; (b) none | (a): if E4v wins, it tells whether the change or the teachers did it |
| 3 | GPU time | 27 runs (+4, +9) | from the fruit match (31 runs in 3 h 33 min at PAR 6), about 3 h, or about 4.5 h with both |

## 4. Vanity and essential figures

| | figure |
|---|---|
| Vanity | E4v's largest single-task gain over C0 at f_min |
| Essential | all 3 groups' F1 verdicts as they came, with mean CE gains and 99 % CIs; the peel; the realised / claimed ratio; one stand-in, simulation, fresh teachers 10-12 |

## 5. Files

| file | content |
|---|---|
| `toqb/s2re4v.py` | `quarter_seed`, `delta_val`, `select_verify` (numpy and `toqb.s2re` only) |
| `toqb/s2re4_run.py` | the runner with the `variant` branch. The default path is E4's code unchanged. Patched from SHA-256 4a9e5964… (pack 9); `s2re4_run_e4v.diff` is the diff, if home's copy has moved |
| `tests/test_s2re4v.py` | numpy only: the check is unbiased and the selection is not (Monte Carlo), noiseless quarters reproduce E4's step, a contrary check refuses the step, flat curves, seeds, input errors |
| `tests/test_e4v_runner.py` | needs PSF, like `test_fruit.py`: the default is E4 exactly, e4v's cost equals E4's, checkpoint costs, fields, input errors. `tests/test_fruit.py` must still pass |
