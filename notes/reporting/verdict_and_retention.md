# How results are shown (owner, 2026-11-05 21:00 JST: "a × verdict can still show what is worth seeing; make readers
# see it"; the form is left to home)

1. **The declared verdict comes first and is never softened.** AGREES / DIFFERS (|M - M_exact| <= 0.05) as declared.
2. **Beside it, always, for every device and problem (no selection):** retention R = M / M_exact, normalised error
   |M - M_exact| / |M_exact|, and the device. A row is never left out because it looks worse.
3. **One footnote under every such table:** "The declared criterion is an absolute difference; the same relative loss
   gives a larger difference when the exact answer is larger. R and the normalised error show the loss relative to the
   answer." Retention is not given when |M_exact| < 0.1 (unstable); the normalised error is then marked "small answer".
4. **One sentence of reading, with both devices**, e.g. for 2026-11-05: "D02 DIFFERS under the declared +-0.05 on both
   devices, yet it kept 0.82-0.86 of its signal, as much as FX-A (0.73-0.85), which AGREES."
5. **The opposite case is said too:** a small-answer problem that AGREES while losing much (FX-A on fez kept 0.73) is
   pointed out, so the reader sees the bias works both ways.
6. Per CZ layer the decay differs by problem family (2026-11-05: D02 0.004-0.005, FX-A 0.007-0.013); no single
   "device health" number is claimed.

Example (2026-11-05):

| Task | Device | AGREES | Retention | Norm error |
|---|---|---|---|---|
| FX-A | marrakesh | yes | 0.85 | 0.15 |
| FX-A | fez | yes | 0.73 | 0.27 |
| D02 | marrakesh | no | 0.86 | 0.14 |
| D02 | fez | no | 0.82 | 0.18 |
