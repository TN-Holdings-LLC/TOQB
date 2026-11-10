# Home check of home VS Claude's isingL 4x3x2 analysis (2026-11-11)

- Zip sha256 b5d6b345...d0dcd20e; SHA256SUMS 36 of 36. (The kit's input copies of the job are not kept here; they are
  the committed `results/night-2026-11-10/isingL/ibm_fez` files.)
- Recounted at home from the committed circuits (4x3x2, place 0, t 4): CZ fold 936, line 504 on the same 29
  couplers; the only couplers where line has more CZ than fold are at bridge qubit 16: 3-16 fold 32 / line 48, 16-23
  16 / 24 (the bridge carries 72 in line against 48 in fold; the other bridge 24 against 48). This agrees with VS.
- Simulation (FakeFez noise model, not fitted, place 0 only): line closer than fold at t 2-4 (d = -0.044, -0.103,
  -0.116), the opposite of the device (+0.077, +0.081, +0.044); the device's line excess sits on sites 13-15 around
  qubit 16, which the model does not reproduce. So the model's noise (gate errors, T1/T2, readout) does not explain
  the device's direction; candidates (the day's calibration, idle crosstalk, CZ crowding on the bridge, a one-off)
  are not separated by this data.
- Process notes: the pod ran 2 h 41 min, about 9.5 USD against an estimate of 2.6; results were written at the end
  of all 160 runs, not per run as instructed (VS reported both).
