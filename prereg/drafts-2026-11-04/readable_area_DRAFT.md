# DRAFT (not declared): the readable area, random Clifford mirrors over area x depth on a placed patch (workplace, 2026-11-04)

Status: a draft for home and the owner. No builder yet; the pieces are `lattice2d` (placement), `mirror2d` (U,
barrier, U^dagger with the CZ-count acceptance) and the stabilizer simulator (any size).

**Prior work, stated first.** Measuring a device's capability over width x depth with mirror circuits is the volumetric
benchmarking of Proctor et al. ("Measuring the capabilities of quantum computers", Nature Physics, 2022, Sandia).
What is new here is the setting: the patch is placed by translation without reading the calibration map, avoiding the
failed and suspect elements (`lattice2d.place`), and the result is read as an extension of our readable depth to a
readable area, on the same patch where P6 and OS2D run.

## Regions and circuits (one job, on the P6 copy chosen by P6's rules)

- **Areas:** the first k qubits of the P6 patch in breadth-first order from its centre (label 26; ties by label), for
  k = 6, 12, 24, 35 (fixed; each region is connected and contains the previous one). Edges: the patch's edges inside the
  region, in the patch's three matchings.
- **Depths:** d = 3, 6, 12, 24 CZ layers forward; each layer = a random single-qubit Clifford on every region qubit,
  then CZ on one matching (matchings in turn: layer 1, 2, 3, 1, ...).
- **Circuit:** the d layers U, a barrier, U^dagger. Ideal output |0...0> on the region: <Z_q> = 1, known exactly at any
  size (and checked by the stabilizer simulator in the builder's tests). Acceptance: exactly twice U's CZ count.
- **Instances:** 3 random circuits per (k, d), seeds fixed in the declaration (for example 20261104 + 100 k + d).
- **Floor:** for k = 35 at each d, U and U^dagger with the single-qubit Cliffords removed (CZ only; ideal 1).
- **Ring sentinel** as usual.

48 mirror circuits + 4 floor + 4 sentinel = 56 circuits; at 1000 shots about 20 s by the time model.

## The quantity

For each (k, d): the signal S(k, d) = mean over the region and the 3 instances of <Z_q>, with 2 SE; and its floor-
normalised form S / S_floor(d). **Readable** at (k, d) if S >= a line fixed in the declaration (proposed: 1/e, a common
choice in volumetric plots; the owner decides). The **readable area at depth d** is the largest k that is readable at d;
the boundary over (k, d) is the result, drawn as a grid, not interpolated.

## Judged (proposed)

1. Sentinel and acceptance.
2. **Area costs depth (Q1):** at every k, S decreases with d; at every d, S does not increase with k (beyond 2 SE).
   Reported as a pass or a list of the cells that break it.
3. **Does the patch read as a whole (Q2):** at k = 35, the readable depth (largest readable d) is at least the readable
   depth at k = 6 halved. A smaller value would say that the larger area is limited by a few bad qubits rather than
   by area itself; the per-qubit map then says where (reported).

## Reported, not judged

Per-qubit <Z_q> maps at each (k, d); which qubits pull S down (the same flag rule as the mirror sentinel); the floor;
the copy and the device. A comparison with the P6 and OS2D results on the same copy and day if they run together.
