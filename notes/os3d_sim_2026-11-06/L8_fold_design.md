# L = 8 in a folded layout: a design and a CZ estimate (workplace, 2026-11-06; home's 06l item 2; not built, not declared)

## The constraint

A heavy-hex row has 16 columns = 4 blocks of 4. With L = 8 and N = 2, one hex row holds the four half-rows of a
lattice row y: (z0, x 0-3), (z0, x 4-7), (z1, x 0-3), (z1, x 4-7). Within a lattice row y they need four "seams":
two x-bonds (3, 4) (one per z) and two z-bond families (x 0-3 and x 4-7 between z0 and z1). The four half-rows form
a cycle of four seams, but four blocks in a line have only three boundaries: **one seam is always missing**.

## The arrangement (home's hint: value-reversed blocks)

Blocks B0..B3 left to right; odd blocks mirrored (as in v3), and blocks holding x 4-7 value-reversed (local index l
holds x = 7 - l), so that a boundary always pairs the same local index on both sides:

| block | holds | mirrored | value order |
|---|---|---|---|
| B0 | z0, x 0-3 | no | x = l |
| B1 | z1, x 0-3 | yes | x = l |
| B2 | z1, x 4-7 | no | x = 7 - l |
| B3 | z0, x 4-7 | yes | x = 7 - l |

- B0 | B1 (pos 3 | pos 3): z-bonds for x 0-3, each local index must visit pos 3.
- B1 | B2 (pos 0 | pos 0): x-bond (3, 4) of z1 when local index 3 is at pos 0 (x 3 against x 4).
- B2 | B3 (pos 3 | pos 3): z-bonds for x 4-7.
- **Missing:** the x-bond (3, 4) of z0, between B0 and B3 (columns 0-3 and 12-15): one bond per lattice row y.
- y-bonds through the bridges as in v3 (CX-RZZ-CX, 3 CZ, the bridge |0> between uses).
- Each step: one fixed block schedule that makes every local index visit positions 0 and 3 and the bridge positions:
  the 10-swap schedule of FOLD_SCHEDULES (all four positions), the same in every block (mirrored where mirrored).

## The missing seam: two options (to be compared when built)

1. **Long-range RZZ by a CX ladder** along the hex row for the one pair (distance 9 columns at the best moment):
   about 2 x 9 CX on each side plus one RZZ, about 37 CZ per lattice row and step. Fixed by formula; no search.
2. **Carry one value** to the far end and back with a SWAP chain at a fixed moment of the schedule: about
   2 x 8 swaps x 3 CZ = 48 CZ per lattice row and step.
Option 1 is cheaper on paper; option 2 keeps every gate between neighbours already used by the schedule.

## Estimate, 8 x 2 x 2 (M = 2 hex rows, N = 2), per step

- Schedule: 10 swaps per block x 4 blocks x 2 rows = 80 swaps = 240 CZ.
- Native x- and z-bonds (one CZ each): 2 rows x (2 x 3 + 2 x 3 + 4 + 4 + 1) = 42.
- y-bonds through bridges: 8 x 2 = 16 bonds x 3 CZ = 48 (one hex-row pair).
- Missing seam (option 1): 2 rows x about 37 = 74.
- **About 400 CZ per step, about 800 at t = 2**, against v2 rows 1,324 and SABRE's best seed 678 (`cost_fez_2026-11-05.json`).

So the folded L = 8 is expected to be cheaper than v2, but **not cheaper than SABRE** in CZ count. Its gain, if any, is
in CZ layers (fixed schedules run in parallel blocks; v3 at L = 4 had 2-4 times fewer layers than SABRE). This is an
estimate from counting, with no build or compile behind it; the 10-swap schedule dominates, and a schedule that
reaches positions 0 and 3 with fewer swaps would change it most.

## Not search

The block assignment, the mirror and value reversal, the schedule and the seam's route are fixed by formula and by the
constant FOLD_SCHEDULES; at placement time only lattice2d-style translations are tried in a fixed order.
