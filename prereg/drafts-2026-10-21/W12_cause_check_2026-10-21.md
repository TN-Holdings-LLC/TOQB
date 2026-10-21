# W12. Why E4 did not win early: the one cause check (2026-10-21)

**Status.** Written at the workplace on 2026-10-21 at about 09:30 CEST, after the fruit match was scored (0 of 3
groups; `fruit_match_score_2026-10-21.md`). The owner approved a bounded plan:

1. one cause check (this file);
2. one improved E4, fixed in advance, on fresh teachers, scored by the frozen W11 scorer;
3. if it does not win, stop and report "no early advantage for E4" as it is.

Nothing here trains anything or draws new tasks. Home runs it. The workplace ran nothing.

## 1. Data

- **The fruit match:** 31 runs, TOQB `69c1b14`, L 8, teachers 7-9.
- **The earlier E4 match:** L 8 and L 16, teachers 4-6. This is the data behind home's L 16 table in `cbc00f5`.

Every run record already holds its parameters at every point: `checkpoints[].theta` and `final_mean`, for E4 and for
C0 (`toqb.s2rc_ckpt`). The training points come from `S2.teacher_data2(task)`, as in the runs.

## 2. What to compute, at every recorded point of every run (Z, C0, E4)

| id | quantity | how |
|---|---|---|
| T1 | training Brier and accuracy, **noiseless** | the 64 training points, exact ⟨Z0⟩; Brier = mean(((f − y) / 2)^2), the runs' own scale |
| T2 | training Brier, **exact twin** | the same 64 points on the twin with 1,024 trajectories, seed = predict.seed + 5 (fixed here, not used by any run) |
| T3 | test CE and accuracy, **noiseless** | the 500 test points, exact ⟨Z0⟩, toqb.s2r2's CE |
| T4 | E4's claimed training change | the cumulative sum of `brier_change_per_sweep` |

Already recorded, and to be shown in the same table: the stand-in test CE (`standin_p1`) and the C0 and E4 seed SDs
(F3).

## 3. The table to return (one row per run and point)

| teacher | angle | L | arm | point | cost | T1 Brier / acc | T2 Brier | T4 claimed change | T2 realised change | realised / claimed | T3 CE / acc | stand-in CE |
|---|---|---|---|---|---|---|---|---|---|---|---|---|

- The **realised change** is T2 at the point minus T2 at θ = 0.
- Realised / claimed uses T2, not T1. The claim is made on the twin, so T2 compares like with like.

## 4. Readings, written before the numbers

Every reading is reported. None of them selects anything.

| reading | what the numbers would show |
|---|---|
| **R1. A ceiling shared by the methods** | C0's T1 keeps falling after loop 510, while its stand-in CE moves less than its seed SD (F3) |
| **R2. E4's optimism (winner's curse)** | the realised / claimed ratio for E4 is below 1, with the ratio as the size of the optimism. An unbiased choice of step would give about 1 on average |
| **R3. Overfitting** | T1 falls (the model fits the 64 points) but T3 does not (no gain on new points) |
| **R4. A flat landscape (NIBP type)** | T1 and T2 barely move for every arm |

The readings are not mutually exclusive. The expectation, from the records, is that R1 and R2 both hold at L 8, and
that R1 and R3 hold at L 16. This is an expectation, not a result.

## 5. Vanity and essential figures

| | figure |
|---|---|
| Vanity | the run with the largest claimed E4 training gain |
| Essential | the realised / claimed ratio over all E4 points, every run shown; C0's test CE after loop 510 against its seed SD |
