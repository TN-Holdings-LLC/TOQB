# N = 91 dual-unitary chain, second run, ruler in every job (2026-11-10, prereg/du91r_2026-11-10.md)

- Declared at d34cc4d; pushed (GitHub eb833c8..f67734c) at 11:22 CET; queue read 11:23:22 CET (marrakesh 0, fez 0,
  kingston 0) -> ibm_fez by the declared tie rule (of fez and kingston, ties fez); record fetched 11:23:33 CET
  (failed qubits 72, 148, 149; coupler 32-33).
- Build (`gpu/du51_build.py ... --n 91 --rule-c --ruler-every-job`): rule C, chain 0, 1, 2 ... 151, 150; job A 58
  circuits (67.7 s by the model), job B 40 (47.6 s); CZ up to 2205. Answers (by label) equal the table sealed on 11-09
  (441c9c1a..., released then) on all 30 tags; `answers/du91r_fez.json`.
- Pre-run check (`gpu/du91r_check.py`): the 12 ruler circuits at full size by the stabilizer method: ALL PASS.
- Jobs: A dbpfafgou4as73ctiokg, B dbpfailt7fqc7389b7bg, submitted 11:43 CET, both DONE by 11:45 CET; job files
  returned byte-identical to the build.

## Declared verdicts (`gpu/du91r_score.py`)

- READS: MSE 0.2872 against a mean square of 0.7595 (30 on-cone points).
- Rates against the ruler of their own job: h 0.05 k 0.9960 +- 0.0015 (cos 2h 0.9950) AGREES; h 0.10 0.9814 +- 0.0018
  (0.9801) AGREES; h 0.15 0.9590 +- 0.0021 (0.9553) AGREES.
- Readable depth: A0 24, 0.05 24, 0.10 16, B0 24, 0.15 24. Sentinels: A DEAD, B DEAD (as recorded).

## Beside (not judged)

- h 0.15 against job A's ruler (the earlier runs' way): 0.9582 +- 0.0021.
- Ruler ratio B0 / A0: 0.9982 +- 0.0015, near 1: the two jobs saw the device alike.
- Against the declared prediction: 0.15 AGREES, but k - cos 2h = +0.0037, the same as on 11-09 (marrakesh, +0.0037),
  and the ruler ratio is near 1; so the earlier slowness is not explained by a job-to-job difference. It is inside
  2 SE in this run.
- The signal is weaker than on marrakesh 11-09 (MSE 0.287 against 0.039): the ruler reads 0.865 at t 4 and falls to
  about 0.09-0.11 at t 20-24, where every series sits near 0.04-0.11 regardless of its exact value.
