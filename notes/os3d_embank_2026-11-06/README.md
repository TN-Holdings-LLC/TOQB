# Spread the load ("盛り土", owner 2026-11-06 23:15 JST): first numbers (design study, not declared)

v3.1 (fold): 108 CZ per step for 4x2x2; every y-bond of a block crosses that block's single bridge (load 4 on one
bridge; 11-06: q38's two ends decided the run).

Static layouts (no data moves; every bond a parity chain through empty qubits, 2 (d - 1) + 1 CZ; `embank.py`):

| layout | CZ / step | longest chain | max bonds through one qubit | bonds with no empty path |
|---|---|---|---|---|
| S1: 4 heavy-hex rows, x at cols 2,4,6,8 | 151 | 16 | 3 | 3 |
| S2: 4 rows, x at the bridge cols 3,7,11,15 | 152 | 6 | 2 | 4 |
| S3: 4 rows, x at cols 2,6,10,14 | 268 | 16 | 4 | 0 |
| S4: 2 rows, 8-column blocks | 115 | 17 | 3 | 7 |

Reading: a fully static spread either leaves bonds without an empty path (the data block the way) or costs 2.5 times
v3.1 and still puts 4 bonds through one qubit. The ring closure of the 2 x 2 (y, z) plane is what forces long chains
(the fold solved it with the block junction). A layout that spreads the y-bonds over 2-4 bridges needs some data
movement as well (swaps inside pairs), which is a larger design space: to be explored offline (a fixed template
designed once, then a rule), on a pod if it gets heavy.
