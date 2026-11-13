# Ohm on a honeycomb strip: is there a size that reads, means something and has exact answers? (workplace, 2026-11-13)

Handover 11-12 item 2-1. Desk only: not declared, no device, no POD. Heron r2 graph and failed elements from
`results/ohm-kingston-2026-11-12/fetch_in/ibm_kingston/dev/device.json` (rows 0-2 have no failed element).
Scripts: `hc_estimate.py` (strips, colours, CZ by compiling one cycle, MPS answers under the 1-minute rule),
`tn_probe.py` (one site by psf-os's light-cone network, `exact_tn`), `tn_W.py` (W by `exact_tn` over the right half).
Outputs: `estimate.jsonl`, `estimate_t2t4.jsonl`, `tn_W.jsonl`, `tn_W.log`.

## Strips (fixed rule, extending home VS's two-row rule)

Rows 0 .. R-1 (16 qubits each, at 0, 20, 40), columns 0 .. c, and every bridge with both ends inside; labels sorted by
(column, level); the wall after the first half of the labels (the middle column). One cycle = fSim(pi/4, pi/2) on every
bond once, greedy colours in the sorted bond order. Strings: `gpu/ohm_answers.strings` (m 0.5, seed 20261112).

| strip | qubits | bonds | colours | CZ per cycle | CZ layers per cycle |
|---|---|---|---|---|---|
| 2 rows x 11 columns (home VS's 24) | 24 | 24 | 3 | 72 | 9 |
| 2 x 16 | 36 | 38 | 3 | 114 | 9 |
| 3 x 12 | 42 | 45 | 3 | 135 | 9 |
| 3 x 14 | 49 | 53 | 3 | 159 | 9 |
| 3 x 16 | 56 | 61 | 3 | 183 | 9 |

Two rows give at most 36 qubits on Heron r2, so 40-60 needs three rows. Cycles 2 / 3 / 4 / 6 are 18 / 27 / 36 / 54
CZ layers. Check: the 24-qubit strip reproduces home VS's exact W at 3 cycles (0.994, K 6).

## Cost of the exact answers

- **MPS in label order (as the handover asked), 1-minute rule:** 2 cycles: all strips (at most 23 s per circuit);
  3 cycles: 24 and 36 qubits (bond 256-511, at most 15 s), 42-56 qubits over a minute; 4 cycles: over a minute for 36
  to 56; 6 cycles: over a minute already at 24 qubits. A column cut of the strip is crossed by 2-3 bonds per colour
  layer, so the bond grows like a 2D state's.
- **Light-cone tensor network (psf-os `exact_tn`), per site:** 3 cycles 1-3 s (cone about 25 qubits); 4 cycles 4-9 s
  (36 qubits, largest intermediate 2^14-2^18) and 11-12 s (56 qubits, 2^13-2^22); 6 cycles 237 s for one site of the
  36-qubit strip (2^26, 10^11.9 flops) and over 300 s for one site of the 56-qubit strip (stopped).
  A full W at 4 cycles (2 strings and their complements, every right-half site): 10 min for 36 qubits, 21 min for 56,
  on one core here. The network and the MPS agree where both run (W at 2 cycles: 0.795 and 1.366).

## How far from the dead end (W / W of the fully mixed state, every Z = 0, as home's ohm_sim; K 2)

| qubits | 2 cycles | 3 cycles | 4 cycles | 6 cycles |
|---|---|---|---|---|
| 24 | | 0.48 | | 0.81 (home VS, K 6) |
| 36 | 0.23 | 0.32 | 0.39 | not computed (237 s per site) |
| 56 | 0.20 | | 0.28 | not computed (over 300 s per site) |

At 36-56 qubits the 4-cycle state is far from mixed (0.28-0.39, against 0.8 for the 24-qubit strip at 6 cycles):
the wall's spreading is still visible. Exponent of W from 2 to 4 cycles: 0.78 (36 qubits), 0.52 (56 qubits), with
K 2 only, so dominated by which strings were drawn (on the 40-qubit chain, K 100 still left a spread of 0.02-0.05 between string draws);
not a measurement of the honeycomb's transport.

## In one sentence

There is a candidate: **56 qubits (3 rows x 16 columns) at 2 and 4 cycles (18 and 36 CZ layers)**, far from the dead
end (W / W_mixed 0.20 and 0.28) and with exact answers by the light-cone network (about 5 min per circuit at 4 cycles
on one core; a POD for a job's worth), but the window is short (2 -> 4 cycles) and 36 CZ layers is where the 40-qubit
chain's M did not read on either device on 11-12 (its Z did); 6 cycles (54 layers) is past anything read in this
family and past the exact answers here. Whether the honeycomb's M reads better than the chain's at the same layers is
suggested only by the 24-qubit simulator (FakeFez), which did not reproduce the device's exponents.
