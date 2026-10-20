# W5. `toqb/predscore.py`: notes on the prototype (2026-10-20)

**Files (new; no existing file is changed):**

- `toqb/predscore.py`: about 470 lines, numpy and scipy only.
- `tests/test_predscore.py`: 10 tests on synthetic data.

**What was done here.** A syntax check only (`python -m py_compile`). The tests were **not run at the workplace**
(instruction 6); home runs them:

    python -m pytest tests/test_predscore.py      # or: python tests/test_predscore.py

**CLI** (exit 0 done, 1 usage, 2 STOP):

    python -m toqb.predscore PRED.json MEAS.json OUT.json [--ref REF_PRED.json]
    python -m toqb.predscore from-s2rc RECORD.json OUT_PRED.json [--price USD_PER_GPU_HOUR]
    python -m toqb.predscore from-device JOB_DIR CELL OUT_MEAS.json --pred PRED.json
    python -m toqb.predscore from-rehearsal RECORD.json OUT_MEAS.json --pred PRED.json

**Tests and the answers they expect:**

| test | data | expected |
|---|---|---|
| `test_perfect_prediction_is_calibrated` | 2,000 points; twin = truth + its own Monte Carlo error (T = 1,024); counts ~ Binomial(1,000, truth) | 99 % coverage in [0.975, 1.0]; \|z\| < 5; information over itself = 0 exactly; over chance > 0; both classes reported |
| `test_shifted_prediction_is_detected` | the same twin + 0.08 | 99 % coverage < 0.6; z < −10; information over the unshifted twin < −100 nats |
| `test_hash_mismatch_stops` | prediction edited after the measurement named it | exit 2; no score written |
| `test_one_class_is_refused` | all labels +1 | Stop ("one-class evaluation refused") |
| `test_no_overwrite` | the same score twice | the second call exits 2; the file is unchanged |
| `test_exact_truth_kind` | stand-in P(1) given exactly | kind exact-no-shots; not claimable; coverage of the twin error in [0.975, 1.0]; stand-in warning |
| `test_claimable_only_for_device_fixed_before_truth` | the device tier observed after the fix; device observed before; stand-in after | True / False / False |
| `test_converters_from_s2rc_and_rehearsal` | a synthetic s2rc record with the fields the converters read | prediction and measurement written; stand-in, not claimable; cost in dollars = wall time × price |
| `test_converter_from_device` | a synthetic job folder (manifest, raw counts; two classical bits, clbit 0 rightmost) | counts read correctly; claimable (the manifest is written before the result) |
| `test_scorer_cannot_produce_truth` | an AST scan of `predscore.py` | imports only `__future__`, datetime, hashlib, json, math, os, sys, numpy, scipy |

**Choices made in the prototype** (each can be changed; listed for the owner):

1. **The twin's Monte Carlo error** in the predictive distribution is a Normal(p1, p1(1 − p1)/T), clipped, integrated
   by 24-point Gauss-Hermite. `s2rc` uses random draws with the same distribution; this computes the same mixture
   without sampling.
2. **Coverage uses the mid-distribution PIT,** which handles discrete counts without randomisation. The central
   interval's coverage is approximately λ, not exactly.
3. **The test thresholds** (0.975 for 99 % coverage, |z| < 5, z < −10) are set loosely, so that a correct
   implementation does not fail by chance; their false-failure probability was not computed.
4. **The test style** follows plain pytest functions with plain asserts and a `__main__` runner. The existing
   `tests/` folder was not in the pack, so whether it matches is `[ ]` to check at home.
5. **`from-device` checks** that the prediction's P(1) and labels equal the manifest's cell exactly (after a JSON
   round trip), and that the run record's SHA-256 matches.
6. **`claimable`** takes the prediction's fixing time from the prediction itself or from the manifest's `written`
   time. Fixing by hash counts when the prediction says so or when the measurement carries the manifest's SHA-256.

**Points for the owner to decide (W5):**

1. Whether the prototype's choices 1-6 above are kept.
2. Whether `predscore` lives in TOQB (as now) or moves to quantum-infra-vision as `psf-job`'s scoring step later.
3. Whether the stamp's official score stays `s2rc_device score` (design C's H1 / H2), with `predscore` as the
   layer-4 view of the same job. Proposal: yes, so the pre-registered scoring is not touched.
