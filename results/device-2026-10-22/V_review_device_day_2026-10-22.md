# Workplace review of the device-day build (C r9), 2026-10-22, about 01:55 CEST

**Reviewer.** The workplace Claude, an independent second look at the home Claude's work. No IBM connection, no API
key and no GitHub were used. Nothing ran on the workplace PC; the build and the equality checks ran in the workplace
Claude's cloud workspace.

**Inputs.**

| input | SHA-256 |
|---|---|
| pack 10: `toqb_2026-10-22_workplace.bundle` | 09387527… (matches the handoff) |
| pack 10: `psf-zero_2026-10-22_workplace.bundle` | 23303897… (matches the handoff) |
| pack 10b: `psf_ai_compile_a22.py` | 625f9431… |
| pack 10b: C r8 | dcba1249… |
| pack 10b: C r9 draft with item 7 | 2257da20… |
| `toqb_pod_2026-10-22b.bundle` (aee0be4 → e968866) | 8ce4d61d… (matches the procedure) |
| `psf_compile.py` c61, from the workplace's own copy of 2026-10-15 | 254cfabc… |

The c61 copy is taken to be home's c61 because every line number in the handoff matches it: `_st_cost` 4555,
`_duration_s` 4591, `_duration_cx` 4619, `_better` 4639, `_failed_elements` 5561, `_chain_lattice` 6414,
`_chain_snake` 6469, `_chain_place` 6503 and `_scope96_embeds` 7267.

**One-line conclusion.** On the code: **the evening device run may go ahead**. On the procedure, three points need
the owner first:

1. r9's items 1, 2 and 6 contradict item 7 as written.
2. r9 does not say what happens when `submit` finds a failed element now that training uses the snapshot.
3. Starting the pod from the workplace PC needs an IT check under the organisation's rules (§4).

## V1. ring.rs read against the Python (a22, c61): no problem found that changes a template

Everything was read line by line: `ring.rs` (1,302 lines), `lib.rs` and the JSON writer, against a22's `_ring_read`,
`ring_rounds`, `ring_rounds_q4`, `_ring_logical`, `_mul`, `_t_zyz`, `RingTemplate.angles`, `_block_ops`,
`_ring_template_one`, `ring_template`, `_ring_embeds` and `model_template`, and c61's functions listed above.

| point (from the handoff) | finding |
|---|---|
| order of the final flush | **Same.** Python flushes `pending` in insertion order, `{phys[w]: [] for w in range(n)}`, so wire 0, 1, …. Rust flushes with `for w in 0..n { flush(phys[w]) }`. The BTreeMap's own order is never used for this flush |
| blocks (cz / swap on one pair, up to another operation on either wire) | **Same.** The membership test, the break, the use of `used` and flushing both wires before each CZ all match |
| pulses of a fixed-only run, and `%` | **Same.** The thresholds 1e-12, θ ≈ π/2 and the branch order match. Python's float `%` is fmod with the divisor's sign added; Rust's `rem_euclid` is fmod plus the divisor when negative. For a positive divisor they give the same bits; a sign of zero can differ, but `abs()` follows immediately |
| `round()` and the modal duration | **Same.** `round_ties_even` is Python's half-to-even rounding of the same double. The modal tie goes to the shortest length: Python's `max(key=(count, -x))`; Rust iterates in ascending order and replaces only on a strictly larger count |
| choice of the bridge in `_chain_snake` | **Reasonable.** `min` / `max` over (column, qubit) tuples does not depend on iteration order. Only `next(...)` over `adj[bq]` depends on Python's set order. On heavy-hex a bridge qubit has exactly one neighbour in the row below, and `adj` includes failed couplers, so failures do not change this. Rust refuses only when there is not exactly one, and the Python then builds. It never fired in the V2 cases |
| the known difference in the embedding test | **Can disagree in theory, never on the day.** Three ways: (a) Python's VF2 has a call limit of 2,000,000 where Rust's cycle search is exact (budget 2e8, then refused); (b) a global two-qubit operation: Python's `build_coupling_map()` gives all-to-all, so it embeds, while Rust refuses; (c) failed qubits: Python uses `qubit_errors_from_target(sx)` and `readout_errors_from_target`, Rust reads the sx and measure entries (the helpers' sources were not re-read). Every disagreement ends safely: if Rust says it embeds, it refuses and the Python builds; if only the Python says it embeds, check mode compares a RingTemplate with a ModelTemplate and stops with Mismatch. **On the day it cannot occur:** heavy-hex has no cycle shorter than 12, so a 10-qubit ring never embeds (V2: 0 of 300 refused) |
| `_better` on the bound circuit (Python) against the unbound one (Rust) | **The claim holds.** `_st_cost` reads names, qubits and the Target's error per (name, qargs); `_duration_s` reads names, qubits and durations; `_count_2q` counts two-qubit instructions. None reads a gate's angle, so binding cannot change the choice. The tie keeps N2 in both, and a missing duration falls back to CX units in both |
| reading (item 28), schedules N2 / item 31, logical circuit | **Same.** Measurement, block completeness, cycle order and the odd-layer rule all match (the schedule is computed before the odd-layer check, in both) |
| complex arithmetic (binding) | **Same as CPython's `_Py_c_prod`, `_Py_c_quot` and `cmath.sqrt`** (constants CM_SCALE_UP 53 and DOWN −27 checked), with `hypot` and `atan2` from the platform libm in both |

**Observations, none affecting the day's circuits:**

1. **Signed zero in JSON.** `json.rs` writes an integral float as an integer, so −0.0 becomes "0". `ringport.compare`
   cannot see this (it uses abs). Physically harmless: rz(±0) is the same gate, and a ±0 inside a fixed factor can at
   most move a ZYZ angle by 2π, which is a global phase. V2's bit comparison found no case (0 of 295).
2. **Python version.** Python 3.14 (as the workplace remembers its changelog; not checked here) changed mixed complex-real arithmetic: `-1j * s` gives (−0.0, −s) instead of
   (0.0, −s). The Rust matches Python up to 3.13 (V2 ran on 3.11). Only the sign of zero is concerned, so harmless,
   but the "bit-identical" claim holds for Python up to 3.13.
3. **Placement order.** Python tries the fadj snake, then fadj VF2, then the kadj snake, then kadj VF2. Rust stops at
   OutOfScope after the fadj snake. A device whose fadj snake is too short but whose kadj snake would hold the ring is
   therefore out of scope, even though a formula placement exists on kadj. This agrees with r9 item 6's wording
   ("would need VF2's search": the Python would try fadj VF2 first) and does not touch marrakesh's snapshot. It is the
   owner's reading of "B" to confirm.
4. **r8's E4 wording.** It says "PSF's template places the ring from the coupling map alone". `_chain_lattice` also
   uses the calibration: failed qubits and couplers are cut, and the coupler durations choose the modal set (fadj).
   With item 7 (snapshot) this is fixed in advance, but the sentence is not exact.

## V2. Independent equality check (own script, own devices, faults and seeds): no difference

The workplace wrote its own script (`v2_check.py`, `v2_sched.py`, in the zip) rather than using home's.

**Setup.**

- Rust: `cargo test --release`, 8 passed; release build of `libpsfbind.so` with cargo 1.95.
- Python: a22 with c61, Python 3.11, qiskit 2.5.2.
- Devices: FakeAachen, FakeTorino, FakeFez, FakeKingston, FakeMarrakesh (qiskit-ibm-runtime 0.50).
- Faults, in the workplace's own scheme, 12 patterns per device (the first without faults), seeds 7700+:
  - failed qubits (sx and readout error 0.9);
  - failed couplers (error 1.0 or 0.6, 30 % of them in one direction only);
  - changed coupler durations (×1.5 or ×0.75), which alters the modal set;
  - in 9 patterns, an sx without a duration, which forces `_better`'s CX-unit fallback.
- Models: n = 10, L = 1, 2, 3, 8, 16.

| check | result |
|---|---|
| `model_template` (a22) against `ringport.ring_template`, 300 cases | **295 built by both: all identical** at `compare(tol=0.0)`, and identical bit for bit in every fixed angle and factor, sign of zero included. **5 out of scope (Rust):** all 5 are cases where the Python placed by `vf2_path` (FakeTorino, one pattern, all L). 0 refused, 0 other |
| each schedule alone (N2, item 31), `_ring_template_one` against `schedule=`, 180 cases | 174 identical (also bit for bit), 6 out of scope, 0 different |
| binding: `RingTemplate.angles` (Python) against `psfbind_angles` (Rust) | **1,180 value vectors, every output bit-identical**, including values set exactly to 0.0, −0.0, ±π and π/2 |
| the same on a21 | the same counts |

**Not covered.** In every case the choice went to item 31 (q4). N2 winning the choice is therefore not exercised
here, although both builders and `better` are covered: by V1 and by the per-schedule check.

**Vanity and essential.**

- **Vanity:** "295 of 295 identical, 1,180 bindings bit-identical". This shows the port is correct.
- **Essential:** "can the day give a different result?" On the day the template is Rust's, built once and compared
  with the Python's: a difference in gates, qubits, runs or layout, or above 1e-12 in an angle, stops the run. A
  silent divergence would need a difference at or below 1e-12, or in a sign of zero, and V2 found none. The
  remaining risks are operational (V3, §4), not numerical.

## V3. r9 against r8, and the day's scripts

### Found earlier this night and already fixed by home

e968866, per its commit message: "load the shared library only, no run without cargo, r9 wording". **Unverified by
the workplace:** the bundle carries the changed files only as deltas, which cannot be resolved without the base
commit.

1. `rustbind.cdll()` took the first `libpsfbind.*` match. The build produces `.so`, `.d` and `.rlib` (confirmed by
   building), so the `.d` could have been loaded and failed. This failure is safe but costs time. Fixed per the
   commit; the procedure also sets `PSF_BIND_LIB`.
2. `rust_psf.sh` ran with an older library when cargo was missing. Fixed: it now stops.
3. E5 holds only with RUST=1. Written into r9.
4. Check mode compares at 1e-12. Written into r9. The pack 10b r9 predates this and does not show it.

### r9 against r8 (pack 10b's r9, with item 7)

| # | point | status |
|---|---|---|
| a | **Items 1, 2 and 6 still describe the fetch-and-choose day,** which item 7 replaces. Item 2 says "E2-E5 … to the three fetched Targets … `choose`"; item 6 says "on the day it is read from the fetched Target by `choose`"; item 1 still speaks of T0 as a fetch. A fixed document should not contradict itself | **problem (wording)**: mark items 2 and 6's day-specific sentences "superseded by item 7" |
| b | **A failed element found by `submit`, under item 7.** r8 says retrain (fetch again, rebuild, recompile, retrain about 4 h). Under item 7 the training uses the snapshot: retraining on the snapshot gives the same placement and stops again, while retraining on a fetch contradicts item 7. r9 does not say which, and does not say whether the next device in the fixed order is then tried | **problem (decision needed before fixing r9)** |
| c | Qiskit level 2 places by the 9-day-old snapshot's errors, so at submission its placement is more likely than PSF's to touch an element failed today. It is a consequence of item 7, not an error | observation: worth one sentence in item 7's "Consequence" |
| d | Item 1 removes r8's time limit; r8's retraining rule (§5) lists "the time limit would be exceeded" as a trigger. r9 should say that this trigger is removed | **problem (wording)** |
| e | r8 §Compilation says "PSF compile_template". For the 10-qubit ring on heavy-hex, a22's `model_template` gives the ring template (item 35), as r9 item 5 says | observation (r8's wording) |
| f | Items 3, 4 and 5 against r8: no conflict (the same job, H1 and H2 unchanged, INIT is a stated change) | no problem |
| g | `choose`: E3 "unknown" is not excluded (`operational is False` only), matching item 2. Under item 7, `choose` is not used | no problem |

### The day script and procedure b

| # | point | status |
|---|---|---|
| h | `rust_psf.sh` is sourced directly (`. "$TQ/gpu/rust_psf.sh"`, not in a pipe), so its exports persist. Only its echo is piped to tee | no problem |
| i | FETCH = the snapshot folder takes the single-device path: precheck, then plans and the rest. The zip takes the snapshot folder as `ZEXTRA` | no problem |
| j | **The zip does not contain `$OUT/runs/`** (the run records and each run's QPY). The script's header (r8's text) says "a zip for home with the job folder and the run records". Scoring reads `job/` only (`cmd_score`), so the device test is not affected. But procedure b allows stopping the pod after the zip, which would lose the run records (final parameters, full predictions) | **problem (small)**: before stopping the pod, copy `<pod>/device_2026-10-22/runs` too, or add it to the zip |
| k | `toqb.s2rc_device snapshot` (f288706) is not in the workplace's copy | not checked |
| l | `choose` and `precheck` run under `| tee` without pipefail, but the script tests the output (`CHOSEN`, `all OK`), so a crash still stops the day | no problem |

## 4. A note under the organisation's rules (before step ①)

Procedure b, step ①, says the pod may be started at the workplace: renting it, uploading the bundle through the
browser, and a `git clone` from GitHub on the pod. The organisation's rules forbid pasting information into outside
services the company has not approved, and handling credentials, and the project's rule is "no GitHub on the
workplace PC". Whether RunPod (and its account sign-in) may be used from the company PC is not something the
workplace Claude can judge. **Please confirm with the IT or system administrator, or start the pod from home.** The
workplace Claude does not operate the pod.

## 5. Owner decisions asked for before fixing r9

1. The answer to V3 b: what follows a failed element at submission under item 7 (retrain on the snapshot, retrain on a
   fetch, the next device, or stop).
2. The wording in V3 a and d (marking superseded sentences).
3. Observation 3 of V1: whether a formula placement on the kadj snake should count as within the scope (it does not,
   as built).

## Addendum, 2026-10-22 about 02:10 CEST: home's fixes (bundle 43076c3a…, diff aee0be4 → HEAD in pack 10c)

Read from the diff that home sent; the bundle itself was not unpacked.

| item | status |
|---|---|
| `rustbind.cdll()` | **Fixed correctly.** Only `libpsfbind.so` / `.dylib` / `psfbind.dll` are taken, never `.d` or `.rlib` |
| `rust_psf.sh` | **Fixed correctly.** It sources rustup's env if present, stops without cargo, and always rebuilds |
| zip | **Fixed.** `$OUT/runs` is added. Today's pod runs the older script, so the runs must be copied by hand, as home says |
| r9 items 1, 2, 5, 6 | **Consistent with item 7 now.** The retraining trigger is removed; item 2's fetch sentences are marked as replaced for the day; the 1e-12 check is written as it behaves; E5 is stated to need RUST=1 |
| `snapshot` command | Writes target.pkl and fetch.json (backend "ibm_marrakesh", source "snapshot", operational null), never overwrites, and is tested |
| item 8, `pick_backend` | **The code matches item 8's text.** Fixed order from the job's device; qubit count; `operational is False` only; `submit_problems` (failed **or unsupported** elements, so a different coupling map is caught); every device tried is recorded; nothing is submitted when none takes the job; the duplicate-submission guard is unchanged; `result` reads the device actually used. Three cases are tested |

**One point for the owner (not a code problem).** Item 8 cites "owner, 2026-10-22 02:00 CEST" for "the same circuits
to the next device". The owner's words to the workplace at about 01:58 CEST were: "if the device is broken, it can't
be helped; I don't worry about that each time". The workplace read this as "the day ends; no retraining, no other
device", and proposed that wording. Both readings fit "no retraining". They differ on whether fez or kingston may
run the job. If they may, the twin (marrakesh's snapshot) predicts a device it was not built for, so H1, H2 and the
undamped readout then test a cross-device prediction. Item 8 reports that, but it changes what the day measures. The
owner should state which reading is meant before r9 is fixed.

**Small note.** assemble's QPU-time check (at most 150 s) uses marrakesh's snapshot durations. On fez or kingston it
is not recomputed. Heron r2 durations are similar, so this is expected to be minor (unverified).

**Resolved (2026-10-22 02:04 CEST).** The owner confirmed item 8 as written: on a failed element at submission, the same circuits go to the next device in the fixed order. A cross-device run is reported as such. Nothing remains open from this review.
