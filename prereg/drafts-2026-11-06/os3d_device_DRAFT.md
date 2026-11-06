# DRAFT (not declared; workplace, 2026-11-06; home's 06l item 3): the 3D prototype on a device, v3 fold against SABRE in one job

Status: draft for home and the owner. Nothing is fixed. Code: psf-os `grid3d` (v3 fold, df1472f) and `psf-os run3d`;
the simulation notes `notes/os3d_sim_2026-11-06/`.

## Question

On a device, without mitigation, does the folded formula placement of a 4 x 2 x 2 cubic-lattice kicked Ising (16
sites) read the exact answer as well as, or better than, the same circuit routed by Qiskit's SABRE?

## Problem

- 4 x 2 x 2 cubic lattice; each step RZZ(-pi/2) on every lattice edge, then RX(0.8) on every site; Z readout.
- t = 1, 2, 3. Exact answers by statevector (`grid3d.exact`, 16 sites), sealed before the run (hash committed first).

## Arms (same job, same device)

- **A, v3 fold:** `grid3d.build(..., layout="fold")`: the first translation (row offset, column offset in steps of 4)
  in the fixed order that touches no failed element; floor and mirror as in 2D (mirror from the compiled U).
- **B, SABRE:** Qiskit's SABRE layout and routing on the record's coupling graph without failed elements,
  `seed_transpiler = 0` only (not the best of several seeds: choosing the best seed by CZ count would be a search),
  RZZ(+-pi/2) then written as one CZ as in A; floor and mirror built the same way.
- Both read only the coupling graph and the failed marks; no calibration number.

## Job

- 2 arms x 3 depths x (circuit, floor, mirror) = 18 circuits + the ring sentinel (4): 22 circuits, 4000 shots,
  27.6 s by the time model.
- CZ by compile on the fez record of 11-05 (`cost_fez_2026-11-05.json`): A 116 / 232 / 348 at t 1 / 2 / 3;
  B (seed 0) 136 / 269 / 456 (recounted with `sim3d.py`).
- Device: by the queue as the daily record; a device on which A finds no qualifying translation is not used.

## Judged (as 2D, per arm and t)

1. **READS:** MSE against the exact values at most half the mean square of the exact values.
2. **AGREES:** |M - M_exact| <= 0.05.
3. **BEATS:** MSE below the better of all 0 and all 1.
4. **A against B:** per t, R = MSE_A / MSE_B: HELPS (A better) if R <= 0.8, HURTS if R >= 1.25, NO EFFECT between.
Reported beside them: retention M / M_exact, the normalised error, CZ and CZ layers of each arm, the floor and the
mirror means, the sentinel as declared and beside the ledger.

## Honest expectation (simulation only; not evidence about a device)

`notes/os3d_sim_2026-11-06/README.md` (workplace, 400 trajectories each; idle errors in neither model):

| model | R at t 1 | R at t 2 | R at t 3 |
|---|---|---|---|
| uniform (p2 = 0.005 per CZ) | 0.72 | 0.76 | 0.75 |
| FakeFez, the snapshot's dead couplers marked for both arms | 0.58 | 0.59 | 1.27 |
| FakeFez, the 11-05 record as it is | 0.02 | 0.02 | 0.08 |

- Retention: v3 0.82-0.91, SABRE seed 0 0.79-0.89 where no dead coupler is used. HELPS is the most likely verdict at
  t 1 and 2 in both models; t 3 is open (one model gives HURTS at the edge). The earlier line "R near 1 at t 1" (home,
  rounded t 1 values) is superseded: with the thresholds 0.8 / 1.25 the uniform t 1 values give HELPS.
- The last row: SABRE's route crossed one coupler that the FakeFez snapshot has as dead but the record does not mark,
  and lost most of its signal. On a device the same can happen to either arm on a coupler that is bad but not marked
  failed. **To decide (home / owner), not changed here:** whether to report beside each arm, from the day's
  calibration, the worst CZ error and the worst readout error on the elements it uses (reported only; the placement
  still reads no calibration number), so that a verdict decided by one bad element can be seen as such.
- AGREES is unlikely for either arm (signal loss 5-8 % of M_exact gives -0.05 to -0.08); v3 at t 2 under FakeFez
  agreed by 0.004.
- READS and BEATS: every arm in every cell without a dead coupler.
- SABRE seed 0 recounted at the build on the 11-05 record: 136 / 269 / 456 CZ at t 1 / 2 / 3 (139 / 269 / 441 with the
  snapshot's dead couplers marked).

## Limits

One small lattice (16 sites); one device; one seed of SABRE (another seed can differ by 10-20 % in CZ).
