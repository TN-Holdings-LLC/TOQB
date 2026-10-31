# Black bisection on ibm_kingston, 2026-10-31: stopped after round 2 by the rule (SPREAD); post hoc, the first quarter carries the whole gain

- **Declaration:** `prereg/drafts-2026-10-31/black_bisect_note.md` (SHA-256 3697ce48...9abd), fixed 15:09 CET, TOQB
  e189efd. Standard n = 40 ring; off at D = 24 byte-identical to 30 October in both rounds. Block = 38, 49-55, 59.

| round | job (billed) | arm | flipped qubits | block - off at D = 24 | verdict | rest - off |
|---|---|---|---|---|---|---|
| 1 | dbivgc1ffo6c73b8j69g (15 s) | A | 3, 5, 7, 27, 29, 49, 51, 53, 55, 75 | +0.270 +- 0.007 | HELPS | -0.045 |
| 1 | | B | 73, 71, 69, 67, 65, 63, 43, 41, 21, 23 | +0.007 +- 0.007 | NO EFFECT | -0.048 |
| 2 | dbivjthkdqps738vhcbg (15 s) | A | 3, 5, 7, 27, 29 | **+0.299 +- 0.007** | HELPS | **-0.007 +- 0.004** |
| 2 | | B | 49, 51, 53, 55, 75 | +0.019 +- 0.007 | HELPS | -0.044 |

**End by the note:** in round 2 both arms HELP at 2 SE, so the rule stops: SPREAD ("the error is not in one place;
only the global flip helps, at its cost").

**Reported, post hoc (not judged; the rule above stands):** arm B's +0.019 is 2.7 SE but one sixteenth of arm A's
+0.299. Arm A alone (couplers (16, 3) to (29, 38), the first block of the dead run, 3-7, 17, 27-29) gives at least
the global flip's gain (+0.285 and +0.295 in stages 2 and 3) at almost no cost to the rest (-0.007, within 2 SE). The
rule's "both HELP" did not weigh the size of the gains; a new note is needed to test arm A as the fix.
