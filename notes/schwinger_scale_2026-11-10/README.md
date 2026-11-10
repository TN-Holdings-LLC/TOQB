# Schwinger model at N = 12-16: does the swap network still read? (home, 2026-11-10; estimate, no device time)

Owner 2026-11-10 13:16 JST: estimate the swap network's growth for N = 12-16 before planning a larger run.

**Counted, not simulated.** The circuit of `gpu/schwinger.py` (gauge field eliminated, so every pair of sites
interacts; swap network): per step N(N-1)/2 neighbour gates of 3 CZ each, and each qubit takes part in N - 1 of
them, so 3(N - 1) CZ per qubit per step (N 6: 45 per step, N 8: 84, as built on 11-09).

**The line from 11-09 (marrakesh, one run).** N = 6 at 5 steps (75 CZ per qubit) READ for all three sets; N = 8 at
5 steps (105 per qubit) did not read for M1 and M3. Taken as a rough bound of about 90 CZ per qubit (one device, one
day; an estimate, not a rule):

| N | CZ per step (all) | CZ per qubit per step | steps until 90 CZ per qubit | t reached (dt 0.25) |
|---|---|---|---|---|
| 6 | 45 | 15 | 6 | 1.50 |
| 8 | 84 | 21 | 4 | 1.00 |
| 10 | 135 | 27 | 3 | 0.75 |
| 12 | 198 | 33 | 2 | 0.50 |
| 14 | 273 | 39 | 2 | 0.50 |
| 16 | 360 | 45 | 2 | 0.50 |

**What it says.** Pair creation needs t of order 1 / w (4 steps or more at dt 0.25). With this circuit, N = 10 reaches
t = 0.75 and N = 12-16 only t = 0.5 inside the bound. A larger Schwinger run with the swap network would mostly
not read; the cost per qubit grows with N because the eliminated gauge field couples every pair.

**The direction (by formula, not search).** Keep the gauge field on link qubits (a truncated electric field), so every
interaction is between neighbours: about 2N - 1 qubits, and a constant number of CZ per qubit per step, independent
of N. Then N = 16 costs no more per qubit than N = 6. The circuit, its CZ count and the exact check (statevector up
to 28 qubits, so N <= 14 with links) are the next design step; nothing declared.
