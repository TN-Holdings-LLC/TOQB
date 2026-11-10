# toqb.devices "psfos:FOLDER" (failed marks only): same circuits as the full Target (home, 2026-11-10)

Why: the classifier's arms (fold:rule, qiskit:2:blind:template) were compiled in 10-30 from a full Target
(`file:target.pkl`); the daily fetch now stores psf-os's device.json only (geometry and failed marks).
`toqb.devices.failmark_target` rebuilds a Target with every coupler and qubit, error 1.0 on the failed ones and no
other number.

Check (TOQB 7d295e1 + this change, psf-os 0fb4512): for the full Targets of fez (corr-2026-11-04: 1 failed coupler,
1 failed qubit) and marrakesh (corr-marrakesh-2026-11-04: 2 and 4), psf-os `device.from_target` -> device.json ->
"psfos:"; the 10-30 task's first 3 inputs x 3 bases, n 20, L 19: both arms give identical circuits (instruction by
instruction) and the same measured map as "file:". CZ 380 per circuit in both arms.
