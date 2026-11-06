# DRAFT (not declared): the 3D prototype v3.1 on a device, read against the exact answers, with the 2D patch beside
(home, 2026-11-06 14:28 CET; owner: "3D を徹底的に詰める、反省点も含めて改良できるものはすべて")

## What changed since the 11-06 run, and why

| lesson of 11-06 | change |
|---|---|
| no search arm is needed (owner: the formula-against-search question is settled) | no SABRE; each arm read against the exact answer |
| the price of the dimension should be measured against our own 2D | the 16-site 2D patch (device lattice, run2d placement) in the same job |
| one bad element on a block's only bridge decided the result (q29, q49 on bridge q38) | in-job probe: every candidate translation's \|0> and \|1> floor read in the same job; the judged arm is the first candidate that clears +-0.8 |
| q29 relaxed fast: the \|0> floor stayed at 1.00 | the \|1> floor (ideal -1) sees it (test with a planted relaxing qubit) |
| CZ and layers | v3.1: each x-bond rides on its columns' swap (2 CX instead of 3 + 1); 4x2x2 t 1-3: 108 / 216 / 324 CZ, 28 / 55 / 82 layers (v3: 116 / 232 / 348, 33 / 64 / 95); exact to 2e-15 |
| the probe in a separate job waited 97 min | probes inside the main job: no queue between reading and running |

## Job (one device: the night's daily-record device; `gpu/os3d_v31_build.py`)

- Probes: \|0> and \|1> floors at t = 3 of the first 4 qualifying fold translations (fixed order), every touched qubit.
- 3D arms g3d<i>_t<t>: 4 x 2 x 2 kicked Ising (RZZ(-pi/2) on every edge, RX(0.8)), v3.1 at candidate i, t = 1, 2, 3,
  floor and mirror each.
- 2D arms hex_t<t>: the 16-site patch (a hexagon of 12 and two tails of 2, 16 edges), the same step, t = 1, 2, 3, floor
  and mirror each.
- One ring sentinel. 4000 shots. On the 11-06 marrakesh record: 57 circuits, 66.6 s by the model.

## Rule and judged (`gpu/os3d_v31_score.py`)

- The judged 3D arm is candidate i for the first i whose probes read every touched qubit \|0> floor >= 0.8 and \|1>
  floor <= -0.8. If none: candidate 0, marked "probe passed none". The choice reads no answer and no arm's error.
- Judged per t, for the chosen 3D arm and for the 2D arm: READS, AGREES, BEATS (gpu/practice_score.judge).
- Beside (not judged): retention, normalised error, CZ and layers, floor and mirror, the probe readings of every
  candidate, every other candidate's scores (all shown; a best pick after the fact would be visible as such), the price
  of the dimension (3D / 2D: CZ, layers, retention), the sentinel, the calibration beside (report only).

## Answers (sealed at declaration)

The exact values depend only on t and the lattice (the same on every device). For 4 candidates the file the builder
writes has SHA-256 0bce0dab5066cfba1bdc783c0cd447f47173b7b1a35909b4ea428e5e0fa3356b; if fewer translations qualify, the
build prints its own and it is committed before the submit.

## Expectation (simulator only; not evidence)

Uniform model: 3D retention about 0.90 / 0.88 / 0.83 at t 1-3, 2D about 0.96 / 0.94 / 0.92. Replay of the 11-06
faults: see `notes/os3d_sim_2026-11-06/README.md` (filled in when the replay finishes).

## To fix before declaring (owner)

- Threshold +-0.8, k = 4, probe depth t = 3.
- One device or the night's devices.
