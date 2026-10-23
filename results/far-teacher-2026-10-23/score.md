# Far-teacher test: score (report only)

Rules fixed before the run (far_teacher_note.md): shot-free accuracy without correction; A: zipper against item 31 (McNemar); B: what training added (Wilcoxon on per-point gains); Holm over 6 per rule, alpha 0.01.
Truth tier: stand-in.

## A. Accuracy at 500 loops: zipper / item 31

| teacher | zipper / item 31 | McNemar b / c | Holm p | verdict |
|---|---|---|---|---|
| 17 | 0.584 / 0.546 | 51 / 32 | 1.00e-01 | TIE |
| 18 | 0.776 / 0.538 | 153 / 34 | 1.90e-18 | WIN |
| 19 | 0.576 / 0.554 | 70 / 59 | 3.79e-01 | TIE |

**The zipper is more accurate at 500 loops: no** (1 of 3).

## A. Accuracy at 2000 loops: zipper / item 31

| teacher | zipper / item 31 | McNemar b / c | Holm p | verdict |
|---|---|---|---|---|
| 17 | 0.622 / 0.578 | 60 / 38 | 1.00e-01 | TIE |
| 18 | 0.780 / 0.636 | 116 / 44 | 4.54e-08 | WIN |
| 19 | 0.658 / 0.514 | 115 / 43 | 4.51e-08 | WIN |

**The zipper is more accurate at 2000 loops: YES** (2 of 3).

## B. What training added, theta = 0 to 500 loops

| teacher | gain zipper / item 31 | mean per-point difference | Holm p | verdict |
|---|---|---|---|---|
| 17 | +0.008 / +0.008 | +0.0000 | 1.00e+00 | TIE |
| 18 | +0.152 / +0.018 | +0.1340 | 1.31e-06 | WIN |
| 19 | +0.076 / +0.020 | +0.0560 | 1.48e-01 | TIE |

**The zipper learned more by 500 loops: no** (1 of 3).

## B. What training added, theta = 0 to 2000 loops

| teacher | gain zipper / item 31 | mean per-point difference | Holm p | verdict |
|---|---|---|---|---|
| 17 | +0.046 / +0.040 | +0.0060 | 1.00e+00 | TIE |
| 18 | +0.156 / +0.116 | +0.0400 | 4.59e-01 | TIE |
| 19 | +0.158 / -0.020 | +0.1780 | 1.19e-08 | WIN |

**The zipper learned more by 2000 loops: no** (1 of 3).

## Per run and point

| teacher | arm | loops | acc no shots / with shots | +1 share | stand-in AUC | noiseless acc / AUC / CE |
|---|---|---|---|---|---|---|
| 17 | item31 | 0 | 0.538 / 0.561 | 0.93 | 0.765 | 0.574 / 0.674 / 0.9469 |
| 17 | item31 | 500 | 0.546 / 0.574 | 0.94 | 0.767 | 0.598 / 0.724 / 0.7081 |
| 17 | item31 | 2000 | 0.578 / 0.577 | 0.89 | 0.767 | 0.638 / 0.760 / 0.6438 |
| 17 | zipper | 0 | 0.576 / 0.595 | 0.83 | 0.709 | 0.574 / 0.674 / 0.9469 |
| 17 | zipper | 500 | 0.584 / 0.613 | 0.81 | 0.735 | 0.594 / 0.728 / 0.6987 |
| 17 | zipper | 2000 | 0.622 / 0.606 | 0.76 | 0.762 | 0.630 / 0.761 / 0.6231 |
| 18 | item31 | 0 | 0.520 / 0.566 | 0.92 | 0.779 | 0.640 / 0.804 / 0.6895 |
| 18 | item31 | 500 | 0.538 / 0.585 | 0.89 | 0.801 | 0.650 / 0.831 / 0.5287 |
| 18 | item31 | 2000 | 0.636 / 0.670 | 0.84 | 0.864 | 0.758 / 0.887 / 0.4643 |
| 18 | zipper | 0 | 0.624 / 0.642 | 0.78 | 0.819 | 0.640 / 0.804 / 0.6895 |
| 18 | zipper | 500 | 0.776 / 0.711 | 0.56 | 0.886 | 0.770 / 0.874 / 0.4633 |
| 18 | zipper | 2000 | 0.780 / 0.763 | 0.55 | 0.910 | 0.786 / 0.902 / 0.4411 |
| 19 | item31 | 0 | 0.534 / 0.536 | 0.85 | 0.551 | 0.498 / 0.497 / 1.1589 |
| 19 | item31 | 500 | 0.554 / 0.577 | 0.87 | 0.670 | 0.558 / 0.628 / 0.7121 |
| 19 | item31 | 2000 | 0.514 / 0.572 | 0.84 | 0.666 | 0.566 / 0.666 / 0.6850 |
| 19 | zipper | 0 | 0.500 / 0.495 | 0.74 | 0.510 | 0.498 / 0.497 / 1.1589 |
| 19 | zipper | 500 | 0.576 / 0.553 | 0.69 | 0.661 | 0.590 / 0.652 / 0.6811 |
| 19 | zipper | 2000 | 0.658 / 0.612 | 0.62 | 0.739 | 0.640 / 0.705 / 0.6258 |
