# The fruit match, 2026-10-21: scored by the fixed W11 rules

Pod H100, 05:37:54 to 09:11:03 CEST, toqb 69c1b14, `gpu/fruit_match.sh` (owner's short version): Z, E4
(`toqb.s2re4_run`, checkpoints) and C0 (`toqb.s2rc_ckpt`, checkpoints) from theta = 0, angles 0.3, 1.0, 2.0 at L 8,
fresh teachers 7, 8, 9, PSF arm, stand-in snapshot:marrakesh; F3 extra seeds on (1.0, L 8, teacher 7); 31 runs.
Scored once with `toqb/match_score_fruit.py` at the SHA-256 fixed at 05:41 CEST, before the first record existed
(29a152d1…a8d1; W11 03bb0c2d…2572; W8's match_score.py aa40de43…e122; `prereg/drafts-2026-10-21/W11_FIXED.md`).
`score.md`, `score.json`; raw records in `pod/` (pod paths redacted to `<pod>/`).

## Headline (F1: E4's first sweep against C0 at exactly the same cost, 25.5 % of C0's budget)

**Won in the fruit zone in 0 of 3 groups.**

| group | E4 vs C0 | E4 vs theta = 0 |
|---|---|---|
| angle 0.3, L 8 | LOSS (Stouffer Z -8.17) | LOSS (Z -10.67) |
| angle 1.0, L 8 | LOSS (Z -8.35) | WIN (Z +6.61) |
| angle 2.0, L 8 | TIE (Z +1.40) | WIN (Z +11.23) |

## Reported (F2 to F5)

- F2: at every later matched point E4 against C0 gets worse (pooled Z -8.73, -11.01, -16.20 at 25.5, 51.0 and
  76.5 % of the budget); the peel (E4's last sweep against C0's full budget) is a pooled LOSS (Z -18.30), 8 of 9
  tasks LOSS.
- F3 (teacher 7, angle 1.0): E4's spread over its twin seeds is larger than C0's over its seeds (SD of the stand-in CE
  0.0074 / 0.0093 / 0.0133 against 0.0043 / 0.0038 / 0.0057 at the same costs). E4's determinism does not survive
  trajectory noise: its only randomness, the twin's trajectories, moves it more than C0's own draws move C0.
- F4: the prediction layer, 86 of 86 run-points inside the twin's 99 % CE interval (Z 9/9, C0 44/44, E4 33/33).
- F5: E4's stand-in CE rises over its sweeps in 7 of 11 runs.

## Reading

- Vanity: E4 beats doing nothing at angles 1.0 and 2.0 (CE gains up to +0.22 on teacher 7 at 2.0), and its single
  best task against C0 is a WIN (teacher 8, angle 2.0: +0.022 CE, +0.164 accuracy).
- Essential: under trajectory noise E4 is not ahead of C0 early, and it falls further behind with budget. The
  convergence guarantee holds on the twin's estimated training loss only; the estimate's selection on noise (found in
  the test match's L 16 diagnosis) shows here as rising stand-in CE and a larger seed spread. The declared fruit was
  not there for E4 under noise. What held in every run is the prediction layer.
