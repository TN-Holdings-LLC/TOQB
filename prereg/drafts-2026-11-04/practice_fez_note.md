# Declared: the practice test again on ibm_fez (owner's choice of 2026-11-04 13:50 CET)

Everything as `practice_note.md` (SHA-256 22474f14...b595ab): the same 10 P4 circuits, the same judgements (READS,
AGREES, BEATS; RUNS), the same scorer `gpu/practice_score.py`, psf-os ac84182, `psf-os fetch` and one `psf-os run2d`
batch of 22 circuits, 4000 shots, no correction. Changes:

- Device: ibm_fez (the owner's choice).
- P5 on fez's own lattice of 3 November (153 qubits, 170 edges), theta 0.4, 0.8, 1.0, t 2, 4, 6, 8, written by
  `gpu/practice_fez.py` (the same user functions as `gpu/practice_circuits.py`). Answers sealed on 3 November:
  t 1-5 `results/bank-2026-11-04/p5_fez/answers_cpu.json`, t 6-8 `results/kim-e-2026-11-03/X/answers_pod/answers_C.json`
  (4c0b7ce9..., 3087056).
- Checks before this note: P5 cones t 2, 3 max 1.3e-15; compiled on tonight's fez record (11:48 CET), noiseless:
  P5 t 2 (cones) 7.8e-16, P4 t 8 7.1e-6. P4 lands on copy (4, 0) there (coupler (32, 33) failed in copy (0, 0)).
- If the entrance refuses a P5 circuit, the 10 P4 circuits go alone and P5 is NOT TESTED; if it refuses P4, no job.

Reported in addition: fez minus marrakesh (job dblibpd8mdtc73d66v90) per problem for M - M_exact and the floor.
Note: P5 on this lattice ran on fez on 3 November (stage E, X: theta 0.4 DIFFERED); the answers were sealed before that.
