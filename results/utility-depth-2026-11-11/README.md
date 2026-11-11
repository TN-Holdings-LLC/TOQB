# Depth scan of IBM's 2023 utility observables, raw, ibm_fez, 2026-11-11 (prereg/utility_depth_2026-11-11.md)

- Declaration pushed 11:13:03 CET (a22fec3, reflog "update by push"); queue read 11:13:35 CET (marrakesh 1, fez 6,
  kingston 101; chosen marrakesh, fez). `gpu/utility_depth_pick.py`: marrakesh places no cone (14 failed qubits),
  fez all seven on embedding 0 -> ibm_fez (failed qubits 72, 148, 149; coupler 32-33, as on 11-10).
- Build: 137 circuits, 155.9 s by the model (cap 160 s, owner 14:47 JST). Gate hash equal to the try-build's, whose
  pre-run check passed (`ibm_fez/check_trybuild.json`: stabilizer sampled and exact at k = 0, 16; Z_106 4 and 5 steps
  all 17 k by the cone; the five deeper at k = 5, 11 by quimb on the compiled job circuit) -> the PASS carries over
  (rule fixed before the record, `notes/tonight_2026-11-11/PLAN.md`). Answers equal the try-build's within 1.0e-15.
- Job dbq43nc4148s739vgktg, submitted 11:22 CET, DONE; circuits and manifest returned byte-identical. Sentinel DEAD.
- Answers released after the verdicts (`answers/`); sha256 of the five sealed files equal the declared ones.

## Declared verdicts (gpu/utility_score.py)

| observable | steps | CZ | cone | MSE / mean square | verdict | AGREES |
|---|---|---|---|---|---|---|
| Z_106 | 4 | 564 | 17 | 0.0198 / 0.4145 | READS | 7/17 |
| Z_106 | 5 | 705 | 25 | 0.0149 / 0.4073 | READS | 7/17 |
| Z_106 | 6 | 846 | 31 | 0.0117 / 0.4005 | READS | 8/17 |
| Z_106 | 7 | 987 | 38 | 0.0110 / 0.3968 | READS | 8/17 |
| Z_106 | 8 | 1128 | 43 | 0.0108 / 0.3921 | READS | 8/17 |
| weight-10 | 5 | 705 | 37 | 0.0238 / 0.1672 | READS | 11/17 |
| weight-10 | 6 | 846 | 42 | 0.0005 / 0.0038 | READS | 17/17 |

Readable depth on this device and day: Z_106 8 steps or more (every step run reads); weight-10 6 steps or more.

## Prediction (written before the data)

- "Z_106 READS at 4, 5 and 6 steps; 7 and 8 uncertain": held at 4-6; 7 and 8 also READ.
- "The weight-10 product does not READ at 6 steps": **did not hold** (it READS, 17 of 17 within 0.05).

## Beside (not judged)

- Anchors against 11-10 (same device, same circuits): Z_106 4 steps MSE 0.0198 (11-10: 0.0207); weight-10 5 steps
  0.0238 (11-10: 0.0226).
- The Z_106 answer changes little with depth: the exact curves at 4 and 8 steps differ by at most 0.11 (k = 9:
  0.35 and 0.26); the device moved by about the same amount at that k (0.54 and 0.42). The MSE falls with depth
  because the device's tail at large theta_h (0.08-0.17 where the exact value is about 0) shrinks with depth.
  Reading at 8 steps here is reading a slowly changing answer, not a test of a fast-changing one.
- Weight-10 at 6 steps is a small signal: mean square 0.0038, largest exact value 0.13 (k = 13, 14). Against the guess
  "all zero" (MSE = mean square = 0.0038) the device's MSE is 0.0005; the device's largest values sit at the same k
  (0.12, 0.09 at k = 13, 14; 0.02 at k = 16 where the exact value is 0). The READS line was not written for so small a
  signal; it is reported as declared.
- Floor 0.988-0.994 (Z_106), 0.871-0.878 (weight-10); mirror falls with depth: 0.484, 0.406, 0.363, 0.360, 0.315
  (Z_106 4-8), 0.108, 0.045 (weight-10 5, 6).
