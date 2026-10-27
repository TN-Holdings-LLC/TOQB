# Flow K, 2026-10-27: the same classifiers on the same qubits, placed two ways — the count rule against the zipper on the rule's own cycle (rule declared)

Declared in prereg/drafts-2026-10-27/zipcyc_k_note.md (SHA-256 7ee78daf…, `42b6d72`, 13:03 CET). A second H100 pod
(`H100 80GB HBM3`, as flows G-J), toqb `42b6d72`, psf-zero `61d0b545`; Target SHA-256 3b939138… (ibm_kingston,
2026-10-24). Start 13:15:23 CET; main 13:24:14-14:03:57 CET. Files: `check.jsonl`, `main.jsonl` (`.log` copies),
`times.txt`, `rust.txt`; zipcyc_k.zip SHA-256 b055e916ea4c44a8f368874732ce06e67f3a6c3f17bfea59cd365c16ac48e8bf.

**Check (declared): passed.** `fold:rule` at n = 18 and 20, model 0, rerun on this pod, equals flows G and J
(lam 0.68218 and 0.84549, q2, us), so their rule rows are used.

| n | rule (placement, two-qubit gates, us) | `fold:zipcyc` on the same qubits (gates, us) | rule's lam | zipcyc's lam | verdict | ratio | shots fewer |
|---|---|---|---|---|---|---|---|
| 18 | two holes on the 20-cycle (352, 6.7) | the zipper on 18 of its qubits (656, 10.6) | 0.682, 0.614, 0.682, 0.670 | 0.589, 0.542, 0.567, 0.557 | **WIN** (4/4) | 1.13-1.20 | 1.3-1.4 x |
| 20 | the ring itself on the 20-cycle (320, 5.6) | the zipper on the same 20 qubits (736, 10.6) | 0.845, 0.860, 0.779, 0.789 | 0.547, 0.598, 0.494, 0.435 | **WIN** (4/4) | 1.44-1.81 | 2.1-3.3 x |

Standard errors: the rule's 0.014-0.028, zipcyc's 0.028-0.054. Correlation with the noiseless output: zipcyc
0.954-0.975 (n = 18) and 0.892-0.969 (n = 20), the rule's 0.99. zipcyc's qubits: 3-7, 17, 27, 26, 25, 37, 45-41, 36,
21, 22 (and 23, 16 at n = 20), in path order.

- **Predictions:** n = 20 WIN: **held**. n = 18: no direction was predicted; the rule won 4 of 4.
- **Vanity:** on the same qubits the rule has 0.54 (n = 18) and 0.43 (n = 20) of the zipper's two-qubit gates and
  0.63 and 0.53 of its duration.
- **What a device user needs (a twin of a real day's calibration):** with the classifier, the inputs and the qubits
  fixed, the placement alone changed the kept signal by 1.13-1.20 x (holes against the zipper) and 1.44-1.81 x (the
  bare ring against the zipper); the zipper's output was also noisier (correlation down to 0.89).
- **The place matters too.** At n = 18 the zipper placed by PSF-Zero elsewhere on the device (flow G, same models) kept
  0.646, 0.629, 0.662, 0.630, more than on this cycle's qubits on every model (0.06-0.10 more). Placement and place
  are separate effects; this flow fixes the place.

**Not claimed.** No device; one day's calibration of one device; random models; one cycle.
