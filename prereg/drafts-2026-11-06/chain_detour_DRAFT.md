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

## Proposal for the order (workplace, 2026-11-06; home's 06p item 2; not fixed)

1. **Shape rule first.** du91's shapes in the fixed order SHAPES, each with lattice2d's translation copies in their
   fixed order; the first qualifying copy of the first qualifying shape (as today).
2. **Rule C only if no shape qualifies.** `psf_os.chain.place(dev, N)` (psf-os, workplace port): the first start in
   START_ORDER that reaches N sites, with the entrance's health judgement (`suspect=True`, the judgement of
   lattice2d.check that run2d applies).
3. **Otherwise REFUSED**, one line, as the daily record's amendment of 2026-11-06 says; nothing else is tried.

Recorded per chain: which rule placed it (shape name and copy, or "C" with start, steps, budget and starts tried),
the chain's labels, and the device record it was read from. The user circuit is then written on those labels and goes
through run2d unchanged.

Why shape first: every chain run so far keeps exactly the placement it had (fez 11-05: S1 at drow 4 for 51), so no
earlier result changes meaning; C is only a way out where nothing qualified before. "C alone" is the other option:
C's first start is S1 itself on a record without holes in rows 0-6, but where shapes qualify after a translation
(fez 11-05) C picks other rows, so chains would move between days for the same device.

On the records so far (`notes/chain_detour_2026-11-06/`, entrance judgement):

| record | N 51 | N 71 | N 91 |
|---|---|---|---|
| fez 11-05, 11-04 | shape S1 | shape S3 | shape S3 |
| marrakesh 11-05 | C | C | C (1,665 steps) |
| marrakesh 11-04 | shape S1 | C | C |
| kingston 11-03 | C | C | REFUSED (longest 87: every start exhausted) |

Kingston 91 is placeable under grid3d's judgement (ends of failed couplers allowed), but run2d would refuse that chain;
see the finding below.

## Finding: the 2D and 3D placements judge "the ends of a failed coupler" differently

lattice2d.check (2D, run2d) refuses a qubit at an end of a failed coupler ("suspect"); grid3d since 8b0b34f refuses
only failed qubits, failed couplers and non-couplers, so a 3D placement may use a suspect qubit. The rule C port
follows the entrance (suspect=True) so that its chains pass run2d; with suspect=False it is grid3d's judgement
(instruction 06p asked for grid3d's; the default was changed for this reason and can be set back). The declared 3D
test of tonight uses grid3d's judgement as declared; nothing there changes, but a suspect qubit in its arm A, if any,
should be named in the night's README.
