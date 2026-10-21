# The fruit match: E4 against C where the formula has a guarantee (design draft, 2026-10-21)

**Status.** Draft for the owner. Nothing is run until the owner fixes the scope. Rules follow W8's machinery; the
decision rules are fixed by SHA-256 before the first record is read, like W8.

## Why (owner, 2026-10-21)

"Eat the fruit, leave the peel": specialise where the formula wins by construction and cut the rest, but declare the
zone before the results (otherwise it is a lane). The zones:

| zone | content | E4's guarantee |
|---|---|---|
| fruit | how fast and how surely training converges for a given cost; how well the twin predicts | each step is the exact minimum along its direction, u = 0 included, so the training loss never rises (exact twin); with trajectory noise the coefficients are unbiased, so it falls on average |
| peel | the final test quality at a large budget | none, for any method: 64 training points against 170 (L 8) or 330 (L 16) parameters; information, not method, limits it |

Evidence before this design: noiseless (L 8, angle 1.0, teachers 4 to 6), E4 at a third of C0's evaluations matched or
beat C0's full-budget accuracy on all three; on the twin (the match of 2026-10-21, L 8), at the full budget E4 and C0
tie on the fresh teachers. Whether the early advantage survives trajectory noise is not known: this match measures it.

## Claims, declared in advance

- **F1 (headline): equal cost, early budget.** At the first budget point f_min (E4's first sweep; see Tasks), E4
  against C0 at exactly the same cost, per point on the stand-in, with W8's
  statistics (Wilcoxon per task, Holm, Stouffer overall, alpha 0.01). **"Won in the fruit zone"** is written only if,
  on the fresh tasks, F1 is an overall WIN and E4 at f_min against Z (theta = 0) is an overall WIN.
- **F2 (reported, not a claim): the cost curve.** E4 against C0 at every matched budget point, same statistics. The full budget is the peel: reported as it comes, never a headline.
- **F3 (reported): reproducibility.** On one cell (angle 1.0, L 8, teacher 7), C0 with seeds 201, 202, 203 and E4 with
  twin seeds 7, 1007, 2007 (E4's only randomness is the twin's trajectories): the spread (standard deviation) of the
  stand-in CE over the three. Three runs per arm give a spread, not a test.
- **F4 (reported): the prediction layer.** For every run, the stand-in CE inside the twin's 99 % interval: the count
  and the binomial check against 99 %.
- **F5 (reported): E4's convergence on the stand-in.** Whether E4's stand-in CE is non-increasing over its fractions.

## Tasks (W9 option C, owner 2026-10-21: the fixed ladder, every result reported)

- Teacher angles 0.3, 1.0, 2.0; fresh teacher seeds 7, 8, 9 (seeds 4 to 6 have been seen). Arms: Z, E4, C0 (PSF arm
  only). Sizes as today: 64 training, 500 test points, T_pred 1,024, R 20,000, stand-in snapshot:marrakesh.
- **Budget points matched exactly.** One E4 sweep costs 3 x d x 64 x 32 trajectory-circuits (L 8: 1,044,480; L 16:
  2,027,520); one C0 loop costs 16 x 4 x 32 = 2,048. The comparison points are E4's sweeps and C0 at the same cost:
  L 8: sweeps 1 / 2 / 3 against 510 / 1,020 / 1,530 loops (25.5 / 51.0 / 76.5 % of C0's budget); L 16: sweeps 1 / 2
  against 990 / 1,980 loops (49.5 / 99.0 %). f_min is the first point (L 8: 510 loops; L 16: 990). C0's full 2,000
  loops is also run and reported (the peel).
- **Checkpoints, not extra runs.** Each run predicts and verifies on the stand-in at every budget point on the way
  (C0 after 510, 1,020, 1,530 and 2,000 loops at L 8; E4 after each sweep), so a run costs its full training plus a
  few predictions. C0's checkpoints come from `toqb/s2rc_ckpt.py`, a copy of design C's loop with checkpoints added;
  `toqb.s2rc` itself is not changed, and a test requires the copy's final parameters to equal s2rc's on the same plan
  (bit for bit on the CPU). Its training random numbers drive only the point and direction draws and its twin seeds
  depend on the loop number, so a checkpoint is exactly the state of a shorter run.

## Scope and cost (H100 at $3.99 per hour; from the match of 2026-10-21, 6 parallel heavy runs took about 1 h at
L 8 and 1.7 h at L 16; with checkpoints add about 15 to 25 minutes of predictions per run; estimates, not measured)

| option | cells (3 fresh teachers each) | GPU hours (H100) | cost |
|---|---|---|---|
| full | 3 angles x L 8 and L 16, F3 | about 9 | about $36 |
| **recommended** | 3 angles at L 8, angle 1.0 at L 16, F3 | about 6 | about $24 |
| small | 3 angles at L 8 only, F3 | about 4 | about $16 |

An A100 ($1.79) takes about 1.5 times as long for about 0.65 times the cost.

## Division of work

- Workplace: F1 to F5 as a W8-style rule text and `toqb/match_score_fruit.py` (fractions as a task dimension), with
  tests, before the first record.
- Home: the pod script (plans for every cell and fraction, the ordering Z first, then L 8, then L 16), the run, the
  scoring and the record.
