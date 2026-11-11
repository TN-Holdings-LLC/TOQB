# 1D Fermi-Hubbard at 90 and 120 qubits, raw, with the U = 0 ruler: ibm_fez, 2026-11-11 (prereg/hubbard_big_2026-11-11.md)

- Declaration 854592e pushed 13:23:22 CET (reflog "update by push"); queue read 13:23:41 CET (marrakesh 2, fez 3,
  kingston 98; chosen marrakesh, fez). marrakesh first: rule C refused (longest chain 84 sites) -> not buildable;
  ibm_fez (failed qubits 72, 148, 149; coupler 32-33). Chains by rule C.
- Build: 28 circuits, 34.2 s by the model; CZ 884 / 1768 (L 45) and 1184 / 2368 (L 60), equal in both arms;
  circuits_sha256 equal to the try-build whose pre-run check passed (`ibm_fez/check_trybuild.txt`: 2 steps by Aer MPS,
  4 steps by quimb, worst 2.8e-9, mirrors all zeros, arms equal in CZ and depth) -> the PASS carries over.
  Answers sealed (sha256 5e90c416... as declared), released in `answers/`.
- Job dbq619tt7fqc738ad67g, submitted 13:33 CET, DONE; job files returned byte-identical.

## Declared verdicts (gpu/hub_score.py)

| L (qubits) | steps | CZ | CZ / qubit | U4: MSE / mean square | U4 | U0: MSE / mean square | U0 |
|---|---|---|---|---|---|---|---|
| 45 (90) | 2 | 884 | 9.8 | 0.0191 / 0.1672 | READS | 0.0110 / 0.0697 | READS |
| 45 (90) | 4 | 1768 | 19.6 | 0.0101 / 0.0325 | READS | 0.0324 / 0.1383 | READS |
| 60 (120) | 2 | 1184 | 9.9 | 0.0132 / 0.1637 | READS | 0.0062 / 0.0661 | READS |
| 60 (120) | 4 | 2368 | 19.7 | 0.0073 / 0.0290 | READS | 0.0307 / 0.1308 | READS |

AGREES: U4 40 / 45 of 90 and 56 / 59 of 120; U0 56 / 7 of 90 and 81 / 7 of 120.

## Prediction (written before the data)

- "U4 and U0 READ at 2 and 4 steps at L 45 and 60": held (all eight).
- "r(U4) / r(U0) 0.85-1.0 at 2 steps, 1.2-1.5 at 4 steps": held at 2 steps (0.899, 0.906); **failed at 4 steps**
  (1.000, 1.142; at L 20 / 30 earlier tonight 1.30 / 1.38).

## Beside (not judged, never used to correct)

- Amplitude ratio r: U4 0.80 / 0.60 (L 45), 0.81 / 0.66 (L 60); U0 0.88 / 0.60, 0.90 / 0.58 at 2 / 4 steps. Against the
  12:58 CET run (L 20 / 30): U4 at 4 steps 0.75 / 0.69, here 0.60 / 0.66; U0 at 4 steps 0.58 / 0.50, here 0.60 / 0.58.
- Per-site charge |Z_up + Z_dn| (exactly 0): mean 0.057-0.106. Floor 0.965-0.970; mirror 0.55-0.57 / 0.24-0.25 at
  2 / 4 steps.
- 120 qubits and 2368 CZ in one circuit, read raw at 4 steps; the classical check is an MPS on a PC (166 s for the
  4-step answers at L 60): size alone does not make the check hard at fixed steps.
