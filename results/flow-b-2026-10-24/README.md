# Flow B (declared in prereg/drafts-2026-10-24/flow_b_note.md, `4fe51cd`), on the owner's PC (RTX 4070, WSL)

Run by the VS Code Claude on the owner's PC with `run_flow_b_pc.sh` (B1, then B3, then B2); its log is kept on the PC
(`vscode_claude_log.md`). PC paths written `<pc>/`.

## B1, the a24 switch on the GPU: PASS (2026-10-24 07:33-07:40 CEST)

flow_b1.zip SHA-256 ac685473456f3370f03a9241ce78970e03d2580640c53658f8e09d595c24fcae.

- `toqb.check_traj 4000` with the a24 front end, complex64 on the GPU: PASS, largest 2.00 se.
- 20 loops of design C (L 16, teacher 17 at angle 1.0) through each PSF arm, on a24 (default) and on a22 / c61
  (explicit), with TOQB_FAST_PSF=1: the final parameters are equal, max |a24 - a22| = 0 for both arms. The records'
  versions confirm the two front ends (psf_ai_compile 2026-10-22.a24 with PSF_RING_ZIP=1; 2026-10-15.a22 with
  toqb.ring_zip).

## B3, first attempt: stopped by the PC's memory (2026-10-24 07:40-07:52 CEST), no result

Three runs in parallel (PAR=3) took about 11.6 GB of host memory together (about 5 GB each) in a WSL with 15.9 GB;
WSL's out-of-memory killer ended one at 250 of 4,000 loops, and the driver and the other runs ended with it. No
record was written (runs/ empty). Not a result; the declared rule is untouched. To be re-run one at a time (PAR=1, a
setting of execution only: each run is deterministic and does not depend on the others) into a new folder.

## B3, one run at a time (PAR=1): the decaying step is not the better (2026-10-24 12:16-19:17 CEST)

flow_b3.zip SHA-256 72d2a67116a87c62995fa00496f80dacb3e9ef661a06e96eb162250c74f7216a; files in `b3/` (driver
`run_flow_b_pc2.sh`, SHA-256 ef366d3e…; PC paths written `<pc>/`). Six runs of 4,000 loops, all `valid`, about 66 min
each on the RTX 4070, no out-of-memory.

**Rule (flow_b_note.md): TIE on all three teachers, WIN 0, LOSS 0 of 3: the decaying step is the better at 4,000
loops: no.**

| teacher | noiseless accuracy at 4,000 loops, decaying / constant | McNemar b / c | Holm p |
|---|---|---|---|
| 20 | 0.620 / 0.630 | 73 / 78 | 1.00 |
| 21 | 0.618 / 0.652 | 33 / 50 | 0.235 |
| 22 | 0.638 / 0.642 | 30 / 32 | 1.00 |

Reported, without a claim (b3/score.md):

- **No drift to stop.** With the constant step, accuracy rose to 4,000 loops on teachers 20 and 21 and stayed within
  0.002 of its best on 22 (best at 2,000). The drift seen on teachers near the start (zip-long-2026-10-23) did not
  appear on these far teachers within 4,000 loops, so the decaying step had nothing to fix here.
- The decaying step was behind the constant one at 11 of 12 checkpoints (by 0.004-0.034 at 4,000 loops, none significant):
  its smaller step learns more slowly.
- Stand-in accuracy with 250 shots at 4,000 loops: 0.590-0.625 (decaying), 0.602-0.626 (constant).
- Re-scored at home with `toqb.lrdecay_score` on the records (after the path redaction): score.md identical.

## B2, where the readout offset comes from: none of the stand-in's three additions (2026-10-24 19:17-23:01 CEST)

flow_b2.zip SHA-256 dd487dc9b914a545bc43908561069ad8d409f3870bf43a110be22315071c9ac1; files in `b2/`
(`offset_ablate.json`, 1,024 trajectories). Report only.

Share of +1 answers on the 500 balanced test points, stand-in as declared / no_zz / no_over / no_t12 / plain (all
three off):

| arm | teacher | theta = 0 | 2,000 loops |
|---|---|---|---|
| item 31 (psfai:template) | 17 | 0.93 / 0.92 / 0.93 / 0.94 / 0.93 | 0.89 / 0.90 / 0.89 / 0.90 / 0.91 |
| | 18 | 0.93 / 0.89 / 0.93 / 0.93 / 0.91 | 0.82 / 0.81 / 0.83 / 0.82 / 0.82 |
| | 19 | 0.85 / 0.83 / 0.85 / 0.85 / 0.84 | 0.84 / 0.84 / 0.84 / 0.85 / 0.84 |
| zipper (psfai:template_zip) | 17 | 0.83 / 0.82 / 0.83 / 0.83 / 0.82 | 0.75 / 0.74 / 0.76 / 0.75 / 0.75 |
| | 18 | 0.77 / 0.79 / 0.77 / 0.77 / 0.79 | 0.55 / 0.55 / 0.54 / 0.55 / 0.55 |
| | 19 | 0.76 / 0.74 / 0.76 / 0.76 / 0.74 | 0.61 / 0.60 / 0.62 / 0.60 / 0.61 |

- **Read.** Switching off ZZ, over-rotation, the T1/T2 scaling, or all three changes the +1 share by at most 0.04 and
  the offset delta by at most 0.004. The offset is already in the snapshot's own noise model: "plain" is the twin
  (its lam and delta equal the twin's to the printed digit), and the twin's delta is +0.027 to +0.076 for item 31
  against +0.000 to +0.016 for the zipper. With relaxation known to make part of item 31's twin delta
  (lam-ablate-2026-10-22), the likely source is relaxation acting on item 31's longer circuit, not the stand-in's
  additions; not separated further here.
- The +1 share also depends on the model: it falls with training for the zipper (0.76-0.83 to 0.55-0.75), much less
  for item 31.
- Not claimed: one seed; teachers 17-19; the stand-in is TOQB's model of a 2026-10-13 calibration.
