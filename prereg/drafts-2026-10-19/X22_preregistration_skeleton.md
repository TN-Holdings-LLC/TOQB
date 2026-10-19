# X22: pre-registration skeleton — engine × compiler (2 × 2), hybrid quantum-AI scaling

**Status: skeleton, not fixed.** Values marked `[ ]` are filled in after the pod pilot (speed, CUDA-Q first test,
gradient agreement for both compilers at 8 and 16 layers). The document is then fixed by SHA-256 and the CEST time
before any scored run. Revised at the workplace on 2026-10-19 (design text only; nothing was run).

**Revision 2026-10-19.** Added §3 (engine fairness) and §4 (the Qiskit setting, an owner decision). Rewrote §7 so
that the time metrics report the range in which the result holds as the main result. Made the noise-model gate (§2)
explicit for four channels.

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
| E (simulation engine) | `traj2` (TOQB's own trajectory engine) · `CUDA-Q` (version `[ ]`, settings fixed by §3) |
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
| N1 | amplitude damping (non-unitary; Kraus operators, per gate, from T1) | `[ ]` | `[ ]` | `[ ]` |
| N2 | thermal relaxation while idle (from T1/T2 and each qubit's idle time in the schedule) | `[ ]` | `[ ]` | `[ ]` |
| N3 | static ZZ crosstalk (10 kHz between coupled qubits, accumulated over time, idle included) | `[ ]` | `[ ]` | `[ ]` |
| N4 | sx / x over-rotation (coherent, `over` = 0.01) | `[ ]` | `[ ]` | `[ ]` |

- **Rule (unchanged):** if any channel cannot be expressed exactly, the experiment stops and the gap is reported. The
  noise model is not changed to fit, and no approximation is substituted.
- **Then, numerically:** on `[ ]` fixed circuits per compiler and depth, CUDA-Q's outcome distributions must agree
  with traj2's within `[ ]` standard errors. This is the same test traj2 passed against the density matrix, at most
  1.36 se.
- Result of the first CUDA-Q test: `[ ]`.

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

| CUDA-Q setting | value fixed | alternatives tried in the pilot |
|---|---|---|
| version | `[ ]` | – |
| target | `[ ]` | `[ ]` |
| precision | `[ ]` | `[ ]` |
| trajectory batching | `[ ]` | `[ ]` |
| other options / environment | `[ ]` | `[ ]` |
| tuning time used | `[ ]` h | budget `[ ]` h |

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
- **GPUs:** `[ ]` (one model, or several, which widens the range statement of §7).
- **Not tested:** real hardware (decision A is pending), 24 layers, other circuit families.

## 7. How the results are reported, and the interaction test

**The time metrics (M1, M2) are deterministic computations.** Repeated timings under the same conditions vary very
little, so almost any real difference reaches p < 0.01. A p-value therefore says little about the time metrics.

- **Main report for M1 / M2:** a statement of the range in which each result holds. For example: "the combination is
  the fastest cell at every (GPU, n, L) tested", or "it is fastest for n ≥ `[ ]` and L = 16 only; at n = `[ ]`, L = 8
  traj2 · PSF is faster by `[ ]` %". This is given as a table over GPU × n × L, with ratios and their spread across
  replicates.
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
| width actually simulated (qubits) | `[ ]` | `[ ]` | `[ ]` | `[ ]` |
| CUDA-Q agrees with traj2 (§2 gate, N1-N4) | – | – | `[ ]` | `[ ]` |
| gradient agreement sim vs stand-in (cos), L = 8 / 16 | `[ ]` | `[ ]` | – | – |

## 11. What this test cannot conclude

- Anything about real hardware (decision A is pending).
- The behaviour of untested engines, compilers, Qiskit settings, widths, depths or noise models.
- "The only solution".
- If the agreement between the simulator and the stand-in stays near 0.99, any gain in M3 is the simulator's, not
  the stand-in's information. This is recorded as in S2R2-B.
