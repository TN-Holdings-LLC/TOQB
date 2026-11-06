# Long chains around holes: rules without a score (workplace, 2026-11-06; asked by the owner; not declared, no device)

Question: the 91-site chain could not be placed on marrakesh (11-05) or kingston (11-03) because du91's rule needs a
fixed snake shape that, after a translation, touches no failed element. A heuristic walk found a 109-site path on
marrakesh that avoids every failed element, so the device has room; the rule is the limit. Can a rule with no score,
a fixed order and first fit place 51 / 71 / 91 sites there?

Code: `detour.py` (rules A, B, C), `run_check.py` (all records of `notes/du91_2026-11-06/placement.py`),
`check.json`, `marrakesh_1105_N91_ruleC.txt`. Draft: `prereg/drafts-2026-11-06/chain_detour_DRAFT.md`.

## The rules (all fixed before any record is read; starts in the fixed order START_ORDER, first one reaching N used)

- **A, turn before the hole.** Each row is run from the entry column in the row's direction up to the first hole or
  the row's end; the chain turns down at the farthest bridge column of that run; if there is none, the row is run once
  in the other direction. No backtracking. Without holes, start (+1, row 0, column 0) is du91's S1 exactly.
- **B, A plus a bypass.** At a hole inside a row, go round it through the heavy-hex cell of the next row (down a
  bridge, 5 qubits along, up the next bridge). Taken whenever possible.
- **C, fixed-order depth-first walk.** The candidates are all simple paths from a start in one fixed order (along the
  row, then the bridge toward row + v, then toward row - v, then back along the row; a new row reverses direction).
  The first path of N sites in this order is used. No score and no comparison, but it **backtracks** (budget 200,000
  steps per start, fixed).

## Results (`check.json`; "-" = refused; the chain of every success checked: distinct labels, every link a healthy
coupler of the record)

| record | device | N 51: shape / A / B / C | N 71 | N 91 |
|---|---|---|---|---|
| 11-05 daily | marrakesh | - / yes / yes / yes | - / yes / yes / yes | - / - (75) / - (71) / **yes** |
| 11-05 daily | fez | S1 / yes / yes / yes | S3 / yes / yes / yes | S3 / yes / yes / yes |
| 11-04 practice, p6 | marrakesh | S1 / yes / yes / yes | - / yes / yes / yes | - / yes / yes / yes |
| 11-04 practice, p6 | fez | S1 / yes / yes / yes | S3 / yes / yes / yes | S3 / yes / yes / yes |
| 11-03 kim-e | kingston | - / yes / yes / yes | - / yes / yes / yes | - / - (72) / - (72) / **yes** |

(The 11-05 twirl records equal the 11-05 daily ones.) In brackets: the longest chain the rule reached.

- **A** already places 51 and 71 everywhere, including the records where du91's shapes fail (marrakesh 11-05, kingston
  11-03), and 91 on marrakesh 11-04. It stops at 75 / 72 sites for 91 on marrakesh 11-05 / kingston 11-03: holes in
  five consecutive rows narrow the snake row by row.
- **B** does not help (the bypass uses the next row's cell, which the snake then loses).
- **C** places all widths on every record from the first start (+1, row 0, column 0). Steps of the walk for N = 91:
  fez 11-05 776, marrakesh 11-05 1,664, kingston 11-03 56,721 (a walk without backtracking would be 91).

## The marrakesh 11-05 chain of 91 sites (rule C; XX = failed; numbers = chain site; | = unused bridge)

```
row 0   0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15
                 |           |           |          16
row 1   . 31 30 29 28 27 26 25 24 23 22 21 20 19 18 17
          32           |           |           |
row 2   . 33 34 35  .  . XX  .  .  .  .  .  .  .  .  .
                36           |           |           |
row 3   .  .  . 37 38 39 40 41 42 43  .  .  . XX  .  .
           |           |          44           |
row 4   .  . XX 67 66 65 64 63  . 45 46 47  .  .  .  .
                68          62          48           |
row 5   . 71 70 69  . 59 60 61  . 51 50 49  . XX  .  .
          72          58          52          XX
row 6   . 73 74 75  . 57 56 55 54 53 XX  .  .  .  .  .
                76           |           |          90
row 7   .  .  . 77 78 79 80 81 82 83 84 85 86 87 88 89
```

It winds down and back up through the cells of rows 4-6 between the holes, which no snake shape does.

## Through the user entrance

The dual-unitary circuit (`gpu/practice_circuits.p4`, J = b = pi/4, h = 0.1) on this chain, given to `psf-os run2d`
with the marrakesh 11-05 record (offline, nothing submitted): accepted at the copy (0, 0); CZ 405 at t = 4 and 2,205 at
t = 24, exactly (N - 1) / 2 + (N - 1) t = 45 + 90 t, so no SWAP was added. A noiseless MPS check of the 91-qubit
compiled circuit did not finish on the 2 CPUs here (stopped after 10 minutes). **Done instead (06p item 3, by
backward light cones, `lightcone_check.py`):** with the chain from `psf_os.chain.place` (the same chain, 1,665 steps),
run2d's compiled circuits at t = 4 (CZ 405) and t = 8 (CZ 765) give, site by site, the closed form: site t
0.922618835670 (t 4) and 0.851225515933 (t 8), every other site 0; worst deviation over the 91 sites 5.6e-15 and
2.0e-14 (largest cone 10 and 18 qubits).

## What it does not settle

- Whether C counts as search is for the owner: it has no score and takes the first fit in a fixed order (as the
  translations do), but its candidate list is all paths, walked with backtracking.
- A longer, winding chain uses more distinct qubits and couplers; nothing here says it reads as well as a straight
  snake on the device.
- For the dual-unitary problem itself, t <= 24 needs only sites 0..48, so N = 51 (the owner's choice) keeps the content;
  the gain is for problems that need the width.

## Port to psf-os (06p item 1)

`psf_os/chain.py` (psf-os, workplace): rule C as above, iterative, with the step count returned. On every record
here, with grid3d's judgement (suspect=False), it gives the same chains and starts as `detour.chain_dfs`. Default:
the entrance's judgement (suspect=True); see the draft's finding. Tests `tests/test_chain.py` (4): without holes the
first start is the S1 snake; the same record gives the same chain and steps; suspect qubits follow run2d; refusals.
