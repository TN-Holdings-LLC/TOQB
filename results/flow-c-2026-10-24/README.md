# Flow C, 2026-10-24: the zipper and Qiskit on ibm_kingston against a twin of the day's calibration (report only)

Declared in prereg/drafts-2026-10-24/flow_c_note.md (SHA-256 8d48abb6…) and flow_c_amend1.md (SHA-256 32662b40…,
ibm_kingston instead of ibm_marrakesh). No rule, no arm comparison, no readout corrected, nothing chosen from the result.

## The jobs

- **ibm_marrakesh, cancelled.** Job dbe974om94ac738rebfg (540 circuits, manifest SHA-256 3bb3a4a473b09421…), submitted
  13:16:35 CEST, never left the queue (device paused for maintenance, 439 then 541 pending jobs); cancelled at 15:51
  CEST while queued, no QPU time used (flow_c_amend1.md). The job folder is kept at home as submitted.
- **ibm_kingston, run.** Fetch: calibration 2026-10-24 15:26:59 CEST, target SHA-256 3b939138… (fetch.json). Pod step
  16:13-16:21 CEST (toqb a08aac0, psf-zero c7862ef, H100; times.txt): 6 cells x 90 points, all `valid`, predicted
  58.9 s; manifest SHA-256 63ee331f6225d3bb… written before submission. Submitted 16:29 CEST as dbec1jfsstms73fbq0lg;
  done 16:31; **billed 42 s** (0.71 of the model; about 43 s was expected). Only the open plan's free minute was used.
- **The calibration moved before submission.** At submission ibm_kingston's calibration was 16:09:07 CEST
  (device/submission.json); the twin is from 15:26:59. By the decision of 2026-10-20 a new calibration does not stop a
  submission. The "day twin" below is therefore 42 minutes older than the calibration the job ran on.

## Results (flowc.md, flowc.json; `python -m toqb.flowc_score JOB RUNS flowc.md`)

| arm | scale vs day twin | offset | corr | device +1 share / day twin's / noiseless |
|---|---|---|---|---|
| zipper (psfai:template_zip, 336 CZ, 10.76 us) | 1.00 (0.95-1.02 per teacher) | +0.019 | 0.983 | 0.85 / 0.80-0.84 / 0.79-0.83 |
| Qiskit (level 2 on the Target, 506 CZ, 45.80 us) | -0.16 | +0.041 | -0.533 | 0.39 / 0.86-0.92 / 0.83-0.87 |

1. **Question 1 (the zipper behaves as the twin says): yes on this job.** Scale 1.00, correlation 0.98 against the twin
   of the fetched calibration, on all three teachers. Its first hardware run.
2. **Qiskit's circuits came out inverted.** Negative scale and correlation on all three teachers (-0.48 to -0.57). Not
   a software mix-up, as far as checked: Qiskit's own `Statevector` on the submitted circuits agrees with the twin
   (correlation 0.995 on the first 12 points of teacher 17) and anti-correlates with the device (-0.56); clbit 0 is read
   the same way as for the zipper, whose result matches. Points the noiseless circuit puts at P(1) 0.02-0.06 read about
   0.55 on the device: the signal is inverted, not only damped. **Cause not found.** Facts from the fetched
   calibration (15:26:59): Qiskit reads out on qubit 43 (readout error 3.4 %, T2 92 us), its CZ pairs have mean error
   0.22 % (max 0.81 %), and two of its 14 qubits have T2 of 29-31 us (48, 25); the zipper reads out on qubit 59 (0.48 %),
   CZ mean 0.13 % (max 0.18 %), T2 at least 129 us. Dephasing alone damps towards zero and does not invert; a coherent
   error during the long circuit (ZZ, detuning; dynamical decoupling was off) or a change at the 16:09 calibration are
   candidates, not checked.
3. **Question 2 (a twin of a fresh calibration predicts the scale): yes for the zipper; not answerable for Qiskit.**
   On the device day (ibm_marrakesh, 9-day-old snapshot) the twin under-stated the zipper's signal 1.5-2.3x; here,
   with a calibration 1 hour old, scale 1.00. One job, one device: this does not separate "calibration age" from
   "device".
4. The snapshot twin (ibm_marrakesh, 2026-10-13) is another device's twin; its column is reported and not read
   (amendment 1).

## A flaw in the note (Claude's): the 90 points are all of one label

flow_c_note.md says the first 90 test points have "labels balanced to within the draw". They do not: each teacher's
test set is ordered, 250 points of label +1 then 250 of -1, so the first 90 are all +1 (checked on the records;
noiseless_90.json). Consequences:

- The "accuracy" column of flowc.md is the share of +1 answers; it is not an accuracy and is not read.
- The twin's "predicted accuracy" 0.79-0.89 (above the far-teacher test's accuracy on 500 points) is the same artefact.
- The regression (scale, offset, correlation) is unaffected in kind: the points span noiseless P(1) about 0.02-0.70.
  It covers only the +1 half of the input space.
- The free minute is spent; the job is not repeated.

## Files

`fetch.json`; `device/` (manifest.json, submission.json, raw_counts.json.gz and its SHA-256); `runs/` (the 6
`toqb.device_reuse` records; pod paths written `<pod>/`, so their SHA-256 differ from the manifest's, which are in
`job_sha256.txt` with the qpy files'); `flowc.md` / `flowc.json`; `noiseless_90.json` (noiseless P(1) of the submitted
circuits by Qiskit's `Statevector`, home); `assemble.txt`, `times.txt`, `rust.txt`, `reuse.txt`, `logs/`. The qpy
files (71 MB) are not in the repository.
