# XX chain (free fermions) at 91 qubits, depth scan, raw: ibm_fez, 2026-11-12 (prereg/ffxx91_2026-11-12.md)

- Declaration c0feebc pushed 15:32:36 CET (reflog "update by push"); queue read 15:33:01 CET (marrakesh 0, fez 3,
  kingston 44). marrakesh first: rule C reaches 84 sites, not 91 (not buildable) -> ibm_fez.
- Build: 40 circuits, 47.6 s by the model, rule C chain; CZ 360 to 3600 (CZ depth 8 to 80) for both thetas.
  circuits_sha256 56a6d30f... equal to the 11-12 try-build whose pre-run check passed (`check_trybuild_pi2.json`,
  `check_trybuild_pi4.json`) -> the PASS carries over. Build answers equal the declared placement-free answers on the
  chain (`gpu/ffxx91_answers.py check`, worst 0).
- Answers: `answers/xx91_logical_ans.json` sha256 84674136... (as declared), `answers/xx91_ibm_fez_ans.json` by label.
- Job dbqstapabdes73fos5rg, submitted 15:35:19 CET (calibration 15:09 CET), DONE; job files returned byte-identical;
  DD and twirling off; 4000 shots.

## Verdicts (`gpu/hub_score.py`), 91 qubits per circuit

| steps | CZ layers | CZ | theta pi/4: MSE / mean square | verdict | AGREES | r | theta pi/2: MSE / mean square | verdict | r |
|---|---|---|---|---|---|---|---|---|---|
| 2 | 8 | 360 | 0.0170 / 0.2589 | READS | 26 | 0.806 | 0.0475 / 1 | READS | 0.817 |
| 4 | 16 | 720 | 0.0306 / 0.2032 | READS | 8 | 0.681 | 0.1255 / 1 | READS | 0.690 |
| 8 | 32 | 1440 | 0.0555 / 0.1760 | READS | 1 | 0.500 | 0.3173 / 1 | READS | 0.467 |
| 12 | 48 | 2160 | 0.0862 / 0.1703 | DOES NOT READ | 2 | 0.327 | 0.5035 / 1 | DOES NOT READ | 0.308 |
| 16 | 64 | 2880 | 0.1111 / 0.1725 | DOES NOT READ | 0 | 0.219 | 0.6639 / 1 | DOES NOT READ | 0.194 |
| 20 | 80 | 3600 | 0.1337 / 0.1774 | DOES NOT READ | 2 | 0.143 | 0.8018 / 1 | DOES NOT READ | 0.107 |

**Readable depth (theta pi/4): 8 steps (32 CZ layers); the first step that does not read: 12 (48 layers).**
At 12 steps both thetas miss the line narrowly (MSE / mean square 0.506 and 0.504).

## Prediction (written before the data)

- "theta pi/2 READS at every step": **failed** (reads to 8 steps, not from 12).
- "theta pi/4 READS at least to 12 steps": **failed** (reads to 8; 12 just misses).
- 16 and 20 steps: no prediction; neither reads.

## Beside (not judged, never used to correct)

- The amplitude ratio r (how much of the exact pattern the device keeps) is nearly the same for both thetas at every
  step, and falls by e every 41 CZ layers from 16 to 80 layers (log-linear through the five points).
- If the device only shrank the signal (z = r e), MSE / mean square would be (1 - r)^2 and READS would mean
  r >= 1 - 1/sqrt(2) = 0.29 whatever the size of the signal. Here r crosses 0.29 near 52 layers, and the verdicts
  turn between 32 and 48. So the larger signal of theta pi/4 (mean square 0.17 against Hubbard's 0.05 at 48 layers)
  did not move the boundary: with a mainly multiplicative error, the signal's size cancels out of the line.
- Per qubit: the last reading step has 15.8 CZ per qubit, the first non-reading 23.7. Hubbard on 11-11 (fez): read
  at 19.2-19.7 CZ per qubit (4 steps, L 20 to 60), not at 28.8 (6 steps, L 20). The XX brickwork keeps 90 of 91
  qubits busy in every CZ layer, Hubbard about 0.8 of them, so per CZ layer XX loses more.
- Floor 0.964-0.966; mirror 0.68 -> -0.003 (pi/4) and 0.74 -> -0.005 (pi/2) from 2 to 20 steps (the mirror is twice as
  deep). Sentinel and charge columns: the charge is 0 by construction (odd chain, skipped).

## Reproduce

`python reproduce.py xx91-fez-2026-11-12`.
