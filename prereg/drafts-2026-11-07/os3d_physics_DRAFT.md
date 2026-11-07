# DRAFT (not declared): 3D physics on the folded layout — (A) Ising quench in time, bulk against surface;
# (B) 3D Heisenberg, first at 4 x 2 x 2
(owner 2026-11-07 19:46 JST "その方向で進めて", after the literature note below; numbers marked * are open choices)

## Why (literature, 2026-11-07 search)

- D-Wave (King et al., Science 2025, arXiv:2403.00910): quench dynamics of spin glasses in 2, 3 and infinite
  dimensions on an annealer; classical tensor-network and neural methods did not match its accuracy. Analog, not gates.
- Naik, Sun, Heyl (arXiv:2604.05032, 2026-04): 3D transverse-field Ising on cubic lattices, up to 1000 spins, by neural
  quantum states (classical): quenches, collapse and revival, quantum Kibble-Zurek. A classical reference for 3D.
- Tindall et al. (arXiv:2306.14887): IBM's 2D kicked Ising reproduced by tensor networks with belief propagation;
  more loops make that harder: 3D is the harder case for this family of methods.
- Gate-based 3D Heisenberg on hardware: none found in that search (1D/2D only, e.g. arXiv:2512.03341 on IBM).

## (A) 3D kicked Ising: the quench in time, bulk against surface

What is new against the 2026-11-07 runs: a time trace and a theta sweep, and a 3D-specific observable.
- Lattices and depths: 4 x 2 x 2 at t = 1-6* (exact by the full statevector, 16 sites); 4 x 4 x 3 at t = 1-3 (exact
  by the light cone, `gpu/os3d_lightcone.py`). theta in {0.4, 0.8, 1.2}*.
- Observables: M(t) as now; and at 4 x 4 x 3 the bulk sites (the 4 sites with all six neighbours) against the surface
  sites: <Z> averaged over each class, measured against the exact values per class. The bulk is what makes it 3D;
  4 x 2 x 2 has none (all 16 are surface), 4 x 4 x 3 has 4 of 48.
- Choice of place: rule "top" with the gate as a flag (as on kingston today). Verdicts: READS / AGREES / BEATS per
  point, retention; per class (bulk, surface) the same, reported beside.
- Cost: as today (4 x 4 x 3: 488 CZ per step); one job per lattice, about 3 theta x 3 t arms per candidate.

## (B) 3D Heisenberg (XXX), first at 4 x 2 x 2

- Model: Trotter steps U = prod over bonds exp(-i dt (XX + YY + Delta ZZ)), Delta = 1*, dt = 0.25*, t = 1-4*, from the
  Neel state (checkerboard on the cubic lattice). Observable: the staggered magnetization (Neel order) and its
  retention. Exact: full statevector (16 sites), any depth.
- Placement: the folded layout v3.1 as it is, with one change: each bond gate is a general two-qubit unitary. The
  merge of a bond into its swap (today SWAP x RZZ(-pi/2), 2 CX) becomes SWAP x exp(-i dt(XX+YY+ZZ)), synthesised by the
  analytic KAK decomposition of PSF-Zero's core (any two-qubit unitary, at most 3 CZ, no search). Bonds without a
  swap: the same KAK, 3 CZ.
- Expected cost: about 3 CZ per bond against 1 for Ising, so about 2-3 times the CZ of the Ising arm per step.
- Pre-run checks before declaring: (1) the placed circuit against the logical one by the full unitary on 4 x 2 x 2
  (18 qubits with bridges: statevector), every bridge back in |0>; (2) the KAK blocks against their target unitaries
  (to 1e-12); (3) the device-like simulator (realsim, POD) for the expected retention.

## Work items

1. psf-os grid3d: a bond-gate parameter (Ising RZZ as now; Heisenberg via the KAK merge), tests for both.
2. TOQB: `gpu/os3d_v31_build.py` options for theta lists, depth lists, the bulk/surface classes, the Heisenberg
   model; scorer per class.
3. Pre-run checks as above, then a declared file per part. (A) first: it needs no new gate code.

## Open choices for the owner

theta values and t range in (A); Delta, dt and t range in (B); whether (B) waits for (A)'s run.
