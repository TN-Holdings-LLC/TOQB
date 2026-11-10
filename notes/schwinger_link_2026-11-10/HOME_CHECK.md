# Home check (2026-11-10): VS Claude's link-qubit Schwinger study and the card's merge option

- VS zip sha256 136da2e0...376b; SHA256SUMS 12 of 12. TOQB 883df84 (new files only) merged into home's main
  (ca9b36f, --no-ff: home had two commits after 2fd563e); psf-os 99d2246 fast-forwarded (card.py option `merge`,
  default off; docs and tests).
- At home: tests/test_schwinger_link.py 12 passed; psf-os tests/test_card.py 66 passed; the merge acceptance
  (notes/card_2026-11-10/merge/card_merge_accept.py) re-run: merged against plain worst 1.4e-13; CZ Heisenberg
  textbook 168 -> 84 (6 -> 3 per bond), heisE line t 4 672 -> 336, Schwinger N 6 80 -> 52, kicked Ising 28 -> 28.
- Home's reading of the link study: the cost per qubit stays below 4 CZ per step for N 6-16 (the swap network 3(N-1)),
  but one qubit per link changes the physics (only neighbouring pairs; M1 and M3 become the same model; nu off by
  0.02-0.1 from t 1). Stopped as instructed. Next candidates (VS): two qubits per link (L in {-1, 0, +1}) or a
  second-order Trotter; neither is decided.
