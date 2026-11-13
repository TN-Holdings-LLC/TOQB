# The entrance, built (workplace, 2026-11-13; OS gap 2 of the owner's list; desk only, no device, no POD)

Design: `DESIGN.md` (this folder). Built in psf-os: `psf_os/entrance.py` (new), `psf_os/strip.py` (new, the honeycomb
strip rule ported from `notes/ohm_honeycomb_2026-11-13/hc_estimate.py`), `psf_os/chain.py` (functions added only:
`SHAPES`, `snake`, `shape_place`, `chain_of`, ported from `daily/du91.py` and `gpu/hub_build.py`; rule C unchanged),
`psf_os/cli.py` (`psf-os entrance check / build / score`), `tests/test_entrance.py` (12 tests).
Not changed: `user2d.py`, `compile.py`, the builders of this notebook, any declaration, results/.

## What it does

From logical circuits (qubit k = logical site k), grouped by their own interaction graph (as hub_build placed each L
on its own chain), the fixed tests in this order: chain (path), ring (cycle), Heron labels (every edge a coupler),
honeycomb strip (in the strip's own label order). Then user2d.build_batch (translation copy, compile, floor, mirror,
one ring sentinel), with the mirror from the compiled circuit by default (set for the build only and restored), the
sentinel fallback and the Clifford twin as options, and the `special` hook (`quirk_ledger`: the qualifying translation
copies ranked by `psf_os.quirk.rank`, the first pinned for the build only; psf_os/quirk.py is the VS's and is not
present yet, so it is tested with a fake). build.json records the family, the tests, the placement, the mapping,
`special` (null by default), mirror, sentinel fallback, twin and the cost. The score: user2d's card plus READS /
AGREES / r and the split (1 - r)^2 + rest, and for twins r_twin against 1 - 1/sqrt(2) with the r thread's caveat.

## Refused now (with the reason)

3D and 2D square grids (4-cycles; heavy-hex has none), a site of degree above 3, a disconnected graph, anything else;
a ring whose rule outline needs pendants or holes (those schedules are written for the ring classifier only); a family
that does not fit the day's record says why (e.g. ibm_marrakesh 11-12: "chain of 91: rule C: no start reaches 91 sites;
longest 84") and the entrance does not move to another family on its own.

## Regression (`regress_entrance.py`, `regress_entrance.json`)

The declared jobs built through the entrance from their logical circuits alone, on the records they were built from,
with the builders' shots and max_seconds: the gate hash equals the recorded job's, and the answers written by label
equal the recorded answers file, for all five.

| job | device | groups (family, n, rule) | gate hash | recorded | answers by label |
|---|---|---|---|---|---|
| hubbard-2026-11-11 | ibm_fez | chain 40 S1, chain 60 S3 | 1af20d01467a24aa | same | same |
| xx91-2026-11-12 | ibm_fez | chain 91 rule C | 9e8330a96154f469 | same | same |
| ohm-2026-11-12 | ibm_fez | chain 40 S1 | 860d31336b97d2d1 | same | same |
| ohm-kingston-2026-11-12 | ibm_kingston | chain 40 S1 | 138851f7f748750b | same | same |
| hubbard-big-2026-11-11 | ibm_fez | chain 90 C, chain 120 C | ebe6b5c27190b872 | same | same |

`chain.chain_of` equals `gpu/hub_build.chain_of` on all 32 device records under results/ at n = 24, 40, 60, 90, 91
(test with TOQB_DIR). hub-dt was not run through the entrance (its builder reads answers per file; left out for time).

## Limits

The boundary hint reads `notes/boundary_*/boundary.json` when given; rows without CZ layers (xx91, utility, du91 among
them) give no hint. Recognition is by labelled tests: a strip written in another label order, or a ring that is not a
plain cycle on the device, is refused rather than searched. Observables other than per-qubit Z are not in the card.
