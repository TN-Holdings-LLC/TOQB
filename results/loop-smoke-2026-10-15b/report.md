# TOQB loop smoke (v15): for the same money, which compiler returns the best model?

Device fake:FakeFez; front end pennylane; task {"n": 4, "layers": 2, "enc": 1.5707963267948966, "teacher_seed": 4, "teacher_gap": 0.2, "n_train": 64, "n_test": 24}; optimizer {"name": "SPSA", "iterations": 30, "batch": 8, "a": 3.0, "c": 0.2, "A": 2, "init": 0.5, "loop_seed": 11}; evaluation {"shots": 400, "shot_seed": 20261015, "every": 10, "target_accuracy": 0.75}.

Price: 0.00027 s per shot + 0.036 s per circuit + the circuit's duration per shot, at $1.60 per QPU second (rate: PSF-Zero TIME1 / FRAC1 on ibm_fez (2026-10-14); price: IBM Pay-As-You-Go, 'starts at $96 USD / minute', billed per second (ibm.com/quantum/pricing, 2026-10-15)).

Budget: batch $117.24, session $119.66 (what the reference arm qiskit:2:target:template spent on the whole training, plus 5%).

## 1. The result for the money

Accuracy / margin on the test set at the last evaluation within the budget (iteration in brackets); dollars to reach accuracy 0.75; noiseless accuracy of the final angles.

| arm | valid | batch: within budget | session: within budget | $ to target (batch / session) | spent on the whole training (batch / session) | final noiseless accuracy |
|---|---|---|---|---|---|---|
| psfai:recompile | yes | 0.708 / 0.302 (30) | 0.625 / 0.195 (20) | not reached / not reached | $111.43 / $138.82 | 0.750 |
| psfai:template | yes | 0.708 / 0.326 (30) | 0.708 / 0.326 (30) | not reached / not reached | $111.43 / $113.15 | 0.708 |
| qiskit:2:target:template | yes | 0.750 / 0.366 (30) | 0.750 / 0.366 (30) | $111.66 / $113.96 | $111.66 / $113.96 | 0.750 |
| qiskit:3:target:recompile | yes | 0.750 / 0.359 (30) | 0.625 / 0.244 (20) | $111.64 / $121.69 | $111.64 / $121.69 | 0.708 |
| qiskit:3:target:template | yes | 0.708 / 0.325 (30) | 0.708 / 0.325 (30) | not reached / not reached | $111.64 / $113.74 | 0.708 |

## 2. The trajectory

iteration: accuracy / margin (dollars spent so far, batch / session)

| arm | evaluations |
|---|---|
| psfai:recompile | 0: 0.333 / -0.318 ($0.0 / $0.0); 10: 0.583 / 0.181 ($37.1 / $46.6); 20: 0.625 / 0.195 ($74.3 / $92.8); 30: 0.708 / 0.302 ($111.4 / $138.8) |
| psfai:template | 0: 0.333 / -0.335 ($0.0 / $0.0); 10: 0.583 / 0.190 ($37.1 / $37.6); 20: 0.625 / 0.214 ($74.3 / $75.5); 30: 0.708 / 0.326 ($111.4 / $113.2) |
| qiskit:2:target:template | 0: 0.292 / -0.339 ($0.0 / $0.1); 10: 0.625 / 0.220 ($37.2 / $38.1); 20: 0.625 / 0.247 ($74.4 / $76.0); 30: 0.750 / 0.366 ($111.7 / $114.0) |
| qiskit:3:target:recompile | 0: 0.333 / -0.326 ($0.0 / $0.0); 10: 0.583 / 0.205 ($37.2 / $40.4); 20: 0.625 / 0.244 ($74.4 / $80.9); 30: 0.750 / 0.359 ($111.6 / $121.7) |
| qiskit:3:target:template | 0: 0.333 / -0.336 ($0.0 / $0.0); 10: 0.604 / 0.211 ($37.2 / $37.7); 20: 0.667 / 0.238 ($74.4 / $75.9); 30: 0.708 / 0.325 ($111.6 / $113.7) |

## 3. Secondary: the cost of compiling

Reference qiskit:2:target:template: 0.30 s per loop.

| arm | version | circuits | compile s | per circuit ms | tier | classical s per loop | templates built / not available | 2q gates | duration us |
|---|---|---|---|---|---|---|---|---|---|
| psfai:recompile | psf_compile 2026-10-14.1, psf_ai_compile 2026-10-15.a21; PennyLane 0.45.1 | 576 | 19.29 | 33.49 | over 10x | 17.12 | 0 / 0 | 14.0 | 2.73 |
| psfai:template | psf_compile 2026-10-14.1, psf_ai_compile 2026-10-15.a21; PennyLane 0.45.1 | 576 | 0.36 | 0.61 | 1x | 1.07 | 1 / 0 | 14.0 | 2.74 |
| qiskit:2:target:template | 2.5.2; PennyLane 0.45.1 | 576 | 0.30 | 0.46 | 1x | 1.44 | 1 / 0 | 17.0 | 3.48 |
| qiskit:3:target:recompile | 2.5.2; PennyLane 0.45.1 | 576 | 6.64 | 11.49 | 10x | 6.28 | 0 / 0 | 17.0 | 3.41 |
| qiskit:3:target:template | 2.5.2; PennyLane 0.45.1 | 576 | 0.28 | 0.44 | 1x | 1.32 | 1 / 0 | 17.0 | 3.40 |

## Checks

- psfai:recompile: structural failures 0, operations on failed elements 0, equivalence 3 of 3 checked
- psfai:template: structural failures 0, operations on failed elements 0, equivalence 3 of 3 checked
- qiskit:2:target:template: structural failures 0, operations on failed elements 0, equivalence 3 of 3 checked
- qiskit:3:target:recompile: structural failures 0, operations on failed elements 0, equivalence 3 of 3 checked
- qiskit:3:target:template: structural failures 0, operations on failed elements 0, equivalence 3 of 3 checked
