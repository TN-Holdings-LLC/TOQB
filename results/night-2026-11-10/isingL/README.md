# Ising line against fold at the same places, ibm_fez, 2026-11-10 (prereg/isingL_2026-11-09.md)

- Declared 2026-11-09 (fd88a28, on GitHub since 3d3cdb1); the declared pre-run condition (every 4 x 3 x 2 arm READS
  and AGREES noiselessly) met on 2026-11-10 (`notes/isingL_noiseless_2026-11-10`).
- Device: the declared order gave ibm_marrakesh, where the declared job cannot be built (the ring sentinel does not
  land); owner 19:51 JST: next in the order, ibm_fez (`DEVICE_NOTE.md`). Record 11:23:33 CET (failed qubits 72, 148,
  149; coupler 32-33). 148 circuits, 168.2 s by the model; answers equal the sealed table (8aa3d53d, released here).
- Job dbpfo8gqtr0c738ebfjg, submitted 12:12 CET, DONE; job files returned byte-identical to the build. Sentinel DEAD.

## Declared comparison (main measure nMSE; d = nMSE(line) - nMSE(fold), resolved if |d| > 2 sqrt(SE^2 + SE^2))

| lattice | judged place | t 1 | t 2 | t 3 | t 4 |
|---|---|---|---|---|---|
| 4 x 2 x 2 (CZ fold 108 / line 60 per step) | 3 (t1 mirror 0.844) | -0.0007 (within) | -0.0022 (within) | -0.0082 (resolved) | -0.0244 (resolved) |
| 4 x 3 x 2 (234 / 126) | 0 (0.735) | +0.0026 (within) | +0.0772 (resolved) | +0.0812 (resolved) | +0.0439 (resolved) |

- Prediction (d <= 0 at every t on both judged places): held on 4 x 2 x 2; failed on 4 x 3 x 2 (the line is
  farther from the exact answer at t 2-4, resolved, with 46% fewer CZ).
- Every arm READS (48 of 48); AGREES 4 of 48.

## Beside (not judged)

- 4 x 2 x 2, all four places x four t: the line has the lower nMSE in 12 of 16 (resolved lower 8, resolved higher 3,
  the higher ones all at place 0, t 2-4).
- 4 x 3 x 2, both places x four t: the line has the lower nMSE in 0 of 8 (resolved higher 7).
- Retention (fold / line) on 4 x 3 x 2 judged place: 0.835 / 0.845, 0.839 / 0.801, 0.811 / 0.737, 0.784 / 0.742.
- Fewer CZ did not give a closer answer on 4 x 3 x 2 on this device and day; why is not known from this run.
