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

## Added 2026-11-13g: the 3D family and the chain candidates of the special condition

Built in psf-os (`psf_os/entrance3d.py` new; `entrance.py`, `cli.py` extended; `tests/test_entrance3d.py` 10 tests;
grid3d.py, user2d.py, compile.py unchanged):

- **3D family** (`grid3d`, tested after `labels`, before `strip`): G a 4 x M x N lattice in the user's own product
  order (M <= 8 rows and N <= 4 blocks of the fold, or the reverse; axes permuted so the side of 4 is grid3d's x;
  N = 1 is a 4 x M square grid). Kicked-Ising circuits (gate for gate `grid3d.logical`) go through `grid3d.prepare`
  itself (fold v3.1 by default, `fold="v3.2"` carry, `fold="line"`). Any other circuit goes through the generic
  fold walker: grid3d's fold layout and fixed block schedules; a gate runs once its qubits' earlier gates have run
  (diagonal gates commute among themselves) and its sites sit where the layout joins them, otherwise one schedule
  round of swaps; y-bonds through the bridge: diagonal gates by CX copies (as grid3d), others by moving the state
  into the empty bridge (2 CX each way). Records as grid3d writes them (labels = site indices), mirror
  `grid3d.mirror_of_compiled`. Cost adds swaps, bridge moves and schedule rounds. Twin and special are refused for
  this family (not wired). Correctness: statevector of the placed circuit (bridges back at |0>) against the logical
  circuit, fidelity 1 to 1e-9 for 4 x 2 x 2 with fSim, RZZ and mixed gates, permuted axes, and a 4 x 3 square grid.
- **Chain candidates for the quirk hook**: with `special="quirk_ledger"` on a chain, the candidates are the chain rule's
  own starts from `psf_os.quirk_chain.candidates(dev, n)` (the workplace VS's; not present here yet, tested with a
  fake); the record says whether the first equals the chain chain_of places. `special=None` is unchanged.

Regression of the 3D jobs (`regress_entrance.py ... 3d`, rows in `regress_entrance.json`): every 3D arm (user, floor,
mirror) of the declared kicked-Ising jobs rebuilt through the entrance from `grid3d.logical` at the arm's recorded
translation and fold version, and every 2D hex arm through the entrance (labels family, user2d's own mirror):

| result | part | device | records equal by gate hash |
|---|---|---|---|
| os3d-physA-2026-11-07 | j1 4 x 4 x 3 | ibm_fez | 162 of 162 |
| os3d-physA-2026-11-07 | j2 4 x 2 x 2 | ibm_fez | 270 of 270 |
| os3d-kingston-top-2026-11-07 | mid 4 x 4 x 3 | ibm_kingston | 54 of 54 |
| os3d-kingston-top-2026-11-07 | big 4 x 6 x 3 | ibm_kingston | 18 of 18 |

The probes and the sentinel of those jobs come from the builder (gpu/os3d_v31_build.py), not from the entrance, so
the comparison is record by record, not of the whole job. Not rebuilt: the Heisenberg 3D jobs of 11-08 (their own
builder, not kicked Ising) and lc3d (line layout with a flipped site). The five 2D jobs above, rebuilt again after
this change: same gate hashes and answers.

Cost of the generic path on the ibm_fez 11-12 record (fSim(pi/4, pi/2) or RZZ(0.3) in colour layers, `cost3d_fez.json`):

| lattice | gate | cycles | CZ | CZ layers | logical layers | swaps | bridge moves |
|---|---|---|---|---|---|---|---|
| 4 x 2 x 2 | fSim | 1 / 2 | 260 / 520 | 70 / 143 | 4 / 8 | 48 / 96 | 8 / 16 |
| 4 x 3 x 2 | fSim | 1 / 2 | 550 / 1046 | 88 / 170 | 5 / 10 | 180 / 342 | 16 / 32 |
| 4 x 4 x 3 | fSim | 1 / 2 | 1392 / 2460 | 100 / 186 | 6 / 12 | 480 / 804 | 36 / 72 |
| 4 x 2 x 2 | RZZ(0.3) | 1 / 2 | 144 / 180 | 37 / 45 | 4 / 8 | 24 / 24 | 0 |

The fSim lattices inflate 15-18 times in CZ layers against the logical layers (swaps dominate). With RZZ the
compiler merges the same pair's angles across cycles, so the second cycle is cheaper.
