# TOQB loop smoke (v15): report

Device fake:FakeFez; task {"n": 4, "layers": 2, "enc": 1.5707963267948966, "teacher_seed": 4, "teacher_gap": 0.2, "n_train": 64, "n_test": 24}; optimizer {"name": "SPSA", "iterations": 30, "batch": 8, "a": 3.0, "c": 0.2, "A": 2, "init": 0.5, "loop_seed": 11}; evaluation {"shots": 400, "shot_seed": 20261015, "every": 10, "target_accuracy": 0.75}.

Reference arm: qiskit:2:target:template (compile time per loop 0.18 s).

## The loop's cost

| arm | version | valid | circuits | setup s | compile s | per circuit ms | budget tier | simulation s | 2q gates | duration us |
|---|---|---|---|---|---|---|---|---|---|---|
| psfai:recompile | psf_compile 2026-10-14.1, psf_ai_compile 2026-10-15.a21 | yes | 576 | 0.00 | 29.15 | 50.61 | over 10x | 102.9 | 14.0 | 2.73 |
| psfai:template | psf_compile 2026-10-14.1, psf_ai_compile 2026-10-15.a21 | yes | 576 | 0.01 | 0.21 | 0.34 | 1x | 103.6 | 14.0 | 2.74 |
| qiskit:2:target:template | 2.5.2 | yes | 576 | 0.04 | 0.18 | 0.23 | 1x | 121.9 | 17.0 | 3.48 |
| qiskit:3:target:recompile | 2.5.2 | yes | 576 | 0.02 | 10.59 | 18.34 | over 10x | 114.6 | 17.0 | 3.41 |
| qiskit:3:target:template | 2.5.2 | yes | 576 | 0.04 | 0.17 | 0.22 | 1x | 113.2 | 17.0 | 3.40 |

## The loop's result

Noisy test accuracy / margin at each evaluation (iteration: accuracy / margin); the noiseless accuracy of the final angles; the first evaluation at or above 0.75.

| arm | evaluations | final noiseless accuracy | to target: iteration, compile s, wall s |
|---|---|---|---|
| psfai:recompile | 0: 0.333 / -0.318, 10: 0.625 / 0.194, 20: 0.625 / 0.208, 30: 0.792 / 0.353 | 0.792 | 30, 29.15, 133.4 |
| psfai:template | 0: 0.333 / -0.335, 10: 0.583 / 0.190, 20: 0.625 / 0.214, 30: 0.708 / 0.326 | 0.708 | not reached |
| qiskit:2:target:template | 0: 0.292 / -0.339, 10: 0.625 / 0.220, 20: 0.625 / 0.247, 30: 0.750 / 0.366 | 0.750 | 30, 0.18, 124.0 |
| qiskit:3:target:recompile | 0: 0.333 / -0.326, 10: 0.625 / 0.225, 20: 0.625 / 0.238, 30: 0.750 / 0.367 | 0.750 | 30, 10.59, 127.2 |
| qiskit:3:target:template | 0: 0.333 / -0.336, 10: 0.604 / 0.211, 20: 0.667 / 0.238, 30: 0.708 / 0.325 | 0.708 | not reached |

## Checks

- psfai:recompile: structural failures 0, operations on failed elements 0, equivalence 3 of 3 checked
- psfai:template: structural failures 0, operations on failed elements 0, equivalence 3 of 3 checked
- qiskit:2:target:template: structural failures 0, operations on failed elements 0, equivalence 3 of 3 checked
- qiskit:3:target:recompile: structural failures 0, operations on failed elements 0, equivalence 3 of 3 checked
- qiskit:3:target:template: structural failures 0, operations on failed elements 0, equivalence 3 of 3 checked
