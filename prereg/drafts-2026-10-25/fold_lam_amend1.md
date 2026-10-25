# Flow D, amendment 1 (owner, 2026-10-25 13:10 CET): Qiskit's limit lowered to 20 active qubits. Fixed before the rest of the run

**What happened.** The run of fold_lam_note.md started 12:35:42 CET on an H100. By 13:08 it had finished L = 8 for
n = 9-13 (every arm) and n = 14 (fold, zipper); Qiskit at n = 14 (20 active qubits) had run over 30 minutes. With 24
active qubits (Qiskit at n = 15 and 17) each cell would take about 16 times longer: more than a day in all. The
fold and zipper cells take minutes. The owner chose to lower the limit.

**Change.** `--max-active 20` instead of 24. The running process is stopped; its finished lines (L8.jsonl) are kept as
they are. The rest runs as declared otherwise: L = 8 for n = 14-19 (L8b.jsonl; n = 14's fold and zipper cells are
computed again with the same seeds, so they must equal L8.jsonl's), then L = 16 for every n (L16.jsonl). A Qiskit cell
above 20 active qubits is recorded as skipped.

**Effect.** Fold and zipper: every n, as declared. Qiskit: only where its circuit has at most 20 active qubits.
Nothing else changes; no rule; report only.
