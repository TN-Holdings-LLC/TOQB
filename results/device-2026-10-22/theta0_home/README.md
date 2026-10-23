# Device day's task at theta = 0 (post hoc, home, 2026-10-23; not declared)

The device day (C r9) compared PSF-Zero (item 31) and Qiskit on teacher 4 at angle 0.3. The untrained model (theta =
0, design C0's start) already answers that task well; the twin training made both arms' models worse (noiseless, the
logical model; test labels regenerated and identical to the records):

| | L 16 (500 points) | L 8 (150 points) |
|---|---|---|
| theta = 0 | 0.934 (CE 0.297) | 0.940 (CE 0.312) |
| trained, PSF (item 31) | 0.762 (CE 0.498) | 0.880 (CE 0.404) |
| trained, Qiskit | 0.730 (CE 0.509) | 0.787 (CE 0.461) |

Read: the device day's difference between the arms was not a difference in learning; it was which arm's training
moved its model less far from a good start, plus each circuit's readout. The day's verdicts are not shown wrong by
this; what they measured is narrower than "which compiler trains better". Script: `theta0_device_day.py`.
