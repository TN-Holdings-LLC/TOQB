# P6 again, on ibm_marrakesh (the tutorial's device), 2026-11-04 evening

**Why.** P6 on ibm_fez (`results/p6-device-2026-11-04`, 735226d) DIFFERED from t = 1, with a low floor (0.92-0.80)
on that day's fez. The owner chose to run the same job on ibm_marrakesh, the device of the tutorial's numbers, to see
how much of the miss belongs to the device.

**Everything as `prereg/drafts-2026-11-04/p6_device_note.md`** (SHA-256 d97af6a6...4fa5e6b3) except the device:
the same circuits (theta_x 0.53 t 1-9, floor theta_x 0 t 1, 5, 9, bank cells theta_x 0.3 and 0.8 t 1-9, ring
sentinel), the same answers (sealed: f183ca5, c9097e5, 563d123), the same placement rule (`ising2d.place`, psf-os
61e9edd), 4000 shots, no mitigation, "stay", the same verdicts (sentinel; READS; AGREES within 0.05 at every t),
the same reported items (against the tutorial; the answer card; rule R as the sub-analysis), scored by
`gpu/p6_score.py` (written for the fez run, unchanged).

**Device:** ibm_marrakesh by the owner's choice (not by queue). If no copy qualifies on marrakesh, no job is sent and
that is reported (no move to another device: the point of this run is the device).

**Reported in addition:** the differences marrakesh - fez per t (both raw and divided by each job's floor).

**Stop.** One run.
