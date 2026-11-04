# OS2D on ibm_fez, 2026-11-04: the mirror of the user's own circuit LOCATES the problem's errors (ratio 4.1) and dropping its flags HELPS (0.79)

- **Declaration:** `prereg/drafts-2026-11-04/os2d_note.md` (SHA-256 c42bc83b...99ffd235), fixed 06:04 CET, TOQB 81ba8d4.
- Same device and fetch as P6 (fez, 11:14:55 CET), copy (0, 0); built with psf-os 58b1423 as declared (d229642);
  13 circuits; job dblgchl8mdtc73d64ebg, sent 11:17:42 CET (after P6), DONE, 16 s billed. Scored by `gpu/os2d_score.py`.

## Judged

- **Flags** (floor minus mirror, line median + max(5 MAD, 0.05) = 0.387): labels **17, 26, 28**; no edge.
- **Q1:** MSE of the flagged qubits / the rest = 0.0915 / 0.0221 = **4.13: LOCATES** (line 2).
- **Q2:** MSE without the flagged / all = **0.788: HELPS** (line 0.8; close to it).
- **Ring sentinel:** DEAD.

## Reported

- P6 cells (t 1-5): READS, DIFFERS (-0.077 to -0.157, as in the P6 job five seconds earlier).
- Answer card: the same bias pattern as P6 (floor 0.92-0.84).
- The mirror and rule R flag different qubits: the mirror 17, 26, 28 (gate, floor subtracted), rule R 27, 28 (readout).
  28 is in both. The two checks see different faults, as intended.
- Q2's 0.788 is 0.012 inside the line; the run-to-run spread is not measured in this job.
