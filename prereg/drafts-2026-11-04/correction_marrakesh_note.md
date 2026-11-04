# Declared: the correction test again on ibm_marrakesh (owner's choice of 2026-11-04 11:55 CET)

Everything as `correction_note.md` (SHA-256 7ef2013d...2e541816): the same job builder `gpu/corr_device.py`, the same
correction, the same judgements and the same scorer `gpu/corr_score.py`, all unchanged, psf-os 1250c90. Only the
device rule changes: ibm_marrakesh, chosen by the owner (not by the queue). If no copy qualifies there, no job.

Why it matters: the correction was chosen and first passed on fez. marrakesh is a device it was not tuned on, with
a worse floor this morning (0.85 to 0.75) and two nearly dead readouts (29, 31) inside copy (0, 0).

Reported in addition: marrakesh minus fez (job dblgrsm74qds73dqfbqg) per theta_x for the gate decay per step, the MSE
ratio and the corrected differences.
