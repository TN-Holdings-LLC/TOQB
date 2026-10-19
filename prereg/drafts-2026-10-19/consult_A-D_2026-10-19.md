# Instruction 4, points A-D: options and grounds for the owner (2026-10-19)

**Status.** Written at the workplace, 2026-10-19, 10:00 CEST. This is advice, not a decision: every point is the
owner's. The workplace ran nothing on a GPU and nothing on IBM. The model calculations for C were done in the
workplace's cloud sandbox (script `pn_power2.py`, attached).

**Sources.**

- The numbers come from instruction 4.
- Some definitions were read from the TOQB bundle of 2026-10-19 (`toqb/s2rc.py`, `toqb/cudaq_engine.py`,
  `toqb/check_cudaq.py` and the result notes). The bundle was read only; no code from it was run.

**Two facts from the code that the points below depend on.**

1. **"P(1) rms" in the learning-rate table** is the rms of twin P(1) − stand-in P(1). The stand-in's value is its
   *exact* P(1), a mean over many trajectories (`twin_vs_standin_p1_rmse`, from `z_dev_exact`); it is not the
   1,000-shot estimate. On a device only the shot estimate exists. Shot noise alone adds about 0.5/√N per point
   (0.016 at N = 1,000; 0.032 at N = 250). That is larger than PSF's 0.006-0.010. This matters for H2 (point C).
2. **The CUDA-Q wrapper already builds one kernel per circuit structure,** with the slot angles as a `list[float]`
   argument (`CudaqEngine.kernel`, cached per plan). The 68 × 32 timing was taken after that kernel had already been
   built and called during the agreement step. So the 42.6-102.2 s are not first-call costs (point A).

---

## A. X22: fairness of the CUDA-Q engine

### A1. A rule for "each engine in its best use"

Proposed text for X22 §3 (it is also put into X22 r3 as a proposal):

**F1. Same model first.**

- The noise-model gate (§2) must pass with the exact call pattern that is timed.
- It passed on 2026-10-19 with the current pattern: largest deviation 1.66 se against a limit of 4 se.
- Any change to the call pattern repeats `check_cudaq` before it is timed.

**F2. Equal precision, not only equal trajectory count.**

- CUDA-Q records one ±1 shot per trajectory, so its variance per trajectory is 1 − z². traj2 averages each
  trajectory's exact P(1), so its variance per trajectory is Var_j(z_j) ≤ 1 − z².
- At equal T, CUDA-Q's estimate is therefore noisier.
- **Proposal:** report time at equal T and time at equal standard error of ⟨Z⟩, with T_CUDA-Q = T_traj2 · (1 − z̄²) /
  Var_j(z_j), the ratio measured on pilot circuits. The owner chooses which one is primary (`[ ]`).

**F3. Best use per workload shape, from a short list declared in advance.**

- Before any timing, the CUDA-Q call patterns are listed (A2 has the candidates; at most 4). Each is a documented use
  of the CUDA-Q API.
- Each is timed once on pilot seeds, after the F1 check.
- The fastest pattern that passes F1 is fixed for the scored runs, and every pattern tried is listed with its time.
- **"Best" means:** the lowest median wall time of the training-step shape (68 circuits × 32 trajectories, or the
  F2-equivalent trajectory count), warm, over 5 repeats.
- First-call time is reported separately and amortized over the run's loops (F5).
- **Alternative for the owner,** if a choice by measurement among patterns counts as the kind of search the owner's
  policy excludes: fix the pattern by documentation alone (CUDA-Q's documented batch interface), with no timing-based
  choice.

**F4. A cap on the effort.** The cap is `[ ]` engineering hours and `[ ]` pod hours (proposal: about 1 working day and
2 pod hours).

- The cap is stated with the result.
- If CUDA-Q is still slower when the cap is reached, the result is reported as "with the best pattern found within
  the cap, CUDA-Q was X × slower on this shape". It is not reported as a limit of CUDA-Q.

**F5. Cold and warm are reported separately for both engines:**

- the first-call (kernel build or JIT) time per structure;
- the warm time per call;
- their total over a full run of N loops.

**F6. traj2 is frozen too.**

- traj2 is fixed at a commit before CUDA-Q's tuning starts, so that the comparison is not against a moving target.
- traj2's own earlier hand-tuning is disclosed as in §3.3.

**F7. Versions.** CUDA-Q 0.15.1 (0.16.0 fails on general Kraus channels), target `nvidia`. The precision is recorded
(`[ ]`; the default single precision matches traj2's complex64).

### A2. Improving the calls

**What the timings say.**

| | PSF L 8 | Qiskit L 8 | PSF L 16 | Qiskit L 16 |
|---|---|---|---|---|
| 68 × 32, CUDA-Q (s) | 42.6 | 51.8 | 86.5 | 102.2 |
| per call (÷ 68) | 0.63 | 0.76 | 1.27 | 1.50 |
| 1 × 4,096, CUDA-Q (one call) | 0.75 | 1.83 | 1.40 | 3.72 |

- **A call costs about the same at 32 trajectories as at 4,096** (PSF L 8: 0.63 s against 0.75 s). The cost grows
  with circuit length: L 16 costs about 2 × L 8.
- **Likely reading: a fixed cost on every call,** for example processing the kernel or noise model on each call
  rather than simulating. This is inferred from the numbers and not checked.
- **This is not the 4-40 s "first call".** Those were the two 8,192-trajectory calls of the agreement step, including
  the kernel build.
- **Consequence.** The improvement suggested in the instruction ("one kernel per structure, angles as arguments") is
  already in the wrapper, so it does not explain the cost. The remaining lever is the number of calls, or whatever
  processing happens on each call.

**Candidates** (each unverified on this pod; at most 4 go into the F3 list):

| # | change | expected effect if the fixed cost is per call | risk |
|---|---|---|---|
| C1 | broadcast: pass all 68 argument sets in one `cudaq.sample` call | 68 calls → 1; large gain if the cost is on the host side or at launch | it may still process each argument set separately; broadcasting a `list[float]` argument under a noise model needs a check |
| C2 | compile each structure once as a `@cudaq.kernel` (generated source) instead of the `make_kernel` builder | removes repeated lowering, if the builder repeats it on every call | code generation per structure; must pass F1 again |
| C3 | gate-attached noise (noise model keyed to gate type and qubits) instead of inline `apply_noise` | may let the kernel be prepared once | the channels must stay exactly traj2's (gate-attached amplitude damping is known to work on 0.15.1) |
| C4 | `sample_async` with several calls in flight | overlaps host work with GPU work | helps only if the cost is host-side and can run in parallel |

**Measurements after any change** (same H100, GPU otherwise idle):

1. 68 × 32 and 1 × 4,096 wall times, warm, median of 5 repeats.
2. The number of distinct structures per training step and per run. One per cell is expected, because the template
   fixes the structure.
3. First-call time per structure, in a fresh process (kernel build plus first execution).
4. The fixed cost per call against the cost per trajectory: the same kernel called 10 times each at T = 1, 32, 256
   and 4,096. Fitting a line gives the intercept (fixed per call) and the slope (per trajectory).
5. Calls per training step (68 now; 1 with C1).
6. The F2 variance ratio Var_j(z_j) / (1 − z̄²) on the same circuits.
7. A whole training loop, compile included, for both engines: 2 warm-up loops, then the median of 20.
8. `check_cudaq` again (F1), with the pattern being timed.

---

## B. Placement confound in design C's PSF-vs-Qiskit comparison

**The confound.** Compiled against the Marrakesh calibration, Qiskit level 2 chooses its qubits using the calibrated
error rates. PSF's template places its circuit by the coupling map alone.

- In the tuning run Qiskit reached the lower stand-in CE: 0.535 against 0.581 at L 8, 0.613 against 0.640 at L 16
  (lr 0.4).
- In B's FakeFez pilot the order was the reverse.
- So the PSF-vs-Qiskit difference mixes compression and placement. Placement is the likely cause; it is not checked.
- None of the options below changes C's hypotheses H1 and H2 or their tests. Options 2 and 3 add or change an arm,
  which is the owner's decision.

| | 1. As is, record only | 2. Control arm: PSF on Qiskit's qubits | 3. Calibration-aware placement in PSF-Zero |
|---|---|---|---|
| What changes | nothing; the placement of each arm is recorded (physical qubits, summed calibrated error) | 2 more cells: PSF L 8 / L 16 compiled onto the physical qubits of Qiskit's initial layout | PSF-Zero's placement picks the qubits from the day's calibration |
| Pod time, training | 0 | + 3.6 s per loop pair (PSF-sized circuits) = +24 % of the 15.0 s total; rehearsal (3 seeds, 2,000 loops) about +1.0 GPU-h; main run M = 5 about +1.7 GPU-h | none in C itself; development and validation (exactness, unchanged structure) at home or on the pod; possibly a lr re-check for the PSF cells (about 0.5 GPU-h) |
| Device job | unchanged | +2 cells, +50 % (for example +$195.84 at P = 200, N = 1,000, M = 1) | unchanged |
| What can be claimed | "PSF-Zero as it is (placement by the coupling map) against Qiskit level 2 (calibration-aware)": a whole-pipeline comparison; H2 or CE differences cannot be attributed to compression | splits the difference: placement effect = PSF(Qiskit's qubits) − PSF(own); compression effect = Qiskit − PSF(Qiskit's qubits), on the same qubits. The strongest attribution | "calibration-aware PSF against calibration-aware Qiskit": closer to like for like, and PSF may also gain absolute CE; but two different placement methods remain, so it does not split the effects cleanly. Combined with 2, it is the cleanest and the most expensive |
| Main risk | the comparison reads as unfair to PSF (or to Qiskit, under FakeFez) | Qiskit's layout must contain the structure PSF's template needs on 10 qubits (Qiskit uses 14 qubits, including routing). If it does not, a rule declared in advance applies: the arm is reported as not buildable, with no fallback search | a change to PSF-Zero itself, which needs its own validation; it conflicts with an earlier owner rule (below) |

**Variant 2′ (for completeness): Qiskit on PSF's qubits** (`initial_layout` = PSF's placement).

- It is always buildable and separates the same two effects from the other side.
- It is more expensive: Qiskit-sized circuits cost 11.4 s per loop pair, about +76 % training time.

**Option 3, written as a formula (as asked).**

- Let φ be an embedding of the template's fixed qubit structure into the coupling map. Let the counts come from the
  fixed template: n_e two-qubit gates on logical edge e, n_q one-qubit gates on qubit q, and idle time τ_q.
- The predicted error of φ, from the day's backend.target, is:

      E(φ) = Σ_e n_e ε_cz(φ(e)) + Σ_q [ n_q ε_sx(φ(q)) + ε_readout(φ(q)) + τ_q (1/T1 + 1/T2)(φ(q)) ]

  This is the first-order expansion of −log ESP, plus the idle terms.
- **Exact minimization.** For a chain, the minimum over φ is exact by dynamic programming over paths of fixed length
  (deterministic: no random restarts, no simulation, no tuning). For a ring, the cycles of the required length are
  enumerated and E is evaluated on each.
- **Two things for the owner to judge:**
  - (i) Whether an exact argmin over a finite set (by dynamic programming or enumeration) counts as "solving by a
    formula" or as the search the policy excludes.
  - (ii) This is an ESP-type criterion. An earlier owner rule in this project said: no selection by ESP or by
    simulation, and no proposals that use calibration data. This instruction asks for option 3 explicitly. Adopting
    it needs the owner to lift that rule explicitly for placement.

**Workplace view (not a decision).**

- Option 1 is enough for C's H1.
- For H2 and the "PSF makes the twin faithful" message, the placement confound is the main threat. Option 2 removes
  it for about +24 % of pod time and +50 % of QPU cost, without touching PSF-Zero.
- Option 3 is a product change and is better decided separately from C.

---

## C. Design C: choosing P and N (device cost)

**Formulas.**

- Cost per cell: P × (0.036 + N × 0.00027) s × $1.60/s. The time model is the workplace's estimate; the price is
  IBM's.
- Accuracy needs only the sign of the measured ⟨Z⟩. A point whose label-side probability is c = ½ + d is correct with
  probability A_N(d) = P(Binomial(N, c) > N/2), with ties counted wrong.
- Over the test points, a(N) = ∫ f(d) A_N(d) dd. For a margin density f that is smooth near 0:

      a(N) ≈ a(∞) − f′(0) / (8 N)

- **So cutting N lowers accuracy only through the few points with |d| ≲ 1/√N,** and the loss falls like 1/N. In the
  scenarios below (d normal with sd σ = 0.12, or 0.06 as a sharper case), the loss from N = 1,000 to N = 250 is
  0.006-0.008 (σ 0.12) or 0.014-0.024 (σ 0.06).

**Caveats.**

- f is not known. A normal margin model cannot match the pilot's CE and accuracy together: real margins have heavier
  tails. So the scenarios are set by accuracy alone.
- f(0) and f′(0) can be estimated without a new run from the records already on the pod (`twin_p1` and `standin_p1`
  per test point).
- The device's accuracy may be lower than the stand-in's.

**H1: power at L 16.**

- One-sided exact binomial; the probability that a cell reaches significance.
- With both L 8 cells far above chance, the L 16 cells meet Holm's levels α/2 = 0.005 and then 0.01. The worst case,
  α/4 = 0.0025, is in brackets.
- σ = 0.12.

| a(1,000) | N | P = 200 | P = 300 | P = 500 |
|---|---|---|---|---|
| 0.56 | 250 / 500 / 1,000 | 0.14 / 0.16 / 0.18 (0.08-0.11) | 0.23 / 0.28 / 0.30 (0.17-0.23) | 0.41 / 0.48 / 0.52 (0.34-0.45) |
| 0.60 | 250 / 500 / 1,000 | 0.51 / 0.56 / 0.59 (0.39-0.47) | 0.74 / 0.79 / 0.81 (0.66-0.74) | 0.94 / 0.96 / 0.97 (0.91-0.95) |
| 0.62 | 250 / 500 / 1,000 | 0.72 / 0.77 / 0.79 (0.62-0.70) | 0.91 / 0.93 / 0.95 (0.86-0.91) | 0.99 / 1.00 / 1.00 (0.99-1.00) |

- **Accuracy needed for p < 0.0025 / 0.005 / 0.01:**
  - P = 100: 0.65 / 0.64 / 0.63
  - P = 200: 0.605 / 0.595 / 0.585
  - P = 300: 0.583 / 0.577 / 0.570
  - P = 500: 0.564 / 0.560 / 0.554
- **H1 at L 8** (a = 0.69 PSF, 0.72 Qiskit; α = 0.0025): power 0.78-0.84 / 0.93-0.95 at P = 100, ≥ 0.95 at P = 150,
  ≥ 0.99 at P = 200.

**H2: power** (one-sided paired t over the P points, α = 0.005; Wilcoxon is similar).

- **Simulation model:** e = |p̂ − p1|. The model deviation per point is drawn from Normal(0, δ²), and the shot noise
  from Normal(0, 1/(4N)).
- **The δ values are scenarios.** PSF 0.008 with Qiskit 0.015 or 0.020 is like the stand-in at L 16, and Qiskit 0.047
  is like L 8. The last row, both larger, is a plausible device case.

| δ_PSF, δ_Qiskit | N = 250 (P 200 / 300 / 500) | N = 500 | N = 1,000 |
|---|---|---|---|
| 0.008, 0.015 | 0.05 / 0.07 / 0.14 | 0.18 / 0.29 / 0.51 | 0.54 / 0.76 / 0.96 |
| 0.008, 0.020 | 0.21 / 0.35 / 0.62 | 0.68 / 0.88 / 0.98 | 0.98 / 1.00 / 1.00 |
| 0.008, 0.030 | 0.89 / 0.98 / 1.00 | 1.00 | 1.00 |
| 0.008, 0.047 | 1.00 | 1.00 | 1.00 |
| 0.030, 0.045 | 0.68 / 0.88 / 0.99 | 0.91 / 0.98 / 1.00 | 0.97 / 1.00 / 1.00 |

- **With M = 5 models averaged per point:** δ 0.008 / 0.015 gives 0.32 / 0.78 at N = 250 (P 200 / 500), and 1.00 at
  N = 1,000.
- **N matters for H2 because the shot floor 0.5/√N swamps small deviations.** P matters for H1.
- **One statistic note (owner's choice; it would change the statistic, not the hypothesis).** Squared errors with the
  shot term subtracted, (p̂ − p1)² − p̂(1 − p̂)/(N − 1), remove the floor in expectation. They might gain power at small
  N. Not evaluated.

**Cost** (M = 1; multiply by M):

| P | N = 250: cell / 4 cells | N = 500 | N = 1,000 |
|---|---|---|---|
| 100 | $16.56 / $66.24 | $27.36 / $109.44 | $48.96 / $195.84 |
| 200 | $33.12 / $132.48 | $54.72 / $218.88 | $97.92 / $391.68 |
| 300 | $49.68 / $198.72 | $82.08 / $328.32 | $146.88 / $587.52 |
| 500 | $82.80 / $331.20 | $136.80 / $547.20 | $244.80 / $979.20 |

**Different P for L 8 and L 16** (4 cells, M = 1):

| P_8, P_16 | N = 250 | N = 500 | N = 1,000 |
|---|---|---|---|
| 100, 300 | $132.48 | $218.88 | $391.68 |
| 100, 500 | $198.72 | $328.32 | $587.52 |
| 200, 300 | $165.60 | $273.60 | $489.60 |
| 200, 500 | $231.84 | $383.04 | $685.44 |

**Example settings, side by side** (scenario a_16 = 0.60; H2 shown for the L 16-like gap 0.008 / 0.015; the L 8-like
gap gives about 1.00 everywhere):

| setting | cost (M = 1) | H1 power, L 16 (α 0.005) | H1 power, L 8 (α 0.0025) | H2 power, L 16-like |
|---|---|---|---|---|
| P_8 200, P_16 500, N 500 | $383.04 | 0.96 | ≥ 0.99 | 0.51 |
| P_8 200, P_16 500, N 1,000 | $685.44 | 0.97 | ≥ 0.99 | 0.96 |
| P_8 100, P_16 300, N 1,000 | $391.68 | 0.81 | 0.84-0.95 | 0.76 |
| P_8 200, P_16 300, N 500 | $273.60 | 0.79 | ≥ 0.99 | 0.29 |
| all P 500, N 1,000 (current upper case) | $979.20 | 0.97 | ≈ 1.00 | 0.96 |

- **Reading.**
  - For H1, P at L 16 is what costs; N can drop to 500 with little loss.
  - For H2 at L 16, small gaps need N = 1,000, or M > 1.
  - So the choice depends on whether H2 at L 16 must be powered.
- **These are model scenarios from the stand-in.** On a device, accuracy may be lower and deviations larger. A device
  L 16 accuracy at or below 0.56 leaves H1 at L 16 unlikely at any P considered here.
- **Pooling M models in H1** (option (a) of C §2) multiplies the trials by M. Whether pooled points count as
  independent is the open owner question in C §2.

---

## D. The rehearsal (seeds 201-203, 2,000 loops, P = 500, lr 0.4): tonight, or after A and B

**What A and B can change.**

- A concerns X22's engine, not C. C's twin is traj2, so A does not change the rehearsal unless the owner also wants
  CUDA-Q in C.
- B-1 changes nothing.
- B-2 adds two control cells. They can be run later with the same seeds, about +1.0 GPU-h.
- B-3 changes the PSF cells: their 2 of 4 runs per seed, about 24 % of the time, would be rerun after PSF-Zero changes
  and is validated.

| | Run tonight | Run after A and B are decided |
|---|---|---|
| For | finds procedure faults (check (a)) a day earlier; gives measured 2,000-loop times for C §5's time limit; gives 2,000-loop accuracy on 500 points per cell (better inputs for point C's power); shows whether Qiskit L 8 stays outside the interval; the GPU is otherwise idle | the rehearsal matches the final design in one go; nothing is rerun; B is decided before more stand-in results are seen |
| Against | if B-3 is chosen, about 24 % is redone (about $6-10); if B-2, the control cells are added later (not all in one run); the (b) results are seen before B is decided, which could colour that decision | (a)'s faults are found later; C §5 and point C stay on B's and the tuning run's numbers for another day; the GPU sits idle |
| Cost | $24-40 now, plus at most about $10 later | $24-40 (+ control cells if B-2) |

**Workplace view (not a decision).**

- Running tonight costs little to undo. The B options affect only the PSF part or add cells.
- Its main product, the procedure check, does not depend on A or B.
- If it runs tonight, the order is recorded ("rehearsal run before decision B"), so that seeing its (b) results first is
  on record.
