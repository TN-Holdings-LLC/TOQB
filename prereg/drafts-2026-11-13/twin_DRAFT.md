# DRAFT (home, 2026-11-13; not declared until the owner agrees): does the Clifford twin tell how much of the user circuit survives?

## Question

`psf_os/twin.py` makes, from each compiled user circuit, a Clifford twin with the same physical pulses (RZ angles
rounded to multiples of pi/2; RZ is virtual). Its answer is exact at any size. On one device-day, does the device keep
the same share of the twin's pattern as of the user circuit's (r_twin against r)?

## Circuits (start from configurations that have read before)

- XX chain, 91 qubits, theta pi/4, 4 / 8 / 12 steps (r on 11-12 fez: 0.68 / 0.50 / 0.33), each with its twin.
- 1D Hubbard, L 20 (40 qubits), U 4, 2 / 4 / 6 steps (r on 11-11 fez: 0.84 / 0.75 / 0.42), each with its twin.
Each user circuit and twin with floor and mirror as before, one sentinel per job, 4000 shots; two jobs (one per
family). Twins are submitted as built (no later optimisation), and `check_same_schedule` must hold for each pair.
Builders to extend (home, tonight): `gpu/ffxx91.py`, `gpu/hub_build.py` (option `--twin`).

## Answers

User circuits: as before (free fermions; quimb MPS for Hubbard), already released for these sizes, so this run tests
the twin, not the answers. Twins: stabilizer simulation, sealed until the verdicts.

## Verdicts and prediction (to fix with the declaration)

- Per pair: r_twin and r, the difference, and both READS verdicts (user circuit against its answers, twin against its).
- Proposed prediction: |r_twin - r| <= 0.05 for every XX pair and for Hubbard at 2 and 4 steps; Hubbard at 6 steps open
  (shape errors there).
- Beside: does r_twin >= 0.293 predict the user circuit's READS verdict (6 pairs)?

## Limits

One device-day; the twin sees the multiplicative part of the error only; angle-dependent coherent errors can differ.
