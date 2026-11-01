# PSF-Zero OS layer: plan (DRAFT, home, 2026-11-01; not declared — each milestone gets its own fixed note before it runs)

## What exists (kingston, 30 October - 1 November, all declared tests)

| OS part | in a computer | here | evidence |
|---|---|---|---|
| self-test | memtest | the rule's mirror echo read per ring site (D = 24), about 10 s per device | the same 18-site dead run in every standard n = 40 run from 30 October to 1 November |
| defect registry | bad-block list | dead paths per device; LISTED after 2 jobs; 7-day expiry (`toqb/defect_list.py`) | coverage days 1, 2 |
| allocator | page allocator that skips bad pages | the rule's placement with listed paths masked | usable sites 22 -> 40 (n = 40), 38-39 -> 72 (n = 72), two days |
| repair | remapping / microcode patch | local frame flip (X around the CZ layers of alternate layers at chosen qubits, virtual Z on edge neighbours; the ideal circuit unchanged) | flip at 27, 29: dead block +0.322 and +0.298 on two days, no cost elsewhere |

Two kinds of defect were seen: black (the same qubits on every run for days) and gray (weak, gone within 90 minutes).

## Principles (kept from the tests)

1. Map-free: no calibration quality number is read; the device's coupling graph and its failed elements only.
2. Self-measured: every avoid or repair entry comes from the user's own runs, with dates; outputs say which category
   they ran in (standard / self-checked) and which entries were applied.
3. Avoid by default; repair only with an entry verified on at least two days.
4. Black entries carry over days; gray ones are not carried (same-day scan only).
5. No cause is chased; an entry is kept or dropped by what it does.
6. Each new claim is a declared test with one sentence per outcome; stop rules weigh the size of effects (the
   bisection's "both HELP" rule stopped on a +0.019 beside +0.299).

## The layers

- **L0 device access.** Gate-level (ISA) circuits through the Sampler, options off. Cached per device: coupling
  graph; per submission: failed elements.
- **L1 health scan.** The echo scan on the rule's standard rings (n = 20, 40, 72); dead (< 0.12) and weak
  (< max(0.12, half the ring median)) runs, 3 sites or more.
- **L2 registry.** Per device: dead paths (black), weak paths (gray, same day), repair entries (path -> flipped
  qubits, days verified), contradictions.
- **L3 allocator.** The rule's placement on the fetch masked by the registry (`defect_list mask`); reports what it
  skipped.
- **L4 repair pass.** For each repair entry on the placed ring, local frame flips on its qubits; exact by operator
  identity; optional Pauli-frame tracking (drop the second X, flip later gate angles and the final bits) as a later
  optimisation, checked by operator equality.
- **L5 sentinels.** A few echo circuits added to each user job on the region used; if they read below the registry's
  line, the job's result is flagged and a rescan is scheduled (gray drift).
- **L6 job interface.** In: a logical circuit (CZ layers and single-qubit gates on a ring or line). Out: counts mapped
  back to logical bits, plus a report (category, entries applied, sentinel health).

## Milestones (each a separate declared test; QPU seconds by the time model)

| # | what | QPU | decides |
|---|---|---|---|
| M1 | coverage day 3 (2 November, declared) | 18 s | whether black entries persist over 3 days |
| M2 | the repair on general circuits: random Clifford circuits (CZ layers + random single-qubit Cliffords) on the standard n = 40 ring, with and without the flip at 27, 29; ideal outputs by stabilizer simulation | about 20 s | whether L4 helps computation, not only the echo |
| M3 | the allocator on general circuits: the same Clifford circuits on the standard and the avoiding n = 40 and 72 rings | about 20 s | whether L3 helps computation |
| M4 | a second device (fez or marrakesh): scan, register, avoid in one session (2 jobs) | about 18 s each | whether the layer is device-independent |
| M5 | one command for the chain (fetch -> scan if stale -> place -> repair -> sentinels -> assemble), dry runs on fake devices first | 0 (CPU) | automation |
| M6 | sentinels in a user job and the drift flag | about 10 s | L5 |
| M7 | repair discovery as a procedure (bisection with a size-weighted stop rule), capped at 5 jobs per defect | up to 90 s per defect | whether repairs can be found without the owner |
| M8 | the placement, mask and flip passes in Rust (PSF-Zero's crate) | 0 (CPU) | build time from minutes to seconds |

Order: M1, M2, M3 first (they decide whether the OS helps computation at all); then M4; then M5-M8.

## Gates (fixed now)

- M2 fails (no gain on Clifford circuits): repairs stay limited to echo-like circuits; the OS ships avoid-only.
- M3 fails: the allocator's value is the usable width only, not the accuracy of a computation.
- M4 fails on both other devices: the layer is kingston-specific; no general claim.
- Paper 6 (the self-checking layer) is written after M1-M4, whatever they show.

## Not in scope

Hardware or pulse control (not offered by IBM); calibration numbers; error correction; the cause of a defect.
