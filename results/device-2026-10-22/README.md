# C r9 device day, 2026-10-22: results

Job dbcubfoc77vs73872leg, ibm_marrakesh (calibration in effect 12:01 CEST; the twin's: the 2026-10-13 snapshot),
submitted 12:30:03 CEST, done 12:33 CEST, QPU charged 100 s (open plan). Scored at home with the fixed code; the score
was reproduced in the cloud from the same raw counts (identical tables). Files: `device/`.

## Pre-registered (r8 H1, H2; r9 unchanged)
| cell | correct / P | H1 (Holm, alpha 0.01) | CE device (predicted) | inside 99 % | accuracy device (predicted) |
|---|---|---|---|---|---|
| PSF L 8 | 109 / 150 | confirmed (p 5.2e-8) | 0.5087 (0.5618) | no | 0.733 (0.771) |
| Qiskit L 8 | 79 / 150 | not confirmed (p 0.28) | 0.6613 (0.5205) | no | 0.527 (0.739) |
| PSF L 16 | 277 / 500 | not confirmed (p 0.018) | 0.5716 (0.6291) | no | 0.563 (0.624) |
| Qiskit L 16 | 305 / 500 | confirmed (p 1.5e-6) | 0.5867 (0.5852) | yes | 0.625 (0.648) |

H2 (PSF's predictions closer to the device than Qiskit's): not confirmed at L 8 (mean d +0.019, Wilcoxon p 0.57) or
L 16 (d -0.068).

## Reported (r9 item 3, the undamped readout with the twin's lam, delta fixed before submission)
Qiskit L 16 improved and fell inside (0.587 -> 0.524, accuracy 0.625 -> 0.722); PSF L 8 slightly (0.509 -> 0.504);
PSF L 16 worse (0.572 -> 0.797); Qiskit L 8 worse (0.661 -> 0.691).

## Post hoc diagnostic (after the results; not a hypothesis): the device's own shrink on the test points
`device/lam_posthoc.txt` (`toqb.device_lam_posthoc`; no labels; in-sample, so a diagnostic only).

| cell | twin lam / delta | device lam / delta | correlation device vs noiseless |
|---|---|---|---|
| PSF L 8 | 0.334 / +0.052 | 0.666 / +0.162 | 0.924 |
| Qiskit L 8 | 0.614 / +0.085 | 0.367 / +0.284 | 0.599 |
| PSF L 16 | 0.268 / +0.046 | 0.711 / +0.137 | 0.885 |
| Qiskit L 16 | 0.496 / +0.087 | 0.552 / +0.103 | 0.916 |

- The twin (snapshot + TOQB's noise model) under-states how much signal PSF's circuits keep on the device by a factor of
  2.0 to 2.7; on the device PSF keeps more signal than Qiskit (0.71 against 0.55 at L 16), the reverse of the twin.
  Undamping with the twin's lam therefore over-corrected PSF (L 16: CE 0.797).
- The device adds a larger offset delta (+0.14 to +0.28) than the twin; it biases the answers toward label +1.
- Qiskit L 8's answers correlate weakly with its own noiseless output (0.60) with a large offset: the cause is not known
  (its calibration-aware placement used the 9-day-old errors; not checked).
- This motivates measuring (lam, delta) on the device itself from the training inputs (label-free), as a pre-registered
  next step; it is not claimed from these numbers.

## Post hoc diagnostic 2: the calibration in effect during the run (fetched 12:58 CEST, calibration 12:21 CEST)
`device/map_posthoc.txt` (`toqb.device_map_posthoc`), snapshot (2026-10-13) against the run's calibration, on each
cell's own qubits and couplers:

- PSF (both depths, qubits 47-55 and 59): its qubits improved since the snapshot (median T1 144 -> 181 us; mean CZ
  error 0.0077 -> 0.0061; worst coupler 47-48 0.0285 -> 0.0201); the readout qubit 47's T1 doubled (133 -> 249 us).
  This explains part of the twin's under-statement of PSF's signal; whether it explains a factor 2 to 2.7 is not known
  (it would need the twin rebuilt on this calibration).
- Qiskit L 8 read out on qubit 102, which degraded (readout error 0.019 -> 0.043, T1 95 -> 77 us), and coupler 116-121
  worsened (CZ error 0.002 -> 0.007). Qiskit L 16 read out on qubit 143, which did not degrade. A plausible part of
  Qiskit L 8's collapse and offset; not shown to be the whole cause.
