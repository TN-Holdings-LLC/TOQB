# Paper 7 figure candidates (DRAFT, workplace, 2026-11-06)

Each figure is drawn from committed records by a script (none written yet); no number by hand.

| # | figure | data source | note |
|---|---|---|---|
| 1 | The OS's 2D flow: user circuit -> placement by translation (copies, refusal reasons) -> compile (rzz_exact) -> floor, mirror, ring -> answer card | psf-os `user2d.py`, `lattice2d.py` | schematic |
| 2 | The patches on a Heron r2 lattice (P32, B42, B72, B102, C33) with their translation copies, and the copies refused on 11-05 (failed elements marked) | `daily/pool.py`; `results/daily/2026-11-05/*/dev/device.json` | geometry only |
| 3 | Practice: measured M against exact M, both devices, P4 (by t) and P5 (by theta, t); y = x line and the +-0.05 band | table (a) / `results/practice*-2026-11-04/run/scores.json` | the declared band drawn, nothing else fitted |
| 4 | Retention R against the declared difference for every row (practice and daily), colour by family | tables (a), (b) | shows the bias of the absolute criterion in both directions |
| 5 | FX-A day to day: M - M_exact per night and device (11-04 practice, 11-05, ...) | table (c) | the time series the fixed problem exists for |
| 6 | Decay per CZ layer by family and device | table (b) `decay_per_layer` | no single device-health number |
| 7 | Correction: corrected against raw MSE, declared (11-04) and exploratory (11-05, hatched) | table (d) | exploratory marked on the figure |
| 8 | After the fact: corrected residual by distance to rule-R-dropped qubits (marrakesh, fez, 11-04) | `notes/s1_2026-11-05/out/s1_result.json` | labelled "after the fact" |
| 9 | Hard problems H01-H03 (when run): per-qubit measured against exact | the night's `scores.json` | with the largest light cone and 2^cone in the caption |
