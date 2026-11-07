# Pre-run checks for part A (3D kicked Ising: theta sweep, time trace, bulk against surface), 2026-11-07

- Builder `gpu/os3d_v31_build.py --thetas`, scorer `gpu/os3d_v31_score.py` (theta tags, bulk/surface classes);
  regression: the recorded fez 4 x 4 x 3 run scores as recorded (rule top: candidate 1).
- Light-cone answers for 4 x 4 x 3 at theta 0.4, 0.6, 0.8; t = 1 equals cos theta (0.9211, 0.8253, 0.6967). A first
  attempt passed theta 0.12 instead of 1.2 by a shell slip; caught by that t = 1 check and recomputed.
- Noiseless run (`noiseless.py`, Aer statevector) of the whole 4 x 2 x 2 job (t = 1-6, theta 0.4/1.2/0.8 first):
  87 of 90 arms READ/AGREE/BEAT; the 3 that did not were theta 1.2 at t = 6, where the exact M is 0.016. With theta
  1.2 the exact M is at most 0.05 from t = 3 on (4 x 4 x 3: 0.049 at t = 3), so the owner replaced 1.2 by 0.6
  (19:56 JST, "1"). With theta 0.4/0.6/0.8: 90 of 90 READ/AGREE/BEAT (`noiseless_4x2x2_kingston.txt`).
- Try-builds on kingston's record of 11:14 CET: 4 x 4 x 3, 5 places, 181 circuits, 205 s by the model; 4 x 2 x 2,
  4 places, t = 1-6, 286 circuits, 322 s.
- Not checked: noise at 4 x 4 x 3 (56 qubits, beyond the statevector simulator).

# Part B (3D Heisenberg on the folded layout), first checks (2026-11-07 night)

- `gpu/heis3d.py`: the folded layout v3.1 unchanged except the bond gate U = exp(-i dt (XX + YY + delta ZZ)) (one
  two-qubit block, at most 3 CZ by the analytic KAK; SWAP . U on the swaps that carry an x-bond; y-bonds by moving
  the qubit onto the empty bridge and back), Neel start, every bond logged as a site pair.
- Placed against logical (kingston record of 14:35 CET, 4 x 2 x 2, 18 qubits, statevector): t = 1 and 2, every site
  <Z> equal to the logged Trotter product to 1e-16, every bridge back in |0> to 4e-15.
- Compiled by psf-os's RuleCompiler: 176 CZ in 49 layers per step (Ising v3.1: 108 in 28), t = 2: 348 CZ, 95 layers.
- The draft's dt = 0.25 leaves almost no signal: exact Neel order m_s = 0.104 at t = 1, -0.007 at t = 2. By dt
  (t = 1-4): 0.05: 0.932 0.757 0.530 0.308; 0.08: 0.831 0.487 0.162 -0.068; 0.10: 0.746 0.314 -0.007 -0.192.
