# Data and gradient test: score (report only)

Rules fixed before the run (data_grad_note.md): accuracy without correction (stand-in exact P(1), no shots), exact McNemar on paired test points, Holm over 3 teachers, alpha 0.01. Truth tier: stand-in.

## A. item31: 256 training points against 64

| teacher | acc 256 / 64 | McNemar b / c | Holm p | verdict |
|---|---|---|---|---|
| 14 | 0.610 / 0.612 | 32 / 33 | 1.00e+00 | TIE |
| 15 | 0.644 / 0.570 | 70 / 33 | 1.02e-03 | WIN |
| 16 | 0.652 / 0.626 | 42 / 29 | 3.08e-01 | TIE |

**item31: the data was the wall: no** (1 of 3).

## A. zipper: 256 training points against 64

| teacher | acc 256 / 64 | McNemar b / c | Holm p | verdict |
|---|---|---|---|---|
| 14 | 0.804 / 0.818 | 52 / 59 | 9.42e-01 | TIE |
| 15 | 0.830 / 0.792 | 62 / 43 | 2.35e-01 | TIE |
| 16 | 0.818 / 0.800 | 66 / 57 | 9.42e-01 | TIE |

**zipper: the data was the wall: no** (0 of 3).

## B. Zipper against item 31 at 256 training points (the rule)

| teacher | acc zipper / item 31 | McNemar b / c | Holm p | verdict |
|---|---|---|---|---|
| 14 | 0.804 / 0.610 | 118 / 21 | 4.19e-17 | WIN |
| 15 | 0.830 / 0.644 | 117 / 24 | 1.38e-15 | WIN |
| 16 | 0.818 / 0.652 | 109 / 26 | 2.77e-13 | WIN |

**The zipper's gain survives more data: YES** (3 of 3).

## B. Zipper against item 31 at 64 training points (reported)

| teacher | acc zipper / item 31 | McNemar b / c | Holm p | verdict |
|---|---|---|---|---|
| 14 | 0.818 / 0.612 | 136 / 33 | 9.43e-16 | WIN |
| 15 | 0.792 / 0.570 | 142 / 31 | 1.06e-17 | WIN |
| 16 | 0.800 / 0.626 | 118 / 31 | 3.73e-13 | WIN |

## Per run

| teacher | train points | arm | acc (no shots) / with shots | CE (no shots) / with shots | noiseless CE test / train | grad cos twin-noiseless start / end | twin-twin start / end | grad scale start / end |
|---|---|---|---|---|---|---|---|---|
| 14 | 64 | item31 | 0.612 / 0.644 | 0.6276 / 0.6284 | 0.4951 / 0.3896 | 0.828 / 0.590 | 0.831 / 0.627 | 0.180 / 0.229 |
| 14 | 64 | zipper | 0.818 / 0.718 | 0.6414 / 0.6443 | 0.4340 / 0.2977 | 0.933 / 0.647 | 0.683 / 0.540 | 0.179 / 0.213 |
| 14 | 256 | item31 | 0.610 / 0.626 | 0.6285 / 0.6296 | 0.5034 / 0.4895 | 0.702 / 0.513 | 0.377 / 0.224 | 0.100 / 0.240 |
| 14 | 256 | zipper | 0.804 / 0.707 | 0.6439 / 0.6484 | 0.4376 / 0.4217 | 0.871 / 0.764 | 0.541 / 0.342 | 0.179 / 0.207 |
| 15 | 64 | item31 | 0.570 / 0.614 | 0.6383 / 0.6414 | 0.5238 / 0.4698 | 0.831 / 0.464 | 0.782 / 0.649 | 0.146 / 0.196 |
| 15 | 64 | zipper | 0.792 / 0.686 | 0.6479 / 0.6506 | 0.4673 / 0.3830 | 0.914 / 0.782 | 0.720 / 0.516 | 0.184 / 0.202 |
| 15 | 256 | item31 | 0.644 / 0.631 | 0.6316 / 0.6353 | 0.4836 / 0.4833 | 0.581 / 0.694 | -0.129 / 0.618 | 0.076 / 0.203 |
| 15 | 256 | zipper | 0.830 / 0.701 | 0.6431 / 0.6459 | 0.4409 / 0.4223 | 0.923 / 0.814 | 0.441 / 0.307 | 0.168 / 0.177 |
| 16 | 64 | item31 | 0.626 / 0.642 | 0.6200 / 0.6222 | 0.4904 / 0.4470 | 0.825 / 0.555 | 0.338 / 0.414 | 0.128 / 0.190 |
| 16 | 64 | zipper | 0.800 / 0.694 | 0.6468 / 0.6514 | 0.4702 / 0.3542 | 0.894 / 0.797 | 0.593 / 0.466 | 0.183 / 0.232 |
| 16 | 256 | item31 | 0.652 / 0.639 | 0.6197 / 0.6200 | 0.4535 / 0.4684 | 0.844 / 0.507 | 0.722 / 0.432 | 0.192 / 0.207 |
| 16 | 256 | zipper | 0.818 / 0.735 | 0.6373 / 0.6399 | 0.4276 / 0.4301 | 0.905 / 0.530 | 0.440 / 0.393 | 0.159 / 0.219 |
