# 2D Hubbard 4 x 4: one Trotter step per fermion-to-qubit mapping (workplace VS Claude, 2026-11-12; desk study, not declared, no device)

`hub2d_mappings.py` counts the CZ and CZ layers of one step by formula. The gate costs come from the circuits counted
on 11-11: onsite 2 CZ, hop 2, FSWAP 2, site swap 8 CZ in 6 layers, snake bond 8, 1D step 10n - 8 CZ in 12 layers.
Mapping 1 is also built as a circuit, as a check of the formula.

## Table (one step, 4 x 4 = 16 sites, 32 modes)

| mapping | qubits | CZ | CZ layers | heavy-hex | how it is known |
|---|---|---|---|---|---|
| 1D L = 16, for comparison | 32 | 152 | 12 | one chain, no bridge | circuit (11-11) |
| JW, one line, naive vertical swaps (11-11) | 32 | 1088 (848 at transpile level 3) | 126 (88) | one chain, no bridge | circuit (11-11) |
| **1. JW, one line, vertical bonds by an interleaving swap network** | 32 | **800** | **112** | one chain, no bridge | CZ by formula = circuit; layers from the circuit |
| 2. heavy-hex bridges | | **0 extra** for mappings 1 and naive (a path of 32 qubits); see below for 3 | | | reasoning |
| 3a. compact (Derby-Klassen type) | about 42 | about 416 | about 34 | not native (see below) | formula, estimate on the encoding's own graph; unverified |
| 3b. Verstraete-Cirac (auxiliary qubit per mode) | 64 | about 416 | about 34, plus preparing the auxiliary state | not native | formula, estimate on its own graph; unverified |

Readable on ibm_fez on 11-11 (1D Hubbard, raw): 4 steps at 48 CZ layers READ; 6 steps at 72 layers DID NOT READ (L 20
and L 30, both arms).

## Mapping 1

- **The network.** In each two-row block, the line order is a0 a1 a2 a3 b3 b2 b1 b0, because row r+1 runs backwards.
  The vertical pairs (a_p, b_p) are nested. An odd-even transposition of whole sites goes toward a0 b0 a1 b1 ... and
  each pair is hopped as a site-level bond when it meets; then the swaps are undone.
- **Swaps per block.** Interleaving needs W (W - 1) site swaps: each b passes the a's after its partner, and the b's
  reverse among themselves. Undoing takes as many again.
- **Formula.** CZ = (10n - 8) + (R - 1) [2 W (W - 1) x 8 + (W - 1) x 8] = 152 + 3 x 216 = 800. The circuit gives the
  same 800 at transpile levels 1 and 3.
- **First formula was wrong.** My first formula counted W (W - 1) / 2 swaps to interleave, which leaves out the
  reversal of the b's. It gave 512, and the circuit showed the mistake. The formula above is the corrected one.
- **Layers.** The odd-even layers overlap, so the layers come from the circuit: 112.
- **Against the naive scheme.** Fewer CZ than the naive scheme (1088), but more layers than the naive scheme after
  merging (88).
- **Check.** On 2 x 4 (16 qubits, one block with 3 nested pairs), the circuit is compared, from a Neel start, with the
  product of exp(-i dt h) of the applied terms: difference 1.4e-15, up to the global phase. Every grid bond is hopped
  once.
- **Not done.** Faster networks for the vertical bonds may exist, for example hop-and-swap fused gates, or keeping
  the rows reversed between steps. Cade et al. (arXiv:1912.06007) treat swap networks for the snake order; their depth
  numbers are not used or checked here.

## 2. Heavy-hex bridges

- **JW-on-a-line mappings need no bridge.** They need only a path of 32 qubits, which heavy-hex has. Every 1D job so
  far used such a chain.
- **Placing the 2D lattice on heavy-hex as it is.** The square lattice has degree 4, and heavy-hex has degree at most
  3 with a bridge qubit on every long edge. Each gate between neighbours of the encoding that falls on a distance-2
  pair needs the bridge. A CNOT across one bridge costs about 4 CZ instead of 1 (or a SWAP in and out, 6 CZ).
- **Cost for 3a and 3b.** This makes up to about 4 times the CZ and layers of the estimates in the table: roughly 1600
  CZ and well over 100 layers. Unverified.

## 3. Mappings with auxiliary qubits

- **3a. Compact (Derby, Klassen, arXiv:2003.06939; journal version with Bausch and Cubitt, Phys. Rev. B 104, 035118).**
  - About 1.5 qubits per mode. Here that is 16 per spin plus about one auxiliary per two faces, 5 per spin, so about 42
    qubits.
  - Hopping terms have Pauli weight at most 3. The follow-up arXiv:2101.10735 (other lattices) states weight at most 3
    and fewer than 1.67 qubits per mode; the square-lattice numbers used here are unverified.
  - Upper estimate with every hop at weight 3: two rotations of 4 CZ each, per spin, gives 24 bonds x 2 spins x 8 +
    onsite 32 = 416 CZ.
  - Lower estimate of layers: 4 colour classes x 8 + 2 = 34. Hops that share an auxiliary may need more classes.
    Unverified.
- **3b. Verstraete-Cirac (arXiv:cond-mat/0508353).**
  - One auxiliary per mode, 64 qubits.
  - Estimate: horizontal hops of weight 2 and vertical hops of weight 4, giving about 416 CZ and 34 layers. Unverified.
  - The exact map holds on the low-energy (stabiliser) sector, so the auxiliary state must also be prepared. That cost
    is not counted here.
- **Both need degree above 3,** so on heavy-hex they need bridges (see section 2).
- **Not done:** Bravyi-Kitaev superfast, and other encodings.

## One-line conclusion

Of the mappings counted, none puts one 4 x 4 step within 48 CZ layers on heavy-hex: JW on a line gives 112 layers (88
naive, merged). Only the compact or Verstraete-Cirac estimates on their own graph (about 34 layers, unverified) fit
one step, and two steps would not fit (about 68). On heavy-hex with bridges, they no longer fit.
