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
