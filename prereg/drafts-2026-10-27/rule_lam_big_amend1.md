# Flow J, amendment 1 (owner, 2026-10-27 "２４の準備もしておいて"): add n = 24. Fixed by SHA-256 and CET time before n = 24 runs

Everything as in rule_lam_big_note.md (SHA-256 5b5b69ad…, `5da4fff`), with n = 24 added as a separate run after
n = 20 and 22 have finished. The note's open choice for n = 24 ("later, if at all") is taken: it runs if the owner
starts it; if he does not, it is reported as not run.

- **n = 24 on this Target:** the ring itself on a 24-cycle (384 two-qubit gates, 5.6 us, 24 active qubits; compile,
  2026-10-26). This cycle is not the 20-cycle used at n = 18, 20 and 22, so n = 24 is compared with them only as a
  different place on the same device.
- **Run.** `TARGET=… OUT=<new folder> NS="24" NOTE=prereg/drafts-2026-10-27/rule_lam_big_amend1.md bash
  TOQB/gpu/rule_lam_big.sh` (the same command line for each n as in the note), started only after the first run has
  written "all done".
- **Expected time on one H100:** about 12-20 h (flow I: 12,693 s a model at 24 active qubits for 699 two-qubit gates;
  the rule has 384; the noiseless reference on the CPU adds 1-2 h a model). The owner may stop it; finished models are
  in the jsonl, but no statement is drawn unless all four are done.
- **Prediction (not a rule).** As for n = 20 (the ring on a cycle, no extra gate): lam at least 0.61 on every model.
- **Not claimed.** As in the note.
