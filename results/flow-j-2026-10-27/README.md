# Flow J, 2026-10-27: how much signal the count rule keeps at n = 20 and 22 on the kingston day twin (rule only; prediction declared)

Declared in prereg/drafts-2026-10-27/rule_lam_big_note.md (SHA-256 5b5b69ad…, `5da4fff`, 07:49 CET). H100 pod, toqb
`5da4fff`, psf-zero `61d0b545`; Target SHA-256 3b939138… (ibm_kingston, 2026-10-24; flows C, G, I). n = 20
07:51:05-08:12:27 CET, n = 22 08:12:27-11:36:48 CET. `fold:rule` only, L = 16, P = 24, T = 256, models 0-3, twin
("sim"), noiseless reference by Qiskit's Statevector on the CPU. Files: `n20.jsonl`, `n22.jsonl` (the `.log` files are
copies), `times.txt`, `rust.txt`; rule_lam_big_n22.zip SHA-256 806839d20dd3f5f895cb37e097d358a464a376d555b56b14c3a3e711d202dbf6.
n = 24 (amendments 1 and 2, the reference on the GPU) is a separate run, reported below and in `n24/`.

| n | the rule's placement | two-qubit gates (per layer) | us | lam per model (± standard error) | corr | prediction |
|---|---|---|---|---|---|---|
| 20 | the ring itself on a 20-cycle | 320 (20) | 5.6 | 0.845 ± 0.028, 0.860 ± 0.014, 0.779 ± 0.019, 0.789 ± 0.023 | 0.988-0.997 | >= 0.61 every model: **held** |
| 22 | two pendants on the same 20-cycle (leaves on qubits 2 and 46) | 384 (24) | 9.2 | 0.749 ± 0.023, 0.844 ± 0.021, 0.773 ± 0.016, 0.760 ± 0.012 | 0.990-0.997 | 0.50-0.860 every model: **held** |

Offsets (delta) +0.001 to +0.005. Seconds per model: n = 20 141 for the trajectories (about 180 more for the noiseless
reference on the CPU); n = 22 938 (about 2,100 more for the reference).

**One cycle, three placements.** On this Target the rule uses the same 20-cycle (qubits 3-7, 16, 17, 21-23, 25-27, 36, 37,
41-45) at n = 18 (two holes, flow G), 20 and 22:

| n | placement on the 20-cycle | two-qubit gates per layer | us | lam (four models) |
|---|---|---|---|---|
| 18 | two holes moved each layer | 22 | 6.7 | 0.61-0.68 (flow G) |
| 20 | the ring itself | 20 | 5.6 | 0.78-0.86 |
| 22 | two pendants | 24 | 9.2 | 0.75-0.84 |

- **Vanity:** at n = 20 the ring needs no extra gate (320 against the zipper's 736); at n = 22, 384 against 816.
- **What a device user needs (a twin of a real day's calibration):** the rule keeps 0.75-0.86 of the signal at n = 20
  and 22 (shots for a fixed precision 1.35-1.8 times those of a noiseless circuit), about as much as at n = 13-17
  (0.69-0.82, flow G). On the same qubits, two pendants (24 two-qubit gates per layer) kept nearly what the bare ring
  kept and clearly more than two holes (22 per layer): the placement, not the gate count, decided most of the
  difference.
- The random models differ between n (seeded by n), so the comparison across n mixes the placement with the model;
  with four models each the ranges do not overlap between holes and the other two.

**Not claimed.** No device; one day's calibration of one device; random models; one placement per n; no second arm, so
no match.

## n = 24 (amendments 1 and 2)

Declared in prereg/drafts-2026-10-27/rule_lam_big_amend1.md (`6924d12`, 08:57 CET) and rule_lam_big_amend2.md (SHA-256
04b70974…, `90e7127`, 09:09 CET: the noiseless reference on the GPU). Same pod, toqb `90e7127`, psf-zero `61d0b545`.
**Checks (declared): passed** (11:37:38-11:40:23 CET, read from the pod's `rule_lam_big_n24_2026-10-27_check/times.txt`,
not retrieved as a file): the direct statevector equals Qiskit's within 2.78e-15 (numpy and cupy, n = 3-13); n = 20,
model 0, rerun with the reference on the GPU equals the CPU-reference row. n = 24 11:40:23-19:56:15 CET, 7,415 s a
model. Files in `n24/` (`n24.jsonl`, `.log` copy, `times.txt`, `rust.txt`); rule_lam_big_n24.zip SHA-256
fe54d590f4a8faf57dc294e140229f93d17e950b3ae874f6f4b536a95c615a3a. Rows carry "noiseless": "cupy".

| n | placement | two-qubit gates (per layer) | us | lam per model (± standard error) | corr | prediction |
|---|---|---|---|---|---|---|
| 24 | the ring itself on a 24-cycle (qubits 3-7, 16, 17, 21-23, 27-29, 36, 38, 41-49) | 384 (24) | 5.6 | 0.833 ± 0.024, 0.832 ± 0.015, 0.810 ± 0.009, 0.805 ± 0.013 | 0.991-0.999 | >= 0.61 every model: **held** |

- **Vanity:** 384 two-qubit gates against the zipper's 896; 5.6 us.
- **What a device user needs:** the bare ring on a 24-cycle kept 0.80-0.83 of the signal (shots 1.44-1.54 times those
  of a noiseless circuit), the same level as the bare ring on the 20-cycle (0.78-0.86). The 24-cycle shares most of
  its qubits with the 20-cycle but not all, and the classifiers differ, so this is a comparison of places and models
  as well as of size.
