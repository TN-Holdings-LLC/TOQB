# Boundary table: how far the raw device records read, across problems (workplace, 2026-11-11; not declared, no device)

`boundary.py` builds `boundary.md` and `boundary.json` from committed records only (no number typed by hand; no
circuit file opened). It covers the 24 results in `reproduce.py` RESULTS (papers 7, 8, 9): 207 judged units. Run from
the TOQB root: `python notes/boundary_2026-11-11/boundary.py`.

This is a side-by-side list of records. It is not a declaration, and no boundary line is drawn or fitted.

## One row

One judged unit: one observable, size and step count, as each test declared it.

- Dual-unitary chains (du51, du71, du91, du91r): one row per h. The step count runs 4 to 24 inside the row.
- IBM 2023 (utility): one row per observable.
- 3D tests (physA, heisB, heisE, isingL, lc3d): only the judged place (`chosen`). physA has both the 3D and 2D arm.
- p6, corr, os2d: one row per angle (steps 1 to 9 inside the row). corr has the raw and corrected verdicts.

## Where each column comes from

| column | source |
|---|---|
| qubits | `n` in scores (p6 rows, practice, daily, physA, schw); the length of the per-qubit arrays in scores (corr `gate_rate_per_qubit`, os2d `floor`); `used` in scores (isingL); the size of `mapping` in report.json (heisB, heisE, lc3d); N in the result name (du) |
| CZ | `cz` in scores (du points at the deepest t, physA arms, heis arms, isingL arms, schw items, lc3d rows, utility); `items[tag].cz` or `cz` in report.json (practice, daily) |
| CZ/qubit | CZ / qubits, whole circuit |
| CZ layers | `cz_layers` in scores or report.json where present (physA, heis, isingL, lc3d); empty elsewhere |
| verdict | the declared words copied from scores.json (READS / DOES NOT READ, AGREES / DIFFERS, BEATS, rate verdicts, readable depth, AGREES count) |
| common | `mse / mean_square_answer` or `mse / mean_square_exact` from scores (0.5 is the READS line). du: computed from the points of that h (`on`, `exact`) |
| mirror, floor | `mirror_mean` / `floor_mean` (du at the deepest t; utility `mirror` / `floor`; lc3d `mirror_flip`) |
| cone | utility only: `cone_qubits` in report.json, and the CZ inside the light cone from `gpu/utility_tn_diag.network_diag` |

## Checks (fixed before building)

1. Every one of the 24 results has rows: 24 of 24 (207 units).
2. Every verdict word in the table is read again from its scores.json at its key path: 555 lookups, 0 mismatches.
3. The CZ count matches `notes/paper8/out/tables.json` on the same row (Tables 1, 2, 3, 6, 8, 9): 75 pairs, 0 mismatches.
4. Every row that DOES NOT READ is in figure (a): 4 rows, 4 points. Before utility's qubits were filled it was 2.
5. Light-cone qubits from network_diag against report.json: 4 rows, 0 mismatches.

## Left empty (not in the records the script reads)

- **p6, corr, os2d (2026-11-04): CZ.** build.json counts CZ per cell, which does not map one to one onto the judged
  unit. Reading the circuit files would give the count, but they are not opened here.
- **corr: common.** scores.json has no mean square of the exact values. **lc3d: common.** Its rows are per-distance
  AGREES, with no MSE.
- **utility (filled on 2026-11-11, after a home check):**
  - qubits = 127, the nodes of Eagle's graph (`utility_exact.eagle_edges`), for the whole circuit. CZ (564 / 705 / 690)
    is the whole circuit, with the gates on failed elements left out (they are outside the light cone).
  - Cone CZ = the R_ZZ inside the light cone, 36 / 131 / 253 / 253. It is half of the `"zzd"` slots of
    `gpu/utility_tn_diag.network_diag` (once on the ket side, once on the bra side). It is computed from the circuit
    definition; no circuit file is opened.
  - The light-cone qubits of network_diag equal report.json `cone_qubits` (17 / 37 / 68 / 68).

## Cautions

- **CZ/qubit counts the whole circuit.** For a local observable, the qubits and CZ inside its light cone matter more.
  du is one light-cone site per point, and utility is one observable on Eagle's graph. A large whole-circuit CZ/qubit
  there does not mean the read used all of it.
- **The problem's type matters.** Problems read one site at a time (du, lc3d) and problems where every site depends on
  every gate (Schwinger, the 3D magnetisation) read differently at the same CZ.
- **The "common" measure is after the fact for most tests.** Each test's declared verdict used its own measure (agreement,
  rate, AGREES count). The common measure only puts them side by side.
- **One device, one day per row.** Nothing here generalises beyond that record.
- **Per qubit.** `notes/hubbard_2026-11-11/README.md` quotes "CZ participations per qubit" (2 CZ / qubits), which is
  twice the CZ/qubit here.

## Planned (not in the table)

- 1D Hubbard (paper 9): no device result yet. Estimates are in `notes/hubbard_2026-11-11/README.md`: CZ 10L - 8 per
  step, 12 layers per step.

## Number format

In boundary.md, values below 0.1 are in exponent form. In boundary.json, floats are strings in exponent form with 4
significant digits. Either way, no number with 4 decimals appears (seal.py leakcheck matches those).

## Figures

- `boundary_a_whole.png`: CZ / qubits for the whole circuit against common, every row that has both.
- `boundary_b_cone.png`: the 4 IBM 2023 rows only, CZ inside the light cone against common. In (a), the whole circuit
  has 127 qubits and puts these rows low. What matters for a local observable is the cone, so (b) shows it.
- In both, READS is a circle and DOES NOT READ a cross; the dotted line is 0.5.

## Per-qubit count

CZ / qubits is the definition here. `notes/hubbard_2026-11-11/README.md` first used 2 x CZ / qubits (CZ taken part in
per qubit). It now has a correction with both counts.
