# Light cone of one flipped spin (4 x 2 x 2 XXX, dt 0.05, t 1-6): simulator estimate before declaring (2026-11-08)

Not declared. `realsim.py --expect 40` on the try-built job's candidate 0 (fez r0 1, c0 0), fez calibration of
2026-11-06 23:22 CET, nothing fitted; S = P(flip) - B(no flip) per distance from the source (1, 0, 0):

| t | d0 sim / exact | d1 | d2 | d3 | excitation kept K | background total (exact 0) |
|---|---|---|---|---|---|---|
| 1 | 0.696 / 0.961 | 0.071 / 0.038 | -0.046 / 0.001 | 0.065 / 0.000 | 0.82 | 1.09 |
| 2 | 0.559 / 0.854 | 0.060 / 0.138 | -0.034 / 0.007 | -0.010 / 0.000 | 0.60 | 1.55 |
| 3 | 0.425 / 0.696 | 0.230 / 0.266 | -0.088 / 0.036 | -0.037 / 0.002 | 0.42 | 2.15 |
| 4 | 0.306 / 0.523 | 0.093 / 0.379 | 0.017 / 0.089 | 0.150 / 0.008 | 0.57 | 2.60 |
| 5 | 0.182 / 0.353 | 0.003 / 0.440 | -0.039 / 0.180 | 0.109 / 0.026 | 0.22 | 3.21 |
| 6 | 0.135 / 0.218 | 0.074 / 0.438 | 0.086 / 0.279 | 0.032 / 0.063 | 0.29 | 3.68 |

The noise makes 1.1 to 3.7 spurious flipped spins over the 16 sites (the no-flip arm), more than the one excitation
being followed; beyond d = 1 the front is not readable even after subtracting that background (which is itself a
correction, outside the no-mitigation rule), and this simulator is optimistic for Heisenberg circuits (11-07). A
domain-wall start was checked exactly as well: at dt 0.05, t <= 6 the profile changes by 0.02-0.3, smaller than the
uniform loss of signal (retention 0.7-0.8). Draft kept in `prereg/drafts-2026-11-08/lc3d_DRAFT.md`; not run.
