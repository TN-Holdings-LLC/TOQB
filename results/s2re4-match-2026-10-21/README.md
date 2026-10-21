# The test match E4 against C0 on the twin, 2026-10-21: scored by the fixed W8 rules

Pod H100, 02:37:57 to 05:15:49 CEST, toqb dcbc4be, `gpu/s2re4_match.sh`: Z (theta = 0), E4 (`toqb.s2re4_run`) and
C0 (`toqb.s2rc` from theta = 0), teacher angle 1.0, teachers 4 (development), 5 and 6, L 8 and 16, PSF arm, stand-in
snapshot:marrakesh. Scored with `toqb/match_score.py` at the SHA-256 fixed before the record was read
(aa40de43…e122, `prereg/drafts-2026-10-21/W8_FIXED.md`): `score.md`, `score.json`. Raw records in `pod/`
(`jobs.txt` with the pod's paths redacted to `<pod>/`).

## Headline (owner's criterion)

**Won from lane 1: NO.** On the fresh tasks (teachers 5 and 6), E4 against C0 is a TIE overall (Stouffer Z -2.47,
p 0.014, leaning towards C0), with two task LOSSes (L 8 teacher 6: CE -0.012; L 16 teacher 5: CE -0.019) and two
TIEs. E4 against theta = 0 is a WIN overall (Z 12.19). E4 stayed within C0's budget (L 8: 76.5 %, L 16: 99.0 %).

## Reading

- Vanity: E4 beats doing nothing by a wide margin at L 8 (CE gains +0.107 and +0.062, accuracy +0.24 and +0.18), and
  the largest accuracy gain over C0 is +0.090 on teacher 4 (the development task, not in the headline).
- Essential: on fresh tasks, at C0's budget, E4 is not better than C0 and is slightly worse in CE. At L 16 neither
  method learns much (theta = 0, C0 and E4 all near chance; E4 on teacher 5 ends below theta = 0 in CE).
- The prediction layer: 18 of 18 runs inside the twin's 99 % CE interval (twin-standin P(1) rms 0.003 to 0.012).
- Next: the fruit match (`prereg/drafts-2026-10-21/F1_fruit_match_design_2026-10-21.md`) asks the declared question
  of the convergent zone: whether E4 is ahead of C0 early, at the same cost.

## Diagnosis of L 16 (2026-10-21, from these records; asked by the workplace: NIBP, overfitting or twin mismatch?)

1. **Twin against stand-in: not the cause.** In all 18 runs the twin's test CE and the stand-in's differ by at most
   0.002 (L 16 included).
2. **C0's gradient norm (an NIBP sign): no flattening at L 16.** Mean over the first / last 200 loops: L 8 0.39-0.41 /
   0.32-0.40; L 16 0.40-0.47 / 0.28-0.37. C0's estimate carries trajectory noise, so this is not decisive alone.
3. **Training fit, noiseless (`diag_trainfit.py`, `diag_trainfit.txt`: exact <Z0> on the 64 training points at the
   final parameters):**

| | theta = 0 Brier / acc | C0 | E4 |
|---|---|---|---|
| L 8, teachers 4 / 5 / 6 | 0.241 / 0.594, 0.314 / 0.469, 0.228 / 0.672 | 0.165 / 0.766, 0.108 / 0.875, 0.087 / 0.891 | 0.155 / 0.875, 0.119 / 0.828, 0.083 / 0.938 |
| L 16, teachers 4 / 5 / 6 | 0.319 / 0.531, 0.296 / 0.531, 0.225 / 0.641 | 0.175 / 0.812, 0.222 / 0.594, 0.164 / 0.719 | 0.232 / 0.641, 0.251 / 0.547, 0.175 / 0.609 |

Reading:
- At L 16, C0 fits the training points (accuracy up to 0.81) while its test stays near chance: overfitting, not a
  flat landscape (a barren plateau would stop the training fit too).
- E4's estimated training Brier change at L 16 (about -0.28 over two sweeps) is far larger than its noiseless training
  fit shows (-0.05 to -0.09). The coefficients are unbiased, but each step takes the minimum of a noisy estimate, so
  the estimated decrease is optimistic (selection on noise, a winner's curse), and it accumulates over 330
  parameters. This is a flaw of E4 under noise, found here; the running fruit match (L 8) is unchanged.
