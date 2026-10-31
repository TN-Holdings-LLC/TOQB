# Stage-1 reading checked on the simulator, and a post-hoc look at 30 October (2026-10-31; no device run)

For the draft `prereg/drafts-2026-10-31/coherent_stage1_DRAFT.md` (not fixed).

- `validate.py` / `validate.txt`: n = 8 ring, the rule's echo (`toqb.kising_echo` circuit), an error after every CZ
  on qubits 3 and 4 (RX, RZZ, depolarising), read in X, Y, Z through `toqb.echo_tomo.with_basis`, 2000 shots. Made
  with the first-draft verdicts (ROTATED / LOST / MIXED; MONOTONE / OSCILLATES). Finding: a coherent two-qubit error
  (RZZ) shrinks the one-qubit vector just as loss does, so the vector length alone cannot tell them apart; at RZZ 0.3
  the Z signal changes sign over depth, loss never does.
- `validate.py corr` / `validate_corr.txt`: connected ZZ correlation of the error pair against the other pairs at
  D = 12: RX 0.15 0.047 / 0.058; RZZ 0.15 0.736 / 0.212; RZZ 0.3 0.616 / 0.107; depolarising 0.03 0.199 / 0.210.
  The pair correlation separates a two-qubit coherent error from loss. The verdicts were revised after this
  (`verdict_length`, `verdict_depth`, `verdict_corr` in `toqb.echo_tomo`).
- `preview_1030.py` / `preview_1030.txt`: kingston 30 October rerun, post hoc. Block B (38-59) -0.094 / -0.047 /
  0.000 at D = 24 / 50 / 100 (rest +0.429 / +0.005 / +0.001). Connected ZZ at D = 24: dead-run pairs 0.154, block B
  pairs 0.183, healthy pairs 0.315 (sd 0.028); n = 20 ring 0.289. On the device, healthy pairs already carry a large
  correlation (the echo spreads its own errors), so the comparison is against the same ring's healthy pairs.
