# Declared: 1D Fermi-Hubbard at 90 and 120 qubits, raw, with the U = 0 ruler in the same job (Heron)

Home, 2026-11-11 night. Owner 21:14-21:15 JST ("（L=45〜90）", "４５　６０？"). Same circuits, builder, answers
script, check and scorer as `prereg/hubbard_2026-11-11.md` (run 12:58 CET: READS at 2 and 4 steps at L 20 and 30, not at
6), at L = 45 and 60, steps 2 and 4 only. Declared with this commit, pushed before any device record of this run is
fetched; a change after the push is a new declared file. Paper 9, part B.

## Question

Does the Hubbard chain still read raw at 2 and 4 steps when it is 90 and 120 qubits long, and does the ruler behave as
at 40 and 60 qubits?

## Circuits and placement

As the earlier declaration: arms U4 and U0 (onsite RZZ as CZ, barrier, CZ), steps 2 and 4, L 45 and 60; 8 circuits,
each with floor and mirror, one ring sentinel, 4000 shots. Build: `gpu/hub_build.py DEV OUT ANS_IN ANS_OUT --L 45 60
--steps 2 4`. Chains by the dual-unitary rule (shapes, else psf-os rule C).
Device: in the order of fewest pending (ties marrakesh, fez, kingston), the first on which the job builds (both chains,
the sentinel, equal CZ in the arms). If no device builds L = 60, the first on which L = 45 builds, with L 45 only.
(On the 12:39 CET records: marrakesh's longest chain is 84 qubits, so neither builds there; fez places both by rule C.)

## Answers (sealed)

`gpu/hub_answers.py` (U4 quimb, bond cap 1024; U0 free fermions): `hub_answers_big.json`, sha256
5e90c416a0881a9fcc75ed0bc586ff5ef4bef4cc302dabc24ef0efb157687f8f, outside the repository until the verdicts.
Checks: largest bond 55 / 217 at 2 / 4 steps (below the cap), error estimate at most 6.5e-10, sum <Z> at most 1.2e-13,
per-site charge at most 7.6e-9; up minus down equals its conserved value (0 at L 60; -2 at L 45, where the Neel start
has 23 up and 22 down) within 1.2e-14.

## Pre-run check: `gpu/hub_check.py OUT ANS --mps-steps 2 --quimb-steps 4`

On the compiled circuits: 2 steps by Aer MPS without truncation, 4 steps by quimb (bond cap 1024; Aer's MPS took about
25 min for L 30 at 4 steps here, quimb about 1 min; the quimb path checked against the answers on the L 30 4-step
circuits: 2.8e-9 and 2.0e-14), per-qubit <Z> within 1e-6, mirrors all zeros, arms equal in CZ and CZ depth. The 4-step
check uses the same simulator family as the answers (on the compiled, placed circuit); the independent Aer check at 4
steps ran on the same builder at L 20 and 30 (2.3e-8). FAIL anywhere: not run.
Try-build on the 12:39 CET fez record: 28 circuits, 34.2 s by the model; CZ 884 / 1768 (L 45) and 1184 / 2368 (L 60),
equal in both arms; answers file sha256 eceb7754...

## Verdicts

As the earlier declaration (`gpu/hub_score.py`): READS per circuit if MSE <= mean square / 2; AGREES counted; beside:
amplitude ratio r, r(U4) / r(U0), per-site charge, floor, mirror, sentinel.

## Prediction (before any data; not rewritten if wrong)

- U4 and U0 READ at 2 and 4 steps at L 45 and 60 (CZ per qubit at 4 steps 19.6 and 19.7, as L 20 and 30 at 4 steps,
  which read).
- r(U4) / r(U0) as at L 20 and 30: 0.85-1.0 at 2 steps, 1.2-1.5 at 4 steps.

## Limits

One device-day; raw values; 1D, inside the classical check (an MPS on a PC: L 60 at 4 steps took 166 s here); larger
L does not make the classical check hard at fixed steps.
