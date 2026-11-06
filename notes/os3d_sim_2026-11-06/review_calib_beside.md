# Review of gpu/calib_beside.py and a FakeFez check (workplace, 2026-11-06; home's 06m item 1; no IBM)

## What it does (as home wrote it, 812934f)

Groups the job's records by name without `_floor` / `_mirror`, collects the CZ pairs and the measured qubits of each
arm from the QPY files, and reports per arm the worst and the median CZ error and readout error from the backend's
Target. Report only: nothing goes back into psf-os, a placement, a build or a score; it refuses to overwrite its output.

## FakeFez check (`calib_beside_fake/`)

Two arms built offline on the fez record of 11-05, 4x2x2 t 1: v3 fold (`psf-os run3d`) and SABRE seed 0 (as in
`sim3d.compile_sabre`, saved as `p2d_sabre*`).

| arm | worst CZ (at) | median CZ | worst readout (at) | median readout |
|---|---|---|---|---|
| v3 fold | 0.0103 (26-27) | 0.0035 | 0.0459 (41) | 0.0077 |
| SABRE | 1.0 (106-107) | 0.0033 | 0.0227 (69) | 0.0079 |

It finds the snapshot-dead coupler that decided the unmarked FakeFez comparison of 06c, and the values match
`diag_fakefez_t1.log`. Medians are over elements (each pair once), not weighted by how often a pair is used.

## Findings and changes (made in gpu/calib_beside.py; tests `tests/test_calib_beside.py`, 3 passed)

1. **The worst element could disappear from the report.** qiskit-ibm-runtime builds the live Target with
   `filter_faulty=True` (0.51.0, `utils/backend_converter.py`): non-operational qubits and gates are left out. An arm
   that uses such an element (marked bad after the day's record was taken) got it only as a count in `missing`, and
   the printed "worst" was the next one. Test: FakeFez with 106-107 marked non-operational gives, from the Target,
   worst 0.019 at 105-117 and 106-107 missing. Change: `missing_at` lists those elements and a WARNING is printed.
2. **The calibration at the submit is not the calibration at the run.** The job can wait in the queue across a
   calibration. Change: `--job JOB_ID` (with `--backend`) reads `RuntimeJobV2.properties()`, the properties at the time
   the job started running; BackendProperties keep non-operational elements, listed under `non_operational`. Offline
   counterpart `--fake FakeFez --properties` (tested). The `--job` path itself was not run (no IBM at the workplace).
3. **Two-qubit gates other than cz were ignored silently.** Now listed under `other_2q` with a WARNING (a basis with
   ecr or fractional rzz would otherwise hide elements).
4. Fine as written: grouping by name; the refusal to overwrite; reading QPY with the gate list only.
5. For the job: record names must keep arm and depth apart (`run3d` writes `p2d_g3d` for every depth); put into the
   draft's procedure.
