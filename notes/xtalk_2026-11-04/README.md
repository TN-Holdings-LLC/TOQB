# Crosstalk test tools (workplace, 2026-11-04; draft, not declared)

For `prereg/drafts-2026-11-04/xtalk_note_DRAFT.md` (skeleton; filled after tonight's P6/OS2D results).

- `../../gpu/xtalk_device.py`: builds the job (S and D arms interleaved, floor, mirrors, 7 readout patterns, ring
  sentinel). Dry runs: `out/dry_build_Fake*.json` (39 circuits, 46.5 s by the model, all accepted; CZ layers per step
  3 -> 6; pattern coverage d1 all, d2 about 83 %, d3 all).
- `xtalk_answers.py`: sealed answers (per-qubit cone, per-edge union-of-cones triple). FakeKingston's lattice:
  t = 5 union max 23 qubits, 137/137 edges with maxq 24, 224 s per theta.
- `xtalk_score.py`: reads the finished job and runs `psf_os.crosstalk2d.analyse` (bootstrap 200, seed 0). Checked for
  plumbing only on the fake dry-run job with made-up product-state counts (no correlations by construction: R about 0,
  verdicts NOT TESTED); those counts are not data and are not kept.

The analysis itself is tested in psf-os `tests/test_crosstalk2d.py` (7 tests: split equivalence, acceptance and a
missing barrier, pattern read-back, planted correlated readout recovered by the pair model, end to end).
