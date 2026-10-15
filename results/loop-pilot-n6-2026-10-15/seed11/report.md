# TOQB loop pilot n6 L8 (seed 11): for the same money, which compiler returns the best model?

Device fake:FakeFez; front end qiskit; task {"n": 6, "layers": 8, "enc": 1.5707963267948966, "teacher_seed": 4, "teacher_gap": 0.2, "n_train": 64, "n_test": 48}; optimizer {"name": "SPSA", "iterations": 60, "batch": 8, "a": 3.0, "c": 0.2, "A": 2, "init": 0.5, "loop_seed": 11}; evaluation {"shots": 400, "shot_seed": 20261015, "every": 10, "target_accuracy": 0.7}.

Price: 0.00027 s per shot + 0.036 s per circuit + the circuit's duration per shot, at $1.60 per QPU second (rate: PSF-Zero TIME1 / FRAC1 on ibm_fez (2026-10-14); price: IBM Pay-As-You-Go, 'starts at $96 USD / minute', billed per second (ibm.com/quantum/pricing, 2026-10-15)).

Budget: batch $243.93, session $246.83 (what the reference arm qiskit:2:target:template spent on the whole training, plus 5%).

## 1. The result for the money

Accuracy / margin on the test set at the last evaluation within the budget (iteration in brackets); dollars to reach accuracy 0.7; noiseless accuracy of the final angles.

| arm | valid | batch: within budget | session: within budget | $ to target (batch / session) | spent on the whole training (batch / session) | final noiseless accuracy |
|---|---|---|---|---|---|---|
| psfai:template | yes | 0.781 / 0.188 (60) | 0.781 / 0.188 (60) | $226.54 / $230.23 | $226.54 / $230.23 | 0.750 |
| qiskit:2:target:template | yes | 0.385 / -0.019 (60) | 0.385 / -0.019 (60) | not reached / not reached | $232.31 / $235.08 | 0.542 |

## 2. Reference: classical models, and energy

Not a contest: TOQB compares compilers. The classical models (`toqb.classical`, numpy only, one fixed configuration each) are trained on the same training points and scored on the same test points, as the bar a quantum model is read against. Energy is a range from assumed powers, not a measurement: a quantum run is charged 10-25 kW for the seconds it holds the QPU (time share: the system's whole power for the seconds a run holds the QPU), and every classical second 10-50 W (10-25 kW: wall-plug power of superconducting systems (dilution refrigerators 10-25 kW continuous) as cited in arXiv 2605.09580; 10-50 W: one CPU core, assumed).

| row | test accuracy | time | energy, kWh | money |
|---|---|---|---|---|
| classical: logistic | 0.771 | 0.04 s CPU | 1.2e-07-6.2e-07 | - |
| classical: logistic_quad | 0.750 | 0.05 s CPU | 1.3e-07-6.5e-07 | - |
| classical: mlp32 | 0.771 | 0.28 s CPU | 7.7e-07-3.8e-06 | - |
| classical: knn5 | 0.729 | 0.00 s CPU | 1.1e-09-5.7e-09 | - |
| quantum, batch: psfai:template | 0.781 (iteration 60) | 141.6 s holding the QPU | 0.39-0.98 | $226.54 |
| quantum, session: psfai:template | 0.781 (iteration 60) | 143.9 s holding the QPU | 0.40-1.00 | $230.23 |
| quantum, batch: qiskit:2:target:template | 0.385 (iteration 60) | 145.2 s holding the QPU | 0.40-1.01 | $232.31 |
| quantum, session: qiskit:2:target:template | 0.385 (iteration 60) | 146.9 s holding the QPU | 0.41-1.02 | $235.08 |

The least energy any quantum row is estimated at is 102,399 times the most any classical model is; the best classical accuracy is 0.771 (logistic).

## 3. The trajectory

iteration: accuracy / margin (dollars spent so far, batch / session)

| arm | evaluations |
|---|---|
| psfai:template | 0: 0.354 / -0.185 ($0.0 / $0.0); 10: 0.271 / -0.046 ($37.8 / $38.3); 20: 0.479 / -0.009 ($75.5 / $76.7); 30: 0.458 / 0.024 ($113.3 / $115.1); 40: 0.562 / 0.045 ($151.0 / $153.4); 50: 0.688 / 0.148 ($188.8 / $191.8); 60: 0.781 / 0.188 ($226.5 / $230.2) |
| qiskit:2:target:template | 0: 0.344 / -0.154 ($0.0 / $0.1); 10: 0.406 / -0.062 ($38.7 / $39.2); 20: 0.333 / -0.048 ($77.4 / $78.3); 30: 0.365 / -0.036 ($116.2 / $117.5); 40: 0.427 / -0.028 ($154.9 / $156.7); 50: 0.448 / -0.023 ($193.6 / $195.9); 60: 0.385 / -0.019 ($232.3 / $235.1) |

## 4. Secondary: the cost of compiling

Reference qiskit:2:target:template: 1.42 s per loop.

| arm | version | circuits | compile s | per circuit ms | tier | classical s per loop | templates built / not available | 2q gates | duration us |
|---|---|---|---|---|---|---|---|---|---|
| psfai:template | psf_compile 2026-10-15.c61, psf_ai_compile 2026-10-15.a22 | 1296 | 2.23 | 1.72 | 3x | 2.31 | 1 / 0 | 120.0 | 8.71 |
| qiskit:2:target:template | 2.5.2 | 1296 | 1.42 | 1.07 | 1x | 1.73 | 1 / 0 | 158.0 | 18.11 |

## Checks

- psfai:template: structural failures 0, operations on failed elements 0, equivalence 3 of 3 checked
- qiskit:2:target:template: structural failures 0, operations on failed elements 0, equivalence 3 of 3 checked
