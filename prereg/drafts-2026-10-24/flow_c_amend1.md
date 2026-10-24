# Flow C, amendment 1 (owner, 2026-10-24 15:48 CEST): ibm_kingston instead of ibm_marrakesh. Fixed before the new submission

**What happened.** The job of flow C (dbe974om94ac738rebfg, 540 circuits, IBM's estimate 44 s) was submitted to
ibm_marrakesh at 13:16:35 CEST. ibm_marrakesh was in maintenance at submission, came back online, and was paused for
maintenance again by 15:48 with its queue growing (439, then 541 pending jobs); the job never left the queue. The owner
decided to stop waiting: the job is cancelled while queued (no QPU time is used) and flow C runs on another device.

**The device.** ibm_kingston, chosen by the queue alone (0 pending jobs at 15:48, against 1 on ibm_fez and 541 on
ibm_marrakesh), not by error rates. The flow is otherwise unchanged: the same 6 far-teacher models, the first 90 test
points, 540 circuits x 250 shots, at most 60 s by TOQB's model, only the open plan's remaining minute, the twin rebuilt
from the calibration fetched just before submission, no readout corrected, no arm comparison.

**What changes in the questions.**

1. Unchanged: does the zipper's circuit behave on the device as a twin of the day's calibration says (scale, offset,
   correlation per point)? Now on ibm_kingston, for both arms.
2. Narrowed: the snapshot of 2026-10-13 is ibm_marrakesh's, so its twin says nothing about ibm_kingston. The question
   becomes: does a twin built from the calibration fetched just before the job predict the device's scale for both
   arms? (The device day's 1.5-2.3x under-statement was with a 9-day-old snapshot of ibm_marrakesh.) `toqb.device_reuse`
   still writes the snapshot twin's prediction; it is reported as another device's twin and not read.

**Steps.** As in flow_c_note.md with `--backend ibm_kingston` and a new fetch folder and job folder; the ibm_marrakesh job
folder (fc_2026-10-24, manifest SHA-256 3bb3a4a473b09421d8b8276c5446801fd2eff14f19a97463541069e89ef10f39) is kept as
submitted and cancelled.
