# The fruit match: E4 against C0 at equal early cost (with the theta = 0 control)

Rules: W11 (2026-10-21), alpha = 0.01; W8's per-point statistics; groups = (angle, layers), Holm over groups. Truth tier: stand-in (simulation), not a device.

## Headline (F1, at f_min = E4's first sweep and C0 at the same cost)

| group (angle, L) | E4 vs C0 | E4 vs Z | won in the fruit zone |
|---|---|---|---|
| 0.3, L8 | LOSS | LOSS | NO |
| 1.0, L8 | LOSS | WIN | NO |
| 2.0, L8 | TIE | WIN | NO |

Won in the fruit zone in 0 of 3 groups.
Pooled over all tasks (reported, not the headline): E4 vs C0 MIXED, E4 vs Z MIXED.

### F1: E4 vs C0

| group (angle, L) | tasks | Stouffer Z | Holm p | verdict |
|---|---|---|---|---|
| 0.3, L8 | 3 | -8.17 | 6.16e-16 | LOSS |
| 1.0, L8 | 3 | -8.35 | 2.04e-16 | LOSS |
| 2.0, L8 | 3 | +1.40 | 1.60e-01 | TIE |

Pooled over all tasks: MIXED (Z -8.73, p 0.0000).

| teacher | angle | L | points | CE X / CE Y | mean CE gain (99 % CI) | Wilcoxon p | Holm p | verdict | acc diff | McNemar b / c | acc verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 7 | 0.3 | 8 | sweep 1 / loop 510 | 0.5766 / 0.5708 | -0.0058 (-0.0144, +0.0028) | 5.12e-03 | 2.05e-02 | TIE | -0.062 | 52 / 83 | TIE |
| 7 | 1.0 | 8 | sweep 1 / loop 510 | 0.6363 / 0.6341 | -0.0022 (-0.0180, +0.0137) | 1.33e-01 | 4.00e-01 | TIE | +0.042 | 86 / 65 | TIE |
| 7 | 2.0 | 8 | sweep 1 / loop 510 | 0.6039 / 0.6066 | +0.0027 (-0.0077, +0.0132) | 3.33e-01 | 5.30e-01 | TIE | +0.042 | 60 / 39 | TIE |
| 8 | 0.3 | 8 | sweep 1 / loop 510 | 0.5433 / 0.5350 | -0.0082 (-0.0134, -0.0030) | 7.24e-06 | 3.83e-05 | LOSS | -0.044 | 21 / 43 | TIE |
| 8 | 1.0 | 8 | sweep 1 / loop 510 | 0.5818 / 0.5607 | -0.0211 (-0.0308, -0.0114) | 6.72e-08 | 4.70e-07 | LOSS | -0.100 | 31 / 81 | LOSS |
| 8 | 2.0 | 8 | sweep 1 / loop 510 | 0.6664 / 0.6881 | +0.0217 (+0.0065, +0.0369) | 6.39e-06 | 3.83e-05 | WIN | +0.164 | 153 / 71 | WIN |
| 9 | 0.3 | 8 | sweep 1 / loop 510 | 0.5690 / 0.5521 | -0.0169 (-0.0231, -0.0107) | 6.65e-12 | 5.32e-11 | LOSS | -0.082 | 22 / 63 | LOSS |
| 9 | 1.0 | 8 | sweep 1 / loop 510 | 0.5606 / 0.5355 | -0.0251 (-0.0362, -0.0140) | 3.90e-14 | 3.51e-13 | LOSS | +0.010 | 63 / 58 | TIE |
| 9 | 2.0 | 8 | sweep 1 / loop 510 | 0.6537 / 0.6527 | -0.0010 (-0.0170, +0.0150) | 2.65e-01 | 5.30e-01 | TIE | +0.008 | 108 / 104 | TIE |

### F1: E4 vs Z

| group (angle, L) | tasks | Stouffer Z | Holm p | verdict |
|---|---|---|---|---|
| 0.3, L8 | 3 | -10.67 | 2.82e-26 | LOSS |
| 1.0, L8 | 3 | +6.61 | 3.76e-11 | WIN |
| 2.0, L8 | 3 | +11.23 | 8.55e-29 | WIN |

Pooled over all tasks: MIXED (Z 4.14, p 0.0000).

| teacher | angle | L | points | CE X / CE Y | mean CE gain (99 % CI) | Wilcoxon p | Holm p | verdict | acc diff | McNemar b / c | acc verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 7 | 0.3 | 8 | sweep 1 / loop 510 | 0.5766 / 0.5461 | -0.0305 (-0.0376, -0.0233) | 9.74e-25 | 8.77e-24 | LOSS | -0.160 | 18 / 98 | LOSS |
| 7 | 1.0 | 8 | sweep 1 / loop 510 | 0.6363 / 0.6633 | +0.0270 (+0.0085, +0.0455) | 1.74e-02 | 5.21e-02 | TIE | +0.112 | 109 / 53 | WIN |
| 7 | 2.0 | 8 | sweep 1 / loop 510 | 0.6039 / 0.8255 | +0.2216 (+0.1633, +0.2799) | 2.27e-21 | 1.81e-20 | WIN | +0.332 | 255 / 89 | WIN |
| 8 | 0.3 | 8 | sweep 1 / loop 510 | 0.5433 / 0.5373 | -0.0060 (-0.0167, +0.0047) | 3.42e-02 | 6.84e-02 | TIE | -0.020 | 41 / 51 | TIE |
| 8 | 1.0 | 8 | sweep 1 / loop 510 | 0.5818 / 0.6450 | +0.0632 (+0.0444, +0.0821) | 9.84e-16 | 6.89e-15 | WIN | +0.120 | 106 / 46 | WIN |
| 8 | 2.0 | 8 | sweep 1 / loop 510 | 0.6664 / 0.6989 | +0.0325 (+0.0111, +0.0539) | 1.70e-06 | 6.80e-06 | WIN | +0.160 | 157 / 77 | WIN |
| 9 | 0.3 | 8 | sweep 1 / loop 510 | 0.5690 / 0.5443 | -0.0248 (-0.0360, -0.0136) | 1.10e-09 | 6.59e-09 | LOSS | -0.124 | 27 / 89 | LOSS |
| 9 | 1.0 | 8 | sweep 1 / loop 510 | 0.5606 / 0.5823 | +0.0216 (+0.0019, +0.0414) | 2.95e-01 | 2.95e-01 | TIE | +0.154 | 120 / 43 | WIN |
| 9 | 2.0 | 8 | sweep 1 / loop 510 | 0.6537 / 0.7462 | +0.0925 (+0.0536, +0.1314) | 2.27e-07 | 1.13e-06 | WIN | +0.128 | 169 / 105 | WIN |

### F1: C0 vs Z

| group (angle, L) | tasks | Stouffer Z | Holm p | verdict |
|---|---|---|---|---|
| 0.3, L8 | 3 | -6.96 | 3.47e-12 | LOSS |
| 1.0, L8 | 3 | +12.77 | 7.21e-37 | WIN |
| 2.0, L8 | 3 | +9.83 | 1.69e-22 | WIN |

Pooled over all tasks: MIXED (Z 9.03, p 0.0000).

| teacher | angle | L | points | CE X / CE Y | mean CE gain (99 % CI) | Wilcoxon p | Holm p | verdict | acc diff | McNemar b / c | acc verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 7 | 0.3 | 8 | sweep 1 / loop 510 | 0.5708 / 0.5461 | -0.0246 (-0.0311, -0.0182) | 8.18e-21 | 6.54e-20 | LOSS | -0.098 | 13 / 62 | LOSS |
| 7 | 1.0 | 8 | sweep 1 / loop 510 | 0.6341 / 0.6633 | +0.0292 (+0.0145, +0.0439) | 2.44e-05 | 9.76e-05 | WIN | +0.070 | 62 / 27 | WIN |
| 7 | 2.0 | 8 | sweep 1 / loop 510 | 0.6066 / 0.8255 | +0.2189 (+0.1575, +0.2803) | 1.53e-17 | 1.07e-16 | WIN | +0.290 | 248 / 103 | WIN |
| 8 | 0.3 | 8 | sweep 1 / loop 510 | 0.5350 / 0.5373 | +0.0022 (-0.0068, +0.0112) | 8.26e-01 | 8.26e-01 | TIE | +0.024 | 40 / 28 | TIE |
| 8 | 1.0 | 8 | sweep 1 / loop 510 | 0.5607 / 0.6450 | +0.0843 (+0.0650, +0.1035) | 1.68e-25 | 1.51e-24 | WIN | +0.220 | 143 / 33 | WIN |
| 8 | 2.0 | 8 | sweep 1 / loop 510 | 0.6881 / 0.6989 | +0.0108 (-0.0037, +0.0253) | 1.87e-01 | 3.74e-01 | TIE | -0.004 | 75 / 77 | TIE |
| 9 | 0.3 | 8 | sweep 1 / loop 510 | 0.5521 / 0.5443 | -0.0079 (-0.0171, +0.0014) | 1.34e-02 | 4.01e-02 | TIE | -0.042 | 33 / 54 | TIE |
| 9 | 1.0 | 8 | sweep 1 / loop 510 | 0.5355 / 0.5823 | +0.0468 (+0.0323, +0.0613) | 8.55e-14 | 5.13e-13 | WIN | +0.144 | 99 / 27 | WIN |
| 9 | 2.0 | 8 | sweep 1 / loop 510 | 0.6527 / 0.7462 | +0.0935 (+0.0601, +0.1270) | 6.96e-13 | 3.48e-12 | WIN | +0.120 | 124 / 64 | WIN |

## F2: every matched point (reported)

- point 1, E4 vs C0: pooled MIXED (Z -8.73); groups: 0.3/L8 LOSS (Z -8.17); 1.0/L8 LOSS (Z -8.35); 2.0/L8 TIE (Z +1.40)
- point 1, E4 vs Z: pooled MIXED (Z 4.14); groups: 0.3/L8 LOSS (Z -10.67); 1.0/L8 WIN (Z +6.61); 2.0/L8 WIN (Z +11.23)
- point 2, E4 vs C0: pooled LOSS (Z -11.01); groups: 0.3/L8 LOSS (Z -10.42); 1.0/L8 LOSS (Z -6.99); 2.0/L8 TIE (Z -1.67)
- point 2, E4 vs Z: pooled MIXED (Z 4.86); groups: 0.3/L8 LOSS (Z -12.79); 1.0/L8 WIN (Z +9.20); 2.0/L8 WIN (Z +12.00)
- point 3, E4 vs C0: pooled LOSS (Z -16.20); groups: 0.3/L8 LOSS (Z -15.89); 1.0/L8 LOSS (Z -5.98); 2.0/L8 LOSS (Z -6.19)
- point 3, E4 vs Z: pooled MIXED (Z 2.56); groups: 0.3/L8 LOSS (Z -16.58); 1.0/L8 WIN (Z +8.49); 2.0/L8 WIN (Z +12.53)

**The peel** (unequal cost: E4's last sweep against C0's full budget): pooled LOSS (Z -18.30).

| teacher | angle | L | points (E4 / C0) | mean CE gain of E4 (99 % CI) | Holm p | verdict |
|---|---|---|---|---|---|---|
| 7 | 0.3 | 8 | sweep 3 / loop 2000 | -0.0209 (-0.0271, -0.0147) | 4.74e-17 | LOSS |
| 7 | 1.0 | 8 | sweep 3 / loop 2000 | -0.0044 (-0.0172, +0.0084) | 8.94e-02 | TIE |
| 7 | 2.0 | 8 | sweep 3 / loop 2000 | -0.0135 (-0.0240, -0.0029) | 6.61e-05 | LOSS |
| 8 | 0.3 | 8 | sweep 3 / loop 2000 | -0.0231 (-0.0322, -0.0139) | 8.51e-17 | LOSS |
| 8 | 1.0 | 8 | sweep 3 / loop 2000 | -0.0203 (-0.0283, -0.0123) | 1.20e-06 | LOSS |
| 8 | 2.0 | 8 | sweep 3 / loop 2000 | -0.0462 (-0.0588, -0.0335) | 7.17e-18 | LOSS |
| 9 | 0.3 | 8 | sweep 3 / loop 2000 | -0.0157 (-0.0218, -0.0096) | 3.37e-12 | LOSS |
| 9 | 1.0 | 8 | sweep 3 / loop 2000 | -0.0218 (-0.0300, -0.0135) | 4.40e-12 | LOSS |
| 9 | 2.0 | 8 | sweep 3 / loop 2000 | -0.0114 (-0.0289, +0.0061) | 1.15e-03 | LOSS |

## F3: spread over seeds (reported)

| task (teacher, angle, L) | arm | cost (traj x circuits) | seeds | mean CE (exact) | SD CE (exact) | SD CE (shots) |
|---|---|---|---|---|---|---|
| 7, 1.0, L8 | C0 | 1,044,480 | [201, 202, 203] | 0.6390 | 0.0043 | 0.0042 |
| 7, 1.0, L8 | C0 | 2,088,960 | [201, 202, 203] | 0.6344 | 0.0038 | 0.0040 |
| 7, 1.0, L8 | C0 | 3,133,440 | [201, 202, 203] | 0.6362 | 0.0057 | 0.0060 |
| 7, 1.0, L8 | C0 | 4,096,000 | [201, 202, 203] | 0.6364 | 0.0040 | 0.0041 |
| 7, 1.0, L8 | E4 | 1,044,480 | [7, 1007, 2007] | 0.6398 | 0.0074 | 0.0073 |
| 7, 1.0, L8 | E4 | 2,088,960 | [7, 1007, 2007] | 0.6369 | 0.0093 | 0.0089 |
| 7, 1.0, L8 | E4 | 3,133,440 | [7, 1007, 2007] | 0.6394 | 0.0133 | 0.0137 |

## F4: the prediction layer (reported)

Stand-in CE inside the twin's 99 % interval: 86 of 86 run-points (exact binomial against 0.99: p = 1.0000; checkpoints of one run are not independent; the binomial p is indicative only). By arm: Z 9/9, C0 44/44, E4 33/33.

## F5: E4's stand-in CE over its sweeps (reported)

Non-increasing in 4 of 11 E4 runs (E4's guarantee is on the twin's training loss; this checks the stand-in's test CE).

- rises in task [7, 0.3, 8], seed 7: CE by sweep [0.5766, 0.589, 0.6008]
- rises in task [7, 1.0, 8], seed 7: CE by sweep [0.6363, 0.6334, 0.6362]
- rises in task [7, 1.0, 8], seed 1007: CE by sweep [0.6483, 0.6474, 0.654]
- rises in task [7, 2.0, 8], seed 7: CE by sweep [0.6039, 0.6069, 0.6077]
- rises in task [8, 0.3, 8], seed 8: CE by sweep [0.5433, 0.5428, 0.5739]
- rises in task [9, 0.3, 8], seed 9: CE by sweep [0.569, 0.5724, 0.584]
- rises in task [9, 1.0, 8], seed 9: CE by sweep [0.5606, 0.5384, 0.5458]

## Vanity and essential figures

| | figure |
|---|---|
| Vanity | the largest single-task CE gain of E4 over C0 at f_min (from the F1 table) |
| Essential | the per-group headline above (every group, as it came), with mean CE gains and 99 % CIs; the peel at full budget as it came; one stand-in, PSF arm only, simulation, fresh teachers 7-9 |

