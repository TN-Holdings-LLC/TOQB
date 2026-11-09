# The Ising line layout in psf-os, and its confirmation without noise (workplace, 2026-11-09; handover 11-08 item 2;
not declared, no device)

## What was done

- psf-os `grid3d_line.py`: VS Claude's `ising_line.py` (TOQB `notes/ising_line_2026-11-08`) moved into psf-os
  unchanged in substance (same constants SCHEDULES, same fixed order of translations: cheapest schedule, then r0, then
  c0; same health check as grid3d since 8b0b34f). Reached as `layout="line"` through `grid3d.physical`, `prepare`,
  `build`, `probe_records` and `run3d --layout line`; never chosen by "auto" (default unchanged).
- New argument `at=[(r0, c0), ...]` of `grid3d.physical` / `prepare` (fold and line): restricts the fixed order to the
  given translations, so the line can be put on the fold's own place for a comparison on the same qubits.
- `physical(..., layout="line")` returns (qc, placed, used, passes) like the fold (home's note: the TOQB version
  returned three values); `probe_build`'s report now names the layout it probed (it wrote "fold" for any layout).
- Tests `tests/test_grid3d_line.py` (6): exact at t 1-3 (4x2x2), CZ 60 / 120 against the fold's 108 / 216, acceptance
  checks at 4x3x2, the line at the fold's place is exact, moves off a failed qubit, "auto" stays fold, 4x4x3 refused.

## Same place, same record, no noise (`same_place.py`, theta 0.6; records of 2026-11-08, `results/os3d-heisE-2026-11-08/fetch_in`)

`same_place.txt`; 4x3x2 at t 2 on fez: `same_place_fez_4x3x2_t2.txt`.

| record | lattice | fold v3.1 place | line at the fold's place: CZ (layers) t 1 / t 4 | fold v3.1: CZ (layers) t 1 / t 4 |
|---|---|---|---|---|
| fez, kingston | 4x2x2 | r0 1, c0 0 | 60 (18) / 240 (72) | 108 (28) / 432 (109) |
| marrakesh | 4x2x2 | r0 1, c0 8 | 60 (18) / 240 (72) | 108 (28) / 432 (109) |
| fez, kingston | 4x3x2 | r0 0, c0 0 | 126 (30) at t 1 | 234 (33) at t 1 |
| marrakesh | 4x3x2 | r0 0, c0 8 | 126 (30) at t 1 | 234 (33) at t 1 |

- At the fold's place the line uses exactly the fold's qubits (18 of 18, 28 of 28) on all three records, with no empty
  swap at 4x2x2 (the bridges fall on line positions 1, 5 there). So a same-qubits comparison of the two layouts in one
  job is possible without any new rule: the line takes the fold's translation (`at=`).
- The line's own first place differs (4x2x2: r0 0, c0 1 on all three; it shares 7 / 7 / 1 qubits with the fold's).
- Placed against `grid3d.exact`: 4x2x2 t 1-4 at most 1.6e-14 (statevector, 18 qubits), 4x3x2 t 1 at most 3.6e-15
  (MPS, 28 qubits); 4x3x2 t 2 on fez by a single-precision statevector: fold 3.4e-7, line 7.5e-7 (single precision; CZ 468 / 252,
  layers 64 / 60). Every arm passed the
  acceptance checks (floor and mirror).
- Fold v3.2 (merge="carry") was not put beside here; VS Claude's table has it (92 / 222 CZ per step).

## For a declaration (not written; the owner decides)

- Arms: fold (v3.1, or v3.2) and line, same job, same place (the fold's chosen place, `at=`), t 1-4; main measure nMSE
  (owner 2026-11-08), retention beside.
- Place: rule "top" picks the place by the fold's own probes; the line then takes that place. Alternatively each layout
  probes its own candidates; then the comparison is no longer on the same qubits.

## Beside: N = 91 by rule C on the records of 11-07 and 11-08 (handover item 5)

`psf_os.chain.place(dev, 91)` (entrance judgement), where du91's shapes find no copy: placed on every record read
(fez daily 11-07 also by shape S3; fez, kingston, marrakesh 11-08 and kingston, marrakesh 11-07 by C only), always
from the first start, 100-1,665 steps (`n91_rule_c.txt`). Whether to run 91 is not decided.
