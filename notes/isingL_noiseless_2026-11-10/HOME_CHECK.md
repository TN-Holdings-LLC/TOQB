# Home check of VS Claude's noiseless run of the isingL job (2026-11-10)

- VS zip sha256 517d88d784ea0eccdb8e9c8347aa4825841c7c968b89f81708269412330d6f39; its SHA256SUMS hold.
- Input: the try-build on the kingston record of 11-08 (`isingL_trybuild_kingston_1108.zip`); the manifest in VS's
  output is byte-identical to the one built at home.
- Answers: `IL_answers.json` (2ece3130...) gives, for all 48 arms, exactly the entry of the sealed table of
  `prereg/isingL_2026-11-09.md` (8aa3d53d..., keyed by lattice and t, one table for both layouts and every place).
  This answers VS's open point 2.
- Re-scored at home with `gpu/isingL_score.py` (psf-os 0fb4512) from VS's raw counts: scores.json identical to VS's.
  48 of 48 arms READS and AGREES; largest nMSE 0.00098; largest |M - M_exact| 0.0087; no line - fold pair resolved.
- The sentinel reads DEAD because noiseless.py writes stand-in counts for the 40-qubit ring (as built).
- So the declaration's pre-run condition (every 4 x 3 x 2 arm READS and AGREES noiselessly) holds. Not a device result.
