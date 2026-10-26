# The device test's rehearsal on ibm_kingston's 2026-10-24 twin (report only, 2026-10-26 11:28 CET)

`gpu/lam_rehearse.sh` (toqb `8726ca1`, H100 pod): `fold:rule` and the zipper at n = 13, L = 16, models 0 and 1, 96
random inputs, compiled for the Target of flow C (SHA-256 3b939138…) and predicted by its twin (256 trajectories); then
the job's outcome if the device were that twin, shot noise drawn 2000 times. The text below is the pod's
`rehearse.txt` and build lines as printed (pasted from the terminal; the zip follows).

| | fold:rule (pendants) | zipper |
|---|---|---|
| twin lam, model 0 / 1 | 0.771 / 0.761 | 0.685 / 0.657 |
| two-qubit gates, duration | 224, 9.2 us | 464, 10.8 us |

On the same model (0) the twin of ibm_marrakesh's 2026-10-13 snapshot gave 0.71 against 0.27 (flows E, F): on the
twin that matched the device on 2026-10-24 the pendants' lead is about 0.08-0.10, not 2-4 times.

| points x shots | slope error per arm | difference error | the rule (> 2 SE) decides for the pendants |
|---|---|---|---|
| 48 x 250 | 0.10-0.11 | 0.14-0.16 | 6-10 % |
| 48 x 1000 | 0.05-0.06 | 0.07-0.08 | 14-26 % |
| 96 x 250 | 0.07-0.08 | 0.10-0.11 | 11-15 % |
| 96 x 1000 | 0.04 | 0.05 | 31-47 % |

- A two-arm device comparison at n = 13 would be decided in at most about half of the cases even at about 1 min of QPU
  time: not run. The 18 s left go to a one-arm test (D1, prereg/drafts-2026-10-26/pend_device_note.md).
- The noiseless z spread of random models at L = 16 is 0.08-0.09, the cause of the large slope errors.
