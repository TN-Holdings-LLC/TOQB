# Schwinger-model pair production on a device (prereg/schw_2026-11-09.md)

- Declared at TOQB 514b98e, pushed before the fetch; the same record as the N = 91 run (ibm_marrakesh, 11:59 CET
  2026-11-09, results/du91-2026-11-09/fetch_in).
- Chains: shape S1 copy (0, 0) for N = 6 and 8. 18 circuits, 58 with floors, mirrors and the sentinel, 67.7 s by the
  model; answers ea735cff... equal the sealed site table (189b8e6a...) written on the labels.

## Run

Job dbopkrs4148s739tdik0, submitted 12:03 CET, DONE by 12:05 CET. Sentinel CLEAN. Scored by `gpu/schw_score.py`
(`ibm_marrakesh/scores.json`). Answers released in `answers/`.

- READS 16 of 18, BEATS 18 of 18 (both guesses), particle density AGREES 14 of 18.
- The prediction held: every N = 6 circuit and every step-1 and step-2 circuit READS and BEATS. At N = 8 step 5
  (420 CZ) M1 and M3 do not READ (nMSE 0.68, 0.57); M2 READS (0.23).
- Particle density: steps 1 and 2 within 0.05 (step 1 reads 0.13-0.15 against 0.10); step 5 M1 and M3 high by
  0.09-0.14 at both N; M2 within 0.02.
- Charge (exact 0): +0.12 to +0.26 at step 1, +0.21 to +0.37 at step 2, +0.37 to +0.61 at step 5 (raw check; spins
  relaxing towards |0> raise the sum of Z).
