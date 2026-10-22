# S2R design C: pre-registration r9 = r8 + this amendment (draft, 2026-10-21)

**Status.** Fixed on 2026-10-22 (see `prereg/drafts-2026-10-22/C_r9_FIXED.md`). The base is `prereg/drafts-2026-10-20/C_preregistration_r8_final_draft.md`, unchanged except as
listed here. Fixed on the device day by the SHA-256 of this file, of r8, of `job/manifest.json` and of
`job/undamp.json`, with the CEST time, before the submission.

## Changes (owner, 2026-10-21 and 2026-10-22)

1. **No time limit from T0 to submission.** r8's limit (6.32 h, §5 and §7) is removed. The calibration in effect at
   submission is recorded (`submission.json`: calibration_at_submit, as r8), and, if fetched again before
   submitting, its difference from T0's (`toqb.s2rc_device drift`) is reported. Neither stops the submission.
   - With it, r8's retraining condition "the time limit would be exceeded" (§5, "Retraining with the day's
     calibration") is removed. r8's other condition (a failed element at submission) is replaced by item 8.
2. **Device and placement: no choice by calibration.** *For the day, the fetch of three Targets and `choose` below are
   replaced by items 7 and 8 (no Target is fetched before training; the fixed order is applied at submission). The
   text is kept for a day that fetches.* r8's rule stays (E1-E4, then the fixed order marrakesh, fez,
   kingston), with E5 added (item 6). The only check on the calibration is r8's: a job that uses a failed qubit or
   coupler is not submitted (E4 and submit's check). PSF's placement is its fixed template. Qiskit's
   calibration-aware placement is recorded as Qiskit's own choice.
   - E2-E5 are applied on the pod to the three fetched Targets in the fixed order (`toqb.s2rc_device choose`,
     `FETCHES=` in `gpu/s2rc_device_day_r9.sh`); the first eligible device is used and `choice.json` records why
     the others were not. E1 (the plan) is confirmed at home. E3 is read from each fetch; "unknown" is recorded, not
     excluded.
3. **The undamped readout, added and reported (not a hypothesis).**
   - After assemble, for each cell, (lam, delta) come from the day's twin on the run's 64 training inputs (1,024
     trajectories, seed predict.seed + 5) against the exact noiseless model. No labels and no device data are used.
   - They are written with the undamped prediction to `job/undamp.json` (`toqb.s2rc_device_undamp fix`) before
     submission, and hashed with the job.
   - After the results: per cell, the CE and accuracy of the device's answers read as
     z_u = clip((z - delta) / lam, -1, 1), beside the raw ones, and whether the undamped CE falls inside the undamped
     prediction's 99 % interval (`toqb.s2rc_device_undamp score`).
   - H1 and H2 are r8's, unchanged, on the raw readout. The QPU time is unchanged: it is the same job.
   - Evidence before the day (post hoc, `results/readout-2026-10-21/`): on stand-in records the undamping recovered
     0.05 to 0.08 in CE for trained models, and turned Qiskit's raw CE lead (0.035, L 8) into a PSF lead (0.010).
     It can hurt a poor model.
4. **The training's start: theta = 0 (C0; INIT 0.0), owner, 2026-10-21** (r8 had uniform(-1, 1), INIT 1.0).
   - On the stand-in (2026-10-20, L 8, angle 0.3), C0 scored 0.815 against 0.745 in accuracy.
   - The script `gpu/s2rc_device_day_r9.sh` takes INIT; its default is now 0.0.
5. **The PSF template built in Rust (owner, 2026-10-21: use it on the day).**
   - The PSF arm's ring template (psf_ai_compile a22's `model_template`: reading, schedules N2 and item 31, placement
     on the device's snake, blocks, runs, the choice by duration then CZ count) is built by PSF-Zero's
     `rust/psfbind` (`toqb.ringport`), and on the day also by the Python beside it: any difference stops the run
     (`TOQB_RUST_TEMPLATE=check`, `gpu/rust_psf.sh`): a difference above 1e-12 in a fixed angle or factor, or any
     difference in the gate list, the runs' structure, the layout or the values' order (`ringport.compare`; bit-identical
     on every case checked at home and at the workplace). A case the Rust does not port (an embedding ring; not the
     S2R model's case) is built by the Python and listed in the run's arm stats. A placement by search is never
     made (item 6).
   - Evidence before the day: bit-identical templates (fixed angles and factors differ by 0.0) on the stand-in at
     L 2, 8, 16, and identical on 146 of 150 cases over five devices with random failed elements (the other 4 would
     need VF2's search: out of scope by item 6).
   - Nothing else changes: the circuits (gates, qubits, angles bit for bit), the binding (`RingTemplate.angles`),
     the QPY export and the job. Checked on a device-style run (verify false): the same record, times aside, and the
     same QPY bytes once Qiskit's automatic circuit names are set aside (`assign_parameters` appends a process-wide
     counter that counts the circuits made before; the Python builder makes more of them).
6. **Formula only: no placement by search (owner, 2026-10-21, "B").** psf_ai_compile a22 places the ring on the
   longest surviving piece of the device's snake and, when no piece is long enough, falls back to rustworkx's VF2
   search. From r9 that fallback is outside the scope: the template is not built (`ringport.OutOfScope`), nothing
   falls back to the Python, and the device is not eligible for the day:
   - **E5.** PSF's template places the 10-qubit ring (L 8 and 16) on a snake piece of the device, by the formula.
   - E5 is applied by the Rust builder only, so the day runs with `RUST=1` (the script's default); with `RUST=0`
     the Python would place by VF2 without a word, and that is not the day's configuration.
   - With the published calibration of 2026-10-13 (`snapshot:marrakesh`), marrakesh meets E5. On the day it is read
     on that snapshot by `precheck` (item 7; `choose` is for a day that fetches).

7. **The training on the published calibration, not a fetch on the day (owner, 2026-10-22 01:41 CEST: "the placement
   and such need not be held to; drop that idea").**
   - The twin and the plans use ibm_marrakesh's published calibration of 2026-10-13 11:37 CEST (the stand-in's
     snapshot, `snapshot:marrakesh`, the calibration of the tuning run and the rehearsal), written as a fetch folder
     by `toqb.s2rc_device snapshot` on the pod (no IBM connection; `fetch.json` says `source: snapshot`). No Target
     is fetched before training; T0 is the snapshot's calibration time.
   - The device is ibm_marrakesh, the first of the fixed order; E2 and E5 are read on the snapshot (precheck: all OK
     on 2026-10-22). E3 and E4 are read at submission, on the calibration in effect then (item 8);
     `calibration_at_submit` is recorded. r8's reference twin (6b, report only), if run, uses the same snapshot.
   - Consequence, stated before the run: the twin's calibration is nine days older than the device's on the day, so
     the predictions (H1, H2, the undamped readout) are tested against that drift. This is the owner's choice.

8. **A failed element at submission: the same circuits to the next device (owner, 2026-10-22 02:00 CEST).** r8 retrained on a
   new fetch; with item 7 that would rebuild the same placement or contradict item 7. Instead, `submit`
   (`toqb.s2rc_device.pick_backend`) reads, in the fixed order starting at ibm_marrakesh, each device's calibration
   in effect then and sends the job's own circuits (no recompiling, no retraining, the manifest and its hashes
   unchanged) to the first device with the job's number of qubits, not reported non-operational, and with no failed
   or unsupported element under the job (r8's rule, both compilers' circuits). `submission.json` records the device
   used, `trained_for` (ibm_marrakesh) and every device tried with its reasons. If none takes the job, nothing is
   submitted (`submission_refused.json`) and the day ends. H1, H2 and the undamped readout are scored the same way
   on whichever device ran the job; a device other than marrakesh is reported as such.

9. **No reference twin (owner, 2026-10-22, about 02:20 CEST).** r8's step 6b (the reference twin, report only, about
   5 h on the pod's CPU) is not run. H1, H2 and the undamped readout do not use it.

## The day (times are estimates)

| step | where | duration |
|---|---|---|
| pod start and bundle | pod | 10 min |
| snapshot fetch folder (T0 = the snapshot, 2026-10-13 11:37 CEST; item 7) | pod | 1 min |
| Rust (cargo) install and build | pod | 5 min |
| precheck (E2, E5 on the snapshot), plans, training of 4 runs (L 8 and 16, PSF and Qiskit, seed 301), assemble, undamp fix, zip | pod | about 3.5 to 4 h |
| fix r9 (hashes and time) | home | 10 min |
| submit (QPU about 138 s by the job's model) and the queue | home, VPN off | minutes to hours (queue) |
| result, score (r8) and undamp score | home, VPN off | 15 min |

Cost: the pod about 4 h on an H100 (about $16); QPU about 138 s.
