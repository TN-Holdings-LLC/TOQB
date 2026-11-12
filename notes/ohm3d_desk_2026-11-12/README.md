# Ohm in 3D? Desk estimate (home, 2026-11-12 evening; not declared, no device)

Owner 21:37 JST: "シュミレータでも机の上での良いので試してみて" (after the 1D Ohm runs on fez and kingston).

## Cost on Heron (`cost3d.py`, kingston record of 12:06 CET)

psf-os grid3d's fixed layouts (fold for L 4, rows for L 8), converted gate by gate to fSim(pi/4, pi/2): each bond
RZZ -> fSim on the same pair, each bridge CX -> SWAP (so CX RZZ CX through the |0> bridge becomes SWAP fSim SWAP),
compiled to CZ. Counts only; the converted circuit was not checked against a statevector.

| lattice | qubits used | fSim CZ per step | CZ layers per step |
|---|---|---|---|
| 4x2x2 | 18 | 204 | 60 |
| 4x3x2 | 28 | 414 | 69 |
| 4x4x2 | 38 | 576 | 75 |
| 8x2x1 (ladder) | 18 | 186 | 66 |
| 8x2x2 | 38 | 1020 | 165 |

The 1D chain: 117 CZ and 6 CZ layers per cycle (A1, 40 qubits). One 3D step costs 10-27 1D cycles of depth
(swaps on heavy-hex, and fSim = 3 CZ).

## Signal (`signal3d.py`, exact statevector, 8 strings + complements, m 0.5, wall across x)

| lattice | W per step 1..6 | W of the mixed state |
|---|---|---|
| 4x2x2 | 1.00 1.55 1.92 2.07 2.09 2.07 | 2.0 |
| 8x2x1 | 0.47 0.74 1.04 1.26 1.46 1.62 | 2.0 |

At sizes the exact answer reaches by statevector, the lattice is short: 4x2x2 reaches the mixed value by step 3, so
past that a device reading "agrees" without saying anything about transport (noise and physics end in the same state).

## Reading of it

Rough, using tonight's 1D decay per CZ layer as if it carried over (not a noise model, not declared): one step of
60-66 layers already moves W about half-way to the mixed value on kingston. 3D on Heron costs too much depth per
unit time, and the computable sizes saturate within 2-3 steps. Not a route to read Ohm's law raw on this device.
