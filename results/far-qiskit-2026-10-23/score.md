# Far teachers, zipper against Qiskit: score (report only)

Rules fixed before the run (far_qiskit_note.md): A shot-free stand-in accuracy without correction; B the trained model noiseless; McNemar, Holm over 6 per rule, alpha 0.01; 2 of 3 teachers.
Truth tier: stand-in (A), the model itself (B).

## A. stand-in accuracy, shot-free at 500 loops: zipper / Qiskit

| teacher | zipper / Qiskit | McNemar b / c | Holm p | verdict (zipper) |
|---|---|---|---|---|
| 17 | 0.584 / 0.566 | 46 / 37 | 7.60e-01 | TIE |
| 18 | 0.776 / 0.554 | 160 / 49 | 3.67e-14 | WIN |
| 19 | 0.576 / 0.614 | 48 / 67 | 2.78e-01 | TIE |

**More accurate at 500 loops (A): neither** (zipper WIN 1, LOSS 0 of 3).

## A. stand-in accuracy, shot-free at 2000 loops: zipper / Qiskit

| teacher | zipper / Qiskit | McNemar b / c | Holm p | verdict (zipper) |
|---|---|---|---|---|
| 17 | 0.622 / 0.570 | 68 / 42 | 6.70e-02 | TIE |
| 18 | 0.780 / 0.778 | 39 / 38 | 1.00e+00 | TIE |
| 19 | 0.658 / 0.582 | 91 / 53 | 9.71e-03 | WIN |

**More accurate at 2000 loops (A): neither** (zipper WIN 1, LOSS 0 of 3).

## B. noiseless accuracy of the trained model at 500 loops: zipper / Qiskit

| teacher | zipper / Qiskit | McNemar b / c | Holm p | verdict (zipper) |
|---|---|---|---|---|
| 17 | 0.594 / 0.626 | 38 / 54 | 5.87e-01 | TIE |
| 18 | 0.770 / 0.764 | 55 / 52 | 1.00e+00 | TIE |
| 19 | 0.590 / 0.624 | 64 / 81 | 5.87e-01 | TIE |

**More accurate at 500 loops (B): neither** (zipper WIN 0, LOSS 0 of 3).

## B. noiseless accuracy of the trained model at 2000 loops: zipper / Qiskit

| teacher | zipper / Qiskit | McNemar b / c | Holm p | verdict (zipper) |
|---|---|---|---|---|
| 17 | 0.630 / 0.630 | 56 / 56 | 1.00e+00 | TIE |
| 18 | 0.786 / 0.818 | 32 / 48 | 5.57e-01 | TIE |
| 19 | 0.640 / 0.600 | 87 / 67 | 5.87e-01 | TIE |

**More accurate at 2000 loops (B): neither** (zipper WIN 0, LOSS 0 of 3).

## Decision aid for a device run (report only)

Power of one exact McNemar at alpha 0.01 in the stand-in's direction; test points drawn from the 500, 250 shots per point and arm, 2000 repetitions. The device is not the stand-in.

| loops | teacher | stand-in direction | power, 300 points | power, 500 points |
|---|---|---|---|---|
| 500 | 17 | zipper | 0.01 | 0.01 |
| 500 | 18 | zipper | 0.96 | 1.00 |
| 500 | 19 | Qiskit | 0.03 | 0.06 |
| 2000 | 17 | zipper | 0.04 | 0.05 |
| 2000 | 18 | zipper | 0.00 | 0.00 |
| 2000 | 19 | zipper | 0.00 | 0.00 |

## Per run and point

| teacher | arm | loops | acc no shots / with shots | +1 share | stand-in AUC | noiseless acc / AUC / CE | twin-stand-in P(1) rmse |
|---|---|---|---|---|---|---|---|
| 17 | qiskit | 0 | 0.550 / 0.560 | 0.93 | 0.765 | 0.574 / 0.674 / 0.9469 | 0.0423 |
| 17 | qiskit | 500 | 0.566 / 0.580 | 0.90 | 0.769 | 0.626 / 0.746 / 0.6565 | 0.0326 |
| 17 | qiskit | 2000 | 0.570 / 0.571 | 0.91 | 0.771 | 0.630 / 0.764 / 0.6652 | 0.0163 |
| 17 | zipper | 0 | 0.576 / 0.595 | 0.83 | 0.709 | 0.574 / 0.674 / 0.9469 | 0.0136 |
| 17 | zipper | 500 | 0.584 / 0.613 | 0.81 | 0.735 | 0.594 / 0.728 / 0.6987 | 0.0122 |
| 17 | zipper | 2000 | 0.622 / 0.606 | 0.76 | 0.762 | 0.630 / 0.761 / 0.6231 | 0.0110 |
| 18 | qiskit | 0 | 0.504 / 0.519 | 0.94 | 0.766 | 0.640 / 0.804 / 0.6895 | 0.0551 |
| 18 | qiskit | 500 | 0.554 / 0.568 | 0.93 | 0.830 | 0.764 / 0.895 / 0.4605 | 0.0299 |
| 18 | qiskit | 2000 | 0.778 / 0.734 | 0.61 | 0.909 | 0.818 / 0.923 / 0.4332 | 0.0182 |
| 18 | zipper | 0 | 0.624 / 0.642 | 0.78 | 0.819 | 0.640 / 0.804 / 0.6895 | 0.0132 |
| 18 | zipper | 500 | 0.776 / 0.711 | 0.56 | 0.886 | 0.770 / 0.874 / 0.4633 | 0.0109 |
| 18 | zipper | 2000 | 0.780 / 0.763 | 0.55 | 0.910 | 0.786 / 0.902 / 0.4411 | 0.0100 |
| 19 | qiskit | 0 | 0.548 / 0.533 | 0.86 | 0.582 | 0.498 / 0.497 / 1.1589 | 0.0424 |
| 19 | qiskit | 500 | 0.614 / 0.585 | 0.81 | 0.708 | 0.624 / 0.687 / 0.6569 | 0.0192 |
| 19 | qiskit | 2000 | 0.582 / 0.589 | 0.83 | 0.730 | 0.600 / 0.738 / 0.6306 | 0.0170 |
| 19 | zipper | 0 | 0.500 / 0.495 | 0.74 | 0.510 | 0.498 / 0.497 / 1.1589 | 0.0128 |
| 19 | zipper | 500 | 0.576 / 0.553 | 0.69 | 0.661 | 0.590 / 0.652 / 0.6811 | 0.0083 |
| 19 | zipper | 2000 | 0.658 / 0.612 | 0.62 | 0.739 | 0.640 / 0.705 / 0.6258 | 0.0078 |

Circuits (per arm, from the records): qiskit: q2 [506], durations [48.216]; zipper: q2 [336], durations [11.652]
