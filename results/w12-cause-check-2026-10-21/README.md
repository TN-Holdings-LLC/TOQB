# W12 cause check, part 1: the noiseless quantities on the fruit match (2026-10-21)

`toqb/w12_check.py noiseless` on the fruit match's 31 records (86 points): T1 (64 training points) and T3 (500 test
points), exact <Z0>, at every recorded theta. `noiseless_fruit.jsonl`, `table_fruit_noiseless.md` (T2 and the
realised / claimed ratio on the twin are pending: they run on the pod after the E4v match). Part 2 (the test match,
L 8 and L 16) is running.

## Means over the 9 headline runs per arm (teachers 7-9, angles 0.3 / 1.0 / 2.0, L 8)

| arm | budget | T1 Brier / acc (training) | T3 CE / acc (test) |
|---|---|---|---|
| Z | 0 | 0.224 / 0.681 | 0.6946 / 0.654 |
| C0 | 25.5 % | 0.126 / 0.845 | 0.5120 / 0.747 |
| C0 | 51.0 % | 0.115 / 0.889 | 0.4996 / 0.766 |
| C0 | 76.5 % | 0.107 / 0.899 | 0.4982 / 0.764 |
| C0 | 100 % | 0.108 / 0.868 | 0.4984 / 0.758 |
| E4 | 25.5 % | 0.133 / 0.851 | 0.5202 / 0.730 |
| E4 | 51.0 % | 0.116 / 0.892 | 0.5138 / 0.744 |
| E4 | 76.5 % | 0.128 / 0.849 | 0.5446 / 0.695 |

E4's claimed cumulative training change (T4, on the twin) against its noiseless realised change (T1 at the sweep minus
T1 at theta = 0), means over the 9 runs: sweep 1 -0.075 / -0.091; sweep 2 -0.112 / -0.108; sweep 3 -0.157 / -0.097.
At angle 0.3 the realised change is positive (worse than theta = 0 on the training points) in 2 of 3 runs at sweep 3.
The two scales differ (the twin's noise shrinks the outputs, so twin changes are smaller than noiseless ones); the
like-for-like ratio is T2's.

## Readings (W12 section 4)

- R1, a ceiling shared by the methods: holds. C0 fits the training points (accuracy 0.85 to 0.90) and its test CE
  stops moving after 51 % of the budget (0.4996, 0.4982, 0.4984).
- R2, E4's optimism: holds from sweep 2 on. E4's claim keeps falling while its real training fit stops improving at
  sweep 2 and gets worse at sweep 3 (Brier 0.116 to 0.128, test CE 0.514 to 0.545): the steps after sweep 1 mostly
  follow the twin's noise.
- R3, overfitting: mild (C0 training 0.87 to 0.90 against test 0.76).
- R4, a flat landscape: no (every arm moves T1 far from theta = 0).
- For the workplace's hybrid ② (handover 3b): C0 fits the training points well and the ceiling dominates, so by the
  handover's own rule ② is skipped.
