# One yardstick for every recorded result with an exact answer (desk, 2026-11-14; for paper 9)

`line_all.py` (output `line_all.txt`, `line_all.json`): 179 results (XX chains 75, Hubbard 31, the daily record 11,
dual-unitary curves 3, and from the workplace r-thread IBM 2023 utility 11 and 3D Ising 48; written after all of them
were scored).

**What is guaranteed and what is measured.** With r = sum z e / sum e^2, the error splits exactly as
MSE / mean square = (1 - r)^2 + rest with rest = mean((z - r e)^2) / mean square >= 0. So r < 0.293 means DOES NOT
READ always (13 of 13 here, by the identity, not by the data). The measured part is the other direction: of the 166
results with r >= 0.293, **160 read**. The six that do not:

- Hubbard at 6 steps, three times (11-11 L = 20 and 30; 11-13 L = 20): r 0.38-0.51 but rest 0.27-0.32, the error
  that is not a shrink (the shape) decides.
- The XX chain just past the line, three times (MSE / mean square 0.504-0.518; rest 0.03-0.06).

The practice tests of 11-04 are not included (their score files keep no per-qubit exact values); Ohm (declared on M
per circuit), Schwinger and the light-cone 3D test use other observables and are not on this yardstick.
