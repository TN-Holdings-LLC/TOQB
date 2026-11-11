# 1D Fermi-Hubbard on heavy-hex: first numbers (workplace, 2026-11-11; not declared, no device)

Model: H = -J sum (c+_{i s} c_{i+1 s} + h.c.) + U sum n_{i up} n_{i dn}, open chain of L sites, 2L qubits, Jordan-Wigner
in the interleaved order (u0 d0 u1 d1 ...). First-order Trotter step (dt = 0.25 / J, U = 4 J): onsite RZZ + RZ, then
even and odd bonds by fermionic swaps (FSWAP = SWAP . CZ) and XX+YY hopping (`hub_count.py`).

## Exactness

`hub_check.py`: the circuit step against exp(-i dt H_odd) exp(-i dt H_even) exp(-i dt H_U) built from the fermion
operators, L = 3 (6 qubits): 1 - |Tr(V^dag T)| / d = 5.6e-16.

## Cost on a line (transpiled to cz / rz / sx / x, line coupling, no routing)

CZ per step = 10 L - 8; CZ layers per step = 12 for every L; CZ participations per qubit about 9.6 per step.

| L (qubits) | 4 steps: CZ / layers / per qubit | 6 steps | 8 steps |
|---|---|---|---|
| 20 (40) | 768 / 48 / 38 | 1152 / 72 / 58 | (1536) / 96 / 77 |
| 30 (60) | 1168 / 48 / 39 | 1752 / 72 / 58 | (2336) / 96 / 78 |

(8 steps from the per-step rule.)

## Against what has been read on devices (CZ participations per qubit, CZ layers)

- du51 / du71 / du91, t 24: 48 per qubit, 49 layers: read (one light-cone site per point).
- Schwinger 11-09 (marrakesh, every site depends on every gate): N 6, 5 steps, 75 per qubit, 90 layers: READS;
  N 8, 5 steps, 105 per qubit, 120 layers: DOES NOT READ for 2 of 3 parameter sets.
- So Hubbard 4-6 steps (38-58 per qubit, 48-72 layers) sits inside what has been read; 8 steps (77, 96) at the edge.

## Classical side

- Exact diagonalisation, half filling, Sz = 0 subspace (16 bytes per amplitude): L 16 2.7 GB, L 18 38 GB, L 20 546 GB,
  L 24 117 TB, L 30 about 385 PB.
- Aer MPS without truncation (2 CPUs here; `mps.log`): L 8 equals the statevector to 8e-10; L 20 at 4 steps (Jt 1.0)
  120 s; L 20 at 6 steps (Jt 1.5) not finished after 27 min (stopped). A tensor-network code with conserved charges
  and a POD would go further; this is a cost measurement of one simple tool, not a claim of classical hardness.

## 2D, 4 x 4 (32 qubits) on a line: one step (`hub2d_count.py`, workplace 2026-11-11; not declared, no device)

- Jordan-Wigner along the snake order of the sites, spins interleaved, one line of 32 qubits (a chain on heavy-hex).
- The snake-neighbour bonds (12 horizontal and the 3 vertical bonds at the row turns) are done as in the 1D step.
- The other 9 vertical bonds: in each two-row block, whole sites are moved by fermionic swaps (odd-even
  transposition, a site swap = 4 FSWAPs) until each vertical pair has been neighbours once, then the swaps are undone.
  Blocks (0,1) and (2,3) go first, then (1,2).

| one step | CZ | CZ layers | CZ / qubit |
|---|---|---|---|
| 2D 4 x 4, transpile level 1 (as hub_count.py) | 1088 | 126 | 34.0 |
| 2D 4 x 4, transpile level 3 (2-qubit blocks merged) | 848 | 88 | 26.5 |
| 1D L = 16, same 32 qubits (level 1 and 3) | 152 | 12 | 4.75 |

- Check, 2 x 2 (8 qubits): the circuit against the product of exp(-i dt h) for every applied term, in the applied order,
  from fermion operators. 1 - |Tr(V^dag T)| / d = 1.0e-15. From a Neel start, |V psi - T psi| = 1.2e-15 up to the
  global phase. Every grid bond is hopped once.
- This simple swap scheme is not optimised. One 2D step costs about 7 (level 1) or 5.6 (level 3) 1D steps of the same
  32 qubits.
- Not done this time (next candidates): other mappings (Bravyi-Kitaev, Verstraete-Cirac, compact encodings), smarter
  swap networks for the vertical bonds, and placing the 2D lattice on heavy-hex directly.
