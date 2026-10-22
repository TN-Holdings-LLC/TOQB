# Depth sweep, the zipper against item 31 (report only; rule fixed before the run in prereg/drafts-2026-10-22/zip_depth_note.md, `0bbf228`)

H100 pod, 2026-10-22 13:40-15:56 CEST (24 runs of design C, then the undamped readout); `score.md` is the score as
written on the pod (`toqb.zip_depth_score`); zip SHA-256 e62ed790c1b6d4e736b6db141cdf69084fcd708df7a7a1042f5466157d774201.
All runs valid; the undamp step reproduced the stand-in's shots on all 24. Pod paths written `<pod>/`.

## The rule (undamped stand-in CE without shots, Holm over 3 teachers, alpha 0.01; noiseless CE in the same order)

| L | teachers counted | widened |
|---|---|---|
| 8 | 3 of 3 | YES |
| 12 | 1 of 3 (2 TIE) | no |
| 16 | 3 of 3 | YES |
| 20 | 2 of 3 (1 TIE) | YES |

## Vanity and essential numbers (means over the 3 teachers)

| L | undamped CE, no shots: item 31 / zipper | raw CE: item 31 / zipper | lam: item 31 / zipper | shots for 250-shot noise: item 31 / zipper |
|---|---|---|---|---|
| 8 | 0.404 / 0.364 | 0.554 / 0.548 | 0.398 / 0.375 | 1,576 / 1,778 |
| 12 | 0.462 / 0.437 | 0.606 / 0.615 | 0.282 / 0.244 | 3,141 / 4,214 |
| 16 | 0.510 / 0.459 | 0.633 / 0.644 | 0.248 / 0.167 | 4,059 / 8,977 |
| 20 | 0.556 / 0.490 | 0.644 / 0.662 | 0.249 / 0.113 | 4,040 / 19,518 |

- Vanity: by the rule the zipper widens the range at 3 of 4 depths, by up to 0.106 in CE (L 20, teacher 11).
- Essential: the zipper's lam falls with depth much faster than item 31's (0.113 against 0.249 at L 20). Read raw
  it is worse from L 12 on; undamped with the run's own 250 shots its L 20 CE rises to 0.75-0.87 (`progress.txt`),
  worse than raw. The gain needs 1 / lam^2 more shots: 4.8 times item 31's at L 20 (QPU 2,656 against 566 s per 500
  points).
- Where the gain comes from: the trained model itself. The zipper's noiseless CE is lower in 11 of 12 cells
  (L 12 teacher 13 the exception). Together with the noise-source check (results/lam-ablate-2026-10-22: on the
  zipper's circuit the twin's noise acts as one uniform shrink, on item 31's it does not), one reading, not tested:
  a uniform shrink scales the training gradient without bending it, so training through the zipper finds a better
  model of the task.
- No depth reached chance (undamped CE >= 0.683) up to L 20, on the stand-in.
- Not claimed: one seed; the stand-in is TOQB's twin of a 2026-10-13 calibration; on the device of 2026-10-22 the
  twin under-stated PSF's lam by 2 to 2.7 times, so the shot cost on a device is unknown.
