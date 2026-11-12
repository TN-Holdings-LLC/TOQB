# Ledger: how far the classical check reached, per problem (task E; home, started 2026-11-12)

One line per computed set of exact answers used to judge a device run (or a desk study). Machine "home container" =
2 CPUs, 7 GB; "home PC" = the owner's PC (home VS); "POD" = rented CPU pod. Times are wall clock. Add a line whenever
a new set of answers is made. Never write "classically impossible": this ledger records what was reached, with what.

| problem | size / depth | method | machine | time | record |
|---|---|---|---|---|---|
| dual-unitary chain (k = cos 2h) | any N (91 run) | closed formula; Clifford points by Aer stabilizer | home container | seconds | `gpu/du91r_check.py`, results/night-2026-11-10/du91r |
| XX chain (free fermions) | any N, any depth | single-particle matrix | home container | seconds | `gpu/ff_xx.py` |
| IBM 2023 utility, Z_106 | 127 q graph, 4 steps | `utility_exact.tn_value` | home container | seconds | results/utility-2026-11-10 |
| IBM 2023 utility, weight-17 | 5 steps | diagonal light-cone TN (`utility_tn_diag`) | home PC | minutes per value | notes/utility_repro_2026-11-10 |
| IBM 2023 utility, Z_106 | 5 / 6 / 7 / 8 steps (cone 25-43 q) | `gpu/reach_tn.py` (sliced diagonal TN) | home container | 13 s per value at 8 steps | notes/reach_2026-11-11 |
| IBM 2023 utility, weight-10 | 6 steps (cone 42 q) | `gpu/reach_tn.py` | home container | 57-92 s per value | notes/reach_2026-11-11 |
| IBM 2023 utility, Z_62 8 / weight-10 7 / weight-17 6 / Z_106 10 | trees only | cotengra search | home container | not computed (sent to home PC) | notes/reach_2026-11-11 |
| Hubbard 1D, U 4 | L 20 (40 q), 2 / 4 / 6 steps | quimb MPS, bond cap 1024 (largest bond 610) | home container | about 5 min in all | results/hubbard-2026-11-11/answers |
| Hubbard 1D, U 4 | L 30 (60 q), 6 steps | quimb MPS (bond 625) | home container | 691 s | results/hubbard-2026-11-11/answers |
| Hubbard 1D, U 4 | L 45 / 60 (90 / 120 q), 4 steps | quimb MPS (bond 217) | home container | 166 s at L 60 | results/hubbard-big-2026-11-11/answers |
| Hubbard 1D, U 4 | L 20-30, up to 8 steps | quimb / Aer MPS (bond 1722 at 8 steps) | POD 16 vCPU | 41 min for L 30, 8 steps | notes/hubbard_2026-11-11/pod_result.md |
| Hubbard 1D, U 0 | any L | free fermions (`hub_ruler.ruler_z`) | home container | seconds | notes/hubbard_2026-11-11 |
| classifier (fold:rule ring) | 20 q, 984 circuits | Aer statevector, batched | home container | 25-34 min | gpu/qclf_check.py |
| kicked Ising / Heisenberg 3D | up to 24 sites exact; larger by cone up to 26-29 q | statevector (psf-os grid3d, kim, job) | home container | minutes | psf-os; widened by psf-os exact_tn (41ed030) |
| Ohm desk study, weak wall | N 20 / 24, 12 cycles | statevector with typicality | home container | 130 s at N 24 | notes/ohm_2026-11-11 |
| Ohm desk study, one product state | N 40, 6 / 7 / 8 cycles | quimb MPS (bond 608 / 1496 / about 3700) | home container | 4 s / 50 s / over 10 min | notes/ohm_2026-11-11 (11-12) |
