# S2R design C: pre-registration r9 = r8 + this amendment (draft, 2026-10-21)

**Status.** Draft. The base is `prereg/drafts-2026-10-20/C_preregistration_r8_final_draft.md`, unchanged except as
listed here. Fixed on the device day by the SHA-256 of this file, of r8, of `job/manifest.json` and of
`job/undamp.json`, with the CEST time, before the submission.

## Changes (owner, 2026-10-21)

1. **No time limit from T0 to submission.** r8's limit (6.32 h, §5 and §7) is removed. The calibration in effect at
   submission is recorded (`submission.json`: calibration_at_submit, as r8), and, if fetched again before
   submitting, its difference from T0's (`toqb.s2rc_device drift`) is reported. Neither stops the submission.
2. **Device and placement: no choice by calibration.** r8's rule stays (E1-E4, then the fixed order marrakesh, fez,
   kingston). The only check on the calibration is r8's: a job that uses a failed qubit or coupler is not submitted
   (E4 and submit's check). PSF's placement is its fixed template. Qiskit's calibration-aware placement is recorded as
   Qiskit's own choice.
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
     (`TOQB_RUST_TEMPLATE=check`, `gpu/rust_psf.sh`). A case the Rust does not port (VF2 placement, an embedding
     ring) is built by the Python and listed in the run's arm stats.
   - Evidence before the day: bit-identical templates (fixed angles and factors differ by 0.0) on the stand-in at
     L 2, 8, 16, and identical on 146 of 150 cases over five devices with random failed elements (4 refused, VF2).
   - Nothing else changes: the circuits (gates, qubits, angles bit for bit), the binding (`RingTemplate.angles`),
     the QPY export and the job. Checked on a device-style run (verify false): the same record, times aside, and the
     same QPY bytes once Qiskit's automatic circuit names are set aside (`assign_parameters` appends a process-wide
     counter that counts the circuits made before; the Python builder makes more of them).

## The day (times are estimates)

| step | where | duration |
|---|---|---|
| pod start and bundle | pod | 10 min |
| fetch (T0) | home, VPN off | 10 min |
| precheck, plans, training of 4 runs (L 8 and 16, PSF and Qiskit, seed 301), assemble, undamp fix, zip | pod | about 3.5 to 4 h |
| fix r9 (hashes and time) | home | 10 min |
| submit (QPU about 138 s by the job's model) and the queue | home, VPN off | minutes to hours (queue) |
| result, score (r8) and undamp score | home, VPN off | 15 min |

Cost: the pod about 4 h on an H100 (about $16); QPU about 138 s.
