# Pre-run check of the N = 71 dual-unitary jobs (2026-11-07; no device, no noise; POD 64 cores, VS Code Claude)

Kit `du71_dry_kit_2026-11-07.zip` plus the patch to `mps_dry.py` (its depth filter tested the prefix "p2d_du51", so
the first attempt computed t 12-24 at 71 qubits; found on the POD and fixed, 3c429ba). Records of 11:14 CET:
kingston (shape S1) and fez (shape S3). Every point up to t = 8 run noiselessly with Aer MPS ordered along the chain,
scored by `gpu/du51_score.py --ts 4,8` (`dry_scores.txt`): on-cone <X_t> within shot noise of cos(2h)^t at t = 4, 8
(e.g. h 0.15: 0.838 / 0.833, 0.692 / 0.694), decay rates AGREE at all three h (0.9939 / 0.9799 / 0.9557 against
0.9950 / 0.9801 / 0.9553), off-cone max 0.028-0.068. The two shapes give identical numbers: noiselessly, with the
simulator's qubits in chain order and the same seed per circuit, the two compiled jobs are the same computation, and
the scorer maps each card back to chain sites; the answers files differ by shape (S1 07b6d574..., S3 905a736d...).
Started 20:48 JST, finished 21:08 JST.

## 2026-11-08: N = 91 on the 7 November records (checked for paper 7)

`daily.du91.place(dev, 91)` on kingston's record (`results/du71-2026-11-07/ibm_kingston/dev`, the same failed
elements as the du51 record) and on marrakesh's record of 14:34 CET (`results/du71-2026-11-07/fetch/marrakesh_device.json`):
no shape qualifies on either (marrakesh: none for N = 71 either, as recorded in the build).
