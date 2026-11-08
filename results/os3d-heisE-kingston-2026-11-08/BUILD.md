# heisE's three-layout comparison on ibm_kingston (prereg/os3d_heisE_kingston_2026-11-08.md)

- Declared at TOQB fe7dd79, pushed before the fetch (12:19 CET 2026-11-08). Record: failed qubits 112, 113, 121, 146;
  couplers 112-113, 121-122, 130-131, 145-146, 146-147.
- Job `kingston/`: candidates (1, 0), (1, 4), (1, 8), (3, 0) (all odd rows); old / carry / line at t = 1-4; 148
  circuits, 168.2 s by the model; answers 79360c3e... (the same places as the 11-07 fez try-build); every answer
  equals the released tables' entry. CZ at t = 1 / 4: old 176 / 692, carry 152 / 596, line 116 / 404.

## Run

Job dbo5megou4as73b5ib30, submitted 12:30 CET, DONE before 13:29 CET. Sentinel CLEAN. Scored with the declared rule:
`kingston/scores.json`. The run's answers in `answers/`.

## Judged candidate 1 (r0 1, c0 4; mean t1 mirror 0.694)

| t | old: retention (CZ) | carry | line | carry - old | line - old | shot bound |
|---|---|---|---|---|---|---|
| 1 | 0.801 (176) | 0.806 (152) | 0.822 (116) | +0.006 | +0.022 | 0.048 |
| 2 | 0.659 (348) | 0.670 (300) | 0.715 (212) | +0.011 | +0.056 | 0.059 |
| 3 | 0.554 (520) | 0.560 (448) | 0.604 (308) | +0.006 | +0.050 | 0.084 |
| 4 | 0.475 (692) | 0.481 (596) | 0.423 (404) | +0.006 | -0.051 | 0.145 |

Every judged arm READS and DIFFERS. Predictions: carry - old >= 0 held at every t; line - old >= 0 held at t = 1-3
and failed at t = 4 (-0.051, inside the shot bound 0.145). None of the judged differences is resolved.

Beside: candidate 2 (r0 1, c0 8) line - old +0.057 / +0.109 / +0.144 / +0.109 (resolved at t = 1-3), carry - old
+0.035 / +0.071 / +0.103 / +0.124 (resolved at t = 2, 3); candidate 3 (r0 3, c0 0) line - old +0.080 / +0.057 /
+0.096 / +0.001; candidate 0 (r0 1, c0 0) +0.029 / +0.044 / 0.000 / 0.000. Mean over the four places: line - old
+0.047 / +0.066 / +0.072 / +0.015; carry - old +0.023 / +0.032 / +0.031 / +0.039.

Against marrakesh the same evening (results/os3d-heisE-2026-11-08, judged place): line - old there +0.039 / +0.079 /
+0.096 / +0.077; the old layout's retention at t = 4 0.610 there, 0.475 here.
