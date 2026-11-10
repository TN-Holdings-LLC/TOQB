# Utility observables, 2026-11-10 (prereg/utility_2026-11-11.md)

- Declared at 22ecaf0 (pushed as 52a3a87 after the large-file fix, GitHub f67734c..52a3a87, 13:44 CET); queue read
  13:44:25 CET: marrakesh 1, fez 1, kingston 12 -> order marrakesh, fez (ties in the declared order).
- ibm_marrakesh: no observable's cone avoids the failed elements (failed qubits 30, 32, 34, 41, 46, 47, 48, 56, 73, 82,
  113, 119, 130, 136; coupler 113-119): not buildable -> ibm_fez.
- ibm_fez (failed qubits 72, 148, 149; coupler 32-33): z106_t4 and w10_t5 on embedding 0, w17_t5 and w17b_t5x on
  embedding 1; 80 circuits, 92.3 s by the model; CZ per circuit 564 / 705 / 690 / 690. Answers file sha256 92a989df...
  (it differs from the try-build's f19ae7ac... only in Z_106's last digits, at most 1.2e-15: the contraction order
  varies; the sealed weight-10 / weight-17 values are identical).
- Pre-run check (gpu/utility_check.py): ALL PASS (Clifford points of all four on the whole device; Z_106 all 17 k by
  its cone, 1.2e-13).

## Run

Job dbph4f0ou4as73ctllq0, submitted 13:46 CET, DONE; job files returned byte-identical to the build. Sentinel DEAD.
Answers released in `answers/` (the three sealed files match the declared sha256; the build's answers file 92a989df...).

## Declared verdicts (gpu/utility_score.py)

| observable (paper's figure) | CZ per circuit | verdict | MSE / mean square | AGREES (of 17) | at theta_h = pi/2: raw / exact |
|---|---|---|---|---|---|
| Z_106, 4 steps (Fig. 2) | 564 | READS | 0.0207 / 0.4145 | 7 | +0.14 / 0.00 |
| weight-10, 5 steps (Fig. 3) | 705 | READS | 0.0226 / 0.1672 | 11 | +0.61 / +1.00 |
| weight-17, 5 steps (Fig. 3) | 690 | DOES NOT READ | 0.1091 / 0.1348 | 12 | -0.09 / -1.00 |
| Fig. 4a, 5 steps + R_X | 690 | DOES NOT READ | 0.1023 / 0.1200 | 12 | -0.07 / -1.00 |

- Against the prediction: Z_106 READS (as predicted); the weight-10 and weight-17 values near pi/2 keep their sign and
  the small mid-range values are near zero (as predicted); of the uncertain 17-point verdicts, weight-10 READS and both
  weight-17 products do not.
- Beside: Z_106 follows the exact curve from theta_h 0 to about 0.5 and stays above it at large theta_h (raw +0.14 to
  +0.28 where the exact value is 0 to 0.06). Weight-10 keeps 61% of its value at pi/2; the weight-17 products keep 7-9%.
  Floor / mirror parity: Z_106 0.991 / 0.504, weight-10 0.852 / 0.122, weight-17 0.310 / -0.004, Fig. 4a 0.305 / -0.009.
- IBM's published values were error-mitigated; no numerical comparison with them is made here.
