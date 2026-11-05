# Daily record (prereg/daily/standing_rules.md)

Raw values, no correction. AGREES: |M - M_exact| <= 0.05. BEATS: MSE below the better trivial guess. Every night and
device is a line, failures included.

| date (CET) | device | problem | RUNS | READS | AGREES | BEATS | M - M_exact | MSE / trivial guess | floor | sentinel | job |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-11-05 | ibm_marrakesh | FX-A (fixed) | yes | READS | AGREES | BEATS | -0.024 | 0.0023 / 0.0264 | 0.952 | CLEAN | dbm5hgd8mdtc73d7bang |
| 2026-11-05 | ibm_marrakesh | D02 | yes | READS | DIFFERS | BEATS | -0.111 | 0.0162 / 0.0482 | 0.954 | CLEAN | dbm5hgd8mdtc73d7bang |
| 2026-11-05 | ibm_fez | FX-A (fixed) | yes | READS | AGREES | BEATS | -0.043 | 0.0033 / 0.0264 | 0.968 | DEAD | dbm5hid8ft8s738u88g0 |
| 2026-11-05 | ibm_fez | D02 | yes | READS | DIFFERS | BEATS | -0.147 | 0.0354 / 0.0482 | 0.969 | DEAD | dbm5hid8ft8s738u88g0 |

FX-A before the record (the same circuit as the practice test's p4_b0.485_t12, 2026-11-04 13:32 / 13:57 CET):
marrakesh -0.022, fez -0.041.
