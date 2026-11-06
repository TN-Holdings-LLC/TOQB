# Daily record, day 2 (2026-11-06; prereg/daily/standing_rules.md and standing_rules_amendment_2026-11-06.md)

- Queue read 11:12 CET: marrakesh 0, fez 52, kingston 147 -> ibm_marrakesh only.
- Problems: FX-A (fixed) and D03 (pool order). **D03 REFUSED** on marrakesh: run2d found no qualifying copy (failed
  qubits 46, 73, 82; see `ibm_marrakesh/D03_REFUSED_run2d.txt`). By the amendment declared this morning, FX-A was run
  alone (7 circuits, 10.8 s by the model, CZ 400, copy (0, 0)); D03 counts as used, day 3 takes D04.
- Job dbmqhbu74qds73dsrde0, submitted 11:15:12 CET (calibration 10:35 CET), 4000 shots.
- FX-A run alone is psf-os run2d's single-circuit form, whose tag is `user`; it is scored with
  `ibm_marrakesh/answers_by_tag.json` = {"user": answers["FX-A"]} (the released FX-A values, nothing else changed).

| device | problem | READS | AGREES | BEATS | M - M_exact | MSE / guess | floor | sentinel |
|---|---|---|---|---|---|---|---|---|
| ibm_marrakesh | FX-A | READS | AGREES | BEATS | -0.008 | 0.0016 / 0.0264 | 0.977 | DEAD |

Beside: retention 0.949 (11-05 on marrakesh: 0.846), slope 0.957, decay per CZ layer 0.0017 (11-05: 0.0070).
The ring sentinel was DEAD on marrakesh tonight (CLEAN on 11-05).
