# DRAFT (not fixed): the paper 3 classifier through the OS alone, on several devices and days, raw, labels sealed

Home, 2026-11-10. From the workplace's blueprint of 2026-11-10 and the owner's decisions of 2026-11-10:

- 09:56 JST: the bands are reported beside, not judged; shots and test points as 10-30.
- 10:09 JST: arm fold:rule as 10-30; new seeds, so that the labels can be sealed; psf-os's own checks in the job.
- 10:54 JST: the stop rule (first 6 jobs passing rule G, at most one per device per day); one task for the series,
  answers released after the last verdict.
- 11:05 JST: the OS alone, no Qiskit arm (QPU time and compute kept); depth 19 as 10-30; no separate L* job.
- 11:06 JST: "進めて" on the verdicts below.

Inventory of 10-30: `notes/qclf_2026-11-10/stageA.md`. The SABRE draft of earlier today is superseded by this file
(git history).

## Question

Does the untrained classifier that the OS delivers (fold:rule placement from the coupling graph and failed marks
only, no mitigation) read on other days and devices, and how close does it come to its noiseless ceiling? On 10-30
kingston the same arm on the 10-30 task gave 0.810 at S = 250 against a ceiling of 0.840.

## Task (gpu/qclf_task.py; 10-30's form, new seeds)

- n = 20 ring; per layer RY(pi/2 x_q), RZ(pi/2 x_q), CZ on every ring edge; depth L = 19 (as 10-30).
- Features <X_q>, <Y_q>, <Z_q> (60, three circuits per input); least squares with intercept, sign.
- Inputs x uniform in [-1, 1]^20, public seed 20261110, pool 520; teacher w from a secret seed (written only in the
  sealed answers); centred labels; margin cut 0.25 sd; 128 train, 200 test; no redraw.
- One task for the whole series: `results/qclf-series/task/task.json` (public: the inputs and settings). Answers
  (seed, w, features, all labels) sealed: sha256 **(filled in at fixing)**. Each run is scored locally with them and
  its verdict committed; the answers are released after the last run's verdict.

## Job (gpu/qclf_build.py)

- Device record: psf-os fetch (coupling graph and failed marks only), read through `toqb.devices` "psfos:"
  (checked: the same circuits as from a full Target, `notes/qclf_2026-11-10/failmark_target_check.md`).
- fold:rule; rule G: one measured map, no failed element; else that job is NOT RUN.
- 984 circuits (point-major, basis-minor), 250 shots; floor and mirror of point 0's three circuits; one ring
  sentinel; 994 circuits, 105.9 s by the time model.
- Before each run: gpu/qclf_check.py on every circuit (each <Z> equals its noiseless feature to 1e-9; floors and
  mirrors read all zeros). FAIL means NOT RUN.

## Devices and days

The daily record's rule (right before the fetch: pending jobs of ibm_marrakesh, ibm_fez, ibm_kingston; at most 10
pending, else the fewest). The series is the first 6 jobs that pass rule G, at most one per device per day. A job
not run for any reason (rule G, the noiseless check) does not count.

## Verdicts per job (gpu/qclf_score.py)

- **A:** READS if the S = 250 test accuracy is above the majority-class guess: one-sided exact binomial test of the
  number correct (of 200) against p0 = the majority share of the test labels, at 0.05; else DOES NOT READ.
- **M (main measure):** signed margin, the mean over the test points of y z at S = 250 (z the least-squares
  output), with its SE.
- Beside, never judged: accuracy at S 16 / 32 / 64 / 125 / 250; the noiseless ceiling and the reach
  (acc - 0.5) / (ceiling - 0.5); median lambda per basis (device against noiseless features, training points);
  share of test points answered +1 (readout bias); floor and mirror P(0); the sentinel; the calibration beside
  (`gpu/calib_beside.py`).

## The series

Reported, not combined: the number of the 6 jobs that READ; the range (lowest to highest) of the S = 250 accuracy,
of the reach and of M. No p values are pooled.

## Prediction (from 10-30, before any new data)

All 6 jobs READ; the reach near 10-30 kingston's (0.810 - 0.5) / (0.840 - 0.5) = 0.91 or above if the devices are
less noisy now. Not rewritten if wrong.

## The four confounds (as 10-30)

| confound | held down by |
|---|---|
| answer at the starting point | no trained circuit; one least-squares solve |
| readout bias | least squares with intercept absorbs per-feature offsets and scales; share answered +1 beside |
| shot weakness | fixed shots; subsampled S; lambda and margins beside |
| model scale | no model in any verdict |

## Not claimed

Quantum advantage (n = 20 features are classically computable); anything about other placements or compilers.
