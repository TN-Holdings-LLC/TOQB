# DRAFT (not declared; workplace, 2026-11-06; home's 06l item 3): the 3D prototype on a device, v3 fold against SABRE in one job

Status: draft for home and the owner. Nothing is fixed. Code: psf-os `grid3d` (v3 fold, df1472f; coupler check 8b0b34f) and `psf-os run3d`;
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

## Procedure (steps; the calibration step added at the workplace 2026-11-06 for the owner's 06:28 decision)

1. **Build (offline).** Both arms and all depths into one job folder with `psf-os` on the day's record (no quality
   number read). Record names must keep arm and depth apart (e.g. `p2d_g3d_t1`, `p2d_sabre_t1`, each with `_floor`
   and `_mirror`): `calib_beside.py` groups records by name with the role suffix removed. Note: `run3d` builds one arm
   and one depth per folder (`p2d_g3d`); a builder for the combined job is still to be written.
2. **Seal.** Exact answers by `grid3d.exact`, sealed (hash committed before the submit); gate hashes of the job's
   circuits committed (`psf-os gatehash`).
3. **Submit (home, IBM step, VPN OFF).** As the daily record.
4. **Calibration beside, at the submit (home, right after the submit, VPN OFF).**
   `python gpu/calib_beside.py RUNS CALIB_BESIDE_submit.json --backend DEVICE`: per arm, the worst and the median CZ
   error and readout error on the elements it uses, from the Target as it is at the submit. Elements the live Target
   does not report (it leaves out non-operational qubits and gates) are listed under `missing_at` and printed as a
   WARNING.
5. **Fetch the results**, then **calibration beside, at the run (home, VPN OFF).**
   `python gpu/calib_beside.py RUNS CALIB_BESIDE_run.json --backend DEVICE --job JOB_ID`: the same, from the
   properties at the time the job started running (a queue can cross a calibration); non-operational elements are kept
   there and listed under `non_operational`.
6. **Judge** (below) from the counts alone; release the sealed answers after the verdicts are committed. The two
   CALIB_BESIDE files are reported beside the verdicts and are never fed into a build, a placement or a score.

## Judged (as 2D, per arm and t)

1. **READS:** MSE against the exact values at most half the mean square of the exact values.
2. **AGREES:** |M - M_exact| <= 0.05.
3. **BEATS:** MSE below the better of all 0 and all 1.
4. **A against B:** per t, R = MSE_A / MSE_B: HELPS (A better) if R <= 0.8, HURTS if R >= 1.25, NO EFFECT between.
Reported beside them: retention M / M_exact, the normalised error, CZ and CZ layers of each arm, the floor and the
mirror means, the sentinel as declared and beside the ledger, and per arm the worst and median CZ and readout errors
of its elements at the submit and at the run (steps 4 and 5), with any missing or non-operational element named.

## Honest expectation (simulation only; not evidence about a device)

`notes/os3d_sim_2026-11-06/README.md` (workplace, 400 trajectories each; idle errors in neither model):

| model | R at t 1 | R at t 2 | R at t 3 |
|---|---|---|---|
| uniform (p2 = 0.005 per CZ) | 0.72 | 0.76 | 0.75 |
| FakeFez, the snapshot's dead couplers marked for both arms | 0.58 | 0.59 | 1.27 |
| FakeFez, the 11-05 record as it is | 0.02 | 0.02 | 0.08 |

- Retention: v3 0.82-0.91, SABRE seed 0 0.79-0.89 where no dead coupler is used. HELPS is the most likely verdict at
  t 1 and 2 in both models; t 3 is open: the uniform model gives HELPS, the FakeFez model HURTS (R 1.27-1.30 over six
  trajectory seeds, so not a sampling accident, but one model of an older calibration). The earlier line "R near 1 at t 1" (home,
  rounded t 1 values) is superseded: with the thresholds 0.8 / 1.25 the uniform t 1 values give HELPS.
- The last row: SABRE's route crossed one coupler that the FakeFez snapshot has as dead but the record does not mark,
  and lost most of its signal. On a device the same can happen to either arm on a coupler that is bad but not marked
  failed. **Decided (owner, 2026-11-06 06:28 CET: report it):** beside each arm, from the day's calibration, the
  worst CZ error and the worst readout error on the elements it uses (with the medians), by `gpu/calib_beside.py`
  at the IBM step right after the submit (VPN OFF; written to CALIB_BESIDE.json next to the run). Reported only:
  psf-os still reads and stores no quality number, the placement and the verdicts do not change, and nothing from
  the file is fed back into any build or score.
- AGREES is unlikely for either arm (signal loss 5-8 % of M_exact gives -0.05 to -0.08); v3 at t 2 under FakeFez
  agreed by 0.004.
- READS and BEATS: every arm in every cell without a dead coupler.
- SABRE seed 0 recounted at the build on the 11-05 record: 136 / 269 / 456 CZ at t 1 / 2 / 3 (139 / 269 / 441 with the
  snapshot's dead couplers marked).

## Limits

One small lattice (16 sites); one device; one seed of SABRE (another seed can differ by 10-20 % in CZ).
