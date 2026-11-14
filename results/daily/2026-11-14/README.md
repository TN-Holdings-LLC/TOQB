# Daily record, day 4 (2026-11-14; standing rules and the amendment of 11-06; notice `prereg/night_2026-11-14.md`)

- Queue read 11:17:50 CET (19:17 JST): marrakesh 2, fez 0, kingston 236 -> ibm_marrakesh and ibm_fez. Problems FX-A
  (fixed) and D05 (pool order). psf-os 0.1.1 (checked before the night to write the 11-07 job byte for byte).
- marrakesh record (calibration 2026-11-13 18:22 CET): failed qubits 82, 94, 113, 119, 130, coupler 113-119; FX-A and
  D05 at (0, 0). Job dbs3c7vv5hds73dignng, 10 circuits, 4000 shots, submitted 11:21 CET.
- fez record (calibration 2026-11-13 17:27 CET): failed qubits 72, 148, 149, coupler 32-33; FX-A and D05 at copy
  (drow 4, dcol 0). Job dbs3c9ejjaos73ajnvu0, 10 circuits, 4000 shots, submitted 11:21 CET.
- Days 2026-11-08 to 2026-11-13: not run under these rules (lines "not run" in RECORD.md).

| device | problem | READS | AGREES | BEATS | M - M_exact | MSE / guess | floor | retention | slope | sentinel |
|---|---|---|---|---|---|---|---|---|---|---|
| marrakesh | FX-A | READS | AGREES | BEATS | -0.012 | 0.0013 / 0.0264 | 0.983 | 0.923 | 0.900 | DEAD |
| marrakesh | D05 | READS | AGREES | BEATS | +0.005 | 0.0010 / 0.0052 | 0.981 | (exact 0.065) | 0.976 | DEAD |
| fez | FX-A | READS | AGREES | BEATS | -0.042 | 0.0032 / 0.0264 | 0.965 | 0.732 | 0.716 | DEAD |
| fez | D05 | READS | AGREES | BEATS | -0.020 | 0.0017 / 0.0052 | 0.965 | (exact 0.065) | 0.610 | DEAD |

D05's signal is small (mean square answer 0.0052, M_exact 0.065): it reads on both devices, with little room
between READS (MSE at most 0.0026) and the result. The marrakesh sentinel was CLEAN on 11-05 and has been DEAD since;
the fez sentinel has been DEAD every day since 11-04.
