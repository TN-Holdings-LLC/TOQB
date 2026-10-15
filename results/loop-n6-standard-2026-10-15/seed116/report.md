# TOQB loop standard run n6 L8 (seed 116): for the same money, which compiler returns the best model?

Device fake:FakeFez; front end qiskit; task {"n": 6, "layers": 8, "enc": 1.5707963267948966, "teacher_seed": 4, "teacher_gap": 0.2, "n_train": 64, "n_test": 48}; optimizer {"name": "SPSA", "iterations": 60, "batch": 8, "a": 3.0, "c": 0.2, "A": 2, "init": 0.5, "loop_seed": 116}; evaluation {"shots": 400, "shot_seed": 20261015, "every": 10, "target_accuracy": 0.7}.

Price: 0.00027 s per shot + 0.036 s per circuit + the circuit's duration per shot, at $1.60 per QPU second (rate: PSF-Zero TIME1 / FRAC1 on ibm_fez (2026-10-14); price: IBM Pay-As-You-Go, 'starts at $96 USD / minute', billed per second (ibm.com/quantum/pricing, 2026-10-15)).

Budget: batch $243.93, session $248.60 (what the reference arm qiskit:2:target:template spent on the whole training, plus 5%).

## 1. The result for the money

Accuracy / margin on the test set at the last evaluation within the budget (iteration in brackets); dollars to reach accuracy 0.7; noiseless accuracy of the final angles.

| arm | valid | batch: within budget | session: within budget | $ to target (batch / session) | spent on the whole training (batch / session) | final noiseless accuracy |
|---|---|---|---|---|---|---|
| psfai:template | yes | 0.531 / 0.011 (60) | 0.531 / 0.011 (60) | not reached / not reached | $226.54 / $232.53 | 0.583 |
| qiskit:2:target:template | yes | 0.375 / -0.057 (60) | 0.375 / -0.057 (60) | not reached / not reached | $232.31 / $236.76 | 0.438 |

## 2. Reference: classical models, and energy

Not a contest: TOQB compares compilers. The classical models (`toqb.classical`, numpy only, one fixed configuration each) are trained on the same training points and scored on the same test points, as the bar a quantum model is read against. Energy is a range from assumed powers, not a measurement: a quantum run is charged 10-25 kW for the seconds it holds the QPU (time share: the system's whole power for the seconds a run holds the QPU), and every classical second 10-50 W (10-25 kW: wall-plug power of superconducting systems (dilution refrigerators 10-25 kW continuous) as cited in arXiv 2605.09580; 10-50 W: one CPU core, assumed).

| row | test accuracy | time | energy, kWh | money |
|---|---|---|---|---|
| classical: logistic | 0.771 | 0.08 s CPU | 2.2e-07-1.1e-06 | - |
| classical: logistic_quad | 0.750 | 0.08 s CPU | 2.3e-07-1.2e-06 | - |
| classical: mlp32 | 0.771 | 0.45 s CPU | 1.3e-06-6.3e-06 | - |
| classical: knn5 | 0.729 | 0.00 s CPU | 1.5e-09-7.3e-09 | - |
| quantum, batch: psfai:template | 0.531 (iteration 60) | 141.6 s holding the QPU | 0.39-0.98 | $226.54 |
| quantum, session: psfai:template | 0.531 (iteration 60) | 145.3 s holding the QPU | 0.40-1.01 | $232.53 |
| quantum, batch: qiskit:2:target:template | 0.375 (iteration 60) | 145.2 s holding the QPU | 0.40-1.01 | $232.31 |
| quantum, session: qiskit:2:target:template | 0.375 (iteration 60) | 148.0 s holding the QPU | 0.41-1.03 | $236.76 |

The least energy any quantum row is estimated at is 62,771 times the most any classical model is; the best classical accuracy is 0.771 (logistic).

## 3. The trajectory

iteration: accuracy / margin (dollars spent so far, batch / session)

| arm | evaluations |
|---|---|
| psfai:template | 0: 0.323 / -0.170 ($0.0 / $0.0); 10: 0.438 / -0.057 ($37.8 / $38.8); 20: 0.490 / -0.020 ($75.5 / $77.6); 30: 0.500 / -0.027 ($113.3 / $116.3); 40: 0.458 / -0.023 ($151.0 / $155.0); 50: 0.490 / -0.017 ($188.8 / $193.7); 60: 0.531 / 0.011 ($226.5 / $232.5) |
| qiskit:2:target:template | 0: 0.271 / -0.131 ($0.0 / $0.0); 10: 0.375 / -0.082 ($38.7 / $39.6); 20: 0.292 / -0.080 ($77.4 / $79.0); 30: 0.302 / -0.071 ($116.2 / $118.5); 40: 0.354 / -0.060 ($154.9 / $157.9); 50: 0.333 / -0.051 ($193.6 / $197.3); 60: 0.375 / -0.057 ($232.3 / $236.8) |

## 4. Secondary: the cost of compiling

Reference qiskit:2:target:template: 2.18 s per loop.

| arm | version | circuits | compile s | per circuit ms | tier | classical s per loop | templates built / not available | 2q gates | duration us |
|---|---|---|---|---|---|---|---|---|---|
| psfai:template | psf_compile 2026-10-15.c61, psf_ai_compile 2026-10-15.a22 | 1296 | 3.47 | 2.68 | 3x | 3.74 | 1 / 0 | 120.0 | 8.71 |
| qiskit:2:target:template | 2.5.2 | 1296 | 2.18 | 1.66 | 1x | 2.78 | 1 / 0 | 158.0 | 18.11 |

## Checks

- psfai:template: structural failures 0, operations on failed elements 0, equivalence 3 of 3 checked
- qiskit:2:target:template: structural failures 0, operations on failed elements 0, equivalence 3 of 3 checked
