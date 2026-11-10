# DRAFT (not fixed): the paper 3 classifier again, on several devices and days, raw, labels sealed

Home, 2026-11-10. From the workplace's blueprint of 2026-11-10 and the owner's decisions of 2026-11-10 (09:56 and
10:09 JST): arm B is SABRE; the bands are reported beside, not judged; 210 s per job accepted, shots and points as
10-30; arm A fold:rule as 10-30; new seeds so that the labels can be sealed; psf-os's own checks in the job.
Inventory of 10-30: `notes/qclf_2026-11-10/stageA.md`. Nothing here is fixed until the owner's go; the depth L and
the answers' hash are filled in when fixed.

## Question

Does the placement that keeps more signal give the more accurate untrained classifier on other days and devices,
with paper 3's four confounds held down as in 10-30? Here: fold:rule against Qiskit's SABRE (level 2, seed 0, no
map). On 10-30 kingston this pair gave 0.810 against 0.750 at S = 250 (p 0.067, reported, not judged).

## Task (gpu/qclf_task.py; 10-30's form, new seeds)

- n = 20 ring; per layer RY(pi/2 x_q), RZ(pi/2 x_q), CZ on every ring edge; depth L (below).
- Features <X_q>, <Y_q>, <Z_q> (60, three circuits per input); least squares with intercept, sign.
- Inputs x uniform in [-1, 1]^20, public seed 20261110, pool 520; teacher w from a secret seed (written only in the
  sealed answers); centred labels; margin cut 0.25 sd; 128 train, 200 test; no redraw.
- One task for the whole series. The answers (seed, w, features, all labels) are sealed by sha256 at fixing; each
  run is scored locally with them and its verdict committed; the answers are released after the last run's verdict.

## Depth L

By 10-30's formula, L = a b ln(a / b) / (2 (a - b)) with a = L*(fold:rule), b = L*(SABRE), rounded, from a new L*
measurement (declared separately; VS Claude is building it, 10-29's P1 shortened: n = 20, the two arms, L 24 / 50 /
100). **Open for the owner:** which device's L* sets L if they differ (proposal: the median over the devices
measured), and L is then fixed for the whole series.

Why: with 10-30's L = 19, if L* has doubled since, the predicted S = 250 gap falls from 0.062 to 0.023 (home's
computation by the declared model, `notes/qclf_2026-11-10`), below one test-set SE.

## Arms and job (gpu/qclf_build.py)

- Device record: psf-os fetch (coupling graph and failed marks only), read through `toqb.devices` "psfos:"
  (checked: the same circuits as from a full Target, `notes/qclf_2026-11-10/failmark_target_check.md`).
- A: fold:rule. B: qiskit:2:blind:template (preset level 2, seed_transpiler 0, only the working couplers and the
  basis reach Qiskit). Rule G per arm: one measured map, no failed element; else that run is NOT RUN.
- Per arm 984 circuits (point-major, basis-minor), 250 shots; floor and mirror of point 0's three circuits; one
  ring sentinel; 1,984 circuits, 208.3 s by the time model (full-size build on the fez record of 11-04, L 19: 7.6 min on 2 CPUs).
- Before each run: gpu/qclf_check.py on every circuit (each <Z> equals its noiseless feature to 1e-9; floors and
  mirrors read all zeros). FAIL means NOT RUN.

## Devices and days

The daily record's rule (right before the fetch: pending jobs of ibm_marrakesh, ibm_fez, ibm_kingston; at most 10
pending, else the fewest). One job per device-day. The series is at least 3 devices x 2 days (6 jobs). **Open:** the
exact stop rule (proposal: the first 6 device-days that pass rule G, at most one per device per day).

## Verdicts per job (gpu/qclf_score.py)

- **A:** rule more accurate than SABRE: one-sided McNemar on the 200 test points at S = 64 and S = 250 (S = 64
  subsampled without replacement from the 250-shot counts, seeds as 10-30), Holm at 0.05 -> RESOLVED / NOT RESOLVED.
- **M (main measure):** signed margin, mean over the test points of y z at S = 250, per arm; rule - SABRE with the
  paired SE.
- Beside, never judged: accuracy at S 16 / 32 / 64 / 125 / 250; majority and noiseless ceiling; median lambda per
  basis; share of test points answered +1 (readout bias); floor and mirror P(0); the sentinel; the band from the
  L* measurement (reference only); the calibration beside (`gpu/calib_beside.py`).

## The series

Counted, not combined: the number of the 6 jobs where (i) A is RESOLVED, (ii) M's difference is positive, (iii)
the S = 250 accuracy difference is positive. A sign test over (ii) is reported, not judged. No p values are pooled.

## Prediction (from 10-30, before any new data)

Rule ahead of SABRE in M and in accuracy on most jobs; A RESOLVED on few single jobs (10-30's gap was about 2 SE at
S = 64 and 1-2 SE at S = 250). If the L* measurement shows the gap closing (L*s close to each other), the prediction
is that the series shows no consistent direction. Not rewritten if wrong.

## The four confounds (as 10-30)

| confound | held down by |
|---|---|
| answer at the starting point | no trained circuit; one least-squares solve |
| readout bias | least squares with intercept absorbs per-feature offsets and scales; share answered +1 beside |
| shot weakness | fixed shots; subsampled S; lambda and margins beside |
| model scale | no model in any verdict; the band is beside only |

## Not claimed

Quantum advantage (n = 20 features are classically computable); that SABRE is worse in general (one task, one
depth, these days).
