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
- Owner 22:51 JST: dt = 0.05. `gpu/heis3d_build.py` (every fitting fold translation up to k = 4, t = 1-4, floor and
  mirror, ring sentinel) and `gpu/heis3d_score.py` (rule top; READS, AGREES on m_s within 0.05, retention). Try-build
  on kingston's record of 14:35 CET: 4 places, 52 circuits, 61.0 s by the model, CZ 176 / 348 / 520 / 692, exact m_s
  0.932 / 0.757 / 0.530 / 0.308. The whole job run noiselessly (`noiseless.py`): every arm READS and AGREES,
  retention 0.97-1.05 (shot noise). Noise estimate: `heis_sim_kit_2026-11-07.zip` on a POD (realsim, FakeFez noise).

## 2026-11-08: x-bonds carried on swaps (`--carry`; not declared for a device run)

The 6-swap fold schedules are reduced words of the reversal of the four columns: every pair of columns is swapped
exactly once per step, so every x-bond can ride on its swap. The declared layout took an x-bond at the first round
boundary where its columns were adjacent, and the later swap of the same pair went plain. With carry (an x-bond waits
when a later round of the step swaps its columns), per row and step 3 plain swaps instead of 5.

4 x 2 x 2 Heisenberg on the ibm_fez record of 2026-11-07 15:58 CET, compiled: CZ 176/348/520/692 -> 152/300/448/596
(t = 1-4), CZ layers 49/95/141/187 -> 46/89/132/175. Placed against logical (full statevector, 18 qubits): sites
to 7e-16, bridges back in |0>. The whole job run noiselessly: every arm READS and AGREES. The order of bonds changes,
so the exact answers change slightly (m_s at t = 4 0.3086 instead of 0.3078).

The same happens in psf-os's Ising fold layout (not changed): one step before compiling, 4 x 2 x 2 108 -> 92 CZ,
4 x 4 x 3 488 -> 464 (there the 10-swap schedule is not a reduced word, so fewer swaps carry).
