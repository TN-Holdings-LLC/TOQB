# E4 against C0, noiseless, same start, same cost (2026-10-21; exploratory preview, not the match, not scored by W8)

Cloud CPU, exact <Z0>, L 8, teacher angle 1.0, teacher seeds 4, 5, 6 (4 was used in E4's development on
2026-10-20), 64 training and 500 test points. Owner principle of 2026-10-21: same start (theta = 0), same cost.

- **C0**: design C's update (8 pairs, batch 4, h 0.1, lr 0.4, 2,000 loops, seed 201) from theta = 0;
  128,000 circuit evaluations.
- **E4**: `toqb.s2re.train_e4`, the exact quartic Brier minimum per parameter, fixed order from theta = 0; the whole
  sweeps that fit in 128,000 evaluations (5 sweeps, 108,864 evaluations, about 85 % of C0's; the 64 re-evaluations of
  the training outputs at the start of each sweep are not counted).
- **theta = 0**: no training.

Script `round6.py`; job lists `jobs6.txt`, `jobs6b.txt`. The first E4 runs of teachers 4 and 5 crashed on a parameter
with no effect (all coefficients below 1e-14 relative; `*_crashed.txt`); `trig2_min` now keeps such a parameter still
(tested), and the reruns are `r6b_*`. Teacher 4's theta = 0 value is from 2026-10-20 (round 2).

## Test accuracy / CE (500 points; one standard error of an accuracy about 0.02)

| teacher seed | theta = 0 | C0 (128,000 evaluations) | E4 sweep 2 (43,584) | E4 sweep 5 (108,864) |
|---|---|---|---|---|
| 4 (development) | 0.596 / 0.764 | 0.698 / **0.536** | 0.722 / 0.585 | **0.762** / 0.563 |
| 5 | 0.590 / 0.766 | 0.816 / 0.423 | 0.876 / 0.404 | **0.880 / 0.385** |
| 6 | 0.624 / 0.627 | 0.798 / 0.404 | 0.808 / 0.433 | **0.830 / 0.398** |

Reading (no test; the match on the twin with W8's rules decides):

- E4 is above theta = 0 everywhere and above C0 in accuracy on all three teachers, at 85 % of C0's evaluations.
- CE: E4 is better on teachers 5 and 6 and worse on teacher 4 (0.563 against 0.536).
- E4 at sweep 2 (a third of C0's evaluations) already matches or passes C0 in accuracy on all three.
- Noiseless only, one C0 seed, one depth.
