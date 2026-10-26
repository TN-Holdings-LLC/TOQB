# The count rule at n = 20-30 (compile only; 2026-10-26, the workplace's proposal 1)

`fold:rule` (toqb `145f38b`) on `snapshot:marrakesh`, `rule_big.py` (cloud container, CPU):

| n | 20 | 21 | 22 | 23 | 24 | 25 | 26 | 27 | 28 | 29 | 30 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| choice (cycle m) | ring (20) | pend (20) | pend (20) | holes (24) | ring (24) | pend (24) | pend (24) | holes (28) | ring (28) | pend (28) | pend (28) |
| two-qubit gates per layer | 20 | 22 | 24 | 25 | 24 | 26 | 28 | 29 | 28 | 30 | 32 |
| zipper, for comparison | 46 | 49 | 51 | 54 | 56 | 59 | 61 | 64 | 66 | 69 | 71 |
| active qubits | 20 | 21 | 22 | 24 | 24 | 25 | 26 | 28 | 28 | 29 | 30 |

- **Exact by Clifford simulation:** every rotation angle set to a random multiple of pi/2 (3 instances per n and
  L = 2, 4); every clbit's P(1) equals the logical model's (difference 0). A Clifford check is weaker than the
  statevector checks at n <= 19 (P(1) is 0, 1/2 or 1), but it catches a wrong edge, a missing CZ or a wrong read-out
  qubit.
- "ring": a cycle of exactly n, no extra gate.
- **Vanity:** 0.42-0.47 of the zipper's two-qubit gates. **Not known:** lam at these sizes (not run; 21-30 active
  qubits on the trajectory engine); no device.
