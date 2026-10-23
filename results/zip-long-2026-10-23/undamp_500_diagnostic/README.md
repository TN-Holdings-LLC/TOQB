# Diagnostic only: the undamped readout at the 500-loop point (2026-10-23, not for use)

Run on a fresh H100 pod (the earlier one could not restart), `toqb.undamp_run --final-only` on copies of the run
records with the 500-loop checkpoint as the final point; shots reproduced in all 6. Zip SHA-256 in the commit.

Shot-free stand-in accuracy at 500 loops, per-point McNemar, Holm over 3 teachers (home, matches the workplace's
Addendum 3): raw zipper / item 31: 0.866 / 0.682, 0.908 / 0.626, 0.942 / 0.654; with item 31's offset delta removed:
0.878 / 0.736 (Holm p 1e-11), 0.932 / 0.802 (9e-14), 0.912 / 0.768 (2e-13). The twin's delta overshoots item 31
(after the shift it calls +1 on 33-39 %), so +0.13 to +0.14 is on the high side; with 250 shots the undamped gap is
about 0. Whether the lead is learning or readout is open: the untrained model (theta = 0) already scores 0.90 and 0.96
noiseless on teachers 12 and 13 (0.66 on 11). The theta = 0 readout check settles it.
