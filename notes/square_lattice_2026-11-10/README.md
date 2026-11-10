# Preparing for a square-lattice device (home, 2026-11-10; no device, nothing declared)

Why: IBM's next processor (Nighthawk) is, as far as home knew on 2026-11-10 (from IBM's 2025 announcement; not
checked against a current specification), a square lattice of 120 qubits with 218 couplers. A 10 x 12 grid has
exactly 120 qubits and 110 + 108 = 218 couplers, so it is the stand-in used here.

## What psf-os does on it today (psf-os 82560ff, a fake 10 x 12 device with no failed element)

| placement | result |
|---|---|
| daily/du91 shape rule, N = 91 | no shape (the shapes are Heron label patterns) |
| rule C (psf_os.chain.place), N = 91 | refused: "written for Heron r2 labels (156 qubits)" |
| grid3d fold, 4 x 2 x 2 | refused: no translation fits ("the coupling graph lacks a bridge for a block") |
| grid3d line, 4 x 2 x 2 | refused: no translation fits |

So every placement rule is written for Heron's heavy-hex labels. A square-lattice device needs its own rules.

## What a square lattice offers, counted by formula

- **Chains:** a row-by-row snake of the grid is native everywhere (120 sites on 10 x 12); no rule C needed.
  The dual-unitary and XX rulers would run at N up to 120 with no detour.
- **2D lattices:** native (the device is one).
- **3D lattices:** x along the columns, the (y, z) cross-section along the rows in a Gray-code order (z alternates
  within each y). Bonds that are grid neighbours:

| lattice | bonds | native | not native (farthest, grid steps) | grid used |
|---|---|---|---|---|
| 4 x 2 x 2 | 28 | 24 | 4 (3) | 4 rows x 4 columns |
| 4 x 3 x 2 | 46 | 38 | 8 (3) | 6 rows x 4 columns |
| 4 x 4 x 3 | 104 | 80 | 24 (5) | 12 rows x 4 columns |

  For comparison, on heavy-hex the Ising step costs 108 CZ (fold) and 60 (line) at 4 x 2 x 2, 234 / 126 at 4 x 3 x 2;
  the bonds alone are 28 and 46 (one CZ each with the exact RZZ). The few far bonds need swaps; their cost and the
  schedule are the design step, not done here.

## Proposal (cheap, by formula, kept until the device is offered)

1. A geometry layer in psf-os: the placement rules chosen by the device's coupling graph (Heron heavy-hex as now;
   square grid: snake chains, native 2D, the Gray-code 3D), never by quality numbers.
2. The 3D schedule for the far bonds on a grid, its CZ count, and the exact check (as grid3d's).
3. Nothing is run until a square-lattice device is offered on the cloud; whether and when is not known here.
