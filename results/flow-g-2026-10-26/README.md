# Flow G, test match 3, 2026-10-26: the count rule against the zipper on the twin of ibm_kingston's 2026-10-24 calibration (rule declared)

Declared in prereg/drafts-2026-10-26/rule_match_k_note.md (SHA-256 c1cddfb6…, `4a7e6bb`, 05:07 CET). H100 pod, toqb
`8726ca1`, psf-zero `62ae3c2`; 11:27-11:56 CET. Device: the Target of flow C (SHA-256 3b939138…), twin only. L = 16,
P 24, T 256, models 0-3. rule_match_k.zip SHA-256 4f21aab3eeaedb585c31abf7f4e54fd4507295e046791c916d678e8f01c6718d.

| n | verdict (models won) | rule's lam | zipper's lam | ratio | two-qubit gates | us | active qubits |
|---|---|---|---|---|---|---|---|
| 13 | **WIN** (4/4) | 0.76-0.81 | 0.64-0.70 | 1.15-1.19 | 224 / 464 | 9.2 / 10.8 | 13 / 13 |
| 14 | **WIN** (4/4) | 0.73-0.82 | 0.63-0.77 | 1.07-1.18 | 256 / 496 | 9.2 / 10.8 | 14 / 14 |
| 15 | **WIN** (4/4) | 0.78-0.81 | 0.67-0.69 | 1.15-1.19 | 288 / 544 | 9.3 / 10.8 | 15 / 15 |
| 16 | **WIN** (4/4) | 0.77-0.80 | 0.60-0.70 | 1.12-1.28 | 320 / 576 | 9.3 / 10.8 | 16 / 16 |
| 17 | **WIN** (4/4) | 0.69-0.75 | 0.58-0.65 | 1.15-1.28 | 352 / 624 | 9.3 / 10.8 | 17 / 17 |
| 18 | **WIN** (3/4) | 0.61-0.68 | 0.63-0.66 | 0.98-1.06 | 352 / 656 | 6.7 / 10.8 | 20 / 18 |

The prediction (WIN at every n, with smaller ratios than flow F's 1.5-8.2) held.

- **Vanity:** six WINs, 23 of 24 models; about half the zipper's two-qubit gates, a shorter duration.
- **What a device user needs (a twin of a real day's calibration, the kind that matched the device for the zipper on
  2026-10-24):** the lead is **1.07-1.28 times** the zipper's lam at n = 13-17 (shots for the same precision 1.15-1.6
  times fewer), and about even at n = 18 (holes). Flow F's 1.5-8.2 times on the marrakesh snapshot came mostly from
  that snapshot's pessimism for the zipper (on model 0 at n = 13 the zipper's lam is 0.27 there, 0.66 here); the
  direction did not change, the size did.
- Not a device; one day's calibration of one device; random models.
