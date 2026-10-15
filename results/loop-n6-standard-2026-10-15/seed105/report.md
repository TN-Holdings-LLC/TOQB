# TOQB loop standard run n6 L8 (seed 105): for the same money, which compiler returns the best model?

Device fake:FakeFez; front end qiskit; task {"n": 6, "layers": 8, "enc": 1.5707963267948966, "teacher_seed": 4, "teacher_gap": 0.2, "n_train": 64, "n_test": 48}; optimizer {"name": "SPSA", "iterations": 60, "batch": 8, "a": 3.0, "c": 0.2, "A": 2, "init": 0.5, "loop_seed": 105}; evaluation {"shots": 400, "shot_seed": 20261015, "every": 10, "target_accuracy": 0.7}.

Price: 0.00027 s per shot + 0.036 s per circuit + the circuit's duration per shot, at $1.60 per QPU second (rate: PSF-Zero TIME1 / FRAC1 on ibm_fez (2026-10-14); price: IBM Pay-As-You-Go, 'starts at $96 USD / minute', billed per second (ibm.com/quantum/pricing, 2026-10-15)).

Budget: batch $243.93, session $248.60 (what the reference arm qiskit:2:target:template spent on the whole training, plus 5%).

## 1. The result for the money

Accuracy / margin on the test set at the last evaluation within the budget (iteration in brackets); dollars to reach accuracy 0.7; noiseless accuracy of the final angles.

| arm | valid | batch: within budget | session: within budget | $ to target (batch / session) | spent on the whole training (batch / session) | final noiseless accuracy |
|---|---|---|---|---|---|---|
| psfai:template | yes | 0.625 / 0.048 (60) | 0.625 / 0.048 (60) | not reached / not reached | $226.54 / $232.33 | 0.625 |
| qiskit:2:target:template | yes | 0.521 / 0.022 (60) | 0.521 / 0.022 (60) | not reached / not reached | $232.31 / $236.76 | 0.542 |

## 2. Reference: classical models, and energy

Not a contest: TOQB compares compilers. The classical models (`toqb.classical`, numpy only, one fixed configuration each) are trained on the same training points and scored on the same test points, as the bar a quantum model is read against. Energy is a range from assumed powers, not a measurement: a quantum run is charged 10-25 kW for the seconds it holds the QPU (time share: the system's whole power for the seconds a run holds the QPU), and every classical second 10-50 W (10-25 kW: wall-plug power of superconducting systems (dilution refrigerators 10-25 kW continuous) as cited in arXiv 2605.09580; 10-50 W: one CPU core, assumed).

| row | test accuracy | time | energy, kWh | money |
|---|---|---|---|---|
| classical: logistic | 0.771 | 0.09 s CPU | 2.6e-07-1.3e-06 | - |
| classical: logistic_quad | 0.750 | 0.07 s CPU | 1.9e-07-9.6e-07 | - |
| classical: mlp32 | 0.771 | 0.53 s CPU | 1.5e-06-7.3e-06 | - |
| classical: knn5 | 0.729 | 0.00 s CPU | 1.5e-09-7.7e-09 | - |
| quantum, batch: psfai:template | 0.625 (iteration 60) | 141.6 s holding the QPU | 0.39-0.98 | $226.54 |
| quantum, session: psfai:template | 0.625 (iteration 60) | 145.2 s holding the QPU | 0.40-1.01 | $232.33 |
| quantum, batch: qiskit:2:target:template | 0.521 (iteration 60) | 145.2 s holding the QPU | 0.40-1.01 | $232.31 |
| quantum, session: qiskit:2:target:template | 0.521 (iteration 60) | 148.0 s holding the QPU | 0.41-1.03 | $236.76 |

The least energy any quantum row is estimated at is 53,712 times the most any classical model is; the best classical accuracy is 0.771 (logistic).

## 3. The trajectory

iteration: accuracy / margin (dollars spent so far, batch / session)

| arm | evaluations |
|---|---|
| psfai:template | 0: 0.229 / -0.167 ($0.0 / $0.0); 10: 0.604 / -0.007 ($37.8 / $38.7); 20: 0.562 / 0.022 ($75.5 / $77.4); 30: 0.625 / 0.035 ($113.3 / $116.1); 40: 0.625 / 0.044 ($151.0 / $154.8); 50: 0.562 / 0.046 ($188.8 / $193.6); 60: 0.625 / 0.048 ($226.5 / $232.3) |
| qiskit:2:target:template | 0: 0.260 / -0.143 ($0.0 / $0.0); 10: 0.469 / -0.005 ($38.7 / $39.4); 20: 0.427 / 0.004 ($77.4 / $78.9); 30: 0.479 / 0.009 ($116.2 / $118.3); 40: 0.583 / 0.027 ($154.9 / $157.8); 50: 0.646 / 0.034 ($193.6 / $197.3); 60: 0.521 / 0.022 ($232.3 / $236.8) |

## 4. Secondary: the cost of compiling

Reference qiskit:2:target:template: 2.20 s per loop.

| arm | version | circuits | compile s | per circuit ms | tier | classical s per loop | templates built / not available | 2q gates | duration us |
|---|---|---|---|---|---|---|---|---|---|
| psfai:template | psf_compile 2026-10-15.c61, psf_ai_compile 2026-10-15.a22 | 1296 | 3.50 | 2.70 | 3x | 3.62 | 1 / 0 | 120.0 | 8.71 |
| qiskit:2:target:template | 2.5.2 | 1296 | 2.20 | 1.68 | 1x | 2.78 | 1 / 0 | 158.0 | 18.11 |

## Checks

- psfai:template: structural failures 0, operations on failed elements 0, equivalence 3 of 3 checked
- qiskit:2:target:template: structural failures 0, operations on failed elements 0, equivalence 3 of 3 checked
