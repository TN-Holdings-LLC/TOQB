# Pre-run confirmation of the gate rule (2026-11-07; simulator, not a device result)

POD, 64 CPU cores, realsim (relaxation on delays). Same 4 candidates as the 11-07 fez job; t3 probes (run_t3, this
morning's job) and t1 probes (run_t1, rebuilt from the same fez record). 600 shots per circuit.

| | noise | candidates' errors (MSE sum t1-t3) | gate passed | gate chose | best (weakest probe) chose |
|---|---|---|---|---|---|
| check3_fakefez | FakeFez (couplers 27-28, 68-69, 80-81 failed in that snapshot) | 0: 0.014, 1: 0.430, 2: 0.187, 3: 0.204 | 0 | 0 | 0 |
| check5_fez_calib | fez calibration at this morning's run (q72 failed, no T2: T2 = T1 in memory) | 0: 0.026, 1: 0.061, 2: 0.042, 3: 0.022 | 0, 3 | 3 | t3: 3, t1: 0 |

In both, the gate judged the candidate with the smallest error. Not shown by the simulator: why candidate 0 was the
worst on the device this morning (simulated 0.88-0.90 retention, device 0.83-0.78); the device's own t1 mirror did
order the candidates as their errors (0.84 > 0.80 > 0.71 = 0.71). Not confirmed: the |1> floor at t1 depth on a device.
