# Home check (2026-11-08)

On the 2026-11-08 records of ibm_kingston and ibm_marrakesh (results/os3d-heisE-2026-11-08/fetch_in): Ising 4 x 2 x 2,
theta 0.6, t = 4: line 240 CZ against the fold v3.1's 432 (psf-os prepare, RuleCompiler); placed against
grid3d.exact at t = 1 and 3: 4e-15 and 1.2e-14. The line layout chose r0 0, c0 1 on both records (its own fixed order:
cheapest schedule, then r0, then c0), so its qubits differ from the fold's places; a same-qubits comparison would need
the fold's translation forced. Note: `physical_line` returns three values without info (qc, placed, used).
