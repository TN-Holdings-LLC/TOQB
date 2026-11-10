# Home check of VS Claude's problem cards (2026-11-10)

- VS zip sha256 3dbf8e12...434a; its SHA256SUMS hold (10 of 10).
- psf-os bundle 0fb4512..82560ff verified and fast-forwarded at home (one commit, The Architect; new files only:
  psf_os/card.py, docs/card.md, examples/cards/, tests/test_card.py; user2d.py and compile.py untouched).
- `tests/test_card.py`: 64 passed at home.
- `scripts/card_accept.py` re-run at home against this TOQB: A (kicked Ising 4x2x2) worst 1.4e-13, B (Heisenberg
  4x2x2, textbook order and heisE's own orders, kingston 11-08, 48 cases) worst 1.2e-13, C (Schwinger N 6, M1) worst
  1.7e-14: all MATCH, tolerance 1e-10.
- Home's view of VS's points: the per-step `orders` extension is needed (one order for every step misses by up to
  2.2e-2 for heisE and 5.4e-2 for Schwinger: the order is part of the problem as run); kept. Next steps, not done:
  a placement should return its own order as a card (so the card can state the circuit actually run); commuting
  terms on one pair merged into one gate (Heisenberg 6 CZ per bond in the card against at most 3 in heis3d).
