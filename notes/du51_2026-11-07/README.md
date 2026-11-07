# Pre-run check of the N = 51 dual-unitary jobs (2026-11-07; no device, no noise)

Kit: `gpu/du51_build.py`, `gpu/du51_score.py`, `notes/du51_2026-11-07/mps_dry.py`; ibm_kingston's record of 04:33 CET
(S1 at copy (0, 0)); ring sentinel at its Clifford point (`--dry-clifford-sentinel`). Every point up to t = 8 and its
floor and mirror run with Aer MPS, noiseless, 4000 shots; deeper points and the sentinel get a placeholder count (so
the sentinel reads DEAD and the deeper points read 1: not part of the check). Run here on 2 cores, 15:03-16:15 JST.

Found and fixed before any device run:
1. The answer card lists a circuit's qubits by sorted label, not by chain site; the first scorer took site t as the
   card's t-th entry. Now the on-cone qubit is looked up by its label (the shape's snake, site t).
2. The MPS check ordered qubits by clbit (= sorted label), which put chain neighbours up to 15 apart; ordered along the
   placed chain it takes seconds per circuit.
3. A noiseless +-1 has SE 0 and made the rate fit divide by zero: the scorer floors the SE at 1e-4 (no effect on a
   device run with finite counts).

Result (`dry_scores_t4_t8.txt`, `gpu/du51_score.py ... --ts 4,8`): on-cone <X_t> against cos(2h)^t at t = 4, 8:
h 0.05 0.981 / 0.980, 0.958 / 0.961; h 0.10 0.922 / 0.923, 0.841 / 0.851; h 0.15 0.832 / 0.833, 0.698 / 0.694
(shot-noise SE about 0.01); off-cone max 0.029-0.048 (50 sites, SE 0.016); decay rates k 0.9948 / 0.9790 / 0.9556
against cos 2h 0.9950 / 0.9801 / 0.9553: AGREES at all three. The pipeline (placement, compile, cards, scoring)
returns the closed form.
