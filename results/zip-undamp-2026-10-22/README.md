# The undamped readout on the zipper comparison's four runs (report only; 2026-10-22, pod H100, 07:5x-08:10 CEST)

Declared before any output in `prereg/drafts-2026-10-22/zip_undamp_note.md`. `toqb.undamp_run --final-only` on the four
records of `results/zip-compare-2026-10-22/runs/` (seed 301, teacher 4, angle 0.3, stand-in snapshot:marrakesh).
The zip's SHA-256: 9f0629f06ba08aeeecaa67a8c6214e8890f01eee082855070458a624b66bbdf2.

**A mistake, kept on record.** `gpu/zip_undamp.sh` first ran with TOQB_TRAJ_MEM_GB=8 (the runs used 4). For L 16 this
reshaped the trajectory batches, so the stand-in's shots were not redrawn as in the record ("shots reproduced False" in
`zu_2026-10-22/logs/`). L 16 was run again with 4 (`zu4/`): reproduced True. The L 16 rows below are `zu4`'s; the L 8 rows
(reproduced True) are `zu_2026-10-22`'s. The script's default is now 4.

| run | lam | delta | stand-in CE raw -> undamped | accuracy raw -> undamped | undamped inside | noiseless CE / accuracy |
|---|---|---|---|---|---|---|
| L 8, item 31 | 0.334 | +0.052 | 0.5629 -> 0.4040 | 0.783 -> 0.833 | yes | 0.4044 / 0.880 |
| L 8, zipper | 0.369 | +0.011 | 0.5662 -> 0.4096 | 0.823 -> 0.840 | yes | 0.4058 / 0.860 |
| L 16, item 31 | 0.268 | +0.046 | 0.6323 -> 0.5599 | 0.618 -> 0.680 | yes | 0.4981 / 0.762 |
| L 16, zipper | 0.158 | +0.015 | 0.6446 -> 0.5191 | 0.710 -> 0.712 | yes | 0.4467 / 0.834 |

- The undamping improved every run's stand-in CE (0.07 to 0.16), each inside its undamped prediction.
- L 8: zipper and item 31 tie (0.410 against 0.404). L 16: the zipper is ahead (0.519 against 0.560), but the
  undamped CE moves by about 0.03 with the shots alone (item 31: 0.527 with the unreproduced draw, 0.560 with the
  record's), and the zipper's undamped interval is wide (0.50-0.69): one seed, no claim.
- W12's check: the trained models' noiseless outputs are not small (mean |z| 0.32-0.43); at L 16 the model trained
  through the zipper is better even without noise (CE 0.447 against 0.498).
- Not understood: the zipper's L 16 lam (0.158) is smaller than item 31's (0.268) although its circuit is shorter.
