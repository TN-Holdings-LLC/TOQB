# DRAFT (not declared): the floor probe inside the main job (home, 2026-11-06 13:12 CET)

Replaces the two-job probe (`prereg/os3d_probe_2026-11-06.md`, not run: a queue of 87 put hours between the probe
and the main run).

## Job (one device, the night's daily-record device; one job)

- For each of the first k = 4 qualifying fold translations in the fixed order (candidate 0 = the first translation,
  as on 11-06): its probe circuit (the floor at t = 3 with every touched qubit read, bridges included) and its arm
  A_k (t = 1, 2, 3, each with floor and mirror).
- B = SABRE seed 0 (t = 1, 2, 3, floor and mirror); the ring sentinel.
- 4 + 4 x 9 + 9 + 4 = 53 circuits (about 65 s by the model; to be measured on the night's record before declaring).

## Rule (fixed before the run; reads only the probe circuits of the same job)

The scored arm A is A_k for the first k whose probe reads every touched qubit at floor >= 0.8. If none does: "probe
passed none", and A = A_0. The choice never looks at an answer or at any arm's MSE.

## Judged

- R = MSE_A / MSE_B per t (HELPS <= 0.8, HURTS >= 1.25), and, when A is not A_0, R_probe = MSE_A / MSE_A0.
- Beside: every candidate's probe floors and every A_k's scores (all are in the job and all are shown; only A is
  judged), CZ and layers, mirror, sentinel, calibration beside.

## Cost and honesty

About 2.4 times the QPU time of the 11-06 job, to read the floors at the same moment as the run. Showing every A_k
beside makes visible what a post-hoc best pick would have given; the judged arm stays the one the floor rule chose.

## To build (not yet)

`gpu/os3d_compare_build.py --candidates 4` (probe circuits and A_0..A_3 in one job), a scorer that applies the rule
from the job's own probe records, and tests (the rule's choice from planted noise, as tests/test_grid3d.py).
