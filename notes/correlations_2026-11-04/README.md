# Connected correlations of P5, after the fact (workplace, 2026-11-04; not declared, nothing judged)

`correlations.py` -> `out/correlations_posthoc.json`, `out/tables.md` (`tables.py`), `out/run.txt`. Existing counts of
P5: kingston stage B, stage C/D (tag b; tag c for the theta-0 floor at t = 6-8), stage E job K; fez stage E job X.
C_ij = <Z_i Z_j> - <Z_i><Z_j> for pairs at lattice distance 1, 2, 3, against the exact value from a statevector of the
union of the two causal cones (t <= 5, unions of at most 18 qubits; fewer pairs are answered at t = 4, 5). The
theta = 0 cells give the correlation floor (raw <Z_i Z_j>, ideal 1).

Summary (cells with |exact C| >= 0.01; ratio = measured / exact mean over the answered pairs):

| job | floor raw <ZZ> | theta 0.4 ratio | theta 0.8 ratio | theta 1.0 ratio |
|---|---|---|---|---|
| kingston B | 0.951-0.955 | 1.04-1.17 (mean 1.12) | 0.68-0.91 (0.85) | 0.49-0.91 (0.82) |
| kingston b (C/D) | 0.955-0.958 (tag c) | 1.00-1.17 (1.08) | 0.64-0.90 (0.82) | 0.42-0.91 (0.80) |
| fez X | 0.893-0.924 | 1.10-1.27 (1.17) | 0.66-0.89 (0.84) | 0.59-0.91 (0.82) |

The headline would be "the device reproduces the correlations within a few hundredths (largest mean |difference| 0.039)".
The essential numbers: correlations are attenuated to 0.8-0.85 of exact at theta 0.8 and 1.0, but **amplified** to
1.08-1.17 of exact at theta 0.4, on both kingston runs and on fez. Noise that only shrinks each <Z> would attenuate C
at every theta; an excess at theta 0.4 (where <Z> is near 0.9) points to correlated errors or to fluctuations of the
device during the job. Which one is not tested here. The floor (0.95 on kingston, about the square of the single-qubit
floor 0.977) confirms that correlations carry the readout error twice.
