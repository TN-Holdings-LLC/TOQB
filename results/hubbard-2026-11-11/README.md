# 1D Fermi-Hubbard, raw, with the U = 0 ruler in the same job: ibm_fez, 2026-11-11 (prereg/hubbard_2026-11-11.md)

- Declaration d5abb33 pushed before the record (owner's push output "d5abb33e"); queue read 12:39:45 CET (marrakesh 1,
  fez 8, kingston 154; chosen marrakesh, fez). marrakesh first by the order: the ring sentinel did not land -> not
  buildable; ibm_fez (failed qubits 72, 148, 149; coupler 32-33).
- Build: 40 circuits, 47.6 s by the model; chains by shapes S1 (L 20) and S3 (L 30); CZ equal in both arms (384 / 768 /
  1152 and 584 / 1168 / 1752). circuits_sha256 equal to the try-build on the 11:13 record, whose pre-run check passed
  (`ibm_fez/check_trybuild.txt`: L 20 and 30 at 2 and 4 steps by Aer MPS against the answers, worst 2.3e-8, mirrors all
  zeros; arms equal in CZ and CZ depth at every step) -> the PASS carries over. Answers file sha256 13b6bc72... (from
  the sealed values eaa5cfcd..., both declared/printed before the run; released in `answers/`).
- Job dbq5gs0qtr0c738fc0e0, submitted 12:58 CET, DONE; job files returned byte-identical.

## Declared verdicts (gpu/hub_score.py)

| L (qubits) | steps | CZ | CZ / qubit | U4: MSE / mean square | U4 | U0 ruler: MSE / mean square | U0 |
|---|---|---|---|---|---|---|---|
| 20 (40) | 2 | 384 | 9.6 | 0.0094 / 0.1814 | READS | 0.0063 / 0.0824 | READS |
| 20 (40) | 4 | 768 | 19.2 | 0.0080 / 0.0460 | READS | 0.0395 / 0.1316 | READS |
| 20 (40) | 6 | 1152 | 28.8 | 0.0141 / 0.0219 | DOES NOT READ | 0.0480 / 0.0512 | DOES NOT READ |
| 30 (60) | 2 | 584 | 9.7 | 0.0093 / 0.1725 | READS | 0.0043 / 0.0742 | READS |
| 30 (60) | 4 | 1168 | 19.5 | 0.0068 / 0.0375 | READS | 0.0422 / 0.1312 | READS |
| 30 (60) | 6 | 1752 | 29.2 | 0.0125 / 0.0176 | DOES NOT READ | 0.0361 / 0.0452 | DOES NOT READ |

AGREES (|z - e| <= 0.05): U4 17 / 20 / 12 of 40 and 21 / 30 / 16 of 60; U0 26 / 7 / 4 of 40 and 45 / 2 / 3 of 60.

## Prediction (written before the data)

- "U4 READS at 2, 4 and 6 steps at L 20 and L 30": held at 2 and 4; **failed at 6** (both L).
- "The ruler reads at every step too, and r(U4) / r(U0) lies within 0.9-1.1": the ruler read at 2 and 4, not at 6;
  the ratio held at 2 steps (0.935, 0.900) and **failed at 4 and 6** (1.30 / 3.40 at L 20, 1.38 / 1.77 at L 30).

## Beside (not judged, never used to correct)

- Amplitude ratio r = sum z e / sum e^2: U4 0.84 / 0.75 / 0.42 (L 20), 0.82 / 0.69 / 0.38 (L 30); U0 0.90 / 0.58 /
  0.12 and 0.91 / 0.50 / 0.21. With the same CZ count and CZ depth the ruler kept less of its pattern than U = 4 from
  4 steps on: equal gate counts did not give equal retention here. The two exact patterns differ (at U = 0 the
  fermions spread ballistically, at U = 4 the Neel pattern decays slowly), so r compares different signals; the
  ruler, as built, is not a stand-in for the noise felt by the U = 4 pattern beyond 2 steps.
- Per-site charge |Z_up + Z_dn| (exactly 0 at any U): mean 0.05-0.10 on the device.
- Floor 0.966-0.971; mirror 0.58 / 0.28 / 0.11 (L 20) and 0.49-0.51 / 0.17-0.18 / 0.04 (L 30) at 2 / 4 / 6 steps.
- CZ per qubit at 6 steps (28.8, 29.2) is above the dual-unitary N = 91 (24.2, read) and below Schwinger N = 6 (37.5,
  read): CZ per qubit alone does not order what reads across problems.
