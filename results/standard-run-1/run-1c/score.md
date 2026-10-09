# TOQB standard run 1: score

start 2026-10-09T10:31:08Z UTC; end 2026-10-09T11:23:08Z UTC; wall 3120.2 s; 12 CPUs, 4 at a time; Linux-6.18.33.2-microsoft-standard-WSL2-x86_64-with-glibc2.43; Python 3.12.13; TOQB head 3bfc6663c6635a84abf630523699a12c141a1552

**P0: PASS**

- 126 tests drawn from the committed seed: True
- the six adapters: True
- one record per adapter and test: True
- run with --lock; no uncommitted change in TOQB, PSF-Zero or Benchpress: True
- PSF-Zero release and head: True
- Benchpress head: True
- package versions: True
- the circuit breakers of amendment 1: True
- the run is complete (not stopped by a STOP file or the run budget): True

| ID | prediction | value | verdict |
|---|---|---|---|
| T1 | every output of every compiler is valid, and every checked one is equivalent | {"qiskit:2:target": [4, 0], "qiskit:1:target": [4, 0], "qiskit:3:target": [4, 0], "tket:2": [0, 0], "psf:default": [4, 0], "psf:recommended": [4, 0]} | **REFUTED** |
| T2 | psf:default Q_all <= 1.07 (REFUTED > 1.10) | 1.012 | **CONFIRMED** |
| T3 | psf:default within 10x >= 0.90 (REFUTED < 0.80); 10x at most 600 s (amendment 1) | 0.968 (under the pre-registration's own stopping: 0.968-0.968) | **CONFIRMED** |
| T4 | psf:recommended places no two-qubit gate on FakeTorino's failed elements | [0, 17] | **CONFIRMED** |
| T5 | tket:2 Q_all >= 1.05 (REFUTED < 1.00) | 1.145 | **CONFIRMED** |
| T6 | psf:default fails on <= 2% of the tests the reference finishes (REFUTED > 5%); stopped at its largest budget (amendment 1) | 0.000 (under the pre-registration's own stopping: 0.000-0.000) | **CONFIRMED** |

Reported without prediction:

| adapter | within 1x | within 3x | within 10x | Q_all (95%) | n | Q_1x (n) | Q_3x (n) | Q_10x (n) | depth Q_all | time / ref (median) | invalid | not equiv. | checked | failed (time, memory, adapter, harness) | not run (no reference) | run again after an interruption | FakeTorino tests with gates on failed elements | trailing gates | peak memory (MB) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| qiskit:2:target | 0.968 | 0.968 | 0.968 | 1.000 (1.000-1.000) | 122 | 1.000 (122) | 1.000 (122) | 1.000 (122) | 1.000 | 1.000 | 4 | 0 | 47 | 0 (0, 0, 0, 0) | 0 | 0 | 5 of 18 | 0 | 1600 |
| qiskit:1:target | 0.968 | 0.968 | 0.968 | 1.239 (1.171-1.324) | 122 | 1.239 (122) | 1.239 (122) | 1.239 (122) | 1.234 | 0.540 | 4 | 0 | 47 | 0 (0, 0, 0, 0) | 0 | 0 | 5 of 18 | 0 | 1327 |
| qiskit:3:target | 0.532 | 0.929 | 0.952 | 0.972 (0.958-0.985) | 120 | 0.994 (67) | 0.976 (117) | 0.972 (120) | 0.972 | 1.216 | 4 | 0 | 47 | 2 (2, 0, 0, 0) | 0 | 0 | 4 of 18 | 0 | 2246 |
| tket:2 | 0.071 | 0.143 | 0.254 | 1.145 (1.073-1.244) | 74 | 1.193 (9) | 1.130 (18) | 1.143 (32) | 1.059 | 47.307 | 0 | 0 | 36 | 52 (47, 0, 4, 0) | 0 | 0 | 2 of 6 | 210 | 2080 |
| psf:default | 0.690 | 0.921 | 0.968 | 1.012 (1.004-1.021) | 122 | 1.009 (87) | 1.013 (116) | 1.012 (122) | 1.013 | 1.204 | 4 | 0 | 48 | 0 (0, 0, 0, 0) | 0 | 0 | 10 of 18 | 0 | 1893 |
| psf:recommended | 0.643 | 0.873 | 0.952 | 1.012 (1.004-1.021) | 121 | 1.013 (81) | 1.012 (110) | 1.012 (120) | 1.014 | 1.211 | 4 | 0 | 47 | 1 (0, 0, 0, 0) | 0 | 0 | 0 of 17 | 0 | 1896 |

Q_all by family:

| adapter | QASMBench | HamLib | HamLib, FakeTorino | Feynman, FakeTorino |
|---|---|---|---|---|
| qiskit:2:target | 1.000 (76) | 1.000 (28) | 1.000 (10) | 1.000 (8) |
| qiskit:1:target | 1.194 (76) | 1.332 (28) | 1.373 (10) | 1.202 (8) |
| qiskit:3:target | 0.990 (74) | 0.920 (28) | 0.973 (10) | 0.993 (8) |
| tket:2 | 1.175 (56) | 1.039 (12) | 1.031 (4) | 1.206 (2) |
| psf:default | 1.007 (76) | 1.013 (28) | 1.029 (10) | 1.032 (8) |
| psf:recommended | 1.007 (76) | 1.013 (28) | 1.036 (10) | 1.023 (7) |

On the 32 tests every compiler returned within 10x: qiskit:2:target 1.000, qiskit:1:target 1.355, qiskit:3:target 1.002, tket:2 1.143, psf:default 0.998, psf:recommended 0.998
