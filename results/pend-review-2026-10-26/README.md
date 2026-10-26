# Workplace review of `fold:pend` and the "time order" design (2026-10-26 01:01 CET)

**Scope.** This answers 依頼書_職場Claude_2026-10-26 (requests 1 and 2).

- **Code reviewed:** `toqb_full_2026-10-26a.bundle`, main = `94b442c`; `toqb/fold.py` (`pend_place`,
  `pend_circuit`) and `tests/test_fold.py`.
- **No code in TOQB was changed.** The review scripts are separate files, `review/r1`-`r6`.
- **Environment:** qiskit 2.5.2 and the snapshot:marrakesh Target. Everything is simulation and counting; nothing
  ran on a device.
- **Baseline:** `pytest tests/test_fold.py`: 8 passed.

Each item is marked **verified** (measured here) or **inferred** (reasoning, not measured).

## Request 1: independent review of pend

### 1. Exactness and dead ends of `pend_circuit`

**Verified:** exact for every pendant placement with k < m, where k = n − m is the number of pendants.

| check | scope | result |
|---|---|---|
| statevector, every clbit | synthetic cycles m = 3-8, every pendant subset, n ≤ 13, L = 1, 2, 3; 1,398 cases | worst clbit distance 5.2e-15 |
| structural replay (each ring edge exactly one CZ per layer, single-qubit gates on the qubit holding their ring node, measurements on the right qubit) | every pendant subset for m = 3-12, n up to 23, L = 3; 8,184 cases | no error |

- **Covered cases** include pendants on adjacent cycle nodes, a pendant on the last cycle position (the ring's seam
  n−1 → 0), a pendant on position 0, and pendants on both seam positions.
- **Script check.** The structural checker agrees with the statevector check on every case where both ran.

**Verified: one dead end.** When every cycle node carries a pendant (k = m, n = 2m), `pend_circuit` raises
"pend: no schedule step left" for every m (10 of 10 cases).

- **Cause:** each block waits for its node's other ring edge, which waits for the neighbouring block, all the way
  round the cycle.

**Inferred: unreachable on heavy-hex.** The bridge and end nodes of a cycle have no outside neighbour, so k < m.

- **Observed on snapshot:marrakesh:** at most 6 spots on a 12-cycle; n = 18 used 6.
- **Suggestion:** a guard with a clear message, below.

**Reproduce:**

```
python review/r1_exhaustive.py TOQB 8     # statevector; prints only the k = m refusals
python review/r2_structural.py TOQB 12    # structural; "refused or wrong 10 (all-pendant cases k = m: 10)"
```

### 2. The decomposition H(b), CX(b,a), CX(a,b), H(a)

**Verified.** It equals CZ followed by SWAP exactly, global phase included, for both qubit orders (`Operator`
comparison in `review/r6_decomp.py` (a)).

### 3. Two-qubit count n + (n − m) per layer

**Verified,** for every pendant subset with k < m, m = 3-12: the count is L·(n + k) = L·(2n − m), and every two-qubit
gate lies on a physical edge (a cycle edge or a node-pendant edge; r1).

- **Arm check.** On snapshot:marrakesh the transpiled arm gives the same count for n = 13-18 (as `tests/test_fold.py`
  for 13, 15, 17).

**Inferred: why it holds in general.** Each pendant does exactly one block per layer, covering one ring edge with 2
two-qubit gates; the other n − k edges are plain CZs.

### 4. Failed elements in `pend_place`

**Verified on snapshot:marrakesh:** no failed element is used. Failed there: cz on (82, 83), (95, 99), (112, 113),
(113, 114), (113, 119), (129, 130), (130, 131), and sx/x on 82, 94, 113, 130.

- **Compiled output:** for n = 13-18, L = 4 and all three modes (pend, pendpack, pendbind), no instruction lands on a
  failed element.
- **Mutated targets.** Setting error = 1 on the pendant's coupler cz(3, 2), on measure(2) or on sx(2) moves the
  pendant: n = 13 then uses {4: 8} instead of {0: 2}.

**Inferred: two theoretical gaps.** Neither has any effect on snapshot:marrakesh.

- **Directional failures.** `edges` keeps a pair if either direction works (`tuple(sorted(qa))`). If only one
  direction had failed, the transpiled CX could land on it. In the snapshot both directions fail together, and every
  pair lists both directions. `fold_place` has the same pattern.
- **The `x` gate is not checked separately from `sx`.** In the snapshot they fail on the same qubits.

### 5. Other points before the λ comparison

| # | point | type |
|---|---|---|
| a | **The k = m dead end.** Add a guard at the start of `pend_circuit`: `if len(pend) >= m: raise FoldRefused("pend: every cycle node has a pendant (k = m); no schedule")`. This changes nothing reachable on heavy-hex. | verified (the dead end); suggestion |
| b | **n = 18 moves to another 12-cycle** (qubits 21, 36, 41-45, 37, 25, 24, 23, 22), because the first cycle (3-7, 17, 27-23, 16) has only 5 spots. A λ step between n = 17 and n = 18 can come from the location, not the schedule. The comparison's reading should say so. | verified (placement); inferred (effect) |
| c | **`pend_place` gives up a whole cycle** when a chosen spot's outside neighbours are all taken, without trying the other spots. This can cause an unnecessary refusal; no case on snapshot:marrakesh for n = 13-18. | inferred |
| d | **The hubs carry the circuit.** Cycle nodes with a pendant do 4 CZ per layer and 3 extra non-mergeable single-qubit gates (5.1 sx per layer, against 2.1 elsewhere), and the circuit's duration equals their busy time (section B). The hub qubits are chosen by index, consistent with the formula principle. A poor hub qubit would therefore dominate λ; this is a reading point, not a reason to change. | verified (counts); inferred (λ) |
| e | **Test coverage.** `tests/test_fold.py` tests n = 13, 15, 17 on one device. Adjacent pendants, both seam positions and n = 14, 16, 18 are untested there. r1 and r2 could become tests (r2 runs every subset to m = 12 in about 30 s). | verified |
| f | **Independent check of "no heavy-hex cycle between 12 and 20".** All simple cycles up to length 22, enumerated by DFS: snapshot:marrakesh 21 of length 12 and 44 of length 20; FakeMarrakesh the same; FakeTorino 18 and 37. No other lengths. | verified |

## Request 2: the "time order" version (design only; for the owner's decision)

### B1. Waiting time per qubit, as emitted today

**Method.**

- Target durations: cz 68 ns (68-96), sx 36 ns, rz 0.
- Idle = time between a qubit's first and last non-measure operation not spent in its own gates.
- L = 16 (`review/r3_idle.py`, `r4_bound.py`, `r5_asap_alap.py`).

| n | duration, with measure | duration, without measure | hub busy time | idle, sum over the n qubits | idle per qubit, mean | idle per qubit, worst (qubit) |
|---|---|---|---|---|---|---|
| 13 | 10.180 µs | 7.496 µs | 7.50 µs | 40.7 µs | 3.13 µs | 4.10 µs (cycle 16) |
| 14 | 10.180 | 7.50 | 7.50 | 43.5 | 3.11 | 4.10 (cycle 16) |
| 15 | 10.372 | 7.688 | 7.30-7.69 | 45.0 | 3.00 | 4.29 (cycle 6) |
| 16 | 10.372 | 7.69 | 7.30-7.69 | 44.4 | 2.78 | 4.29 (cycle 6) |
| 17 | 10.372 | 7.688 | 7.30-7.69 | 44.2 | 2.60 | 4.29 (cycle 6) |
| 18 | 10.244 | 7.560 | 7.30-7.56 | 43.0 | 2.39 | 3.90 (cycle 42) |

- **Who waits:** the plain cycle nodes, especially those next to a hub. They are busy about 3.4-3.7 µs of the 7.5 µs
  window and idle about 3.5-4.3 µs. Pendant qubits are busy about 4.0-4.4 µs.
- **The duration matches home's figures** (10.2-10.4 µs).

### B2. The lower bound, and why reordering does not help

**Verified: the duration is already at the per-qubit bound.** Without measure it equals the busiest hub qubit's own
gate time (7.496 against 7.50 µs at n = 13; 7.69 against 7.69 at n = 15-17). No order of the same gates can make it
shorter.

**Verified: the hub's chain is forced within a layer.** For a hub holding ring node u, with its pendant holding v:

1. the plain CZ (u−1, u) must come before the block, because u leaves the cycle in the block;
2. the block (u, v) follows;
3. the plain CZ (v, w) needs v on the cycle, so it comes after the block.

Four CZ per layer run in a row on the hub; the odd layers are the mirror image.

**The three interior single-qubit gates on the hub** (before, inside and after the block) are each 1 sx today.

- **Numerical check:** no 2-CZ decomposition of CZ·SWAP was found with a diagonal hub-side gate before or after the
  block. Such a gate would commute with the plain CZs and merge into the layer gates for free.
- **Evidence:** least-squares residual 1.17 in all three constrained cases, against 1.7e-29 unconstrained; 300
  restarts each (`r6_decomp.py` (b)).
- **This is numerical, not a proof.** If it holds, the hub's 3 extra sx per layer are the minimum for this chain.

### B3. Rules considered and their estimates

| rule (formula only: depends on the ring and the pendant positions, no error values, no search) | duration, L 16 | idle sum |
|---|---|---|
| as emitted (reference) | 10.18-10.37 µs | 40.7-45.0 µs |
| **R1 "chain edge first"**: on each cycle node, among the commuting plain CZs ready in a step, emit first the one whose completion unlocks a pendant block | unchanged (all n) | +0.0 to +2.3 µs (n = 13: 43.0 against 40.7) |
| **R2 "single-qubit gates ALAP"** | unchanged | unchanged: every qubit acts in the first and the last layer, so only the gaps inside move (r5: ASAP and ALAP give the same idle for n = 13-18) |
| **R3 "blocks as early as possible"** | already the case: `pend_circuit` emits each block in the first step where its other edge is done, and the DAG then runs it as soon as its qubits are free | – |

**Reading.**

- An item-83-style reordering gives about 0 gain on pend: estimated change 0 µs in duration and 0 to −2.3 µs
  (worse) in idle.
- Item 83 worked where the same gates had a freedom of order that changed the critical path. Here the critical path
  is one hub qubit's own gates, and that has no freedom.

| | number |
|---|---|
| vanity | "pend is already time-optimal" |
| essential | optimal only in duration, and only for this chain. Non-hub qubits sit idle for about half the circuit (3.5-4.3 µs of 7.5 µs). Untested on a device. |

### B4. Lines to change

- **Request 2:** none recommended.
- **Request 1:** only the optional guard in 5a, one line at the top of `pend_circuit` after `m = len(cyc)`.
- **A different technique, outside request 2 and needing the owner's decision before any work:** dynamical decoupling
  in the idle gaps of the non-hub qubits. Those gaps are about 2 CZ + 3 sx (about 0.24 µs) per layer, enough for an
  X-X pair. It changes the gate set, not only the order; not estimated here.

## Files (`review/`)

| file | what |
|---|---|
| `r1_exhaustive.py` | statevector exactness, every pendant subset, m ≤ 8, n ≤ 13 |
| `r2_structural.py` | structural replay, every pendant subset, m ≤ 12 |
| `r3_idle.py` | idle per qubit and duration, as emitted and with R1 |
| `r4_bound.py` | busy time per qubit role; the duration against the hub bound |
| `r5_asap_alap.py` | idle under ASAP against ALAP |
| `r6_decomp.py` | the block identity; the diagonal-outer-gate search |

All take the TOQB checkout path as their argument (r6 none) and need qiskit, numpy and scipy (r6).
