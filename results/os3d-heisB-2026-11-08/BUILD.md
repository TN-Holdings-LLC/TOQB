# 3D physics part B on a device (prereg/os3d_heisB_2026-11-07.md)

- Declared at TOQB 342d32b, pushed before the fetch (84f2e88..342d32b). Queue read 15:58 CET: marrakesh 15, fez 11,
  kingston 14 -> ibm_fez (fewest pending; 4 x 2 x 2 fits). Record: failed qubits 72, 148; coupler 32-33.
- Job `fez/`: 4 places ((1, 0), (1, 4), (3, 0), (3, 4), fold), t = 1-4, 52 circuits, 61.0 s by the model,
  gates 1770633f8831, answers d35c7e1c...; every answer equals the sealed table's entry for its place and t.
- CZ per arm 176 / 348 / 520 / 692 (t = 1-4); exact m_s 0.9316 / 0.7568 / 0.5302 / 0.3078.

## Run

Job dbnjqbgqtr0c73ad6rk0, submitted 16:01 CET 2026-11-07, DONE, collected 23:09 CET. Sentinel DEAD (fez, as every
day since 11-04). Scored with the declared rule "top": `fez/scores.json`.

## Judged candidate 0 (r0 1, c0 0; own t1 mirror 0.528, the highest)

| t | CZ | m_s measured / exact | retention | site MSE / mean square | verdicts | mirror |
|---|---|---|---|---|---|---|
| 1 | 176 | 0.669 / 0.932 | 0.72 | 0.076 / 0.868 | READS, DIFFERS | 0.528 |
| 2 | 348 | 0.469 / 0.757 | 0.62 | 0.093 / 0.574 | READS, DIFFERS | 0.273 |
| 3 | 520 | 0.270 / 0.530 | 0.51 | 0.085 / 0.283 | READS, DIFFERS | 0.119 |
| 4 | 692 | 0.164 / 0.308 | 0.53 | 0.036 / 0.096 | READS, DIFFERS | 0.039 |

Beside: candidate 3 (r0 3, c0 4) about the same (retention 0.69 / 0.63 / 0.49 / 0.56, READS at every t); candidate 2
READS to t = 3; candidate 1 (t1 mirror 0.300) READS at t = 1 only (retention 0.47 -> 0.31). The measured m_s falls
monotonically with the exact one at every place. Answers released in `answers/` (as sealed).

Against part A at 4 x 2 x 2 on the same device (Ising, retention about 0.90 at t = 1): each Heisenberg bond is a
general two-qubit unitary (3 CZ), so one step costs 176 CZ; the retention at t = 1 is 0.72 and settles near 0.5 from
t = 3. The mirror (twice the depth) is near 0 at t = 4 while the forward m_s still keeps half its exact value.
