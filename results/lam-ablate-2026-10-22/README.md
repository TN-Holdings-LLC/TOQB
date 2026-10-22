# The noise sources of the shrink lam (report only, declared in prereg/drafts-2026-10-22/lam_ablate_note.md, `e65eb90`)

H100 pod, 2026-10-22 14:07-14:17 CEST, alongside the depth sweep. Output as printed: `la.txt` (cells: lam (delta, fit rms)).
The checks held: the same circuits on every twin; the full twin's lam equal to the lam swap's.

Read at L 16 with item 31's model (lam full / with the source off):

| source off | item 31's circuit | the zipper's circuit |
|---|---|---|
| none | 0.268 | 0.183 |
| CZ error | 0.809 | 0.666 |
| one-qubit error | 0.274 | 0.245 |
| relaxation | 0.268 | 0.198 |
| readout | 0.281 | 0.191 |

- The CZ error makes most of the shrink at both depths (lam about 0.33 to 0.78 at L 8, 0.27 to 0.81 at L 16).
- At L 16 the zipper's circuit shrinks more under every source taken alone: the CZ error's factor (full / off) 0.27
  against 0.33, the one-qubit error's 0.75 against 0.98, relaxation's 0.92 against 1.00. No single source closes the gap.
- Counting does not explain it (home, 2026-10-22, the compiled circuits on the snapshot): at L 16 the zipper's circuit
  has fewer CZ (336 against 448), fewer sx (804 against 964), less summed CZ error (2.37 against 3.74) and one-qubit
  error (0.65 against 0.89), also inside the readout's backward light cone (CZ 294 against 427), and is shorter (11.7
  against 18.0 us).
- On item 31's circuit, lam depends on the model under every twin (L 16: 0.268 against 0.182 full, 0.809 against 0.689
  without the CZ error): no single source makes the noise a global depolarizing one.
- Item 31's circuit keeps an offset delta (+0.03 to +0.08) and a fit rms (0.056 to 0.093) under every twin; relaxation
  gives part of delta (L 16: 0.046 to 0.028). The zipper's fit rms (0.019 to 0.032) is about the trajectory noise.
- Open: whether the compiled circuits equal the ideal model without noise. Checked next with every source off
  (`lam_none_note.md`).
