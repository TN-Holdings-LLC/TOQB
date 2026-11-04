# Design (workplace, 2026-11-04; not run): a second, independent estimate for the depths without exact answers

**Why.** For P5 at t = 20 and P6 at t > 9 the only classical value is the sparse Pauli dynamics (SPD, `rust/spd`),
which is not converged at theta 0.8 and 1.0 (P5) and approaches from below (P6). A second method with a different
error mechanism gives a bracket: if two unrelated approximations agree, the value is likely; if they disagree, the gap
is the honest uncertainty.

## Candidates

| method | error mechanism | fits | cost | tooling |
|---|---|---|---|---|
| SPD (have) | drops Pauli terms below delta (Heisenberg picture) | local observables, short operator spread | grows with spread | rust/spd |
| MPS along a snake path | truncates entanglement across the snake's cuts (bond dimension chi) | 1D-like or narrow lattices; the P6 patch (35 qubits, about 3 rows wide) is a good case | chi^3 per gate; long-range snake bonds hurt | Aer `matrix_product_state` (no new dependency), or psfz's own MPS (`rust/psfz/src/mps.rs`) |
| belief-propagation PEPS (BP-PEPS) | approximates the environment by belief propagation; misses loop correlations | heavy-hex lattices (sparse loops of 12): the tutorial's reference method | modest at small bond dimension | quimb (pip; the tutorial used it) |

Proposal: **MPS first for P6** (Aer is already installed; the patch is narrow) and **BP-PEPS for P5's 151 qubits**
(MPS on a 151-qubit heavy-hex lattice would need a very large chi).

## Steps (each checked against exact answers before any unanswered value is reported)

1. P6, t = 1..9: MPS with chi = 64, 128, 256, 512; per-qubit <Z_q> against the sealed answers (CPU t <= 5, pod t = 6..9).
   Record max and mean errors and the time. Pass mark proposed: magnetisation within 0.005 of exact at t <= 9 at the
   largest chi that runs in one hour on the pod.
2. P6, t = 10..15 (no answer): MPS at the passing chi and the next one up, next to SPD at delta 3e-5 and 1e-5. Report
   the three values and the spread; no verdict.
3. P5, t = 5..8: BP-PEPS at bond dimension 2, 4, 8 against the sealed answers (stage C pod answers, cones <= 33).
4. P5, t = 20: BP-PEPS at the passing bond dimension next to SPD (pod run of `spd_pod.sh`) and the device values (0.819,
   0.253, 0.050). Report the bracket; no verdict.

## What it will not settle

Two approximations can share a blind spot (both are local in some sense). Agreement makes a value plausible, not exact;
the paper would say "two independent classical estimates" and give both with their convergence tables.
