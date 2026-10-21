# W8. Test match E4 against C: decision rules, fixed before the results (2026-10-21)

**Status.** Written at the workplace on 2026-10-21, about 02:00 CEST, before any result of the match. Proposed for
the owner. The code is `toqb/match_score.py`, with tests in `tests/test_match_score.py`; it was syntax-checked only,
and home runs the tests. **Fix this file and the code by SHA-256 before the first run record is read.**

## 1. What is compared

| comparison | role in the verdict |
|---|---|
| E4 against C0 (C's training from θ = 0, the same budget) | **headline** |
| E4 against Z (θ = 0, no training) | **headline** |
| C0 against Z | reported only |

- **A task** is (teacher_seed, teacher_angle, L, arm): here teachers 4, 5 and 6, angle 1.0, L 8 and 16, PSF arm only.
  That makes 6 tasks.
- **Fresh tasks.** A task is fresh unless its (teacher_seed, angle) was used while E4 was developed. Teacher 4 at
  angle 1.0 was used in the noiseless rounds of 2026-10-20, so the headline uses **teachers 5 and 6** (4 tasks).
  Teacher 4 is scored and shown, but marked as not fresh. This follows the owner's "new seeds and teachers".

## 2. Statistics

- **Unit: the test point** (500 per task; the same points for every arm, which the code checks).
- **Per-point CE on the stand-in** uses the stand-in's exact P(1) (`rehearsal.standin_p1`), with toqb.s2r2's
  formula: p = 1 − P(1), clipped to [1e-4, 1 − 1e-4]; −log p for y = +1, −log(1 − p) for y = −1.
  - Per-point shot counts are not stored, so the exact P(1) is used.
  - The job-level CE and accuracy with shots (`rehearsal.ce`, `rehearsal.acc`) are shown beside it.
- **Per task, X against Y:**
  - d_i = CE_i(Y) − CE_i(X); positive favours X.
  - A two-sided Wilcoxon signed-rank test: normal approximation, tie-corrected, zeros dropped.
  - Holm over the tasks of that comparison, computed separately for "all" and for "fresh".
  - **WIN** if the Holm-adjusted p < 0.01 and mean(d) > 0; **LOSS** if adjusted p < 0.01 and mean(d) < 0; otherwise
    **TIE**.
- **Overall, per comparison.** Stouffer's Z = Σ z_t / √T over the tasks' signed-rank z, with a two-sided p.
  - **WIN:** p < 0.01, Z > 0 and no task LOSS.
  - **LOSS:** p < 0.01, Z < 0 and no task WIN.
  - **MIXED:** some task WIN and some task LOSS.
  - **TIE:** otherwise.
- **Why not a sign test over tasks:** with 3 (or 4) tasks its smallest p is 0.125 (0.0625), so it cannot reach 0.01.
- **Accuracy (secondary).** Per-point strict correctness from the exact P(1); an exact McNemar test on the
  discordant points; Holm over the tasks; the same verdict words. It is not part of the headline. If it disagrees
  with CE, both are shown.

## 3. The headline (owner's criterion of 2026-10-21)

> **"Won from lane 1"** is written only if, on the fresh tasks, E4 against C0 is an overall WIN **and** E4 against Z
> is an overall WIN.

Anything else is written as it is: tie, loss or mixed, with the numbers.

**Checks shown with the headline, not folded in:**

- **Budget:** E4's training cost (trajectory-circuits) is at most C0's (2,000 × 16 × 4 × 32 = 4,096,000) in every
  task.
- **Start:** both start from θ = 0.

## 4. Where each figure goes

| place | content |
|---|---|
| Headline line | YES / NO, with the two fresh-task overall verdicts |
| Per task and arm | CE (exact P(1)); accuracy (exact, strict); CE / accuracy with shots; **prediction layer**: stand-in CE inside the twin's 99 % interval, twin–stand-in P(1) rms; training cost |
| Per comparison | the overall verdict (all, fresh), Stouffer Z and p; per task: mean CE gain with 99 % CI, Wilcoxon p, Holm p, verdict, accuracy difference, McNemar b / c, accuracy verdict |
| Vanity | the best single task's accuracy gain of E4 over C0 |
| Essential | the fresh-task overall verdicts with their mean CE gains and 99 % CIs; one stand-in, PSF arm only, simulation, 3 teachers × 2 depths, equal budget, same start |

## 5. Points for the owner to decide

1. **Teacher 4 excluded from the headline** as a development task (the default `--dev 4:1.0`). Proposed: yes.
2. **α = 0.01, two-sided, Holm per comparison**, with Stouffer for the overall verdict.
3. **CE from the exact P(1)** as the primary per-point quantity, with accuracy secondary.
4. **The headline needs both** E4 > C0 and E4 > Z, on fresh tasks.
