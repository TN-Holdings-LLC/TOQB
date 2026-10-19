# X22: pre-registration skeleton (r4) — engine × compiler (2 × 2), hybrid quantum-AI scaling

**Status: skeleton, not fixed.** Values marked `[ ]` are filled in after the pod pilot (speed, CUDA-Q first test,
gradient agreement for both compilers at 8 and 16 layers). The document is then fixed by SHA-256 and the CEST time
before any scored run. Revised at the workplace on 2026-10-19 (design text only; nothing was run).

**Revision 2026-10-19.** Added §3 (engine fairness) and §4 (the Qiskit setting, an owner decision). Rewrote §7 so
that the time metrics report the range in which the result holds as the main result. Made the noise-model gate (§2)
explicit for four channels.

**Revision r2 (2026-10-19).**

- §10 now holds the H100 pilot's traj2 timings and the gradient agreement.
- §6 and §7 take the H100 result (the PSF-vs-Qiskit gap narrows) as their example of a range statement.
- CUDA-Q 0.16.0 ran on the H100 (target `nvidia`); its noise-agreement check (`check_cudaq`) has not been run yet.
- The r1 file is unchanged.

**Revision r4 (2026-10-20, 01:40 CEST, workplace).** The r3 file is unchanged. Changes:

- **§3, the cost per CUDA-Q call.** Home divided the warm cost per call by the plan's inline noise operations and got
  0.23-0.25 ms for all four plans; the workplace checked the arithmetic.
  - Reading (inferred from four points, not profiled): the fixed cost per call is proportional to the number of
    inline noise operations.
  - So C1 (fewer calls) and C3 (gate-attached noise) are tried first.
- **§3, F3's declared list** becomes: current pattern, C1, C3, C1 + C3.
- **§3, a pod procedure for measurement items 1-8,** with an added item 4b for the noise-operation scaling.
- **§10, a correction.** The 1 × 4,096 Qiskit / PSF ratio on CUDA-Q (2.4 × / 2.7 ×) measured mostly the per-call
  cost, not the simulation; home withdrew the reading that PSF's saving carries over to CUDA-Q.

**Revision r3 (2026-10-19, 10:00 CEST).** The r2 file is unchanged. Changes:

- **CUDA-Q is pinned to 0.15.1.** 0.16.0 fails on general Kraus channels ("Invalid dense matrix task size."); 0.15.1
  and 0.14.2 run every construct (TOQB `results/cudaq-diag-2026-10-19/`).
- **§2 noise gate filled.** N1-N4 are expressed exactly; the numerical check passed, largest deviation 1.66 se against
  a limit of 4 se.
- **§10 timings.** The same-H100 timings of both engines are added.
- **§3 fairness rules F1-F7** are added as a proposal for the owner (`consult_A-D_2026-10-19.md` §A).

## 1. The claim, and what it is not

**Claim (form fixed now).**

> Within the tested range (§6), the combination {CUDA-Q, PSF-Zero} is **Pareto-superior** to the other three
> combinations on the primary and secondary metrics. That is, on every metric it is at least as good as each other
> cell, and on at least one metric it is better, with the decision rule of §8.

- **Not claimed:** "the only solution". A finite test can only say that, among the alternatives tried and within the
  range tried, nothing beat the combination. Other engines (for example qsim, Aer GPU or tensor networks), other
  compilers, other circuit families, widths, depths and noise models are outside the claim (§11).
- **Two separate statements**, reported separately:
  1. **Dominance:** the combination is the best cell (Pareto, §8).
  2. **Synergy:** the two factors multiply (the log-scale interaction of §7 is non-zero in the favourable direction).
     Dominance does **not** need synergy: with purely multiplicative main effects and zero interaction, the
     combination can still be the best cell. "The combination is the solution" in the strong sense of "one needs
     both" is the synergy statement.

## 2. Factors, cells, and the noise-model gate

| factor | levels |
|---|---|
| E (simulation engine) | `traj2` (TOQB's own trajectory engine) · `CUDA-Q` (**0.15.1**, target `nvidia`; settings fixed by §3) |
| C (compiler) | `Qiskit` (version 2.5.2, setting chosen in §4) · `PSF` (PSF-Zero release `[ ]`, compile_template) |

There are 4 cells: (traj2, Qiskit), (traj2, PSF), (CUDA-Q, Qiskit), (CUDA-Q, PSF).

**Held fixed across cells:**

- the task (classifier circuit family, teacher, data);
- n = `[ ]`, L ∈ {8, 16} (24 layers dropped, owner decision A);
- the stand-in noise model and its parameters (`t12` 0.3, `over` 0.01, `zz_hz` 10 kHz, seed 20261017);
- the device Target the compilers see (FakeFez);
- precision complex64 (unless §3 records otherwise for CUDA-Q);
- trajectories per circuit `[ ]`;
- shots `[ ]`;
- the GPU model `[ ]` and the pod image `[ ]`;
- seeds (§9).

**Gate: the same noise model (before any scored run).**

CUDA-Q must express each of the stand-in's four noise channels exactly, as traj2 does:

| # | channel | how traj2 applies it | can CUDA-Q express it exactly? | how CUDA-Q expresses it |
|---|---|---|---|---|
| N1 | amplitude damping (non-unitary; Kraus operators, per gate, from T1) | amplitude damping after each gate (fused kernel with its norm); together with depolarizing (1q: Pauli with probability dep/4 each; 2q: each of 15 Paulis dep/16) and phase flip | yes | inline `AmplitudeDampingChannel(g)` after each gate, with `DepolarizationChannel(3 dep/4)`, `Depolarization2(15 dep/16)` and `PhaseFlipChannel(pz)` (0.15.1; 0.16.0 fails here) |
| N2 | thermal relaxation while idle (from T1/T2 and each qubit's idle time in the schedule) | `relax` steps: phase flip and amplitude damping for each idle interval | yes | the same `relax` steps as inline `PhaseFlipChannel` + `AmplitudeDampingChannel` |
| N3 | static ZZ crosstalk (10 kHz between coupled qubits, accumulated over time, idle included) | `zz` steps: RZZ(θ) | yes (exact identity) | cx(a, b) · rz(θ, b) · cx(a, b), noiseless |
| N4 | sx / x over-rotation (coherent, `over` = 0.01) | sx / x as the over-rotated 1-qubit matrix G | yes | u3 with G's parameters (u3 self-test: largest deviation 3.1e-7) |

- **Readout** is applied to ⟨Z⟩ the same way in both engines: z → (1 − p01 − p10) z + (p10 − p01).
- **Estimator difference.** CUDA-Q takes one ±1 shot per trajectory. traj2 takes each trajectory's exact P(1). The
  mean is the same; CUDA-Q's variance per trajectory is larger (see §3, F2).

- **Rule (unchanged):** if any channel cannot be expressed exactly, the experiment stops and the gap is reported. The
  noise model is not changed to fit, and no approximation is substituted.
- **Then, numerically:** on 2 fixed circuits of one structure per compiler and depth, CUDA-Q's ⟨Z⟩ must agree with
  traj2's within 4 standard errors (T = 8,192 trajectories each; se from both estimates). This is the same test traj2
  passed against the density matrix, at most 1.36 se.
- **Result (2026-10-19, H100, CUDA-Q 0.15.1, `check_cudaq` at TOQB `fed598d`): PASS.**
  - Covered: both compilers × L 8 / 16 × both noise models (the twin on FakeFez, and the stand-in).
  - Largest deviation 1.66 se.
- **First CUDA-Q test (0.16.0):** it stopped at "Invalid dense matrix task size" on general Kraus channels, after the
  u3 self-test had passed. That is a 0.16.0 regression; a draft issue for NVIDIA is in TOQB.

## 3. Engine fairness (traj2 is tuned for these circuits; CUDA-Q is off the shelf)

traj2 was written and tuned for exactly these circuits: fused kernels, draws made on the host, in-place updates.
CUDA-Q is a general product. Part of any difference between the engines is therefore a difference in tuning effort,
not in the engine. To keep the comparison honest:

1. **Fixed before the scored runs:** every CUDA-Q setting is chosen and recorded below before any scored run, from the
   documented options only:
   - the target (for example `nvidia`, `nvidia --option fp32`, the trajectory or density-matrix backends);
   - precision;
   - how trajectories are batched (the number per call, and whether noisy trajectories run in parallel batches);
   - kernel compilation or caching;
   - any environment variables.
   No setting is changed after the first scored run.
2. **Allowed tuning budget:** CUDA-Q gets a pre-declared tuning budget of `[ ]` hours of pilot time (traj2's own tuning
   time is recorded for comparison: `[ ]`). Within it, settings are chosen on pilot seeds only. The setting with the
   best pilot time per loop is fixed, with all others listed as tried.
3. **Reported both ways:**
   - the engine factor as measured;
   - a note of what traj2's hand-tuning contributed: traj2's untuned plain path against its fused path, which
     `check_traj2` already compares (`[ ]` × difference).
4. **The gate in §2 comes first.** A faster engine that does not simulate the same channels does not count.

**Proposed rules for "each engine in its best use" (r3; the owner decides each; details and grounds in
`consult_A-D_2026-10-19.md` §A).**

- **F1. Same model first.** The gate (§2) is passed with the exact call pattern that is timed, and rerun after any
  change.
- **F2. Equal precision.** Report time at equal T and time at equal standard error of ⟨Z⟩:
  T_CUDA-Q = T_traj2 · (1 − z̄²) / Var_j(z_j), measured on pilot circuits. Which one is primary is `[ ]`.
- **F3. Best use per workload shape.**
  - It is chosen from at most 4 documented call patterns, declared before timing (broadcast; compiled
    `@cudaq.kernel`; gate-attached noise; `sample_async`).
  - Each is timed once on pilot seeds. The fastest pattern that passes F1 is fixed, and all the others are listed.
  - "Fastest" means the lowest median warm wall time of the training-step shape over 5 repeats.
  - **Alternative:** fix the pattern by documentation alone, if a choice by measurement counts as excluded search.
- **F4. Cap.** `[ ]` engineering hours and `[ ]` pod hours (proposal: about 1 working day and 2 pod hours), stated with
  the result. If CUDA-Q is still slower, the result is reported as "within the cap", not as a limit of CUDA-Q.
- **F5. Cold and warm** are reported separately for both engines (first call per structure; warm per call; total
  over a run).
- **F6. traj2 is frozen** at a commit before CUDA-Q's tuning starts.
- **F7. Versions.** CUDA-Q 0.15.1, target `nvidia`, precision `[ ]` (the default single precision matches traj2's
  complex64).

**The cost per call scales with inline noise operations (r4).**

| plan | warm s per call (68 × 32 ÷ 68) | inline noise operations | ms per operation |
|---|---|---|---|
| PSF L 8 | 0.626 | 2,693 | 0.233 |
| Qiskit L 8 | 0.762 | 3,073 | 0.248 |
| PSF L 16 | 1.272 | 5,313 | 0.239 |
| Qiskit L 16 | 1.503 | 6,262 | 0.240 |

- **Reading** (four points; not profiled): almost all of a warm call is a fixed cost proportional to the plan's
  inline `apply_noise` operations, not simulation.
- **Rough simulation share of one 1 × 4,096 call,** once that cost is subtracted: about 0.12 / 1.07 s (PSF / Qiskit,
  L 8) and 0.13 / 2.22 s (L 16). These are differences of single measurements (home estimate).
- **Consequences:**
  - **C1** (one broadcast call for the 68 argument sets) helps if the cost is paid once per call.
  - **C3** (noise attached to gate types in a `NoiseModel` instead of inline) helps if the cost is paid once per
    inline operation.
  - Either can remove most of the 50-150 × gap. Both are tried first; C2 and C4 only if neither does.
- **F3's declared list (r4 proposal):** current pattern, C1, C3, C1 + C3. Four patterns, each timed once after its
  F1 check.

**What the current timings say** (§10). The wrapper already builds one kernel per structure, with the angles as
argument. The 68 × 32 times (42.6-102.2 s) were taken warm, and they come to 0.63-1.50 s per call. A call costs about
the same at 32 trajectories as at 4,096. The 50-150 × gap is therefore a fixed cost per call: inferred, not checked.
It is not the 4-40 s first call.

| CUDA-Q setting | value fixed | alternatives tried in the pilot |
|---|---|---|
| version | 0.15.1 | 0.16.0 (fails on general Kraus channels); 0.14.2 (runs) |
| target | `nvidia` | `[ ]` |
| precision | `[ ]` | `[ ]` |
| trajectory batching / call pattern | `[ ]` (now: one `cudaq.sample` per circuit; F3 candidates) | `[ ]` |
| other options / environment | `[ ]` | `[ ]` |
| tuning time used | `[ ]` h | budget `[ ]` h |

**Pod procedure for the CUDA-Q measurements (r4 proposal; items 1-8 of consult §A2, plus 4b).**

- **Conditions:**
  - one H100, otherwise idle;
  - CUDA-Q 0.15.1, target `nvidia`;
  - traj2 at a frozen TOQB commit (F6, recorded);
  - circuits: n = 10, L = 8 and 16, both compilers, the twin's model (FakeFez) and the stand-in's model, as in
    `check_cudaq`.
- **Timing rules:** wall time with GPU synchronisation, after one warm-up call unless the item says "fresh process".
- **Output:** one JSON row per measurement, and a summary printed as in `check_cudaq`.
- **Pod budget:** F4's cap (proposal 2 h).
- **Order:** the baseline (current pattern) first, then each F3 candidate.
- **Rule for every pattern:** item 8 (F1) runs first. A pattern that fails F1 is recorded and not timed further.

| # | item | how | recorded |
|---|---|---|---|
| 8 | gate first (F1) | `check_cudaq` with the pattern under test (T = 8,192; both models, both compilers, L 8 / 16) | largest d / se; PASS below 4 |
| 1 | the two workload shapes | 68 circuits × 32 trajectories, and 1 circuit × 4,096, each 5 times warm; both engines | median and range of the 5 |
| 2 | structures | distinct plan structures per training step and per 20-loop run (`R.n_struct`, or the kernel cache size) | counts (1 per cell expected) |
| 3 | first call | in a fresh process: kernel build plus first execution, per structure; both engines | seconds |
| 4 | fixed cost against cost per trajectory | the same kernel called 10 times each at T = 1, 32, 256 and 4,096 | least-squares intercept (s per call) and slope (s per trajectory), with residuals |
| 4b | noise-operation scaling | the same plan with channel kinds switched off one at a time (all inline; without phase flip; without amplitude damping; without depolarizing). For timing only: these variants are not the model and are never used for results | s per call against the number of inline operations: slope (ms per operation) and intercept |
| 5 | calls per step | count of `cudaq.sample` calls per training step | 68 now; 1 expected with C1 |
| 6 | F2's variance ratio | on the 68 circuits: Var_j(z_j) per trajectory from traj2 against 1 − z̄² | ratio per cell; the equal-precision T |
| 7 | a whole training loop | `s2rc` loop with each engine (compile included): 2 warm-up loops, then the median of 20 | s per loop, split into compile / simulate |

- **Reading the result.** C1 should lower item 1's 68 × 32 time toward 1/68 of the fixed cost if that cost is paid
  per call. C3 should lower item 4b's slope if the cost is paid per inline operation. Whichever pattern is fastest and
  passes F1 is fixed (F3), and all four are listed.
- **Scope.** This changes how CUDA-Q is called, not the noise model. The model is fixed by §2, and F1 guards it.

## 4. The Qiskit setting (owner's decision; not a straw man)

The current setting is Qiskit's preset level 2. PSF-Zero's advantage comes from keeping the circuit at 10 qubits.
Qiskit's layout and routing spread it to 14-21 qubits, which raises the simulation cost by 2^4-2^11. A weak Qiskit
setting would exaggerate this. The candidates:

| # | Qiskit setting | expected effect on width and depth | compile cost | owner's choice |
|---|---|---|---|---|
| Q1 | level 2 (current) | as measured: 14 qubits at L 8, about 21 at L 24 | baseline | `[ ]` |
| Q2 | level 3 (default seeds) | possibly fewer SWAPs and qubits; not yet measured | higher | `[ ]` |
| Q3 | level 3 with more layout and routing trials (`layout_trials` / `swap_trials` = `[ ]`) | best Qiskit can do by search; not yet measured | much higher | `[ ]` |
| Q4 | Q2 or Q3 with the best of `[ ]` seeds (selection by width, then two-qubit count) | the strongest fair baseline | highest | `[ ]` |

- **Owner's choice:** `[ ]`.
- **Compile time** is counted in time per loop either way. A stronger setting may narrow Qiskit's circuits and cost more
  compile time. Both effects are reported.
- **Re-check after the choice:** the widths Qiskit actually produces under the chosen setting (`[ ]` qubits at L 8,
  `[ ]` at L 16).

## 5. Primary metric: candidates, chosen by the owner

| # | candidate | definition | scale for §7 | owner's choice |
|---|---|---|---|---|
| M1 | Time per loop | wall time of one training loop (simulator gradient step and stand-in circuits), median over `[ ]` loops after `[ ]` warm-up loops, per cell, n and L | log | `[ ]` |
| M2 | Reach at fixed time | the largest width n (at L = `[ ]`) or depth L (at n = `[ ]`) whose time per loop is at most a budget τ = `[ ]` s; or, continuously, log₂ of the state size handled within τ, from a fitted time–width curve | log (equivalently, n itself) | `[ ]` |
| M3 | Result quality | cross-entropy on the stand-in after a fixed wall-time budget `[ ]` (or a fixed number of loops `[ ]`), on `[ ]` test points; secondary quality figures are circuit duration and two-qubit gate count | difference (CE is not a ratio quantity) | `[ ]` |

**Owner's selection:**

- primary: `[ ]`;
- secondary: `[ ]`, adjusted by Holm at α = 0.01.

**Vanity and essential figures** (both always reported, side by side):

| | figure |
|---|---|
| Vanity | best-cell speed-up over the slowest cell, at the setting where it is largest |
| Essential | the gain a user gets at the setting they would actually run: CE reached per GPU-hour, or the reachable width at fixed time, with its cost |

## 6. Tested range (the claim covers only this)

- **Widths:** n ∈ `[ ]` (at least the 10 qubits PSF keeps).
- **Depths:** L ∈ {8, 16}.
- **Noise model:** the stand-in only.
- **GPUs:** `[ ]` (one model, or several, which widens the range statement of §7). All timings so far are from one H100 80 GB.
  - The GPU matters, not just the scale. Qiskit's traj2 simulator time over PSF's (68 circuits × 32 trajectories) was:

    | depth | RTX 4070 | H100 |
    |---|---|---|
    | L 8 | 5.3 × | 2.5 × |
    | L 16 | 7.4 × | 2.8 × |

  - Ten qubits do not fill an H100, so PSF's narrow circuits gain less from the larger GPU than Qiskit's 14-qubit
    circuits.
  - A claim tested on one GPU model therefore covers that model only.
- **Not tested:** real hardware (decision A is pending), 24 layers, other circuit families.

## 7. How the results are reported, and the interaction test

**The time metrics (M1, M2) are deterministic computations.** Repeated timings under the same conditions vary very
little, so almost any real difference reaches p < 0.01. A p-value therefore says little about the time metrics.

- **Main report for M1 / M2:** a statement of the range in which each result holds. For example: "the combination is
  the fastest cell at every (GPU, n, L) tested", or "it is fastest for n ≥ `[ ]` and L = 16 only; at n = `[ ]`, L = 8
  traj2 · PSF is faster by `[ ]` %". This is given as a table over GPU × n × L, with ratios and their spread across
  replicates.
  - **A real example of the form, from the pilot** (traj2 only, simulator part of a loop):

    > "PSF's circuits simulate faster than Qiskit's on both GPUs and both depths. The gap is 7.4 × on an RTX 4070 and
    > 2.8 × on an H100 at L = 16, and 5.3 × and 2.5 × at L = 8. On the H100 a 10-qubit simulation does not use the
    > GPU fully, so the gap narrows."

  - Whole-loop ratios are smaller still, because compile (CPU) and the stand-in do not scale with the GPU (§10).
- **Tests (kept, secondary for M1 / M2):** the interaction test below, at α = 0.01, with the caveat above.
- **M3 (CE)** depends on seeds and trajectories. For M3 the test is the main evidence.

**Log-scale model.** For each replicate r of cell (e, c), take y = log Y, where Y is the metric (for example seconds
per loop):

    y_ecr = μ + α_e + β_c + γ_ec + ε_ecr       (e ∈ {traj2, CUDA-Q}, c ∈ {Qiskit, PSF}; sum-to-zero constraints)

**Interaction contrast (the quantity tested):**

    I = (ȳ_CUDAQ,PSF − ȳ_CUDAQ,Qiskit) − (ȳ_traj2,PSF − ȳ_traj2,Qiskit)

- exp(I) is the ratio of the two PSF-vs-Qiskit speed ratios: PSF's gain on CUDA-Q divided by PSF's gain on traj2.
- exp(I) = 1 means no synergy: the effects simply multiply.
- For time (smaller is better), synergy means I < 0. For reach (larger is better), it means I > 0.
- A large interaction can also come from a ceiling or floor effect (for example, a small fixed per-call overhead in
  one engine). The time per loop is therefore broken down into compile, simulate and stand-in parts in the report.

**Replicates.** The replicate unit is `[ ]`. A proposal, for the owner: an independent loop sequence with its own seed
and random circuits; timings within one sequence are averaged first (the median of the log). That gives R = `[ ]`
replicates per cell. Run order is randomized and interleaved across cells. The first `[ ]` loops of each sequence are
warm-up and are excluded.

**Test.**

- A two-sided test of H0: I = 0 at α = 0.01, by OLS t-test of γ or by permutation of the additive model's residuals
  (`[ ]` permutations). Choice: `[ ]`.
- Reported: exp(I) with a 99 % confidence interval.
- Per (GPU, n, L): either one model with covariates (`[ ]`) or one test each with Holm correction (`[ ]`).
- **M3:** the same contrast on the raw CE scale.

## 8. Decision rule for dominance (Pareto)

- For each metric, compare the combination with each of the other three cells. **M3** uses a one-sided test at
  α = 0.01, Holm across comparisons and metrics. **M1 / M2** use the range statement of §7 plus the same test.
- **"At least as good"** means not worse by more than a margin δ_M (M1: `[ ]` %; M2: `[ ]` qubits or layers;
  M3: `[ ]` in CE), declared now.
- **"Better"** means better beyond the margin on at least one metric.
- **Outcomes:**
  - Pareto-superior (and in which part of the range).
  - Not superior: a cell is better on some metric, beyond its margin.
  - Undecided.

## 9. Seeds, sample sizes, stopping

- **Seeds:** `[ ]`, disjoint from every earlier range. Already used: 9001-9020, 101-102.
- **Replicates per cell R:** `[ ]`, from the pilot's variance.
- **Interruptions:** a run that fails is restarted from its start with the same seed. The first completed record per
  seed is the one scored.
- **No change** to cells, settings (§3, §4), metrics or margins after the first scored run.

## 10. Values from the pilot (to fill in before fixing)

| item | traj2 · Qiskit | traj2 · PSF | CUDA-Q · Qiskit | CUDA-Q · PSF |
|---|---|---|---|---|
| time per loop, L = 8 (s) | `[ ]` | `[ ]` | `[ ]` | `[ ]` |
| time per loop, L = 16 (s) | `[ ]` | `[ ]` | `[ ]` | `[ ]` |
| H100: traj2 simulator, 68 circuits × 32 traj, L = 8 / 16 (s) | 0.81 / 1.61 | 0.32 / 0.58 | `[ ]` | `[ ]` |
| H100: stand-in, 2 circuits × 100 shots, L = 8 / 16 (s) | 0.14 / 0.28 | 0.13 / 0.25 | – | – |
| compile, 68 circuits, L = 8 / 16 (s, CPU) | 0.17 / 0.31 | 0.26 / 0.62 | (same as traj2) | (same as traj2) |
| H100 / RTX 4070 speed-up of the simulator, L = 8 / 16 | 4.8 × / 5.0 × | 2.3 × / 1.9 × | – | – |
| H100: S2R2-B loop estimate from the components, L = 8 / 16 (s) | 1.09 / 2.14 | 0.69 / 1.42 | `[ ]` | `[ ]` |
| width actually simulated (qubits) | 14 (both depths; to re-check under the §4 setting) | 10 | `[ ]` | `[ ]` |
| CUDA-Q runs on the H100 | – | – | yes (0.15.1, target `nvidia`; 0.16.0 fails on general Kraus channels) | yes |
| CUDA-Q agrees with traj2 (§2 gate, N1-N4; `check_cudaq`) | – | – | PASS (≤ 1.66 se) | PASS (≤ 1.66 se) |
| same H100, 68 circuits × 32 traj (training-step shape), L = 8 / 16 (s; one measurement each) | traj2 0.80 / 1.70 | traj2 0.41 / 0.59 | 51.8 / 102.2 | 42.6 / 86.5 |
| same H100, 1 circuit × 4,096 traj, L = 8 / 16 (s) | traj2 1.58 / 3.16 | traj2 0.77 / 1.00 | 1.83 / 3.72 | 0.75 / 1.40 |
| Qiskit / PSF time ratio, 68 × 32, L = 8 / 16 | traj2: 2.0 × / 2.9 × | | CUDA-Q: 1.2 × / 1.2 × | |
| Qiskit / PSF time ratio, 1 × 4,096, L = 8 / 16 | traj2: 2.1 × / 3.2 × | | CUDA-Q: 2.4 × / 2.7 × (r4: mostly the per-call cost, about 0.24 ms per inline noise operation, not the simulation; not a measure of PSF's saving on CUDA-Q) | |
| CUDA-Q first call (2 circuits × 8,192 traj, kernel build included), twin / stand-in model, L = 8 / 16 (s) | – | – | 10.3 / 15.8; 23.2 / 40.1 | 4.4 / 7.3; 10.2 / 18.6 |
| gradient agreement, simulator vs stand-in (cos), means 5 / 6, L = 8 | 0.80 / 0.85 | 1.00 / 1.00 | – | – |
| gradient agreement, simulator vs stand-in (cos), means 5 / 6, L = 16 | 0.87 / 0.97 | 0.97 / 0.99 | – | – |
| stand-in gradient size ÷ simulator's | 0.34-0.50 (L 8), 0.81 (L 16) | 0.74-0.79 | – | – |

## 11. What this test cannot conclude

- Anything about real hardware (decision A is pending).
- The behaviour of untested engines, compilers, Qiskit settings, widths, depths or noise models.
- "The only solution".
- If the agreement between the simulator and the stand-in stays near 0.99, any gain in M3 is the simulator's, not
  the stand-in's information. This is recorded as in S2R2-B.
