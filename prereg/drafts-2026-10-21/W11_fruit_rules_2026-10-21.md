# W11. The fruit match: decision rules, fixed before the results (2026-10-21)

**Status.** Written at the workplace on 2026-10-21 at about 05:40 CEST, before any result of the fruit match. It is
proposed for the owner. The code is `toqb/match_score_fruit.py`, with tests in `tests/test_match_score_fruit.py`;
it reuses W8's parts from `toqb/match_score.py` (SHA-256 aa40de43…, unchanged). It was syntax-checked only; home runs
the tests. **Fix this file and the code by SHA-256 before the first record is read.**

**Scope.** As home's message of 05:3x says: the short version, TOQB `69c1b14`.

- **Tasks:** angles 0.3, 1.0 and 2.0 at L 8, with fresh teachers 7, 8 and 9. That makes 9 tasks.
- **F3 runs:** extra seeds on (angle 1.0, L 8, teacher 7).
- **L 16 is not run.** The code handles any (angle, L) groups present, so an L 16 group would be scored the same way.

## 1. Runs used

**Roles.**

- **Z:** θ = 0, no training (`s2re4`, sweeps 0).
- **E4:** `s2re4` with sweep checkpoints.
- **C0:** `s2rc` from `toqb.s2rc_ckpt`, starting at θ = 0, with loop checkpoints.

**Headline runs per task:** C0 with training seed 201, and the E4 run whose twin seed equals the teacher seed. Any
other C0 or E4 run of the task is used for F3 only. A task without these runs is a STOP.

**Matched budget points.** Points are matched by `train_traj_circuits`, exactly; a mismatch is a STOP.

| E4 | C0 | share of C0's budget |
|---|---|---|
| sweep 1 (1,044,480) | loop 510 | 25.5 % |
| sweep 2 | loop 1,020 | 51.0 % |
| sweep 3 | loop 1,530 | 76.5 % |
| – | loop 2,000 (the peel) | 100 % |

## 2. Statistics (W8's, unchanged)

- **Per-point CE** on the stand-in, from its exact P(1) (`standin_p1`), with toqb.s2r2's formula.
- **Per task, X against Y at one point:**
  - a two-sided Wilcoxon signed-rank test on d_i = CE_i(Y) − CE_i(X);
  - Holm over all tasks of that comparison at that point;
  - **WIN / LOSS / TIE** by the Holm-adjusted p < 0.01 and the sign of mean(d).
- **Accuracy:** an exact McNemar test, secondary.

## 3. F1, the headline: one per group, every group reported

The comparison is made at **f_min**: E4's first sweep against C0 at exactly the same cost (25.5 % at L 8).

**Groups.** A group is g = (angle, L): here 0.3 / L 8, 1.0 / L 8 and 2.0 / L 8, with 3 tasks each.

**Group verdict, for each comparison (E4 vs C0, E4 vs Z):**

- Stouffer's Z over the group's tasks, with a two-sided p, and Holm over the groups.
- **WIN** if the adjusted p < 0.01, Z > 0 and no task in the group LOSS.
- **LOSS** if the adjusted p < 0.01, Z < 0 and no task WIN.
- **MIXED** if the group has both task WINs and task LOSSes.
- **TIE** otherwise.

> **"Won in the fruit zone" at a group** is written only if, at f_min, E4 against C0 is a WIN **and** E4 against Z is
> a WIN for that group.
>
> The headline is the list of all groups' results, written as "won in k of 3 groups", naming them. No group is
> singled out after the fact.

**The two options asked for, and the recommendation:**

| | per group (recommended) | pooled over all tasks |
|---|---|---|
| what it says | where on the difficulty ladder E4 wins early, and where not | whether E4 wins early on average over the ladder |
| fit with W9 option C (the ladder) | direct: the ladder exists to show how the advantage changes with difficulty | loses that information |
| angle 0.3, if θ = 0 is strong | that group can fail on "E4 vs Z" (training below doing nothing) without hiding wins at 1.0 and 2.0; the failure is a finding, written as such | a loss at 0.3 makes the pooled result MIXED or TIE, so a real early win elsewhere disappears, or is diluted |
| lane risk | none if every group is reported and none is chosen afterwards; Holm over groups pays for having three | none |
| multiplicity | Holm over 3 groups | one test |

**Recommendation: per group.** The pooled verdict is still computed and shown, as a reported line and not the
headline.

**Angle 0.3, written down now.** If E4 against Z is a LOSS at 0.3, that group's result is "not won: E4's first sweep
is below doing nothing". It is reported as is, alongside C0 against Z at the same point. It changes nothing in the
other groups. It shows, as the noiseless rounds suggested, that training from a strong start can damage it.

## 4. Reported only (never a headline)

| item | content |
|---|---|
| F2 | the same statistics at every matched point (sweeps 1-3 against 510 / 1,020 / 1,530 loops), per group and pooled; and **the peel**: E4's last sweep (76.5 %) against C0's full 2,000 loops, labelled as unequal cost |
| F3 | (1.0, L 8, teacher 7): C0 seeds 201 / 202 / 203 and E4 twin seeds 7 / 1007 / 2007; the SD over seeds of the stand-in CE (exact P(1) mean and shots) at every point. Three runs give a spread, not a test |
| F4 | every run and every point (Z, C0, E4, extra seeds): stand-in CE inside the twin's 99 % interval, the count, and an exact two-sided binomial test against 0.99. The points of one run are not independent, so the p is indicative only |
| F5 | for every E4 run, whether its stand-in CE (exact P(1) mean) is non-increasing over its sweeps; the rises are listed. E4's guarantee is on the twin's training loss, not on the stand-in's test CE |

## 5. Vanity and essential figures

| | figure |
|---|---|
| Vanity | the largest single-task CE gain of E4 over C0 at f_min |
| Essential | the per-group headline (all groups, as they came), with mean CE gains and 99 % CIs; the peel as it came; one stand-in, PSF arm only, simulation, fresh teachers 7-9 |

## 6. Points for the owner to decide

1. **The headline per group** (recommended) or pooled.
2. **Angle 0.3's rule:** a LOSS against Z is reported as "not won", and it does not affect the other groups.
3. **The headline condition:** E4 > C0 and E4 > Z at f_min, as instruction 9 states.
4. **F4's binomial test:** kept as indicative, given the dependence between checkpoints of one run.
