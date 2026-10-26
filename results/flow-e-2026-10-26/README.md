# Flow E, 2026-10-26: how much signal the pendant schedule keeps, against the zipper and the holes (report only, no rule)

Declared in prereg/drafts-2026-10-26/pend_lam_note.md (SHA-256 cbea56bd…, `560083c`, 00:55 CET). H100 pod,
`snapshot:marrakesh`, toqb `560083c`, psf-zero `807debe` (a25, psfbind r3); 01:23-01:47 CET. Both repositories reached
the pod as bundles (no network clone). pend_lam.zip SHA-256 c13005f5556626f1ad8ef4b62a3ee8e69963c9748e54fc830090345b266e3a4f.

`toqb.fold_lam` with flow D's settings and seeds: per (n, L) one random model of TOQB's ring classifier and 24 random
inputs, the same for every arm; <Z> of clbit 0 with 256 trajectories on the twin ("sim") and the stand-in ("dev");
z ~ lam z_noiseless + delta. Files: `L8.jsonl`, `L16.jsonl`, the logs, `times.txt`, `rust.txt`.

**Check (declared, not a rule): passed.** The zipper's 24 lines equal flow D's (lam, delta, correlation, two-qubit
count, duration, exactly). Flow D's hole lines are therefore set beside this run's.

**lam, twin / stand-in; two-qubit gates and duration (us): pend / holes / zipper** (holes: flow D)

| n | L | pend | pendbind | holes | zipper | two-qubit gates | us |
|---|---|---|---|---|---|---|---|
| 13 | 8 | 0.85 / 0.86 | 0.85 / 0.84 | 0.60 / 0.57 | 0.58 / 0.58 | 112 / 218 / 232 | 6.5 / 6.3 / 7.2 |
| 14 | 8 | 0.83 / 0.82 | 0.85 / 0.85 | 0.73 / 0.72 | 0.52 / 0.52 | 128 / 208 / 248 | 6.5 / 6.1 / 7.2 |
| 15 | 8 | 0.88 / 0.89 | 0.89 / 0.90 | 0.68 / 0.66 | 0.71 / 0.73 | 144 / 200 / 272 | 6.6 / 6.4 / 7.2 |
| 16 | 8 | 0.83 / 0.79 | 0.84 / 0.81 | 0.72 / 0.70 | 0.54 / 0.55 | 160 / 192 / 288 | 6.6 / 5.9 / 7.2 |
| 17 | 8 | 0.86 / 0.88 | 0.85 / 0.88 | 0.85 / 0.86 | 0.65 / 0.65 | 176 / 184 / 312 | 6.6 / 5.3 / 7.2 |
| 18 | 8 | 0.75 / 0.73 | 0.75 / 0.75 | 0.81 / 0.82 | 0.61 / 0.58 | 192 / 176 / 328 | 6.5 / 5.1 / 7.2 |
| 13 | 16 | 0.71 / 0.72 | 0.72 / 0.69 | 0.12 / 0.07 | 0.27 / 0.25 | 224 / 434 / 464 | 10.2 / 9.7 / 11.7 |
| 14 | 16 | 0.66 / 0.64 | 0.66 / 0.66 | 0.11 / 0.19 | 0.19 / 0.17 | 256 / 416 / 496 | 10.2 / 9.4 / 11.7 |
| 15 | 16 | 0.72 / 0.71 | 0.71 / 0.70 | 0.26 / 0.32 | 0.30 / 0.31 | 288 / 400 / 544 | 10.4 / 10.1 / 11.7 |
| 16 | 16 | 0.73 / 0.71 | 0.73 / 0.72 | 0.40 / 0.43 | 0.33 / 0.33 | 320 / 384 / 576 | 10.4 / 8.8 / 11.7 |
| 17 | 16 | 0.62 / 0.62 | 0.63 / 0.59 | 0.49 / 0.47 | 0.21 / 0.21 | 352 / 368 / 624 | 10.4 / 7.7 / 11.7 |
| 18 | 16 | 0.51 / 0.51 | 0.54 / 0.47 | 0.56 / 0.51 | 0.30 / 0.34 | 384 / 352 / 656 | 10.2 / 7.3 / 11.7 |

**Read (no rule, nothing chosen from it).**

- **Vanity:** at n = 13-17 the pendant schedule has the fewest two-qubit gates (L = 16: 224-352, against the holes'
  368-434 and the zipper's 464-624) on n qubits (the holes use 20).
- **What a device user needs (on TOQB's models, not a device):** at n = 13-17 the pendant schedule keeps the most
  signal in every value: at L = 16, 2.1-4.0 times the zipper's (shots for the same precision 1/lam^2: 4.4-16 times
  fewer) and, at n = 13, 14, 3.4-9.7 times the holes'. Flow D's valley at n = 13, 14, L = 16 (holes 0.07-0.19) is
  gone (pend 0.64-0.72). At n = 18 the holes keep as much or more (L = 16: 0.56 / 0.51 against 0.51 / 0.51; L = 8:
  0.81 / 0.82 against 0.75 / 0.73).
- **The count rule** (the workplace's proposal, owner's decision open): choose pendants when n - m_below < 2 (m_above -
  n), holes otherwise. Its choice (pend at n = 13-17, holes at n = 18) agrees with the larger lam at both depths on
  both models, with n = 17 at L = 8 and n = 18 at L = 16 on the stand-in close to a tie.
- `fold:pendbind` (single-qubit runs merged) is within 0.04 of `fold:pend` everywhere: no difference shown.
- n = 18's pendants are on another 12-cycle than n = 13-17's (the first has 5 spots; workplace review, item 5b), so a
  step between n = 17 and 18 may come from the place; its correlation with the noiseless model at L = 16 is also the
  lowest (0.85, against 0.96-0.98 at n = 13-17).

**Not claimed.** No device; the twin and the stand-in are TOQB's models of a 2026-10-13 calibration. One random model
per cell, one seed; at L = 16 a difference of about 0.1 is within the estimate's spread (flow D). The pendant
schedule is in TOQB's analysis arm `fold:pend`, not in PSF-Zero's compiler.
