# Boundary table, 2026-11-12 (workplace VS Claude; not declared, no device)

The 11-11 table is kept as it was (`notes/boundary_2026-11-11`). This version adds the three 11-11 night results that
home registered in `reproduce.py`:

- `utility-depth-fez-2026-11-11`: Z106 at 4 to 8 steps and weight-10 at 5 and 6 steps.
- `hubbard-fez-2026-11-11`: 1D Hubbard, L 20 and 30, at 2, 4 and 6 steps, U = 4 and the U = 0 ruler.
- `hubbard-big-fez-2026-11-11`: L 45 and 60, at 2 and 4 steps.

`boundary.py` started as the 11-11 script, with two readers added:

- The utility reader now takes any observable in scores.json.
- A new Hubbard reader makes one row per L, steps and arm.

It writes `boundary.md`, `boundary.json` and three figures. Run it from the TOQB root:
`python notes/boundary_2026-11-12/boundary.py`. It needs matplotlib for the figures and rustworkx for the light-cone
count. It covers 27 results and 234 judged units. No number is typed by hand, and no circuit file is opened.

## New columns' sources

| result | qubits | CZ | CZ layers | verdict | common | cone |
|---|---|---|---|---|---|---|
| utility-depth | 127, the nodes of Eagle's graph | `cz` in scores | not recorded | `reads`, AGREES count | `mse / mean_square_exact` | `cone_qubits` in report.json; CZ inside the cone = half of network_diag's `"zzd"` slots, as on 11-11 |
| hubbard, hubbard-big | `qubits` in scores | `cz` in scores | `cz_depth` in `check_trybuild.json` (24 / 48 / 72 at 2 / 4 / 6 steps) | `reads`, AGREES count | `mse / mean_square` | not local, empty |

## Checks (fixed before building)

1. **The three new results have rows:** utility-depth 7, hubbard 12, hubbard-big 8.
2. **Verdict words match scores.json:** every verdict word is read again from its scores.json at its key path. 0
   mismatches; the count of lookups is in boundary.md.
3. **The 11-11 rows are unchanged:** all 207 rows of `notes/boundary_2026-11-11/boundary.json` are present. The fields
   qubits, CZ, CZ/qubit, CZ layers, verdict, common, mirror, floor, cone qubits and cone CZ were compared in the 11-11
   number format: 0 missing, 0 changed.

Still as on 11-11:

- The CZ count agrees with paper 8's tables.json: 75 pairs.
- Every DOES NOT READ row is in figure (a): 8 of 8.
- The light-cone qubits from network_diag equal report.json's: 11 rows.

## Figures

- `boundary_a_whole.png`: CZ / qubits (whole circuit) against common.
- `boundary_b_cone.png`: the IBM 2023 rows (11-10 and 11-11) against the CZ inside the light cone.
- `boundary_c_layers.png`: CZ layers against common. It shows every Hubbard row, with U 4 and U 0 marked differently,
  and every other row whose CZ layers are recorded (physA, heisB, heisE, isingL, lc3d). Filled marks READ; open marks
  DO NOT READ.
- The dotted line in each figure is the READS line, 0.5. No other line is drawn.

## Cautions

- **Different problems on one axis.** The Hubbard rows and the 3D rows are different problems. Every site of the
  Hubbard chain depends on the gates, so the whole circuit matters. Figure (c) only puts the records side by side.
- **The U 0 ruler is a different case.** Its exact value is a free-fermion result, and its verdict uses the same
  READS rule.
- **One device, one day.** Each point is one device on one day (ibm_fez, 2026-11-11, for the new rows). Nothing here
  generalises beyond that record.
- **Number format.** In boundary.md, values below 0.1 are written in exponent form. In boundary.json, floats are
  strings in exponent form. Either way, no number with 4 decimals appears (seal.py leakcheck).
