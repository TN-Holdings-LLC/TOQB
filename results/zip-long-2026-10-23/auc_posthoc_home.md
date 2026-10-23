# Post hoc (home, 2026-10-23): offset-free comparison by AUC, after the workplace's per-point tests

The workplace's note (`workplace_undamp_2026-10-23/`, as received) found that at 16,000 loops item 31's raw accuracy
deficit is mostly a readout offset (it calls +1 on 82-92 % of the points). Home's earlier reading, that the noiseless
accuracy shows a better model "with no offset involved", was **overstated**: item 31's own trained model is offset
too (its noiseless output calls +1 on 59-70 % of the test points at 2,000 and 16,000 loops; the zipper's 51-65 %), so
noiseless accuracy is not offset-free either.

AUC (the ranking of the test points by the output against the labels) does not depend on any offset or scale, so it
compares the two arms with delta and lam set aside. Paired DeLong test, two-sided; not declared, not Holm-adjusted.

| teacher | loops | noiseless AUC zipper / item 31 (p) | stand-in AUC, no shots, zipper / item 31 (p) |
|---|---|---|---|
| 11 | 500 | 0.970 / 0.946 (2e-3) | 0.957 / 0.864 (9e-11) |
| 11 | 2,000 | 0.884 / 0.808 (5e-5) | 0.895 / 0.807 (9e-7) |
| 11 | 16,000 | 0.800 / 0.770 (0.16) | 0.810 / 0.777 (0.07) |
| 12 | 500 | 0.988 / 0.953 (6e-6) | 0.978 / 0.879 (2e-14) |
| 12 | 2,000 | 0.949 / 0.893 (9e-6) | 0.927 / 0.837 (7e-11) |
| 12 | 16,000 | 0.825 / 0.773 (3e-3) | 0.806 / 0.785 (0.18) |
| 13 | 500 | 0.985 / 0.979 (0.24) | 0.984 / 0.899 (5e-11) |
| 13 | 2,000 | 0.937 / 0.907 (0.02) | 0.945 / 0.850 (5e-9) |
| 13 | 16,000 | 0.833 / 0.754 (2e-4) | 0.833 / 0.782 (3e-3) |

Reading, combined with the workplace's:
- At 500 and 2,000 loops (design C's own count) the zipper's readout ranks the points much better than item 31's in
  3 of 3 teachers, offset aside (stand-in AUC +0.09 to +0.10, p <= 1e-6): the zipper learns better early, now on three
  teachers.
- At 16,000 loops the lead has shrunk to +0.02 to +0.05 (higher in 3 of 3, p < 0.01 in 1).
- Item 31 reads out with an offset throughout; the zipper does not. Its smaller lam costs it more under shots.
- Not claimed: post hoc, one seed, the stand-in.
