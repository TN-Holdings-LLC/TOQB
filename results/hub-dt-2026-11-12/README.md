# One time, two Trotter step sizes, raw: ibm_fez, 2026-11-12 (prereg/hub_dt_2026-11-12.md)

- Declaration pushed before the queue read (head 531be78 on GitHub); queue read 11:19:15 CET (marrakesh 1, fez 1,
  kingston 4). marrakesh: the ring sentinel does not build (14 failed qubits) -> ibm_fez.
- Build: 16 circuits, 20.9 s by the model; CZ 192 / 384 / 384 / 768 (T0.5_s1 / T0.5_s2 / T1.0_s2 / T1.0_s4).
  circuits_sha256 134b5db0... equal to the home try-build whose pre-run check passed (`ibm_fez/check_trybuild.json`,
  ALL PASS, worst 2.3e-8) -> the PASS carries over.
- Answers sealed as declared (circuit.json fc3dd009..., continuum.json c690b7c9...), released in `answers/`.
- Job dbqp919abdes73folrpg, submitted 11:27:16 CET (calibration 10:58 CET), DONE; DD and twirling off.

## Verdict 1: each arm against its own circuit answers (`gpu/hub_score.py`, `ibm_fez/scores.json`)

| arm | dt | CZ | MSE / mean square | verdict | AGREES (of 40) | mirror |
|---|---|---|---|---|---|---|
| J t 0.5, 1 step | 0.5 | 192 | 0.0035 / 0.1059 | READS | 29 | +0.740 |
| J t 0.5, 2 steps | 0.25 | 384 | 0.0079 / 0.1814 | READS | 24 | +0.630 |
| J t 1.0, 2 steps | 0.5 | 384 | 0.0044 / 0.0430 | READS | 22 | +0.491 |
| J t 1.0, 4 steps | 0.25 | 768 | 0.0065 / 0.0460 | READS | 20 | +0.317 |

## Verdict 2: against the continuum (Richardson; `ibm_fez/scores_continuum.json`)

| time | arm | MSE / mean square | AGREES | closer | difference of MSEs (shot SE) |
|---|---|---|---|---|---|
| J t 1.0 | 2 steps | 0.0049 / 0.0425 | 30 | **2 steps** | 0.0009 (0.0005) |
| J t 1.0 | 4 steps | 0.0057 / 0.0425 | 26 | | |
| J t 0.5 | 1 step | 0.0288 / 0.2045 | 0 | | |
| J t 0.5 | 2 steps | 0.0116 / 0.2045 | 17 | **2 steps** | 0.0172 (0.0010) |

The shot SE is from the per-qubit SE of the cards (variance of the MSE difference to first order); it does not include
day-to-day drift.

## Prediction (written before the data)

- "J t 1.0: 2 steps closer to the continuum than 4": held, by 1.7 shot SE (small; one device-day).
- "J t 0.5: 2 steps closer than 1": held, by 17 shot SE.
- "All four arms READ against their own circuit answers": held.

## Beside (not judged, never used to correct)

- The 4-step circuit is the 11-11 L 20 U 4 circuit: its device error against its own answers was 0.0080 on 11-11,
  0.0065 tonight. Its Trotter error against the continuum (5.7e-4) is a tenth of either.
- At J t 1.0 the halved depth saves less device error (0.0065 -> 0.0044) than the declaration's basis assumed, and
  adds 7e-4 Trotter error; the net is the small difference above.
- At J t 0.5 one step of dt 0.5 carries a Trotter error (0.0164) larger than the 2-step circuit's whole device error.

## Reproduce

`python reproduce.py hub-dt-fez-2026-11-12` (verdict 1). Verdict 2: run `gpu/hub_score.py` on a copy of `ibm_fez`
with `answers/dt_ibm_fez_ans_continuum.json` (it writes that copy's `scores.json`).
