# XX size test, 2026-11-14: the verdicts on the declaration (prereg/xxsize_2026-11-14.md)

Records: `results/xxsize-2026-11-14-marrakesh/` and `results/xxsize-2026-11-14-fez/` (declaration 2058dbaf pushed
12:25:45 CET, queue read 12:26:04 CET; jobs dbs4ccmjjaos73ajovrg, dbs4cevv5hds73dihon0 (marrakesh N33, N81),
dbs4chfv5hds73dihoq0, dbs4ck1abdes73fqo1fg (fez N33, N81); all four built with the circuits of the checked
try-builds). The sealed answers are released in `answers_released/` (sha256 bbeffe76..., 2690ae4e..., as declared).
Every cell: `verdicts.txt` (`python notes/xxsize_2026-11-14/verdicts.py`).

## Predictions

1. **Angle, |r(pi/4) - r(pi/2)| <= 0.05 in all 20 pairs: failed.** 12 of 20 within; largest 0.074. On marrakesh
   r(pi/2) was above r(pi/4) at every depth and both sizes (by 0.017 to 0.074); on fez the two were within 0.02 at
   N = 33 and apart at N = 81, 48 and 64 layers (pi/4 above, by 0.055 and 0.071).
2. **Size, |r(81) - r(33)| <= 0.05 in all 20 pairs: failed.** 7 of 20 within; largest 0.181. r was lower at N = 81
   than at N = 33 in all 20 pairs; on fez by 0.08 to 0.18 from 32 layers on.
3. **The line, "r >= 0.293" matching READS (pi/4) in at least 18 of 20: held, 20 of 20.** The closest cell: fez N = 81
   at 48 layers, r = 0.292, DOES NOT READ.

## Readable depth (pi/4)

| device | N = 33 | N = 81 |
|---|---|---|
| ibm_marrakesh | 64 layers (the deepest run) | 64 layers (the deepest run) |
| ibm_fez | 64 layers (the deepest run) | 32 layers (48: does not read) |

## Beside (not judged)

Fits r = A exp(-L / lambda) over the CZ layers L:

| device | both sizes, both angles | N = 33 | N = 81 | earlier, N = 91 |
|---|---|---|---|---|
| ibm_marrakesh | 78 | 88 | 71 | 79 (11-13, pi/4, 16-48 layers) |
| ibm_fez | 43 | 57 | 35 | 43 (11-12, both angles, 8-64 layers) |

The pooled lambda equals the earlier N = 91 values on both devices, but the per-size values differ (shorter at
N = 81 than at N = 33, on both devices), so the agreement of the pooled numbers is not by itself evidence that a
device's decay length is the same from day to day. What a larger chain adds that lowers r (more qubits and couplers,
including worse ones, on the same device-day) is not tested here.

Sentinel: marrakesh CLEAN with N = 33, DEAD with N = 81; fez DEAD with both.

## What this changes

The declared reading "r is set by the CZ layers alone, not by size or angle" does not hold: at equal layers r falls
with the length of the chain, and depends a little on the angle. The reading "whether a result reads is told by r
(the 0.293 line)" held in every cell.

## Exploratory, after the verdicts (not declared): size, or the qubits?

`split.py` (output `split.txt`) computes r on subsets of qubits. On marrakesh the N = 33 chain is exactly the first 33
qubits of the N = 81 chain, in the same order; on fez the two chains share 23 qubits.

- **The same qubits keep less in the longer circuit.** marrakesh, pi/4: on the 33 shared qubits r = 0.617 in the
  N = 33 circuit and 0.558 in the N = 81 circuit at 32 layers; 0.411 and 0.343 at 64 layers. fez, pi/4, on its 23
  shared qubits: 0.519 and 0.423 at 32 layers; 0.326 and 0.169 at 64.
- **The added qubits are not the cause on marrakesh.** In the N = 81 circuit, r on its 48 other qubits is close to r on
  the shared ones (pi/4: 0.527 against 0.558 at 32 layers, 0.347 against 0.343 at 64).
- The gap is small at 8 layers (marrakesh 0.830 against 0.821) and grows with depth.

A reading to test, not tested here: in this circuit an error spreads along the chain with the dynamics, so the
shrink of a qubit's value counts the errors inside its light cone; in a 33-qubit chain the light cone stops at the
chain's ends, in an 81-qubit chain it keeps growing with depth. That would make r depend on depth and on size until the
light cone passes the chain's length, and would explain why the gap grows with depth. A declared test would compare
N = 33 and N = 81 at depths below and above the light cone's crossing of 33 sites.
