# Flow H, 2026-10-26: holes against the zipper where item 50's rule keeps the most holes

Declared in prereg/drafts-2026-10-26/holes_vs_zip_note.md (SHA-256 ecc156b4…, `d4ce74d`, 06:18 CET); amendment 1
(n = 10 on the pod). n = 8, 9: cloud CPU, 06:18-08:18 CET, `part0.jsonl` (models 0, 1), `part1.jsonl` (models 2, 3).
n = 10: H100 pod, 11:27-11:28 CET, `n10.jsonl` (flow_h_n10.zip SHA-256 7d39a60b…). Check: model 0 at n = 9 (CPU)
and n = 10 (GPU) equals flow D's L16 lines exactly.

| n (holes) | verdict | holes' lam, 4 models (twin / stand-in) | zipper's lam | two-qubit gates, us: holes / zipper |
|---|---|---|---|---|
| 8 (4) | **LOSS** (0 of 4 won, 4 lost) | 0.10-0.19 / 0.11-0.18 | 0.19-0.25 / 0.21-0.23 | 260, 11.2 / 256, 11.7 |
| 9 (3) | **WIN** (4 of 4) | 0.26-0.37 / 0.26-0.41 | 0.07-0.16 / 0.09-0.16 | 240, 10.0 / 304, 11.7 |
| 10 (2) | **WIN** (4 of 4) | 0.51-0.56 / 0.50-0.57 | 0.09-0.17 / 0.11-0.19 | 224, 8.3 / 336, 11.7 |

At n = 8 the rule's counts tie (8 extra per layer each; the holes' 260 include two more per layer where holes meet),
and the zipper kept more signal on every model. As declared, this is a proposal for item 50's tie rule (ties to the
zipper), not a change.

The prediction held at n = 9, 10 (WIN); at n = 8 (4 holes) the zipper kept more on every model. Not a device; the
marrakesh snapshot's twin, which flow G found pessimistic for the zipper, so the size of the n = 9, 10 leads is an
upper bound.
