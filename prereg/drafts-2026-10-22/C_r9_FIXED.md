# C r9 fixed (home, 2026-10-22 04:01 CEST, before submission; no device result exists)

C r9 = r8 + the amendment below. Fixed by these SHA-256 and this CEST time, before `submit`. The job was built on the
pod from 02:12 to 03:53 CEST (`results/device-2026-10-22/times.txt`); nothing has been sent to IBM.

| file | SHA-256 |
|---|---|
| prereg/drafts-2026-10-20/C_preregistration_r8_final_draft.md (r8) | dcba1249a829eefafec56e4c7b876eb5c3c99bd7e694bc99138fd3991eca41ef |
| prereg/drafts-2026-10-21/C_preregistration_r9_amendment_draft.md (items 1-9) | cc72e64395165eabf0b5b5c4e9569816292354091ece144b9b7c339204432389 |
| job/manifest.json (predictions, labels, hashes; 1,300 circuits x 250 shots; QPU 137.6 s by the job's model) | ef5771eaf9b17023ede689ed409921c07efe277790a83e436fa3a1815e3c2ace |
| job/circuits.qpy | 3565c21865039c002660e20d5ccc19b1d2f8aa3b867904d0b6b265da86a19ef5 |
| job/undamp.json (lam, delta and the undamped prediction per cell; bound to the manifest's SHA-256) | 6c58f2ec3ca8ee38846f0270b035bfe866ed048f1cfde353f0583f3c552c3252 |
| the snapshot Target (target.pkl; fetch.json source "snapshot", calibration 2026-10-13 11:37 CEST) | a715121cdc6ac457960bd0f7586b43822e38b2ae39b56e1eec765e47749df245 |
| toqb/s2rc_device.py (submit with item 8, result, score; equal to the manifest's script_sha256) | 28d8e8498d30c7aed7c4f9a9989caa0e179406ad5a81f6cc8cf1c3d028a1f5ca |
| toqb/s2rc_device_undamp.py (the undamped score) | 7371f415b1760ad65f4d104cb04f260cf97c00ae962e1ac9df431956e50a5525 |

Code: TOQB 5e96bbe on the pod (psf-zero 6269c4f); the PSF template built in Rust and checked against the Python's
(RUST=1, TOQB_RUST_TEMPLATE=check: no difference, all four runs valid). Precheck on the snapshot: all OK.

## The predictions (twin on the snapshot; 99 % intervals; raw readout = H1 / H2's)

| cell | arm | L | points | CE [99 %] | accuracy | undamped CE [99 %] | undamped accuracy | lam |
|---|---|---|---|---|---|---|---|---|
| 0 | PSF | 16 | 500 | 0.6291 [0.6213, 0.6369] | 0.624 | 0.5475 [0.5120, 0.5939] | 0.683 | 0.268 |
| 1 | Qiskit L2 | 16 | 500 | 0.5852 [0.5777, 0.5927] | 0.648 | 0.5070 [0.4919, 0.5251] | 0.727 | 0.496 |
| 2 | PSF | 8 | 150 | 0.5618 [0.5488, 0.5747] | 0.771 | 0.4161 [0.3785, 0.4783] | 0.803 | 0.334 |
| 3 | Qiskit L2 | 8 | 150 | 0.5205 [0.5078, 0.5333] | 0.739 | 0.4430 [0.4233, 0.4634] | 0.790 | 0.614 |

Copies of the manifest, undamp.json, the plans, the run records and the logs are in `results/device-2026-10-22/`,
with the pod's paths written `<pod>/` (so those copies' own hashes differ from the originals; the originals are in
the day's zip, SHA-256 06b203a0d32d7a5042c79d0fbb1ecefd235b48e0a3be8878c258ed04a8db5915). The QPY files (170 MB)
are in the zip only.
