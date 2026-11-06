# Daily record (prereg/daily/standing_rules.md)

Raw values, no correction. AGREES: |M - M_exact| <= 0.05. BEATS: MSE below the better trivial guess. Every night and
device is a line, failures included.

| date (CET) | device | problem | RUNS | READS | AGREES | BEATS | M - M_exact | MSE / trivial guess | floor | sentinel | job |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-11-05 | ibm_marrakesh | FX-A (fixed) | yes | READS | AGREES | BEATS | -0.024 | 0.0023 / 0.0264 | 0.952 | CLEAN | dbm5hgd8mdtc73d7bang |
| 2026-11-05 | ibm_marrakesh | D02 | yes | READS | DIFFERS | BEATS | -0.111 | 0.0162 / 0.0482 | 0.954 | CLEAN | dbm5hgd8mdtc73d7bang |
| 2026-11-05 | ibm_fez | FX-A (fixed) | yes | READS | AGREES | BEATS | -0.043 | 0.0033 / 0.0264 | 0.968 | DEAD | dbm5hid8ft8s738u88g0 |
| 2026-11-05 | ibm_fez | D02 | yes | READS | DIFFERS | BEATS | -0.147 | 0.0354 / 0.0482 | 0.969 | DEAD | dbm5hid8ft8s738u88g0 |
| 2026-11-06 | ibm_marrakesh | FX-A (fixed) | yes (alone) | READS | AGREES | BEATS | -0.008 | 0.0016 / 0.0264 | 0.977 | DEAD | dbmqhbu74qds73dsrde0 |
| 2026-11-06 | ibm_marrakesh | D03 | REFUSED | - | - | - | - | - | - | - | (failed qubits 46, 73, 82 hit every copy; amendment 2026-11-06: FX-A run alone) |
| 2026-11-07 | ibm_fez | FX-A (fixed) | yes (copy drow 4) | READS | AGREES | BEATS | -0.038 | 0.0039 / 0.0264 | 0.966 | DEAD | dbn5ludt7fqc73aivq60 |
| 2026-11-07 | ibm_fez | D04 | yes | READS | AGREES | BEATS | +0.010 | 0.0030 / 0.2362 | 0.978 | DEAD | dbn5ludt7fqc73aivq60 |

FX-A before the record (the same circuit as the practice test's p4_b0.485_t12, 2026-11-04 13:32 / 13:57 CET):
marrakesh -0.022, fez -0.041.

## Reported beside the judgements (added 2026-11-05 evening by the owner's decision; the judgements are unchanged)

R = M / M_exact; slope = per-qubit fit of measured on exact through 0; "after scale": MSE left after that one scale;
decay per CZ layer = -ln(slope) / (CZ layers of the compiled circuit).

| date | device | problem | R | slope | MSE -> after scale | CZ layers | decay / layer |
|---|---|---|---|---|---|---|---|
| 2026-11-05 | ibm_marrakesh | FX-A | 0.846 | 0.838 | 0.0023 -> 0.0016 | 25 | 0.0070 |
| 2026-11-05 | ibm_marrakesh | D02 | 0.860 | 0.860 | 0.0162 -> 0.0036 | 40 | 0.0038 |
| 2026-11-05 | ibm_fez | FX-A | 0.732 | 0.723 | 0.0033 -> 0.0013 | 25 | 0.0130 |
| 2026-11-05 | ibm_fez | D02 | 0.816 | 0.811 | 0.0354 -> 0.0125 | 40 | 0.0052 |
| 2026-11-06 | ibm_marrakesh | FX-A | 0.949 | 0.957 | 0.0016 -> 0.0016 | 25 | 0.0017 |
| 2026-11-07 | ibm_fez | FX-A | 0.763 | 0.739 | 0.0039 -> 0.0021 | 25 | 0.0121 |
| 2026-11-07 | ibm_fez | D04 | 1.022 | 1.014 | 0.0030 -> 0.0030 | 26 | -0.0005 |
