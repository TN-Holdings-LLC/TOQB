# Flow F, test match 2, 2026-10-26: the count rule against the zipper over four random models (rule declared; no Qiskit)

Declared in prereg/drafts-2026-10-26/rule_match_note.md (SHA-256 0b12d811…, `145f38b`, 02:04 CET). H100 pod,
`snapshot:marrakesh`, toqb `145f38b`, psf-zero `807debe` (a25, psfbind r3); 02:05-03:16 CET; both repositories by
bundle. rule_match.zip SHA-256 8abc44a0c11432cace8a9ea0efb4d34d4145b7e2af224fdc0b47d24158b9655f (computed on receipt).
L = 16, P 24, T 256, twin ("sim") and stand-in ("dev"), models 0-3 (model 0 = flows D and E). No cell errored.

**Check (declared): passed.** Model 0's lines equal the earlier ones exactly: `fold:rule` at n = 13-17 flow E's
`fold:pend`, at n = 18 flow D's `fold:template`; the zipper flow E's.

## Main match: `fold:rule` against the zipper (rule: WIN at n if 3 of 4 models larger on both models)

| n | verdict (models won) | rule's lam, 4 models x 2 | zipper's lam | ratio rule / zipper | two-qubit gates | us | active qubits |
|---|---|---|---|---|---|---|---|
| 13 | **WIN** (4/4) | 0.68-0.73 | 0.09-0.27 | 2.7-8.2 | 224 / 464 | 10.2 / 11.7 | 13 / 13 |
| 14 | **WIN** (4/4) | 0.64-0.76 | 0.13-0.46 | 1.6-5.2 | 256 / 496 | 10.2 / 11.7 | 14 / 14 |
| 15 | **WIN** (4/4) | 0.70-0.72 | 0.24-0.31 | 2.3-2.9 | 288 / 544 | 10.4 / 11.7 | 15 / 15 |
| 16 | **WIN** (4/4) | 0.63-0.73 | 0.17-0.40 | 1.6-3.8 | 320 / 576 | 10.4 / 11.7 | 16 / 16 |
| 17 | **WIN** (4/4) | 0.61-0.68 | 0.21-0.31 | 2.1-3.0 | 352 / 624 | 10.4 / 11.7 | 17 / 17 |
| 18 | **WIN** (4/4) | 0.51-0.59 | 0.26-0.34 | 1.5-2.3 | 352 / 656 | 7.3 / 11.7 | 20 / 18 |

The prediction (WIN at every n) held. The rule chose pendants at n = 13-17 and holes at n = 18.

- **Vanity:** six WINs of six, every model, both noise models; half the zipper's two-qubit gates or fewer.
- **What a device user needs (models, not a device):** the rule's lam stays within 0.51-0.76 over the 4 models
  (0.61-0.76 at n = 13-17), while the zipper's ranges 0.09-0.46: the ratio is 1.5-8.2, and the shots for the same
  precision (1/lam^2) 2.3-67 times fewer. One placement per n on one device.

## Reported only: `fold:rulerot` (read-out node moved) against `fold:rule`, n = 13-17

| n | mean lam difference (rot - rule, 8 values) | range | models higher on both | lower on both |
|---|---|---|---|---|
| 13 | **-0.342** | -0.388 to -0.291 | 0 | 4 |
| 14 | +0.012 | -0.047 to +0.068 | 2 | 2 |
| 15 | +0.019 | -0.036 to +0.044 | 3 | 0 |
| 16 | +0.047 | +0.006 to +0.081 | 4 | 0 |
| 17 | +0.036 | -0.011 to +0.072 | 3 | 0 |

- At n = 14-17 moving the read-out node off the pendant's cycle node gains little (+0.01 to +0.05 on average, within
  the spread of about 0.1 except n = 16).
- At n = 13 it loses 0.29-0.39 on every value. Found after the run (not declared): the moved read-out node sits on
  qubit 27, whose ring coupler 27-26 has the snapshot's largest CZ error on this cycle (0.0166; 26-25 0.0147; the
  others 0.0017-0.0039), and its ring neighbour then sits on qubit 26, the cycle's poorest qubit (readout 0.050, sx
  2.7e-3, against qubit 3's 0.012 and 3.4e-4; the workplace's reading points to qubit 26 too); the unmoved node sits
  on qubit 3, far from them. The rule does not read errors, so where
  the read-out node lands relative to a poor coupler is luck of the place; moving it by a formula can land it worse.
  Not separated further (one cycle, one device).

**Not claimed.** No device; the twin and the stand-in are TOQB's models of a 2026-10-13 calibration; four models per
n; one placement per n.
