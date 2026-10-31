# Gray zone, stage 1: where does the signal of a weak, not dead, stretch go? (home, 2026-10-31; declared on the owner's go of 2026-10-31 12:58 CET)

**Why.** The owner: dead runs (black) are not worth recovering; the gray zone is. On 31 October the n = 72 ring that
the rule places around the defect list (coverage day 1 job B, 11:40 CET; clean depth, 12:08 CET; the same circuit,
QPY SHA-256 df8eda3c...) had a weak stretch twice: 35, 19, 15, 14 at 0.12 / 0.10 / 0.12 / 0.11 and then 0.18 / 0.16 /
0.13 / 0.18 (ring median about 0.4); in the first job its neighbours 33, 34, 13, 12, 11 were weak too (0.14-0.18).
Read in Z only, a turned signal and a lost signal look the same. This replaces the dead-run target of
`coherent_stage1_DRAFT.md` (which stays a draft, not run); the reading and its simulator check are the same
(`results/echo-tomo-validation-2026-10-31`).

**Design (one job, ibm_kingston, a new fetch after this note).**
- The day's fetch masked by `results/coverage-days-2026-10-31-day1/list_after.json` (`defect_list mask`; couplers
  (9, 10), (29, 38), (85, 86)); the rule (`fold:rule`) places n = 72. Self-checked category.
- Z at one-way L = 1, 2, 3, 4, 6, 8, 10, 12 (D = 2 ... 24); X and Y at L = 6 and 12 (D = 12, 24); basis change before
  each echo measurement only (`toqb.echo_tomo`). hz = 0, h = 0.6, 4 inputs and 4 references, 1000 shots, options
  off. 12 records, 96 circuits, 32.4 s predicted (`gpu/gray_stage1.sh`; dry run on the 12:20 CET fetch: all
  accepted, one ring holding the block, the D = 24 Z circuit byte-identical to df8eda3c...).
- STOP before submission if the ring does not hold the block; a different D = 24 hash is reported, not a stop.

**Units (fixed).** Block (judged) = 35, 19, 15, 14. Other (reported) = 33, 34, 13, 12, 11. Rest = the ring minus both.

**Precondition P0.** At D = 24 in Z, a weak run (at least 3 consecutive ring sites below max(0.12, 0.5 x the ring's
median)) holds at least 2 block qubits. If not: ABSENT; nothing is judged; all values are reported.

**Judged (`echo_tomo score --n 72 --block 35,19,15,14 --other 33,34,13,12,11 --segment 33,34,35,19,15,14,13,12,11
--path 35,19,15,14 --weak-rel 0.5`).**
- **J1, depth (primary):** the block's mean Z signal over D = 2 ... 24, signs beyond 2 SE in order: OSCILLATES
  (+ - +), CROSSES ONCE (+ -), STARTS INVERTED, NO CROSSING.
- **J2, vector length at D = 12:** block |v| (X, Y, Z) against the rest: KEPT (>= 0.8 x), SHRUNK (< 0.5 x), MIXED.
- **J3, pair correlation at D = 12:** connected correlation of the block's 3 neighbour pairs in X, Y and Z against
  the rest's pairs: ENTANGLED (in some basis above the rest's mean by more than 3 sd / sqrt(#pairs) and by 0.05),
  else NOT SEEN.

**One sentence per outcome (fixed in advance).**
- J2 KEPT: the gray stretch's signal was turned, not lost; a per-site counter-rotation (stage 2) is worth designing,
  with the axis and angle from the D = 12 vector.
- J2 SHRUNK and J3 ENTANGLED: the signal went into the stretch's neighbour pairs; stage 2 needs a two-qubit
  counter-gate on its couplers.
- J2 SHRUNK and J3 NOT SEEN: the signal left what we can read; no stage 2; the gray stretch is avoided like a dead
  one (as the strict list already does).
- J2 MIXED: reported; stage 2 only on the owner's decision.
- J1 goes with each: OSCILLATES gives the angle per layer.

**Stop.** One job. The cause is not pursued.
