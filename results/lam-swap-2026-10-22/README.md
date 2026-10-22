# The lam swap (report only, declared in prereg/drafts-2026-10-22/lam_swap_note.md, `cfdb01e`)

Run on an H100 pod, 2026-10-22 13:28-13:30 CEST, `python -m toqb.lam_swap results/zip-compare-2026-10-22/runs`
(TOQB 72afd4f, psf-zero 6269c4f, RUST=1, TOQB_TRAJ_MEM_GB 4). Output as printed: `lam_swap.txt`.

| L | model \ circuit | item 31 | zipper |
|---|---|---|---|
| 8 | item 31 | 0.334 | 0.366 |
| 8 | zipper | 0.337 | 0.369 |
| 16 | item 31 | 0.268 | 0.183 |
| 16 | zipper | 0.182 | 0.158 |

- L 8: lam follows the circuit (the column); the zipper's circuit shrinks less (lam 0.37 against 0.33).
- L 16: neither alone. Each swap away from item 31 / item 31 lowers lam by about the same (0.268 to 0.18), and both
  together to 0.158. The zipper's circuit shrinks more at L 16 than item 31's (for either model), the reverse of L 8;
  and the zipper's model shrinks more than item 31's on either circuit.
- delta follows the circuit at both depths (item 31's circuit +0.05 to +0.07, the zipper's +0.01).
- One seed and one teacher; TOQB's twin on the 2026-10-13 calibration. Not claimed.
