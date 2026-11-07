# 3D v3.1 with the pre-run gate on a device (2026-11-07 daytime JST; prereg/os3d_gate_2026-11-07.md)

- Declared at TOQB 1ad49e2 (committed 03:19 CET). The first push failed (the bundle carried no `main` ref), so a first
  queue reading and fetch (`fetch_unused/`, 03:21 CET) happened before the declaration was public; it is not used.
  After the push (73cda75..1ad49e2 on GitHub), a second fetch (`fetch2/`, 03:22:57 CET): pending marrakesh 0, fez 5,
  kingston 10 -> ibm_marrakesh (the fewest).
- Built here from `ibm_marrakesh/dev/device.json` (fetched 03:23:02 CET; failed qubits 46, 73, 82, 113, 119, 130,
  coupler 113-119): 61 circuits, 71.1 s by the model, gates e600779e3efc, answers sha256 0bce0dab... (k = 4, as
  sealed). psf-os 55167cf (plus the long-standing local additions in circuits.py and job.py), qiskit 2.5.2.
- Candidates (fixed order): 0 (r0 1, c0 8), 1 (3, 4), 2 (5, 0), 3 (0, 0). Probes at t = 1.

## Run

Job dbn8ploou4as73b42g2g, submitted 03:28:38 CET (calibration at submit 03:03:25 CET), DONE by 03:30:41 CET;
dynamical decoupling and twirling off. Calibration beside at the submit and at the run: `run/CALIB_BESIDE_*.json`
(report only). Scored with `gpu/os3d_v31_score.py run answers gate` (declared rule): `run/scores.json`.

## Declared rule and verdicts

Gate (candidates in order of their own t = 1 mirror: 1 0.832, 0 0.812, 2 0.805, 3 0.712):
candidate 1 PASS (no low mirror site, no |1> floor mark, within 0.1) -> **judged**. (0: one low mirror site and |1>
floor mark q51; 2: |1> floor mark q106; 3: one low mirror site, |1> floor mark q26, not within 0.1.) Sentinel CLEAN.

| t | 3D (candidate 1) | 2D patch |
|---|---|---|
| 1 | READS, DIFFERS, BEATS (M 0.643 / 0.697) | READS, DIFFERS, BEATS (0.617 / 0.697) |
| 2 | READS, AGREES, BEATS (0.409 / 0.425) | READS, DIFFERS, BEATS (0.574 / 0.673) |
| 3 | READS, AGREES, BEATS (0.323 / 0.321) | READS, DIFFERS, BEATS (0.475 / 0.573) |

## Beside

| arm | MSE t1 / t2 / t3 (sum) | retention | CZ t1 | mirror t1 |
|---|---|---|---|---|
| 3D candidate 1 (judged) | 0.0056 / 0.0021 / 0.0042 (0.0119) | 0.92 / 0.96 / 1.01 | 108 | 0.832 |
| 3D candidate 2 | 0.0041 / 0.0047 / 0.0140 (0.0228) | 0.92 / 0.99 / 1.03 | 108 | 0.805 |
| 3D candidate 0 | 0.0122 / 0.0109 / 0.0073 (0.0304) | 0.89 / 0.94 / 0.96 | 108 | 0.812 |
| 3D candidate 3 | 0.0999 / 0.0812 / 0.0814 (0.2625) | 0.78 / 0.78 / 0.73 | 148 | 0.712 |
| 2D patch | 0.0855 / 0.0917 / 0.0828 | 0.89 / 0.85 / 0.83 | 16 | 0.867 |

The judged candidate has the smallest MSE sum of the four; the one the gate refused on every count (3) has the
largest, 22 times the judged one. The 2D patch has no choice of place; it used coupler 28-29 (calibration CZ 0.019)
and qubit 29 (readout 0.23). The two problems differ (28 against 16 edges), so their MSEs are not compared. The |1>
floor at t = 1 marked one qubit on each of candidates 0, 2, 3; those three arms all had a larger MSE sum than the
judged one. Answers released in `answers/` (sha256 0bce0dab..., as sealed).
