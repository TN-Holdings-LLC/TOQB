# Boundary table, 2026-11-13 (workplace VS Claude; not declared, no device)

The 11-12 table (`notes/boundary_2026-11-12`) is kept as it was. This version adds the four 11-12 results registered
in `reproduce.py`:

- `hub-dt-fez-2026-11-12`: 1D Hubbard L 20 with two time steps (time 0.5 and 1.0), 4 circuits.
- `ohm-fez-2026-11-12` and `ohm-kingston-2026-11-12`: Ohm, 6 cycles, on fez and on kingston.
- `xx91-fez-2026-11-12`: XX chain of 91 qubits, two thetas, 6 step counts.

`boundary.py` started as the 11-12 script, with these changes:

- The hub_score reader now also reads hub-dt and xx91.
- An Ohm reader was added.

Run it from the notebook root: `python notes/boundary_2026-11-13/boundary.py`. It covers 31 results and 262 judged
units. No number is typed by hand, and no circuit file is opened.

## New rows

| result | one row | qubits | CZ | CZ layers | verdict | common |
|---|---|---|---|---|---|---|
| hub-dt | one circuit (L, time, steps) | `qubits` | `cz` | `cz_depth` in check_trybuild.json | `reads`, AGREES count | `mse / mean_square` |
| ohm, ohm-kingston | one arm and cycle count (A0 / A1 / A2 x 3 / 6 cycles) | `N` in build.json (40) | `cz` (the same for all the arm's circuits) | `cz_depth` in build.json (the same for all) | the arm's `reads` and AGREES count in scores.json | the arm's `mse / mean_square` |
| xx91 | one circuit (theta, steps) | `qubits` | `cz` | not recorded (no check_trybuild.json, none in build.json): empty | `reads`, AGREES count | `mse / mean_square` |

**The Ohm unit is "M per circuit (the sum over the right half's 20 qubits)"**, not the per-qubit Z of the other rows:

- The verdict, AGREES and common are the arm's, over its 28 circuits (14 strings and their complements), as
  `gpu/ohm_score.py` judges them.
- The per-qubit Z verdict of each circuit (`z_reads`) is in scores.json, but it is not the declared unit and is not
  in this table.
- Mirror and floor are the means over the arm's circuits.

## Checks (fixed before building)

1. **The four new results have rows:** hub-dt 4, ohm 6, ohm-kingston 6, xx91 12.
2. **Verdict words match scores.json:** every verdict word is read again from its scores.json. 0 mismatches.
3. **The 11-12 rows are unchanged:** all 234 rows of the 11-12 version are present and unchanged in every compared
   field (0 missing, 0 changed).

Still as before:

- The CZ count agrees with paper 8's tables.json: 75 pairs.
- Every DOES NOT READ row is in figure (a): 25 of 25.
- The light-cone qubits match report.json: 11 rows.

## Figures

- (a) and (b) are as on 11-12, with the new rows in (a).
- **(c)** adds hub-dt (4 points) and the Ohm arms (12 points), 107 points in all. XX91 has no recorded CZ layers, so
  it is not in (c).
- The dotted line in each figure is 0.5. No other line is drawn. Each point is one device on one day.

## Cautions

- **The Ohm points read differently from the others.** Ohm judges M, a sum over 20 qubits against its exact value per
  circuit. A small shift in each of the 20 qubits adds up in M, so the Ohm points sit high in (c) at few layers. It
  is a different measure, not a shallower boundary.
- **Same circuits, two devices.** The fez and kingston Ohm rows are the same circuits run on two devices. In
  `ohm-kingston`, A0 at 6 cycles READS while A0 at 3 cycles does not. That is how the declared rule fell on that day.
- **Number format.** Floats are written as in the earlier versions: exponent form below 0.1 in boundary.md, and
  exponent strings in boundary.json (seal.py leakcheck).
