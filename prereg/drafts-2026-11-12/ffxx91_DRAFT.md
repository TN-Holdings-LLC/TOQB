# DRAFT (home, 2026-11-12; not declared until the owner fixes theta and the steps): XX chain at 91 qubits, depth scan

## Question

The 11-11/12 records say: within a family, reading stops along depth, at a place set by how fast the exact signal
shrinks (Hubbard: mean square of the answer 0.18 / 0.05 / 0.02 at 24 / 48 / 72 CZ layers; read at 48, not at 72). The
XX chain (free fermions, exact at any size and depth) keeps a large signal: mean square 0.26 / 0.20 / 0.18 / 0.17 at
2 / 4 / 6-8 / 10-12 steps for theta = pi/4 (0.17 / 0.18 at 16 / 20), and exactly 1 at theta = pi/2 (Clifford, every <Z> = +-1). With the same CZ
layers as Hubbard, does it read deeper?

## Circuits

`gpu/ff_xx.py` brickwork (Neel start), 91 qubits, built by `gpu/ffxx91.py` (chain by du91 shapes else rule C, user2d
batch, mirror from the compiled circuit, ring sentinel, 4000 shots). 4 CZ layers per step, 180 CZ per step; the two
thetas have identical CZ counts and layers.
- Home proposal: theta pi/4 (judged) and pi/2 (beside, as the full-signal ruler); steps 2, 4, 8, 12, 16, 20
  (8 / 16 / 32 / 48 / 64 / 80 CZ layers: past Hubbard's failing 72). Owner to confirm.
- Try-build on the 11-11 13:23 CET fez record with steps 2-12: 40 circuits, 47.6 s by the model, rule C chain; CZ 360 to
  2160; pre-run check (gpu/hub_check.py): pi/2 at every step and pi/4 at 2 and 4 steps by Aer MPS against the answers,
  worst 4.6e-11, mirrors at most 8.4e-14, ALL PASS.
- Try-build with the proposed steps (home, 11-12 23:30 JST, owner "進めて") on the 12:06 CET fez record
  (`ffxx91_trybuild_1112b/`): steps 2, 4, 8, 12, 16, 20, rule C chain, 40 circuits, 47.6 s by the model (the same count
  as steps 2-12: six steps replace six); CZ 360 to 3600, CZ depth 8 to 80; circuits_sha256 56a6d30f...; pre-run check:
  pi/2 at every step (Aer MPS, worst 6.9e-14, mirrors at most 8.4e-14) and pi/4 at 2 and 4 steps (worst 4.6e-11, mirrors
  1.4e-13), ALL PASS. Answers sha256 30e29604... (sealed outside the repository).

## Answers

Free fermions (`F.z_exact`), sealed until the verdicts (try-build answers sha256 6d7227d1..., steps 2-12; 30e29604...,
steps 2-20). The declared build writes them again; their hash goes into the declaration.

## Verdicts (gpu/hub_score.py, unchanged; the per-site charge is skipped for an odd chain)

READS per circuit (MSE <= mean square / 2); AGREES (|z - e| <= 0.05); readable depth = the deepest READS step.

## Prediction (to fix with the declaration)

theta pi/2 READS at every step; theta pi/4 READS at least to 12 steps (48 layers, mean square 0.17 against Hubbard's
0.05 there); 16 and 20 steps (64, 80 layers, mean square 0.17 / 0.18) open.
