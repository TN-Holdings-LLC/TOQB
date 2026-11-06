# Daily pool 2026-11-05: answer values released (owner's decision, 2026-11-05 04:34 CET)

The owner decided (11-05, relayed at the workplace): the fixed problem is **FX-A**; the answers **may be seen at home**,
so that home can score each run at once. The blind protocol of `prereg/drafts-2026-11-05/daily_record_DRAFT.md` is not
adopted.

These are the sealed files of 12164be, unchanged: every `<ID>.json` and `answers.json` matches
`../sha256.txt` (committed in 12164be, before this release; checked at the release with `sha256sum -c`).
The commit order (hashes 12164be < these values) shows the answers were fixed before they were released.

- D01-D32 and FX-B: exact (state vector; light cones <= 33 qubits), K1-K4 passed (see `../checks.json`).
- FX-A: sealed on 11-04 (`results/bank-2026-11-04/pod/du_bank/answers.json`, h 0.15, b = pi/4 - 0.3, t 12).
- S01-S06: computed on 2026-11-06 (below).
- H01-H03 (hard problems, task W, 2026-11-06): `H01.json`, `H02.json`, `H03.json`, `answers_hard.json`, unchanged
  from the seal: their four lines were appended to `../sha256.txt` in 89af41e (the 34 lines of 11-05 unchanged), and
  the files match them (`sha256sum -c` at this release). Order: hashes 89af41e < these values. Exact (H01, H02 light
  cones <= 31 qubits; H03 the whole 2^32 state), K1-K3 passed (`../hard/checks.json`).
- S01-S06 (scale problems on B102, done 2026-11-06): `S01.json`-`S06.json`, `answers_scale.json`, unchanged from the
  seal: their seven lines were appended to `../sha256.txt` in 4f8a568 (every earlier line unchanged) and the files
  match them (`sha256sum -c` at this release). Order: hashes 4f8a568 < these values. Exact (light cones <= 31
  qubits), K1-K3 passed (`../scale/checks.json`).
- Y001-Y078 (curveball grid, task Y, 2026-11-06): `Y001.json`-`Y078.json`, `answers_curve.json`, unchanged from the
  seal: their 79 lines were appended to `../sha256.txt` in 6c30dd8 (every earlier line unchanged) and the files match
  them (`sha256sum -c` at this release). Order: grid and rules 90152ed < hashes 6c30dd8 < these values < the
  selection. Exact (P32 whole 2^32 state; B72 light cones <= 19 qubits), K1-K3 passed (`../curve/checks.json`).
