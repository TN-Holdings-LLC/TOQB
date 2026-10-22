# The twin with every noise source off: are the compiled circuits the ideal model? Report only (declared 2026-10-22, before any output)

After the noise-source check (`results/lam-ablate-2026-10-22`): no single source explains why, at L 16, the zipper's
circuit shrinks more than item 31's though it has less error by every count, nor item 31's offset delta and fit rms,
which stay under every twin. One explanation outside the noise: a compiled circuit that differs from the ideal model
even without noise (the template's fixed angles, the zipper's merged blocks), an error that would grow with depth.

`python -m toqb.lam_ablate RUNS OUT full,none` (twin "none": CZ, one-qubit and readout errors 0 and T1 = T2 = 1,000 s,
failed elements kept failed). Expected if the compiled circuits are the model: lam 1.000, delta 0.000 and fit rms about
0 on all 8 (L, model, circuit). Anything else is reported as a mismatch of the compile, with its size. Consequences
stated now: a mismatch would mean training saw a circuit other than the model, and the "noiseless CE" of the trained
models (W12's check; the depth sweep's rule, `zip_depth_note.md`) is of the ideal model, not of the circuit run.
