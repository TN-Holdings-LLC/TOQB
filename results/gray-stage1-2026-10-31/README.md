# Gray stage 1 on ibm_kingston, 2026-10-31: the weak stretch was gone (P0 ABSENT); nothing judged

- **Declaration:** `prereg/drafts-2026-10-31/gray_stage1_note.md` (SHA-256 25f6231a...3a45), fixed 13:04 CET, TOQB
  5403b96. Fetch 13:06:21 CET (calibration 12:53:33 CET, Target 93c82a8a...). Masked by the coverage-days list after
  day 1 (couplers (9, 10), (29, 38), (85, 86)). The n = 72 ring holds the block; its D = 24 Z circuit is byte for byte
  the one of coverage job B (11:40 CET) and clean depth (12:08 CET), QPY SHA-256 df8eda3c....
- **Job** dbitn9o1h92s73845ung, submitted 13:14:33 CET, 96 circuits x 1000 shots, 32.4 s predicted, **28 s billed**.

## Precondition: ABSENT

At D = 24 in Z the block 35, 19, 15, 14 read 0.48, 0.49, 0.49, 0.46 against a ring median of 0.40 (weak line 0.20);
its neighbours 33, 34, 13, 12, 11 read 0.45-0.48. No weak run holds a block qubit. By the note nothing is judged.

## Reported (`gray_score.txt`, `gray_score.json`)

| when (CET) | calibration | 35 | 19 | 15 | 14 | ring median |
|---|---|---|---|---|---|---|
| 11:40 (coverage job B) | 10:56 | 0.12 | 0.10 | 0.12 | 0.11 | 0.38 |
| 12:08 (clean depth, hz averaged) | 11:39 | 0.18 | 0.16 | 0.13 | 0.18 | 0.40 |
| 13:14 (this job) | 12:53 | 0.48 | 0.49 | 0.49 | 0.46 | 0.40 |

- The same circuit on the same qubits: the stretch was weak twice and then among the best sites of the ring, within
  about 90 minutes. The 18-site dead run of n = 40 (30 and 31 October) is the opposite case: the same qubits every
  time.
- The scores, for the record only: block Z signal over D = 2 ... 24 falls from 0.96 to 0.48 with no sign change; |v|
  at D = 12 0.83 (rest 0.75), transverse fraction 0.06; connected pair correlations at or below the rest's.
