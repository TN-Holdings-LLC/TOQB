# Is "READS" set by the share r the device keeps? (workplace, 2026-11-13; desk only)

Home's instruction of 01:50 CET. `r_thread.py` collects every judged unit whose device values z and exact values e
can be had, splits each exactly as MSE / mean square = (1 - r)^2 + rest (r = sum z e / sum e^2, rest = mean of the part
of z orthogonal to e, over the mean square of e), and draws (a) MSE / mean square against (1 - r)^2, (b) r against CZ
layers, (c) r against CZ per qubit. Outputs: `r_thread.json` (every unit, and every unit of the boundary table that
could not be had, with the reason), `r_thread.txt`, the three figures. Results/ and declarations untouched.

## What could be had (107 units; identity worst 2.1e-16; recomputed MSE / mean square equal to the stored up to 6.6e-5,
## scores.json keeping z to 4 digits)

Hubbard 11-11 (U4 and the U0 ruler, 40-120 qubits), hub-dt 11-12, XX91 11-12 (both thetas), IBM 2023 utility 11-10 and
11-11 (per theta point), isingL 11-10 (48 arms, from the cards), Ohm 11-12 fez and kingston at the Z level (per arm
and cycle count, the 28 circuits together; recomputed here, not a declared unit: the declared unit was M per circuit).
Not had (187 units of the boundary table): physA, heisB / heisE, Schwinger, practice, daily (scores keep only scalars),
p6, os2d, du51 / 71 / 91 (scores keep per-step or per-t summaries that do not give the declared MSE), du91r rates,
lc3d fronts, corr (derived values). Rebuilding them from the cards and their own answer formats was not attempted in
the two hours.

## Numbers (beside, not verdicts)

| family | units (READS) | r >= 0.293 gives the verdict | rest's share of MSE / mean square | r falls by e every |
|---|---|---|---|---|
| XX91 theta pi/4 | 6 (3) | 5 / 6 (12 steps: r 0.327, ratio 0.506) | 0.19 | 42 CZ layers |
| XX91 theta pi/2 | 6 (3) | 5 / 6 (12 steps: r 0.308, ratio 0.504) | 0.12 | 36 |
| Hubbard U4 | 10 (8) | 8 / 10 (6 steps: r 0.42 and 0.38, ratio 0.64 and 0.71) | 0.52 | 71 |
| Hubbard ruler U0 | 10 (8) | 10 / 10 | 0.52 | 30 |
| Hubbard U4, two step sizes | 4 (4) | 4 / 4 | 0.49 | (12-48 layers only) |
| IBM 2023 utility | 11 (9) | 11 / 11 | 0.59 (Z106 almost all rest; weight-10 / 17 almost all shrink) | (no CZ layers in the table) |
| Ising 3D (isingL) | 48 (48) | 48 / 48 (r 0.47-0.91) | 0.38 | 279 |
| Ohm Z level A0 / A1 / A2 | 4 / 4 / 4 (all) | all | 0.25-0.27 | 81 / 110 / 141 (fez and kingston mixed) |

## In a few words (within these records; most are one device and one day)

- Where the device's error is mostly a uniform shrink (XX91: rest 0.12-0.19 of the ratio; weight-10 and weight-17), the
  r = 0.293 line gives the verdict: the units sit on the diagonal of figure (a), and the two that disagree (XX91 at 12
  steps) are at the line itself (r 0.31-0.33, ratio 0.504-0.506, rest 0.03-0.05).
- Hubbard U4 does not follow it: at 6 steps the device keeps r 0.38-0.42 and still does not read, because the rest
  (a wrong shape of the pattern, 0.30-0.32) is as large as the shrink (0.34-0.39). Half of its error is rest at every
  depth (0.49-0.52 of the ratio), so for it the line in r sits higher than 0.293.
- r falls with CZ layers at family-dependent rates (e every 30 to 279 layers), so "the boundary is set by the share
  kept, which falls with CZ layers at a family-dependent rate" holds for the shrink-dominated families; for families
  with a large rest (Hubbard U4, the Hubbard ruler) r alone is not enough, and the boundary comes earlier than r says.
- Not shown: whether the rates are properties of the family or of the device and day (one device per family here,
  except Ohm); the 187 units not had.
