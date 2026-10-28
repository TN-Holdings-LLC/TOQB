# Device test D5, amendment 3 (owner, 2026-10-28: "A だけ先に送り、C・B は後で", then "cbはきょうはやめ"): only part A is sent today, as its own job. Fixed by SHA-256 and CET time before any D5 job is assembled

- **Changed:** part A (fold:rule, fold:zipcyc, Qiskit; classifier n = 20, L = 16, model 0, 64 inputs x 1000 shots) is
  sent alone: its three records copied unchanged into `d5/runs_A`, the rehearsal on them, `assemble --max-seconds 90`
  (the time model gives 61.8 s) (`gpu/device_d5_part.sh`, this commit).
- **Not run today:** parts B (n = 22) and C (the formula prediction at n = 32 and 40). The pod step stops once part A's
  cells are built; nothing of B or C is sent. If they are run later, it is under a new note with that day's fetch.
- **Not sent:** any combined job assembled by `gpu/device_d5b.sh`.
- **Unchanged for part A:** the cells, inputs, shots, the fetch (11:36:52 CET), its rules and predictions
  (device_d5_note.md 4d737d05…, amendments 1 3b83d226… and 2 9794d89c…: Qiskit on the device only).
