# Review of grid3d v3 and sim3d (workplace, 2026-11-06; home's 06l item 4; not declared, no device)

Checks: `check_fold.py` (psf-os df1472f, fez record of 11-05); output `check_fold.log`.

## 1. Does FOLD_SCHEDULES visit the positions it claims? Yes.

| schedule | claimed | visited by every value (from identity and from reversed) | swaps | ends |
|---|---|---|---|---|
| 0 | 1, 2, 3 | 1, 2, 3 | 6 | reversed |
| 1 | 0, 1, 2 | 0, 1, 2 | 6 | reversed |
| 2 | all four | 0, 1, 2, 3 | 10 | reversed |

Each schedule ends on the reversal of its start, so the next step starts reversed and the same schedule applies again
(`_covers` checks both the positions and that the end is the identity or the reversal). Bonds are applied after every
round of the schedule (and before the first), so "visits" means a bond can be made there.

## 2. Is the movement rule free of search? Yes.

- `schedule()` returns the first entry of the constant tuple FOLD_SCHEDULES that covers the needed positions (the
  bridge positions of the blocks plus position 3 / 0 for the z-bonds). No score, no cost, no comparison between
  candidates; the order is fixed in the source. The three schedules were designed offline (by hand / exhaustive
  check) and are constants; nothing is tried at placement time except the translations.
- Placement: `fold_offsets` gives a fixed order of translations (and the swapped M/N variant); the first that touches
  no failed qubit or coupler is used. Same rule as lattice2d. It reads only the coupling graph and the failed marks.

## 3. Findings (no change to the design)

1. **FakeFez model was applied to the wrong qubits (fixed in sim3d.py).** `compact()` renumbers the touched qubits to
   0..k-1; a per-qubit backend model (FakeFez) then applied the errors of physical qubits 0..k-1, and no CZ error at
   all on compact pairs that are not fez couplers among 0..k-1. Fix: `remap_noise()` restricts the model to the
   touched qubits and renumbers it the same way; readout from the model is applied per site exactly,
   <Z>_read = (1 - p10 - p01) <Z> + (p01 - p10). The uniform model was not affected (it is the same on every qubit).
   Idle errors (thermal relaxation during waits) are still not in the simulation: Aer applies the model's errors on
   gates only, and the circuits are not scheduled; so CZ-layer differences between the arms are under-counted.
2. **fits() checks failed couplers, not that every pair is a coupler.** On the fez record every two-qubit pair of the
   placed circuit is a coupler for all eight sizes checked (4x2x2 t1-3, 4x3x2, 4x2x3, 4x3x3, 4x6x2, 4x3x4). The labels
   assume the Heron numbering (16 row qubits + 4 bridges = 20 per row); bridges are read from the coupling graph and
   refused if missing, but row couplers are assumed. A one-line guard (`pairs <= couplers`, else try the next
   translation) would make this safe on another numbering. Suggested, not made (home's module).
3. SABRE with seed 0 gives 136, 269 and 456 CZ at t 1, 2, 3 (the best of five seeds in the compile table: 127 and 269 at t 1, 2).
4. Under the FakeFez model SABRE seed 0 crossed a coupler that the snapshot has as dead (106-107, CZ error 1.0) and the
   11-05 record does not mark; see the README. A model-mismatch artifact, recorded so that nobody reads it as a SABRE
   property.
