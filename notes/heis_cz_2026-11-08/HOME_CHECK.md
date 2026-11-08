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
