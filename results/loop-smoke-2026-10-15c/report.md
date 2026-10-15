# TOQB loop smoke (v15): for the same money, which compiler returns the best model?

Device fake:FakeFez; front end pennylane; task {"n": 4, "layers": 2, "enc": 1.5707963267948966, "teacher_seed": 4, "teacher_gap": 0.2, "n_train": 64, "n_test": 24}; optimizer {"name": "SPSA", "iterations": 30, "batch": 8, "a": 3.0, "c": 0.2, "A": 2, "init": 0.5, "loop_seed": 11}; evaluation {"shots": 400, "shot_seed": 20261015, "every": 10, "target_accuracy": 0.75}.

Price: 0.00027 s per shot + 0.036 s per circuit + the circuit's duration per shot, at $1.60 per QPU second (rate: PSF-Zero TIME1 / FRAC1 on ibm_fez (2026-10-14); price: IBM Pay-As-You-Go, 'starts at $96 USD / minute', billed per second (ibm.com/quantum/pricing, 2026-10-15)).

Budget: batch $117.24, session $119.83 (what the reference arm qiskit:2:target:template spent on the whole training, plus 5%).

## 1. The result for the money

Accuracy / margin on the test set at the last evaluation within the budget (iteration in brackets); dollars to reach accuracy 0.75; noiseless accuracy of the final angles.

| arm | valid | batch: within budget | session: within budget | $ to target (batch / session) | spent on the whole training (batch / session) | final noiseless accuracy |
|---|---|---|---|---|---|---|
| psfai:recompile | yes | 0.708 / 0.302 (30) | 0.625 / 0.195 (20) | not reached / not reached | $111.43 / $147.06 | 0.750 |
| psfai:template | yes | 0.708 / 0.326 (30) | 0.708 / 0.326 (30) | not reached / not reached | $111.43 / $113.76 | 0.708 |
| qiskit:2:target:template | yes | 0.750 / 0.366 (30) | 0.750 / 0.366 (30) | $111.66 / $114.13 | $111.66 / $114.13 | 0.750 |
| qiskit:3:target:recompile | yes | 0.750 / 0.359 (30) | 0.625 / 0.244 (20) | $111.64 / $123.93 | $111.64 / $123.93 | 0.708 |
| qiskit:3:target:template | yes | 0.708 / 0.325 (30) | 0.708 / 0.325 (30) | not reached / not reached | $111.64 / $113.72 | 0.708 |

## 2. Reference: classical models, and energy

Not a contest: TOQB compares compilers. The classical models (`toqb.classical`, numpy only, one fixed configuration each) are trained on the same training points and scored on the same test points, as the bar a quantum model is read against. Energy is a range from assumed powers, not a measurement: a quantum run is charged 10-25 kW for the seconds it holds the QPU (time share: the system's whole power for the seconds a run holds the QPU), and every classical second 10-50 W (10-25 kW: wall-plug power of superconducting systems (dilution refrigerators 10-25 kW continuous) as cited in arXiv 2605.09580; 10-50 W: one CPU core, assumed).

| row | test accuracy | time | energy, kWh | money |
|---|---|---|---|---|
| classical: logistic | 0.917 | 0.05 s CPU | 1.4e-07-6.8e-07 | - |
| classical: logistic_quad | 1.000 | 0.06 s CPU | 1.7e-07-8.3e-07 | - |
| classical: mlp32 | 0.958 | 0.24 s CPU | 6.8e-07-3.4e-06 | - |
| classical: knn5 | 1.000 | 0.00 s CPU | 6.6e-10-3.3e-09 | - |
| quantum, batch: psfai:recompile | 0.708 (iteration 30) | 69.6 s holding the QPU | 0.19-0.48 | $111.43 |
| quantum, session: psfai:recompile | 0.625 (iteration 20) | 61.6 s holding the QPU | 0.17-0.43 | $98.57 |
| quantum, batch: psfai:template | 0.708 (iteration 30) | 69.6 s holding the QPU | 0.19-0.48 | $111.43 |
| quantum, session: psfai:template | 0.708 (iteration 30) | 71.1 s holding the QPU | 0.20-0.49 | $113.76 |
| quantum, batch: qiskit:2:target:template | 0.750 (iteration 30) | 69.8 s holding the QPU | 0.19-0.48 | $111.66 |
| quantum, session: qiskit:2:target:template | 0.750 (iteration 30) | 71.3 s holding the QPU | 0.20-0.50 | $114.13 |
| quantum, batch: qiskit:3:target:recompile | 0.750 (iteration 30) | 69.8 s holding the QPU | 0.19-0.48 | $111.64 |
| quantum, session: qiskit:3:target:recompile | 0.625 (iteration 20) | 51.6 s holding the QPU | 0.14-0.36 | $82.56 |
| quantum, batch: qiskit:3:target:template | 0.708 (iteration 30) | 69.8 s holding the QPU | 0.19-0.48 | $111.64 |
| quantum, session: qiskit:3:target:template | 0.708 (iteration 30) | 71.1 s holding the QPU | 0.20-0.49 | $113.72 |

The least energy any quantum row is estimated at is 42,200 times the most any classical model is; the best classical accuracy is 1.000 (logistic_quad).

## 3. The trajectory

iteration: accuracy / margin (dollars spent so far, batch / session)

| arm | evaluations |
|---|---|
| psfai:recompile | 0: 0.333 / -0.318 ($0.0 / $0.0); 10: 0.583 / 0.181 ($37.1 / $49.7); 20: 0.625 / 0.195 ($74.3 / $98.6); 30: 0.708 / 0.302 ($111.4 / $147.1) |
| psfai:template | 0: 0.333 / -0.335 ($0.0 / $0.0); 10: 0.583 / 0.190 ($37.1 / $37.7); 20: 0.625 / 0.214 ($74.3 / $76.0); 30: 0.708 / 0.326 ($111.4 / $113.8) |
| qiskit:2:target:template | 0: 0.292 / -0.339 ($0.0 / $0.3); 10: 0.625 / 0.220 ($37.2 / $38.2); 20: 0.625 / 0.247 ($74.4 / $76.2); 30: 0.750 / 0.366 ($111.7 / $114.1) |
| qiskit:3:target:recompile | 0: 0.333 / -0.326 ($0.0 / $0.0); 10: 0.583 / 0.205 ($37.2 / $41.4); 20: 0.625 / 0.244 ($74.4 / $82.6); 30: 0.750 / 0.359 ($111.6 / $123.9) |
| qiskit:3:target:template | 0: 0.333 / -0.336 ($0.0 / $0.1); 10: 0.604 / 0.211 ($37.2 / $37.8); 20: 0.667 / 0.238 ($74.4 / $75.8); 30: 0.708 / 0.325 ($111.6 / $113.7) |

## 4. Secondary: the cost of compiling

Reference qiskit:2:target:template: 0.45 s per loop.

| arm | version | circuits | compile s | per circuit ms | tier | classical s per loop | templates built / not available | 2q gates | duration us |
|---|---|---|---|---|---|---|---|---|---|
| psfai:recompile | psf_compile 2026-10-14.1, psf_ai_compile 2026-10-15.a21; PennyLane 0.45.1 | 576 | 25.59 | 44.42 | over 10x | 22.27 | 0 / 0 | 14.0 | 2.73 |
| psfai:template | psf_compile 2026-10-14.1, psf_ai_compile 2026-10-15.a21; PennyLane 0.45.1 | 576 | 0.44 | 0.75 | 1x | 1.46 | 1 / 0 | 14.0 | 2.74 |
| qiskit:2:target:template | 2.5.2; PennyLane 0.45.1 | 576 | 0.45 | 0.48 | 1x | 1.54 | 1 / 0 | 17.0 | 3.48 |
| qiskit:3:target:recompile | 2.5.2; PennyLane 0.45.1 | 576 | 8.10 | 14.02 | 10x | 7.68 | 0 / 0 | 17.0 | 3.41 |
| qiskit:3:target:template | 2.5.2; PennyLane 0.45.1 | 576 | 0.33 | 0.52 | 1x | 1.30 | 1 / 0 | 17.0 | 3.40 |

## Checks

- psfai:recompile: structural failures 0, operations on failed elements 0, equivalence 3 of 3 checked
- psfai:template: structural failures 0, operations on failed elements 0, equivalence 3 of 3 checked
- qiskit:2:target:template: structural failures 0, operations on failed elements 0, equivalence 3 of 3 checked
- qiskit:3:target:recompile: structural failures 0, operations on failed elements 0, equivalence 3 of 3 checked
- qiskit:3:target:template: structural failures 0, operations on failed elements 0, equivalence 3 of 3 checked

