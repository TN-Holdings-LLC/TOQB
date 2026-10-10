# TOQB standard run 2: score

start 2026-10-10T05:12:37Z UTC; end 2026-10-10T06:03:18Z UTC; wall 3040.8 s; 12 CPUs, 4 at a time; Linux-6.18.33.2-microsoft-standard-WSL2-x86_64-with-glibc2.43; Python 3.12.13; TOQB head 42a49e2fe41a4076f3ce3a7a61fbb335afdce000

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
- psf-zero-core57 installed, at the version of the release: True

| ID | prediction | value | verdict |
|---|---|---|---|
| S1 | every output of every compiler is valid (v13's structural check), and every checked one is equivalent | {"qiskit:2:target": [0, 0], "qiskit:1:target": [0, 0], "qiskit:3:target": [0, 0], "tket:2": [0, 0], "psf:default": [0, 0], "psf:recommended": [0, 0]} | **CONFIRMED** |
| S2 | psf:default's two-qubit count equals run 1c's on every test where both outputs are usable | {"tests": 122, "differ": []} | **CONFIRMED** |
| S3 | psf:recommended on FakeTorino: geometric mean of its time / the reference's <= 2.2 (REFUTED >= 2.53, run 1c's value) | 2.128 | **CONFIRMED** |
| S4 | psf:recommended places no two-qubit gate on FakeTorino's failed elements | [0, 17] | **CONFIRMED** |
| S5 | psf:default fails on <= 2% of the tests the reference finishes (REFUTED > 5%) | 0.000 (under the pre-registration's own stopping: 0.000-0.000) | **CONFIRMED** |

Reported without prediction:

| adapter | within 1x | within 3x | within 10x | Q_all (95%) | n | Q_1x (n) | Q_3x (n) | Q_10x (n) | depth Q_all | time / ref (median) | invalid | not equiv. | checked | failed (time, memory, adapter, harness) | not run (no reference) | run again after an interruption | FakeTorino tests with gates on failed elements | trailing gates | peak memory (MB) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| qiskit:2:target | 1.000 | 1.000 | 1.000 | 1.000 (1.000-1.000) | 126 | 1.000 (126) | 1.000 (126) | 1.000 (126) | 1.000 | 1.000 | 0 | 0 | 47 | 0 (0, 0, 0, 0) | 0 | 0 | 5 of 18 | 0 | 1611 |
| qiskit:1:target | 1.000 | 1.000 | 1.000 | 1.265 (1.190-1.355) | 126 | 1.265 (126) | 1.265 (126) | 1.265 (126) | 1.265 | 0.556 | 0 | 0 | 47 | 0 (0, 0, 0, 0) | 0 | 0 | 5 of 18 | 0 | 1364 |
| qiskit:3:target | 0.556 | 0.960 | 0.984 | 0.973 (0.960-0.986) | 124 | 0.993 (70) | 0.976 (121) | 0.973 (124) | 0.973 | 1.160 | 0 | 0 | 47 | 2 (2, 0, 0, 0) | 0 | 0 | 4 of 18 | 0 | 2243 |
| tket:2 | 0.071 | 0.143 | 0.254 | 1.145 (1.073-1.244) | 74 | 1.193 (9) | 1.130 (18) | 1.147 (32) | 1.059 | 44.429 | 0 | 0 | 36 | 52 (48, 0, 4, 0) | 0 | 0 | 2 of 6 | 210 | 2079 |
| psf:default | 0.714 | 0.952 | 1.000 | 1.012 (1.004-1.020) | 126 | 1.009 (90) | 1.012 (120) | 1.012 (126) | 1.013 | 1.160 | 0 | 0 | 48 | 0 (0, 0, 0, 0) | 0 | 0 | 10 of 18 | 0 | 1898 |
| psf:recommended | 0.667 | 0.905 | 0.984 | 1.012 (1.004-1.020) | 125 | 1.011 (84) | 1.012 (114) | 1.012 (124) | 1.014 | 1.167 | 0 | 0 | 47 | 1 (0, 0, 0, 0) | 0 | 0 | 0 of 17 | 0 | 1897 |

Q_all by family:

| adapter | QASMBench | HamLib | HamLib, FakeTorino | Feynman, FakeTorino |
|---|---|---|---|---|
| qiskit:2:target | 1.000 (80) | 1.000 (28) | 1.000 (10) | 1.000 (8) |
| qiskit:1:target | 1.236 (80) | 1.332 (28) | 1.373 (10) | 1.202 (8) |
| qiskit:3:target | 0.991 (78) | 0.920 (28) | 0.973 (10) | 0.993 (8) |
| tket:2 | 1.175 (56) | 1.039 (12) | 1.031 (4) | 1.206 (2) |
| psf:default | 1.007 (80) | 1.013 (28) | 1.029 (10) | 1.032 (8) |
| psf:recommended | 1.007 (80) | 1.013 (28) | 1.036 (10) | 1.023 (7) |

On the 32 tests every compiler returned within 10x: qiskit:2:target 1.000, qiskit:1:target 1.363, qiskit:3:target 1.002, tket:2 1.147, psf:default 0.998, psf:recommended 0.998

Beside run 1c (`results/standard-run-1/run-1c`):

| adapter | within 1x (1c / 2) | within 3x (1c / 2) | within 10x (1c / 2) | Q_all (1c / 2) | time / ref, median (1c / 2) | failed (1c / 2) |
|---|---|---|---|---|---|---|
| qiskit:2:target | 0.968 / 1.000 | 0.968 / 1.000 | 0.968 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 0 / 0 |
| qiskit:1:target | 0.968 / 1.000 | 0.968 / 1.000 | 0.968 / 1.000 | 1.239 / 1.265 | 0.540 / 0.556 | 0 / 0 |
| qiskit:3:target | 0.532 / 0.556 | 0.929 / 0.960 | 0.952 / 0.984 | 0.972 / 0.973 | 1.216 / 1.160 | 2 / 2 |
| tket:2 | 0.071 / 0.071 | 0.143 / 0.143 | 0.254 / 0.254 | 1.145 / 1.145 | 47.307 / 44.429 | 52 / 52 |
| psf:default | 0.690 / 0.714 | 0.921 / 0.952 | 0.968 / 1.000 | 1.012 / 1.012 | 1.204 / 1.160 | 0 / 0 |
| psf:recommended | 0.643 / 0.667 | 0.873 / 0.905 | 0.952 / 0.984 | 1.012 / 1.012 | 1.211 / 1.167 | 1 / 1 |

Exit codes of the failed measurements: -9, 1, 3
