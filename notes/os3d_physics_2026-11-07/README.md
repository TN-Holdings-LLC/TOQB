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
