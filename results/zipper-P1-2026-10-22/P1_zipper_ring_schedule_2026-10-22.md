# P1. Prototype: the zipper schedule for the ring template (workplace, 2026-10-22, about 03:30 CEST)

**Status.** This is a prototype, made at the owner's request ("if it can get better, build a prototype"). It does not
touch today's device run, which is fixed at a22 with item 31. Adopting it needs a new pre-registration.

## The idea

One layer of the ring classifier needs each of its 10 CZ edges once, with both qubits adjacent on the device's line.
Item 31 (today's template) brings edges together with 6 plain SWAPs per layer, at 3 CZ each: 28 CZ per layer.

A SWAP done right after a CZ on the same pair is locally an iSWAP, which costs **2 CZ for both together**. a22's block
rule already merges such pairs, but neither N2 nor item 31 ever produces one.

The zipper places the ring so that the two end SWAPs fall on ring edges:

- **Start layout** (line position → ring index): 0, 1, 2, n−1, n−2, 3, 4, n−3, n−4, 5, … The pairs come
  alternately from the two arcs of the ring.

| round | operations | ring edges done |
|---|---|---|
| A | CZ on positions (1,2), (3,4), …, (n−3, n−2) | n/2 − 1 |
| B | CZ followed by SWAP on positions (0,1) and (n−2, n−1) | 2, at 2 CZ each |
| C | SWAP on positions (2,3), (4,5), …, (n−4, n−3) | none (n/2 − 2 SWAPs) |
| D | CZ on positions (1,2), (3,4), …, (n−3, n−2) | n/2 − 1 |

- **Cost per layer:** 5n/2 − 4 CZ. That is 21 at n = 10, against item 31's 28 and N2's 65.
- **Odd layers** run the rounds backwards, as N2 does, which undoes the permutation. Round B is kept apart from round
  A so that, run backwards, each end SWAP is still followed directly by its CZ and is merged.
- **How it plugs in.** It is one more `rounds_fn` for a22's `_ring_template_one`, so nothing else changes. The choice
  among N2, item 31 and the zipper is item 84's fixed rule (`_better`: duration, then CZ count). No search and no
  calibration are involved beyond what `_better` already reads.

## Measured (simulation and counting only; no device, no noise model)

**Setup.**

- Software: a22 with c61, qiskit 2.5.2.
- Devices: FakeMarrakesh, FakeFez, FakeKingston, FakeTorino, FakeAachen.
- Model: n = 10, L = 1, 2, 3, 8, 16, 2 random models each (50 cases).

| | item 31 (today) | zipper | change |
|---|---|---|---|
| CZ, L 8 / L 16 | 224 / 448 | **168 / 336** | −25 % |
| CZ depth, L 8 / L 16 | 72 / 144 | **40 / 80** | −44 % |
| duration on FakeMarrakesh, L 8 / L 16 | 10.29 / 17.92 µs | **7.10 / 11.55 µs** | −31 % / −36 % |
| duration over the 5 devices, L 8 | 8.95–10.29 µs | 5.88–7.10 µs | |
| exactness: statevector, read in clbit order, up to global phase | 4.7e-16 | **4.7e-16** (worst of 50) | |
| chosen by `_better` among the three schedules | – | **50 of 50** | |
| template build time | 0.11 s | 0.10 s | |

The exactness check covers both the logical circuit and the bound device circuit, restricted to its 10 qubits.

## Is it the least? (analysis, not used at compile time)

An exhaustive search (`bound.py`, IDA*) found the least CZ per layer for n = 4, 6 and 8: **6, 11 and 16**. These
equal 5n/2 − 4, so the zipper is optimal there.

**Limits of that claim.**

- The search started from every layout of least total ring length, but not from longer layouts.
- n = 10 did not finish within 10 minutes. 21 is therefore the zipper's count, not a proven minimum.
- A simple potential bound gives at least 14 CZ per layer at n = 10, so a gap may remain.

## Vanity and essential

- **Vanity:** "−44 % CZ depth, −36 % duration".
- **Essential:**
  - The device-side benefit is unmeasured. Fewer CZs and a shorter circuit should lower the noise, but by how much on
    ibm_marrakesh is not known.
  - The next step is the stand-in noise model, as a report only (not a selection), and then a pre-registered device
    comparison against item 31.
  - The zipper covers even n only. Odd n keeps N2 and item 31.

## Files

| file | content |
|---|---|
| `ring_zip.py` | `ring_rounds_zip(n)`; `ring_template_z` (a22's choice with the zipper as a third candidate); `model_template_z` |
| `eval_zip.py` | the exactness and cost check above, with its output `eval_zip.json` |
| `bound.py` | the least-cost search for small n |

**Not done.**

- The Rust port: one more schedule in `ring.rs`, about 40 lines, with the same parity test as V2.
- Tests in TOQB.
- A pre-registration.

## Addendum (about 03:45 CEST): noise simulation on FakeMarrakesh, report only

**Method.**

- Noise model: Aer's `NoiseModel.from_backend` (per-gate depolarizing plus thermal relaxation).
- Idle noise: relaxation on the idle delays, after ALAP scheduling with the Target's durations.
- Simulation: density matrix of the 10 active qubits, taken before measurement, so readout error is left out for both.
- Cases: 10 random models per depth. Same models and same noise for both schedules (`noise_zip.py`,
  `noise_marrakesh.json`). Nothing is chosen from these numbers.

| | item 31 (today) | zipper |
|---|---|---|
| state fidelity, L 8 (mean, range) | 0.369 (0.355–0.382) | **0.456** (0.443–0.465); zipper higher in 10 of 10 |
| state fidelity, L 16 | 0.128 (0.124–0.132) | **0.200** (0.197–0.202); zipper higher in 10 of 10 |
| readout ⟨Z⟩ damping (noisy / ideal), L 8 / L 16 | 0.77 / 0.31 | 0.80 / 0.35 |

- **Damping figures are rough.** Random models have small ideal ⟨Z⟩, so the damping fit is weak. The fidelity is the
  firmer figure.
- **Not done:** the same run on FakeFez, the TOQB stand-in (traj2), and labelled tasks with CE.
- **Limit:** this is Aer's simplified noise (no crosstalk, no drift, no leakage), not the device.
