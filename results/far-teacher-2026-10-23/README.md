# Far-teacher test (report only; rules fixed in prereg/drafts-2026-10-23/far_teacher_note.md, `f5ed070`)

H100 pod, 2026-10-23 08:59-09:47 CEST (trained 09:36); toqb `f5ed070`, psf-zero `9f0d44e`, Rust template in check mode.
`score.md` as written on the pod; zip SHA-256 2772a6d606ff88af038e4af65cad52b91690696b729d594becc63927a84e61a1. All 6
runs and 6 theta = 0 evaluations valid. Test labels are balanced (250 / 500 of each sign) for all three teachers.

## The rules (shot-free stand-in accuracy without correction; Holm over 6 per rule, alpha 0.01; 2 of 3 teachers)

- **A. Is the zipper more accurate?** 500 loops: **no** (1 of 3: teacher 18 WIN, 17 and 19 TIE).
  2,000 loops: **YES** (2 of 3: teachers 18 and 19 WIN, 17 TIE).
- **B. Did the zipper learn more (gain from theta = 0)?** 500 loops: **no** (1 of 3: teacher 18). 2,000 loops: **no**
  (1 of 3: teacher 19). The declared claim "the zipper learns more" is not supported.

## Vanity and essential

- Vanity: at 2,000 loops the zipper is more accurate by the rule; up to +0.24 (teacher 18 at 500: 0.776 / 0.538) and
  +0.14 (teacher 19 at 2,000: 0.658 / 0.514).
- Essential: with the run's 250 shots the gaps at 2,000 loops are smaller: 0.606 / 0.577, 0.763 / 0.670, 0.612 / 0.572.
  Both arms stay low on far teachers (0.51-0.78 without shots). Item 31 answers +1 on 84-94 % of balanced test points
  at every point (the zipper 55-83 %), so its accuracy is capped by its readout offset whatever it learns.

## Post hoc (not declared; read, do not claim)

- Rule B's note assumed a circuit's offset "largely cancels" in the per-point gain. It does not when the offset
  saturates: item 31 on teacher 19 gains +0.068 in noiseless accuracy by 2,000 loops but -0.020 on the stand-in. B
  measures learning only through a threshold the offset has already moved.
- Offset-free views of what training added (zipper / item 31):

  | teacher | loops | noiseless acc gain | stand-in AUC gain | noiseless AUC gain |
  |---|---|---|---|---|
  | 17 | 500 | +0.020 / +0.024 | +0.026 / +0.002 | +0.054 / +0.049 |
  | 17 | 2000 | +0.056 / +0.064 | +0.053 / +0.002 | +0.087 / +0.086 |
  | 18 | 500 | +0.130 / +0.010 | +0.068 / +0.022 | +0.071 / +0.027 |
  | 18 | 2000 | +0.146 / +0.118 | +0.091 / +0.084 | +0.098 / +0.083 |
  | 19 | 500 | +0.092 / +0.060 | +0.151 / +0.119 | +0.155 / +0.131 |
  | 19 | 2000 | +0.142 / +0.068 | +0.230 / +0.115 | +0.208 / +0.169 |

  Read: on teacher 17 the two arms learn the same; on 18 the zipper learns faster (ahead at 500, close by 2,000); on
  19 it learns more. In the logical model (noiseless), the zipper's lead is smaller than on the stand-in.
- At theta = 0 the stand-in AUC differs between arms for the same logical model (teacher 17: item 31 0.765, zipper
  0.709; noiseless 0.674): the circuit's noise reorders points, so stand-in AUC is not purely the model's.
- The trained models compared directly (noiseless accuracy of the logical model, exact McNemar, Holm over 6; the
  rule proposed for the Qiskit test, run here on item 31 as the score's smoke test): zipper against item 31 WIN in 1 of
  3 at 500 loops (teacher 18: 0.770 / 0.650) and 0 of 3 at 2,000 (0.630 / 0.638, 0.786 / 0.758, 0.640 / 0.566). What
  the two arms learned does not differ by this test at 2,000 loops.
- Reproduced at home: `toqb.far_score` on these records gives a score.md identical to the pod's.
- Not claimed: one seed; the stand-in is TOQB's model of a 2026-10-13 calibration.

## Files

`runs/` (s2rc_ckpt records), `theta0/`, `plans/`, `logs/`, `score.md` / `score.json` (pod), `progress.txt`,
`times.txt`, `rust.txt`, `jobs.txt` (pod paths written `<pod>/`).
