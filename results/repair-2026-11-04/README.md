# Self-repair test, 2026-11-04 (ibm_fez): the chain found 4 qubits in OS2D, moved the problem to a copy without them, and the error halved (B / A = 0.49, HELPS)

- **Rules** (owner, 2026-11-04; `prereg/drafts-2026-11-04/repair_note_DRAFT.md` and `owner_decisions_2026-11-04.md`):
  confirm rule (b), 7-day expiry, OS2D as job 1, the ledger from OS2D only; thresholds 0.8 / 1.25 to be confirmed by the
  owner after tonight. psf-os 1250c90.
- **Ledger from OS2D** (`ledger_after_os2d.json`): floor DEAD 27, 28; mirror DEAD 17, 26.
- **Chain** (`job2/chain.json`, sealed in 6b01794 before sending): excluded 17, 26, 27, 28; A copy (0, 0), B copy
  (2, 0) (7 qubits shared); TESTABLE. Re-fetch of fez 11:21:33 CET.
- **Job 2:** dblgf7d8ft8s738t1o2g, sent 11:23:25 CET (5 min 43 s after OS2D), DONE, 21 s billed; 18 circuits.

## Result

| | A (no chain, copy 0,0) | B (chain, copy 2,0) |
|---|---|---|
| MSE | 0.0285 | 0.0140 |

B / A = **0.49**; shot SE 0.00047, run-to-run spread 0.00026 (A in OS2D and job 2): the difference is far beyond both.
**HELPS** at the proposed lines.

## Reported

- Flag lifetime (job 2's floor on A, 6 min later): 27 and 28 still DEAD; 17 and 26 HEALTHY on the floor (they were
  mirror flags, a gate fault the floor does not see, so this is not a lifetime test for them).
- Honest reading: B differs from A by the whole copy (28 of 35 qubits moved), not only by the four qubits; the test
  shows that the chain's move helped, not that those four qubits alone carried the error.
