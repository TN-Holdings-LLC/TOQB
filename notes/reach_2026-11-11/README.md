# Wider exact region for the 2023 utility circuit (home, 2026-11-11)

Owner (09:18 JST): can the exactly computable region be widened now that the light-cone network is faster? (09:49:
"widen it if you can").

Circuit: IBM's 2023 kicked Ising on the Eagle 127-qubit graph (R_X(theta_h) layer, then R_ZZ(-pi/2) on every edge,
per step). Network: the diagonal hyper-edge light-cone form `gpu/utility_tn_diag.network_diag` (home VS, 11-10).
New tool: `gpu/reach_tn.py` (sliced tree so the largest intermediate fits a memory budget; slices summed by hand,
since `ContractionTree.contract` fails on hyper-edges as in utility_tn).

## Checks of the tool

- z106, 4 steps, forced to 512 slices: all 17 values against `utility_exact.tn_value`, worst 1.0e-13; Clifford
  points against Aer's stabilizer method on the whole 127-qubit circuit, |diff| 0 and 1e-17.
- Every new value below: |imag| < 1e-15; theta_h = 0 and pi/2 against Aer's stabilizer method (127 qubits), see
  `clifford_checks.txt` (all |diff| <= 4.4e-16). The angles in between have no independent check at the new depths;
  the network code is the same, depth-generic code that matched `tn_value` at small depth.

## Computed here (2 CPUs, 7 GB; 17 angles theta_h = k pi/32, k = 0..16)

| observable | steps | cone | tree (width / slices / cost) | per value | values (sealed) |
|---|---|---|---|---|---|
| Z_106 | 8 (was 4) | 43 | 26 / 2 / 10^10.0 | 13 s | sha256 ff9c9673... (`z106_t8.jsonl`) |
| weight-10 | 6 (was 5) | 42 | 27 / 4 / 10^10.5 | 57-92 s | sha256 92b0f61e... (`w10_t6.jsonl`) |

Values are not printed or committed (they may become the sealed answers of a later job); the files are held at home
(scratchpad `sealed/reach/`).

## Searched, not computed (trees from `scan.py`; `trees_300s.jsonl`)

| observable | steps | cone | best width / cost found | search |
|---|---|---|---|---|
| Z_62 | 8 | 65 | 31 / 10^11.2 | 60 s |
| weight-10 | 7 | 49 | 30 / 10^11.2 | 300 s |
| weight-17 | 6 | 82 | 35 / 10^12.9 | 300 s |
| Z_106 | 10 | 57 | 38 / 10^14.2 | 300 s |
| Z_62 | 10 | 92 | 52 / 10^17.6 | 300 s |

- The search result depends strongly on search time: Z_106 at 8 steps gave width 76 / 10^24.1 after 60 s and
  26 / 10^10.1 after 150 s; weight-10 at 7 steps gave 58 / 10^19.1 after 60 s and 30 / 10^11.2 after 300 s. The
  numbers above are upper bounds, not limits.
- With a 2^27 memory target here, Z_62 at 8 steps needs 4096 slices (10^13.0, ~3.5 h per value, stopped) and the
  weight-10 at 7 steps search gave 2^30 slices (stopped). Both go to a PC with more memory (larger target, fewer
  slices).
- Speed here: 10^10 flops-equivalent ~ 10-15 s per value (memory bound; weight-10 slower per flop).

## Old and new limits (this circuit)

- Before: Z_106 4 steps, weight-10 5 steps, weight-17 5 steps (11-10).
- Now computed: Z_106 8 steps, weight-10 6 steps.
- In reach on a larger PC (estimated from the trees, not run): Z_62 8, weight-10 7, weight-17 6; Z_106 10 is hours
  per value. Z_62 10 is out of reach with the trees found so far.
