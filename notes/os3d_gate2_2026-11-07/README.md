# Draft rule "gate2" (cost of the marked qubits instead of any mark) against every recorded run (2026-11-07; offline)

Not declared. Owner 12:10 JST "進めて" to the proposal: count what the marked qubits cost the average (at most 0.025,
half the AGREES tolerance) instead of refusing any mark; confirm on the day's records before declaring. All records
below were already seen, so this checks behaviour, not foresight.

| run | gate (declared) | gate2 (draft) | costs (mirror / |1> floor) of the candidates |
|---|---|---|---|
| fez 4x2x2 morning (t3 probes) | none | none | 0: 0.130/0, 1: 0.118/0.070, 2: 0/0.052, 3: 0/0.050 |
| marrakesh 4x2x2 | 1 | 1 | 0: 0.024/0.041, 1: 0/0, 2: 0/0.041, 3: 0.087/0.027 |
| fez 4x6x3 | none | none | 0: 0.044/0.053, 1: 0.044/0.039 |
| kingston 4x6x3 | none | none | 0: 0.040/0.027 |
| sim FakeFez t3 / t1 | 0 / 0 | 0 / 0 | 1-3: 0.16-0.41 / 0.08-0.10 |
| sim fez calibration t3 / t1 | 3 / 3 | 3 / 3 | 1: 0/0.078 (t3), 2: within 0.1 fails |

gate2 keeps every 4 x 2 x 2 choice (marrakesh: candidate 1, the smallest error; candidate 3, error 0.26, refused). At
4 x 6 x 3 it refuses too: the marked qubits cost 0.027-0.053 of the average, above 0.025. That matches the arms: fez
DIFFERS at t 1-3, kingston DIFFERS at t 1-2 (AGREES at t 3 only). So the 87-qubit refusals were not only an artefact
of the relative line: the marked qubits (fez q27, q63, q103; kingston q7, q85, q87 and four low mirror sites) cost
more than the tolerance. With 1-2 fold translations at that size there is no other place to choose.
