# Home check of the VS Claude note (2026-11-08)

- Reproduced `verify_line.py` (bridges at line positions 1 and 5): CZ 116 / 224 / 332 / 440 (Qiskit level 1) and
  116 / 212 / 308 / 404 (level 3); placed against exact to 3e-16, bridges back in |0>, m_s 0.9313 / 0.7571 / 0.5295 /
  0.3037. Added here (`verify_line_check.py`): the compiled circuit itself against the built one, state fidelity
  1.000000000000 at every t and both levels (the level-3 count is not an approximation).
- Placed on ibm_fez's labels (record of 2026-11-07 15:58 CET), rows r0 + y, columns c0 .. c0 + 7, bridges from the
  coupling graph: all four translations used on 11-07, (1, 0), (1, 4), (3, 0), (3, 4), have their bridges at line
  positions 1 and 5 and fit (no failed element, couplers only). Compiled by psf-os's RuleCompiler: CZ 116 / 224 / 440
  (t = 1 / 2 / 4), CZ layers 37 / 70 / 136. The 404 of level 3 needs the step-boundary merge written into the builder
  (two U(dt) on the same pair in a row are U(2 dt); not done yet).
- Not done: the builder in TOQB, a declaration, a noise estimate.

## Joined into TOQB (2026-11-08, owner "合体させて良いとこどりで改良して")

`gpu/heis3d.py` physical_line: VS Claude's two schedules (bridges at line positions 1, 5 and 3, 7), even steps
reversed, y-bonds through the bridges, and a merge written into the builder: a y-bond whose move back is followed by
the next y-bond of the same bridge, with no line operation on that position between, cancels the two moves and joins
the two U(dt) into one U(2 dt) (the log keeps both bonds). Through psf-os's compiler on the 11-07 fez record:
116 / 224 / 332 / 440 without the merge, 116 / 218 / 320 / 422 with it (t = 1-4); sites to 6e-16, bridges back in |0>.
Even rows: 128 / 242 / - / 470. 18 of 21 translations placeable on a fault-free record. The remaining 18 CZ that Qiskit
level 3 finds at t = 4 (404) are not reproduced by an explicit rule here.
