# QELM task A: does a larger λ give a higher accuracy in a search-free classifier? (DRAFT by the workplace, 2026-10-30; owner's confirmation pending; to be fixed by SHA-256 and CET time before any stand-in or device run)

**What is tested.** Paper 5's link λ → readable signal → accuracy, in the one setting where nothing else can cancel λ:

- a fixed data circuit (no trainable angles);
- local features ⟨X_q⟩, ⟨Y_q⟩, ⟨Z_q⟩;
- one ordinary least-squares solve, which is exactly invariant to per-feature affine maps.

So λ enters only through the effective shots S_eff = λ²S.

**Not claimed.** At n = 20 the features are classically computable, so no quantum advantage is claimed. Prior work:
Innocenti et al., Communications Physics 2023 (arXiv:2210.00780); quantum extreme learning machines and reservoirs.

## 1. Model and task (fixed; `toqb/qelm.py`)

| item | value |
|---|---|
| circuit | TOQB's ring: per layer RY(π/2·x_q), RZ(π/2·x_q) on every qubit, then CZ on every ring edge; n = 20 |
| depth | **L = 19** = `depth_formula(56.5, 26.4)` = 18.9, rounded (section 2) |
| features | ⟨X_q⟩, ⟨Y_q⟩, ⟨Z_q⟩ for q = 0..19: 60 numbers per input, 3 circuits per input |
| classifier | least squares with intercept to ±1 targets, sign as prediction (61 weights) |
| inputs | x uniform in [−1, 1]^20, seed 20261030; pool of 520 |
| teacher | w ~ N(0, I_60), seed 20261031; labels sign(w · (f₀(x) − μ)), with μ the pool's mean noiseless feature vector |
| margin | points with \|w · (f₀ − μ)\| < γ are dropped, γ = 0.25 × sd over the pool; the first 128 kept points train, the next 200 test (no redraw: STOP if fewer) |
| noiseless data | `results/qelm-A-2026-10-30/noiseless.json` (SHA-256 32a6d65651abe1ea7ca58b592280d88a2a9af04ed4ee40a13acb545adf7bb38d): kept 425 of 520, γ 0.4126, class share (+1) 0.508 / 0.510 (train / test), feature sd 0.264 (X 0.194, Y 0.164, Z 0.287) |

**The centring.** It is a change from the instruction's sign(w · f₀). Without it the features' non-zero means pushed
81 % of the points into one class: an uncentred first computation, recorded and not used. With it, the classes are
balanced in expectation. No arm or noise entered this decision.

## 2. The depth, by formula (no simulation)

**The assumption.** With λ_arm(L) = exp(−L / L*_arm) per arm, the gap λ_rule² − λ_X² is largest at
L = a b ln(a/b) / (2(a − b)), for L*_rule = a and L*_X = b.

**The inputs.** The strongest competitor's records of 2026-10-29 at n = 20:

| device | rule | blind Qiskit | zipcyc | L for Qiskit | L for zipcyc |
|---|---|---|---|---|---|
| marrakesh | 56.5 | 26.4 | 15.1 | **18.9** | 13.6 |
| kingston | 81.3 | 22.0 | 22.6 | 19.7 | 20.0 |

So L = 19.

- **Assumption, flagged.** The local features decay at the noise wall charge's per-step rate. The circuit family
  differs: data angles here, h = 0.6 there.
- **Concentration is not reached.** At L = 19 the noiseless features keep sd 0.264 (X 0.194, Y 0.164, Z 0.287); a global 2-design would give about
  0.001. So the signal is not lost to concentration.

## 3. Predictions (fixed before any stand-in or device data)

**How they are made.** Every feature is read as λ_arm·f₀ with S binomial shots, λ_arm = exp(−19 / L*_arm) from that
device's 2026-10-29 records; then the test accuracy of least squares, mean and central 99 % over 400 draws
(`qelm.predict`).

**Ceiling.** The noiseless ceiling is 0.840 (chance 0.5; least squares on the raw x 0.555) (least squares, 128 points for 61 weights).

| device (L*: rule / zipcyc / Qiskit) | arm | λ | S 16 | S 32 | S 64 | S 125 | S 250 |
|---|---|---|---|---|---|---|---|
| marrakesh (56.5 / 15.1 / 26.4) | fold:rule | 0.714 | 0.644 [0.550, 0.730] | 0.697 [0.585, 0.785] | 0.748 [0.655, 0.835] | 0.794 [0.705, 0.870] | 0.821 [0.725, 0.905] |
| marrakesh (56.5 / 15.1 / 26.4) | fold:zipcyc | 0.284 | 0.541 [0.445, 0.640] | 0.563 [0.470, 0.650] | 0.607 [0.505, 0.700] | 0.658 [0.555, 0.765] | 0.714 [0.610, 0.795] |
| marrakesh (56.5 / 15.1 / 26.4) | qiskit:2:blind:template | 0.487 | 0.590 [0.475, 0.690] | 0.639 [0.520, 0.725] | 0.690 [0.585, 0.780] | 0.743 [0.645, 0.825] | 0.788 [0.705, 0.865] |
| kingston (81.3 / 22.6 / 22.0) | fold:rule | 0.792 | 0.663 [0.565, 0.750] | 0.714 [0.620, 0.795] | 0.764 [0.645, 0.845] | 0.800 [0.715, 0.885] | 0.830 [0.745, 0.900] |
| kingston (81.3 / 22.6 / 22.0) | fold:zipcyc | 0.431 | 0.575 [0.475, 0.680] | 0.618 [0.530, 0.710] | 0.675 [0.575, 0.780] | 0.723 [0.610, 0.810] | 0.770 [0.690, 0.845] |
| kingston (81.3 / 22.6 / 22.0) | qiskit:2:blind:template | 0.422 | 0.574 [0.465, 0.675] | 0.616 [0.515, 0.710] | 0.666 [0.570, 0.755] | 0.720 [0.605, 0.805] | 0.770 [0.680, 0.855] |

Mean [central 99 %] test accuracy over 400 draws.

## 4. Rules (drafts; the owner confirms)

| id | rule | verdict |
|---|---|---|
| G | every arm compiles n = 20 natively with one measured-qubit map (rule and Qiskit 20 CZ per layer, zipcyc 46) | gate: else NOT RUN for that arm |
| Q1 | the model: per arm, the device features follow a_j + λ_j f₀_j (fit on the training points) with χ²/dof median ≤ 2 over the 60 features | HOLDS / FAILS |
| Q2 | the pre-run prediction: each arm's test accuracy at S = 250 inside its band of section 3 (that device's row) | INSIDE / OUTSIDE per arm |
| Q3a | λ → accuracy: rule more accurate than zipcyc, one-sided McNemar on the 200 test points, at S = 64 and 250, Holm over the two | WIN / not |
| Q3b (reported, not judged) | rule against blind Qiskit, the same test | predicted difference small (section 3): low power, not judged |
| R | baselines: least squares on the raw x; on the noiseless features (the ceiling); the majority class | report |

**Subsampled shots.** S = 16, 32, 64 and 125 are drawn from the same 250-shot counts, without replacement; no extra
device time.

## 5. Device time

**Per arm.** (128 + 200) × 3 = 984 circuits × 250 shots: 984 × 0.036 + 984 × 250 × 0.00027 + 3 = 104.8 s, one job per
arm (at most 120 s).

**Total.** Three arms make 3 jobs, about 5.2 min by the model per device; billed has been 0.72-1.0 of it.

## 6. Stand-in rehearsal (pod)

`gpu/qelm_pod.sh`:

- rule and zipcyc on TOQB's stand-in (T1 / T2 on idles, static ZZ; trajectories, T = 64; a GPU);
- Qiskit is not in pod simulations (owner, 2026-10-28).

**Not judged.** Its numbers are reported as an expectation, not judged.

## 7. Power and options (for the owner, before fixing)

**Power.** Compare the predicted differences with the test set's standard error (about 0.03 per arm at 200 points):

- **rule − zipcyc** (Q3a): 0.11 (marrakesh) / 0.06 (kingston) at S = 250, and 0.14 / 0.09 at S = 64. These are 2-5
  SE, and the paired test on shared points is stronger still.
- **rule − Qiskit** (Q3b, not judged): 0.03 / 0.06 at S = 250, and 0.06 / 0.10 at S = 64. On marrakesh at S = 250
  this is about 1 SE.

**Options, each by formula, none chosen by simulation:**

- (a) as drafted;
- (b) more test points: the SE falls as 1/√N_test, and the device time grows by 0.31 s per point and arm;
- (c) more training points (N_train ≥ 5 × 61 ≈ 300, the P3D lesson N ≥ d with margin), which raises the ceiling at
  the same device-time rate.

## 8. Task B (settings only; declared separately, run once, an example in Paper 5)

| item | value |
|---|---|
| data | breast_cancer, split seed 0, 128 / 200, standardised and PCA to 20 components on the training points, scaled to [−1, 1] by the training range |
| circuit | the same ring, **L = 1**, angle **π/4 · x** in RY and RZ (home: at π/2, sin a cos a = ½ sin πx vanishes at x = ±1; at π/4 the map is monotone in x) |
| classifier | least squares as in A |
| run | once, after its own declaration; its ceiling is unknown until then and is reported as it is |

## 9. Limits

- **Simulation does not settle the outcome.** The stand-in has no drift and no device-specific coherent errors.
- **The decay-rate transfer is an assumption.** λ from the charge's L* is assumed to carry over (section 2).
- **One teacher, one input set, one day per device.**
