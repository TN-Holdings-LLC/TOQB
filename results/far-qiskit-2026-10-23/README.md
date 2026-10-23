# Far teachers: PSF-Zero's zipper against Qiskit (report only; rules fixed in prereg/drafts-2026-10-23/far_qiskit_note.md, `fe488cb`, owner 2026-10-23 12:29 CEST)

H100 pod, 2026-10-23 12:54-17:45 CEST (trained 17:33); toqb `fe488cb`, psf-zero `9f0d44e`, Qiskit 2.5.2. The Qiskit
arm (`qiskit:2:target:template`) here; the zipper's records from results/far-teacher-2026-10-23 (same plans, identical
test labels, checked by the score). `score.md` as written on the pod; zip SHA-256
7b20a90a1a919ce22a9357ec1c045cc8ce31cc72cff1a06eeca7a93807fae3df. All 3 runs and 3 theta = 0 evaluations valid.
Deviation: time and cost. The note estimated 1-1.5 h; it took 4 h 51 min (Qiskit's circuit has 14 active qubits
against the zipper's 10, and the stand-in's verification at each point took about 50-80 min).

## The rules (Holm over 6 per rule, alpha 0.01; an arm wins at a point in 2 of 3 teachers)

- **A. Shot-free stand-in accuracy without correction.** 500 loops: **neither** (zipper WIN 1: teacher 18, 0.776 /
  0.554; TIE 2). 2,000 loops: **neither** (zipper WIN 1: teacher 19, 0.658 / 0.582; TIE 2). No LOSS.
- **B. The trained model, noiseless.** 500 loops: **neither** (0 WIN, 0 LOSS). 2,000 loops: **neither** (0, 0;
  0.630 / 0.630, 0.786 / 0.818, 0.640 / 0.600).
- **Device threshold (power at 300 points at least 0.8 in 2 of 3 teachers at one loop count): not met** (only
  teacher 18 at 500 loops, 0.96). By the rule, the remaining IBM minute is not spent on this comparison.

## Vanity and essential

- Vanity: the zipper beats Qiskit on teacher 18 at 500 loops (0.776 / 0.554, Holm p 4e-14) with a third fewer CZ
  (336 / 506), a quarter of the duration (11.7 / 48.2 us) and 10 active qubits against 14.
- Essential: by the declared rules neither compiler gives the more accurate classifier, and what the two arms learn
  is not distinguishable (B: 0 of 3 either way). A TIE is not a proof of equality (one seed, 3 teachers, 500 points).
  Formula placement reached search placement's result here at a lower circuit cost; it did not beat it.

## Reported, without a claim

- Readout offset: at theta = 0 Qiskit answers +1 on 93, 94 and 86 % of balanced points (item 31: 93, 92, 85; zipper:
  83, 78, 74). Qiskit keeps it after training (0.81-0.93), except teacher 18 at 2,000 loops (0.61).
- The twin predicts the zipper's circuit better: twin-against-stand-in P(1) rmse 0.008-0.014 for the zipper, 0.016-0.055
  for Qiskit (largest at theta = 0). At 500 loops the stand-in's CE fell outside the twin's 99 % interval for Qiskit on
  teachers 17 and 18.
- Shots: from shot-free to 250 shots at 2,000 loops the zipper loses 0.016, 0.017, 0.046, Qiskit -0.001, 0.044,
  -0.007 (its larger signal loses less).
- Stand-in AUC at 2,000 loops: zipper / Qiskit 0.762 / 0.771, 0.910 / 0.909, 0.739 / 0.730.

## The workplace's predictions (written before any Qiskit result; ftq_predictions_workplace_2026-10-23.md)

| # | prediction | outcome |
|---|---|---|
| P1 | Qiskit +1 share at least 0.80 at theta = 0 and both budgets | 8 of 9 (teacher 18 at 2,000: 0.61) |
| P2 | Qiskit theta = 0 accuracy 0.50-0.60 | yes (0.550, 0.504, 0.548) |
| P3 | zipper more accurate at 2,000 loops in 2 of 3 | no (1 of 3) |
| P4 | twin-stand-in rmse for Qiskit at least 0.02, PSF about 0.01 | in part: at theta = 0 (3 of 3), at 500 loops 2 of 3 (teacher 19: 0.019), not at 2,000 (0.016-0.018) |
| P5 | AUC within 0.05 in 2 of 3 at 2,000 loops | yes (3 of 3) |
| P6 | no consistent winner in what was learned | yes |
| P7 | Qiskit loses less to shots in 2 of 3 at 2,000 loops | yes (teachers 17, 19) |
| P8 | teacher 17 at most 0.66 noiseless at 2,000 loops for every arm | yes (0.630, 0.630; item 31 0.638) |

- Reproduced at home: `toqb.farq_score` on these records gives the same score.md except two power cells of the
  decision aid, by 0.01 (teacher 19 at 500 loops, 500 points: 0.07 against 0.06; teacher 17 at 2,000, 500 points: 0.06
  against 0.05); the rules' tables are identical. The power simulation is seeded; the cause of the difference (likely
  the numpy versions) was not checked. The threshold's outcome does not change.
- Not claimed: one seed; the stand-in is TOQB's model of a 2026-10-13 calibration; a stand-in result is never a
  device result.

## Files

`runs/`, `theta0/`, `plans/`, `logs/`, `score.md` / `score.json` (pod), `progress.txt`, `times.txt`, `rust.txt`,
`jobs.txt` (pod paths written `<pod>/`).
