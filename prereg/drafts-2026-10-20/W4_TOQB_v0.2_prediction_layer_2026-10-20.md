# W4. TOQB v0.2: the prediction layer (design proposal, 2026-10-20)

**Status.** Written at the workplace, 2026-10-20, about 06:30 CEST. This is a proposal: the owner decides. Nothing
was run. W5's prototype (`toqb/predscore.py`, `tests/test_predscore.py`) implements §1 and §3 and was syntax-checked
only; the tests are for home to run.

**Basis:**

- TOQB README v0.1;
- `toqb/s2rc.py` and `toqb/s2rc_device.py` (as in workplace_pack_6);
- design C r7, final draft, including §8b;
- quantum-infra-vision ARCHITECTURE v0.2, §3-§4.

## 0. The owner's question

> Should the simulator and the benchmark be linked? If so, is it the benchmark that must change, an older concept?

**Proposed answer: yes, link them, and the benchmark is what grows.**

- **Link them through artifacts, never through the truth.** The twin and the benchmark exchange files: a prediction,
  a measurement and a score, each named by its SHA-256. The code that is scored never produces the truth it is scored
  against.
- **v0.1 is not outdated; it lacks one axis.** v0.1 scores the circuit a compiler returns. Design C added a question
  v0.1 cannot ask: how well a twin predicted the device in advance, and at what cost.
- **v0.2 adds that as layer 4** and makes twins participants alongside compilers. The scored unit is a (twin,
  compiler) pair.

## 1. What is measured

**Notation.** For test point i:

- y_i ∈ {+1, −1} is the label; +1 means ⟨Z⟩ > 0, that is P(1) < ½ (as `toqb.s2r2`);
- p1_i is the twin's predicted P(1), readout included;
- T is the twin's trajectory count, so v_i = p1_i(1 − p1_i)/T is its Monte Carlo variance (as `toqb.s2rc`);
- k_i is the measured count of 1s out of n_i shots.

### 1.1 How well the prediction hit (layer 4, the new axis)

**L4-a. Log score (proper scoring rule).**

    P_i(k) = ∫ Binomial(k; n_i, p) · Normal_clip(p; p1_i, v_i) dp      (Gauss-Hermite, 24 nodes; no sampling)
    LS = Σ_i log P_i(k_i)                                              (nats)
    I_ref = LS(twin) − LS(reference)       "information over the reference", total and per point

- **References:**
  - chance (p = ½);
  - the noiseless simulation of the same circuits;
  - the reference twin (§2).

  Each has its own value of I. On a fixed measurement, I > 0 means the twin assigned the observed counts higher
  probability than the reference did.

**L4-b. Calibration.**

    z = (LS − E_pred[LS]) / SD_pred[LS]

E and SD are computed from the prediction itself, point by point. A perfect prediction gives z ≈ 0. A twin that is
too sure, or biased, gives z ≪ 0.

**L4-c. Coverage.** The mid-distribution PIT is u_i = P_i(K < k_i) + ½ P_i(k_i). The coverage at level λ is the share
of points with (1 − λ)/2 < u_i < (1 + λ)/2, reported at λ = 0.5, 0.9 and 0.99. A calibrated prediction gives about λ.

**L4-d. Job level (design C's R1, R2).** These use the measured fractions p̂_i = k_i / n_i:

- CE, with `toqb.s2r2._ce`'s formula;
- accuracy, both the strict count and with ties counted as ½;
- whether each falls inside the predicted 99 % intervals (twin plus shots, and shots only);
- the gaps from the predicted values.

**Per class.** Every metric is reported for y = +1 and y = −1 separately as well as overall. **A one-class evaluation
is refused** (§3, rule S5). This is the type-level answer to the learning-curve flaw found today (C r7 §8b: the
first 100 test points were all of class +1).

**Exact truth without shots** (the rehearsal records). When only an exact P(1)* is stored (`rehearsal.standin_p1`),
the measurement has kind `exact-no-shots`, and different formulas apply:

- the Bernoulli score per shot, s_i = P* log p1_i + (1 − P*) log(1 − p1_i);
- coverage of the standardised residuals (P* − p1_i)/√v_i.

These are not comparable with shot scores, and the score says so.

### 1.2 What the prediction cost

- GPU seconds and wall seconds, for training and for prediction separately.
- Dollars: GPU hours × the declared price.
- The GPU model.

`s2rc` records today hold only the whole run's wall time and a `times` split in which the prediction sits inside
`eval`, together with the learning curve and, in a rehearsal, the stand-in's verification. The prototype passes them
through with that note. Recording prediction seconds separately is a change to `s2rc`, proposed for after the stamp
(§6).

### 1.3 Task result per money (layer 3, unchanged)

As v0.1's variational-loop scenario: accuracy and margin at the budget, and dollars to a target accuracy.

### 1.4 Trust (a slot only)

The score carries, if present:

- the certificate SHA-256 and its verdict (psf-cert, W1);
- any gate-1 refusal code.

The content comes later; the slot is there so a pair without a certificate is visible as such.

### Proposal for the primary metric of layer 4

**I per point over the reference twin, with z and the 99 % coverage beside it, and the cost next to it.**

- I is proper and uses every point and every shot. It does not depend on the order of the points. It compares twins
  fairly on the same measurement.
- It is not comparable across different measurements, since its value depends on the counts. Pairs are therefore
  ranked only within one measurement set.
- **Not proposed:** combining hit and cost into one number. They are reported side by side, as v0.1 reports quality
  and time.

## 2. Participants

| twin \ status | owner | engine | exists | in layer 4 as |
|---|---|---|---|---|
| traj2 | TOQB | GPU trajectories, exact P(1) per trajectory | yes | participant |
| CUDA-Q 0.15.1 | NVIDIA | GPU trajectories, one shot per trajectory | yes (X22 gate passed) | participant |
| psf-twin (MPS) | PSF-Zero | MPS; noiseless chains now; noise and rings per W2 | prototype | participant |
| Qiskit Aer density matrix | IBM / Qiskit | exact density matrix, noise model from the Target | library | **proposed reference twin** |

| compiler | in layer 4 as |
|---|---|
| Qiskit level 2 against the Target | **reference compiler** (as v0.1 and C r7) |
| Qiskit levels 1 and 3, TKET | participants |
| PSF-Zero | participant, never the reference (conflict of interest, v0.1 principle 5) |

**Why Aer's density matrix as the reference twin.**

- Neither TOQB's nor PSF-Zero's authors wrote it.
- It is exact (no Monte Carlo error), so its own error term is zero.
- It builds its noise model from the vendor's Target by a documented library path (`[ ]`: the exact constructor is to
  be fixed in the pre-registration).

**Limits.**

- The density matrix needs 4^n entries, so the reference covers n ≤ about 12-13. Above that, the reference falls back
  to chance and noiseless only, and the score says so.
- Its noise model differs from traj2's (no ZZ crosstalk, for example). That is acceptable for a reference: it stands
  for "the vendor's standard model", not for a truth.

## 3. The artifacts and the rules that keep truth apart

**Types** (aligned with ARCHITECTURE §3's TwinPrediction, RawCounts and Score; full fields in `toqb/predscore.py`):

| artifact | key fields |
|---|---|
| `toqb-pred/0` (TwinPrediction) | producer and version; inputs (run record, Target, QPY SHA-256); twin {name, traj}; compiler {arm}; cell; shots; points [{i, label, p1}] for **all** P points; job intervals; cost; `fixed_at`, `fixed_by_hash` |
| `toqb-meas/0` (RawCounts, scored form) | kind (`shots` or `exact-no-shots`); tier (`noiseless`, `twin`, `stand-in`, `device`); `observed_at`; inputs {**prediction_sha256**, manifest, raw counts}; points [{i, k, n}] or [{i, p_exact}]; for a stand-in, `declared_deviation` |
| `toqb-score/0` (Score) | inputs {prediction, measurement, reference SHA-256}; kind, tier, `claimable`; the metrics of §1; per class; warnings |

**Rules, each checked by a test** (W5 implements S2, S3, S4, S5 and S6):

| rule | statement | test |
|---|---|---|
| S1 | Truth at the device tier comes only from the vendor edge (raw counts). Truth at other tiers names its producer and engine. If that engine is the participant's own, the score warns "same-engine truth", and the result is never claimable | registry check (proposed; partly in W5 as the stand-in warning) |
| S2 | The scorer imports no simulator or engine: numpy and scipy only. It cannot make truth | AST scan of `predscore.py` (`test_scorer_cannot_produce_truth`) |
| S3 | A measurement names the SHA-256 of the exact prediction file it answers; the scorer recomputes it and stops on a mismatch | `test_hash_mismatch_stops` |
| S4 | `claimable` only if the tier is device, the kind is shots, the prediction was fixed (by hash) before the truth was observed, and the times show it | `test_claimable_only_for_device_fixed_before_truth` |
| S5 | Every point of the cell, and both classes; any subset must be stratified by a rule declared beforehand | `test_one_class_is_refused` |
| S6 | No artifact is overwritten | `test_no_overwrite` |
| S7 | The twin's input calibration is recorded (Target SHA-256), and the truth is observed after T0 (device), or with deviations declared beforehand (stand-in) | fields required by the types (proposed check) |

**Tiers of truth** (instruction 6 §1):

| tier | what | claim |
|---|---|---|
| noiseless | exact noiseless simulation | none; a sanity tier |
| twin | another twin's output | none; agreement between twins |
| stand-in | a simulator with declared deviations (stage 0: `t12` 0.3, `over` 0.01, `zz_hz` 10 kHz, seed 20261017) | none; reported as "stand-in" |
| device | IBM hardware, one job, prediction fixed by hash first | the only claimable tier |

## 4. Fairness: v0.1's calibration split, extended to twins

- **Twins read only the T0 calibration** (the Target fetched at T0, recorded by SHA-256). The truth comes later: the
  job executes after the manifest is written and hashed. That is the device-tier split: the twin cannot see the noise
  it is scored with.
- **Stand-in deviations are declared before the prediction** and recorded in the measurement (`declared_deviation`).
- **All twins in one comparison read the same Target file** and predict the same compiled circuits (the same QPY
  SHA-256).
- **Stale-calibration variant.** A twin built from an older Target (for example T0 − 24 h) is a separate participant
  variant. This replaces v0.1 layer 2's "quality when the calibration is stale" with a measured quantity.

## 5. From v0.1: keep, rename, retire

| item | v0.2 |
|---|---|
| principles 1-2 (budgets as multiples of the reference, timeouts count as failures) | keep |
| layer 1 (compilation) | keep, unchanged; past results cited as they are |
| layer 2 (hardware fitness; not built) | split: failed-element placement stays, as a structural check; "quality with a stale calibration" moves to layer 4 (§4); the estimated success probability becomes report-only or is retired (owner): it is a calibration-derived estimate of what layer 4 now measures, and as a criterion it would select by calibration |
| layer 3 (task per money) | keep, renamed "task per money" |
| new layer 4 | prediction: L4-a to L4-d, cost, trust slot |
| "reference compilers" | "baselines": reference compiler Qiskit level 2; reference twin Aer density matrix |
| calibration split | extended to twins (§4) |
| scored runs and the contamination notice | kept verbatim, citable with their run folders |

**README outline proposed for v0.2:**

1. what TOQB compares, now compilers and twins;
2. why;
3. principles, with the calibration split for twins;
4. the four layers;
5. participants and baselines;
6. artifacts and the truth rules (S1-S7);
7. tiers of truth;
8. sizes;
9. the standard compilation set;
10. how a measurement is made;
11. the loop scenario;
12. layer 4 data: the design C rehearsal (stand-in tier) and the stamp (device tier);
13. scored runs (unchanged list);
14. layout;
15. license.

## 6. The first data: design C

| source | converter (W5) | measurement kind and tier | note |
|---|---|---|---|
| rehearsal records (seeds 201-203) | `from-s2rc` then `from-rehearsal` | exact-no-shots, stand-in | prediction and truth come from one run and one engine family: never claimable |
| device stamp | `from-s2rc` then `from-device JOB CELL` | shots, device | the manifest (hashed before submission) fixes the prediction; claimable when the order holds |

- **Not changed:** `s2rc` and `s2rc_device` stay as on the rehearsal for the device day. Proposed for after the stamp:
  record prediction seconds separately, store per-point shot counts in rehearsals, and shuffle or stratify the curve
  points (C r7 §8b).

**Vanity and essential figures (layer 4):**

| | figure |
|---|---|
| Vanity | "the twin predicted the device within its 99 % interval" |
| Essential | I per point over the reference twin (and over chance and noiseless), z, coverage per class, at the stated cost and tier; one device, one day, one job |

## 7. Points for the owner to decide

1. **The primary metric of layer 4:** I per point over the reference twin, with z, coverage and cost beside it.
2. **The reference twin:** Aer's density matrix with the vendor's noise model; the fallback above n ≈ 12-13 is chance
   and noiseless.
3. **The estimated success probability in layer 2:** report-only or retired.
4. **Stale-calibration twins** as participant variants in layer 4.
5. **Rule S1's registry** (which truth producers exist and which engine each uses), and whether "same-engine truth"
   is only a warning or a refusal.
6. **The changes to `s2rc` after the stamp** (§6): prediction seconds separately, per-point shots in rehearsals,
   stratified curve points.
7. **Ranking only within one measurement set,** with no cross-measurement league table.
