# Checks for Paper 4's lower bounds and cycle lengths (2026-10-26 evening; analysis only, no declaration)

Cloud container, Python 3 and networkx; qiskit-ibm-runtime fake devices for `cycles.py`.

- `cycles.py` -> `cycles.txt`: every simple cycle up to length 22 on FakeMarrakesh, FakeTorino, FakeFez, FakeKingston.
  Only lengths 12 and 20 occur (21 and 44 on Marrakesh, Fez, Kingston; 18 and 37 on Torino); no coupler joins two
  degree-3 qubits on any of them.
- `layer_bound.py` -> `pendants_single_layer.txt`: the cheapest single ring layer by Dijkstra over (layout, ring edges
  applied), from every start layout; operations CZ (1), CZ+SWAP (2), SWAP (3), move onto an empty qubit (2). Cycle
  m = 4, 5, 6 plus one leaf per hub, every set of one or two hubs (m = 6: up to rotation and reflection; the run was
  stopped after hubs (0, 3), the remaining sets (0, 4), (0, 5) being mirror images of (0, 2), (0, 1)). The least is
  n + k in every case, adjacent hubs included.
- `multi_layer.py` -> `pendants_multi_layer.txt`: L layers with interleaving allowed (ring edge e may fire for the
  (c+1)-th time once both neighbouring ring edges have fired c times). The least total is L (n + k) in every case run.
- `holes_only.py` (uses `layer_bound.py`'s search) -> `holes_single_layer.txt`: a bare cycle of m qubits with n nodes,
  cheapest single layer from the best start. Below n + 2h at (m, n) = (6, 4), (7, 4), (8, 5), (9, 6); equal at (8, 6).
  Stopped before (12, 8), which is too large for this search.

A single layer from the best start is not the steady per-layer cost of a schedule; these numbers are lower-bound checks
and counterexamples to the hole class bound outside its class, nothing more.
