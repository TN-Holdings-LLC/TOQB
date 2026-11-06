# DRAFT (not declared; workplace, 2026-11-06; asked by the owner): chains placed around holes, no score

Status: a draft for home and the owner. Nothing is fixed. Evidence: `notes/chain_detour_2026-11-06/`.

## Purpose

Let a chain experiment (dual-unitary chain, P4-type chains) of N sites run on a device whose failed elements leave no
copy of a fixed snake shape, without choosing a placement by any score.

## Candidate rules (one to be chosen by the owner, before any record is read)

- **A, turn before the hole (no backtracking).** Starts in the fixed order START_ORDER (vertical direction +1 then -1;
  rows in order; column 0 then 15). In each row: run from the entry column in the row's direction over healthy qubits
  and couplers up to the first hole or the row's end; turn at the farthest bridge column of the run that has a
  healthy bridge and a healthy qubit below; if none, run the row once in the other direction; the next row runs
  opposite. The chain is the first N sites; the first start that reaches N is used. Equals du91's S1 when there is no
  hole. On the records so far: 51 and 71 everywhere; 91 refused on marrakesh 11-05 (75) and kingston 11-03 (72).
- **C, fixed-order depth-first walk (backtracks).** Same starts; candidates are all simple paths, in the fixed
  neighbour order (along the row, bridge toward row + v, bridge toward row - v, back along the row; a new row reverses
  direction); the first path of N sites is used; at most 200,000 steps per start. On the records so far: every width
  on every record, from the first start (marrakesh 11-05, N 91: 1,664 steps).
- (B, a bypass through the next row's cell, was tried and is not proposed: it does worse than A.)

## Fixed for either rule

- Healthy = not a failed qubit, not a failed coupler, and a coupler of the record (psf-os's check since 8b0b34f).
- Reads only the device record (coupling graph, failed marks); no calibration number. The calibration beside
  (`gpu/calib_beside.py`) is reported per chain as decided for the 3D test, report only.
- The user circuit is written on the chain's labels and goes through `psf-os run2d` as any user circuit (translation
  only); answers depend only on the chain's site order, so the sealing is unchanged.

## For the owner to decide

1. A or C (or neither). A is a plain rule with no backtracking, but it does not reach 91 on the two records with holes
   in many rows. C reaches every width, but walks with backtracking: no score, first fit in a fixed order, yet its
   candidate list is all paths.
2. Whether N = 91 is wanted at all: for the dual-unitary chain with t <= 24 the answer depends on sites 0..48 only
   (the reason for N = 51).
3. If adopted: to which experiments it applies, and that the shape rule stays first (the detour rule only when no
   shape qualifies), or the detour rule alone.

## Limits

Placement only. A winding chain uses more distinct couplers than a straight snake; its reading on a device is untested.

## Owner's decision (2026-11-06 07:38 CET)

- **Rule C adopted.** In the owner's words: holding to a rule when the placement can be made is ego; this time C is
  **not counted as a search, on the ground of reproducibility** (no score, a fixed neighbour order, the first fit;
  the same record gives the same chain, with its step count recorded).
- Items 2 and 3 above (whether N = 91 is run, and to which experiments the rule applies, shape rule first or not) are
  not decided by this; the earlier decision (task X: N = 51 on fez only) stands until the owner changes it.
