# E4 against C0 (and the theta = 0 control): match score

Rules: W8 (2026-10-21), alpha = 0.01, Holm over tasks per comparison; development tasks excluded from the headline: 4:1.0. Truth tier: stand-in (simulation), not a device.

## Headline (owner's criterion)

- Won from lane 1: **NO** (fresh tasks: E4 vs C0 TIE, E4 vs Z WIN).
- E4 within C0's training budget in every task: True; fresh tasks 4 of 6.

## Per task and arm (stand-in)

| teacher | angle | L | fresh | arm | CE (exact P(1)) | acc (exact, strict) | CE / acc (shots) | CE in 99 % (prediction layer) | P(1) rms | training cost (traj x circuits) |
|---|---|---|---|---|---|---|---|---|---|---|
| 4 | 1.0 | 8 | no | Z | 0.6567 | 0.570 | 0.6572 / 0.575 | True | 0.0099 | 0 |
| 4 | 1.0 | 8 | no | E4 | 0.6102 | 0.764 | 0.6100 / 0.754 | True | 0.0084 | 3,133,440 |
| 4 | 1.0 | 8 | no | C0 | 0.6227 | 0.674 | 0.6226 / 0.678 | True | 0.0093 | 4,096,000 |
| 4 | 1.0 | 16 | no | Z | 0.6827 | 0.532 | 0.6817 / 0.529 | True | 0.0118 | 0 |
| 4 | 1.0 | 16 | no | E4 | 0.6884 | 0.544 | 0.6891 / 0.538 | True | 0.0033 | 4,055,040 |
| 4 | 1.0 | 16 | no | C0 | 0.6847 | 0.544 | 0.6841 / 0.567 | True | 0.0069 | 4,096,000 |
| 5 | 1.0 | 8 | yes | Z | 0.6270 | 0.562 | 0.6285 / 0.567 | True | 0.0103 | 0 |
| 5 | 1.0 | 8 | yes | E4 | 0.5198 | 0.806 | 0.5216 / 0.797 | True | 0.0097 | 3,133,440 |
| 5 | 1.0 | 8 | yes | C0 | 0.5209 | 0.790 | 0.5217 / 0.801 | True | 0.0096 | 4,096,000 |
| 5 | 1.0 | 16 | yes | Z | 0.6766 | 0.516 | 0.6777 / 0.489 | True | 0.0108 | 0 |
| 5 | 1.0 | 16 | yes | E4 | 0.6937 | 0.460 | 0.6970 / 0.466 | True | 0.0030 | 4,055,040 |
| 5 | 1.0 | 16 | yes | C0 | 0.6750 | 0.536 | 0.6759 / 0.552 | True | 0.0082 | 4,096,000 |
| 6 | 1.0 | 8 | yes | Z | 0.5877 | 0.614 | 0.5876 / 0.602 | True | 0.0098 | 0 |
| 6 | 1.0 | 8 | yes | E4 | 0.5258 | 0.790 | 0.5272 / 0.784 | True | 0.0099 | 3,133,440 |
| 6 | 1.0 | 8 | yes | C0 | 0.5137 | 0.784 | 0.5146 / 0.783 | True | 0.0104 | 4,096,000 |
| 6 | 1.0 | 16 | yes | Z | 0.6289 | 0.536 | 0.6264 / 0.589 | True | 0.0122 | 0 |
| 6 | 1.0 | 16 | yes | E4 | 0.6131 | 0.506 | 0.6121 / 0.584 | True | 0.0117 | 4,055,040 |
| 6 | 1.0 | 16 | yes | C0 | 0.6142 | 0.506 | 0.6125 / 0.605 | True | 0.0114 | 4,096,000 |

## E4 vs C0

- Overall, all tasks: TIE (Stouffer Z -1.99, p 0.0460); fresh tasks: TIE (Z -2.47, p 0.0136).

| teacher | angle | L | fresh | mean CE gain (99 % CI) | Wilcoxon p | Holm p (all) | verdict (all / fresh) | acc diff | McNemar b / c | acc verdict (all) |
|---|---|---|---|---|---|---|---|---|---|---|
| 4 | 1.0 | 8 | no | +0.0126 (-0.0008, +0.0259) | 8.71e-02 | 2.61e-01 | TIE / - | +0.090 | 82 / 37 | WIN |
| 4 | 1.0 | 16 | no | -0.0037 (-0.0132, +0.0059) | 9.61e-02 | 2.61e-01 | TIE / - | +0.000 | 50 / 50 | TIE |
| 5 | 1.0 | 8 | yes | +0.0011 (-0.0056, +0.0079) | 4.80e-01 | 4.80e-01 | TIE / TIE | +0.016 | 43 / 35 | TIE |
| 5 | 1.0 | 16 | yes | -0.0188 (-0.0352, -0.0023) | 3.20e-03 | 1.60e-02 | TIE / LOSS | -0.076 | 131 / 169 | TIE |
| 6 | 1.0 | 8 | yes | -0.0121 (-0.0199, -0.0042) | 3.05e-07 | 1.83e-06 | LOSS / LOSS | +0.006 | 40 / 37 | TIE |
| 6 | 1.0 | 16 | yes | +0.0011 (-0.0038, +0.0060) | 1.52e-02 | 6.07e-02 | TIE / TIE | +0.000 | 9 / 9 | TIE |

## E4 vs Z

- Overall, all tasks: WIN (Stouffer Z 10.20, p 0.0000); fresh tasks: WIN (Z 12.19, p 0.0000).

| teacher | angle | L | fresh | mean CE gain (99 % CI) | Wilcoxon p | Holm p (all) | verdict (all / fresh) | acc diff | McNemar b / c | acc verdict (all) |
|---|---|---|---|---|---|---|---|---|---|---|
| 4 | 1.0 | 8 | no | +0.0465 (+0.0196, +0.0734) | 4.58e-02 | 1.37e-01 | TIE / - | +0.194 | 141 / 44 | WIN |
| 4 | 1.0 | 16 | no | -0.0057 (-0.0253, +0.0140) | 1.68e-01 | 1.68e-01 | TIE / - | +0.012 | 40 / 34 | TIE |
| 5 | 1.0 | 8 | yes | +0.1072 (+0.0856, +0.1288) | 8.18e-29 | 4.91e-28 | WIN / WIN | +0.244 | 145 / 23 | WIN |
| 5 | 1.0 | 16 | yes | -0.0171 (-0.0372, +0.0030) | 8.10e-02 | 1.62e-01 | TIE / TIE | -0.056 | 136 / 164 | TIE |
| 6 | 1.0 | 8 | yes | +0.0619 (+0.0448, +0.0790) | 3.34e-18 | 1.67e-17 | WIN / WIN | +0.176 | 130 / 42 | WIN |
| 6 | 1.0 | 16 | yes | +0.0159 (+0.0093, +0.0224) | 3.41e-10 | 1.36e-09 | WIN / WIN | -0.030 | 9 / 24 | TIE |

## C0 vs Z

- Overall, all tasks: WIN (Stouffer Z 10.72, p 0.0000); fresh tasks: WIN (Z 13.07, p 0.0000).

| teacher | angle | L | fresh | mean CE gain (99 % CI) | Wilcoxon p | Holm p (all) | verdict (all / fresh) | acc diff | McNemar b / c | acc verdict (all) |
|---|---|---|---|---|---|---|---|---|---|---|
| 4 | 1.0 | 8 | no | +0.0339 (+0.0156, +0.0523) | 1.81e-02 | 5.42e-02 | TIE / - | +0.104 | 114 / 62 | WIN |
| 4 | 1.0 | 16 | no | -0.0020 (-0.0170, +0.0130) | 2.48e-02 | 5.42e-02 | TIE / - | +0.012 | 47 / 41 | TIE |
| 5 | 1.0 | 8 | yes | +0.1061 (+0.0858, +0.1263) | 2.15e-31 | 1.29e-30 | WIN / WIN | +0.228 | 141 / 27 | WIN |
| 5 | 1.0 | 16 | yes | +0.0017 (-0.0045, +0.0079) | 5.52e-01 | 5.52e-01 | TIE / TIE | +0.020 | 36 / 26 | TIE |
| 6 | 1.0 | 8 | yes | +0.0740 (+0.0570, +0.0909) | 4.25e-23 | 2.13e-22 | WIN / WIN | +0.170 | 120 / 35 | WIN |
| 6 | 1.0 | 16 | yes | +0.0147 (+0.0085, +0.0210) | 2.27e-07 | 9.09e-07 | WIN / WIN | -0.030 | 14 / 29 | TIE |

## Vanity and essential figures

| | figure |
|---|---|
| Vanity | the best single task's accuracy gain of E4 over C0 (fill from the table above) |
| Essential | the fresh-task overall verdicts above (E4 vs C0, E4 vs Z), with the mean CE gains and 99 % CIs; one stand-in, PSF arm only, simulation, 3 teachers x 2 depths; equal training budget and the same start |

