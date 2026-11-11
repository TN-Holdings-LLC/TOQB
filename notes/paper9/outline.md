# Paper 9 outline (DRAFT, workplace, 2026-11-11; skeleton for home and the owner; nothing declared, no device)

Status: skeleton only. Built from paper 8 draft 3 (the policy and the "ruler in every job" design of section 2.4) and
the Hubbard numbers of `notes/hubbard_2026-11-11/`. No result exists yet: the classical side waits for the VS POD
(`指示書_ハバード検算POD_2026-11-11.md`), the device side waits for a declaration. Author: TN Holdings.

**Owner's decision (2026-11-11 13:21 JST):** paper 9 = the reproduction of IBM's 2023 utility experiment + the 1D
Hubbard model with the ruler in the same job. Schwinger at larger N and the XX chain alone stay out (own papers).

**Part A, IBM 2023 reproduction (home, added 05:30 CET):**
- Exists: 11-10 ibm_fez, raw, Eagle graph embedded in Heron r2: Z_106 (4 steps) READS, weight-10 (5 steps) READS,
  weight-17 and Fig. 4a do not read (`results/utility-2026-11-10/`; now section and table 10 of paper 8 draft 3).
- New exact reach (`notes/reach_2026-11-11/`): Z_106 to 8 steps and weight-10 to 6 steps computed (Clifford points
  checked against Aer stabilizer on 127 qubits; values sealed); Z_62 8, weight-10 7, weight-17 6 on the home PC (VS).
- Device test to declare: depth scan per observable (where the device stops reading as steps grow), answers sealed.
- Moved from paper 8 (owner 13:23 JST): section text verbatim in `part_a_from_paper8.tex`; table 10 and the figure
  are `notes/paper8/tables.py` t10_utility and `figures.py` fig3. Items the workplace read-through could not confirm
  travel with it: "small mid-range values near zero in every product", and "on kingston only the weight-10 cone was
  clear" (`notes/paper8/review_workplace_2026-11-11.md`).

**Ruler note (home):** the U = 0 ruler has fewer CZ (8L - 8 against 10L - 8) and layers (10 against 12) than U > 0,
so it carries less noise; paper 8's h = 0 ruler had exactly the target's gates. Proposal: at U = 0 keep two mutually
cancelling CZ at each onsite position (kept from optimisation), so CZ and layers match while the answer stays free-
fermion exact. To decide before the declaration.

**Working title (Part B, as drafted):** *Fermions without mitigation: the 1D Hubbard model at 40 to 60 qubits, with its
own free-fermion ruler in every job.* (a joint title for A + B to be set)

**Central question:** paper 8 read spin chains (dual-unitary, 91 qubits) and 3D spin lattices, and checked the device
against an exact ruler run in the same job (h = 0). Does the same policy (placement by fixed rules from the coupling
graph and failed elements only, own controls in the job, no mitigation, answers sealed before the run) read an
interacting fermion model at sizes past exact diagonalisation, where the answer is still checkable classically?

**Not claimed:** quantum advantage (every answer is computed classically, by MPS for U > 0 and exactly for U = 0); that
the classical cost is a hardness bound (it is the cost of named tools on named machines); anything past the range the
classical check reaches.

## What already exists (workplace, checked, not declared)

| Piece | State | Source |
|---|---|---|
| Circuit (interleaved Jordan-Wigner, FSWAP network, first-order Trotter) | equal to the fermion operators, L = 3: 5.6e-16 | `hub_check.py` |
| Line only: needs a chain of 2L qubits | 40 to 60 qubits; rule C placed 91 | `hub_count.py`, paper 8 section 2 |
| Cost, U = 4: CZ 10L - 8 per step, 12 layers | L 20: 768 / 1152 CZ at 4 / 6 steps | `hub_count.py` |
| Ruler, U = 0 (the same circuit without the onsite gates): free fermions, exact at any L | against the statevector, L 2-5: 1.8e-15; L 45 in 0.14 s | `hub_ruler.py` |
| Ruler cost: CZ 8L - 8 per step, 10 layers (the transport and hopping are the same gates) | L 20: 152 against 192 per step | `hub_ruler.py` |
| Raw check per site: Z_up(i) + Z_dn(i) = 0 at any U from the Neel start | statevector, U = 4: 3.3e-16 | `hub_ruler.py` |
| Readable range on devices: 4-6 steps (38-58 CZ per qubit, 48-72 layers) inside what has been read | du91 48 / 49; Schwinger N 6 75 / 90 read, N 8 105 / 120 not | `README.md` |
| Classical check, U = 4 | ED stops at L 18-20 (546 GB at L 20); Aer MPS L 20 4 steps 120 s on 2 CPUs; 6 steps not finished | `mps.log`; VS POD pending |

## Sections

1. **Introduction.** From paper 8 (spin chains, the ruler in every job) to fermions. Why Hubbard: interacting, a
   standard target named in the literature, and its U = 0 limit is a free-fermion circuit of the same shape.
2. **The circuit on a line.** Encoding, FSWAP network, Trotter step, exactness, CZ and layers; why the line suits a
   chain placement (no routing).
3. **The ruler.** U = 0 is a matchgate circuit: the 2L modes map linearly, so every <Z> is exact at any size in
   milliseconds. Run in the same job as U > 0 on the same chain, it measures how the device treats this circuit shape;
   the device's U > 0 result is read beside it (as h = 0 in paper 8, section 2.4). The XX chain of `gpu/ff_xx.py` is
   the same object at one species.
4. **The classical check for U > 0.** MPS (Aer without truncation; quimb at several chi), the criterion fixed before
   the POD ran (02:13 CET 11-11), the (L, steps) reached. This fixes the declared sizes; past it nothing is claimed.
5. **Device runs** (declared): sizes and steps from section 4; per job U = 0 and U > 0 on one chain; floor, mirror and
   sentinels as in paper 8. Verdicts READS / AGREES / BEATS against the MPS answer sealed before the run; the per-site
   charge check recorded raw beside, never used to correct.
6. **Observables.** The charge per site is fixed at 1 by symmetry, so the signal is in the spin: spin imbalance in time,
   and its decay against U = 0 (the interaction slows or damps the free oscillation). To fix in the declaration.
7. **Limits.** Single device or day if so; Trotter error is part of the circuit's answer (the check is of the circuit,
   not of the continuum model); the classical cost depends on tools and machines.
8. **Reproducibility.** `reproduce.py` entries; answers sealed by hash; job IDs.

## Optional tracks (owner's choice; each could stay in its own paper)

- Schwinger at larger N (paper 8 section 7 read N 6, not N 8 at 5 steps): also a Jordan-Wigner chain; the per-qubit
  numbers above say where it stops.
- The XX ruler alone at 91 qubits (`gpu/ff_xx.py`, 180 CZ per step): a fermionic counterpart of du91.
- Not here: the classifier series (`prereg/qclf_2026-11-10.md`) belongs to paper 3's line.

## Open before writing (owner and home)

1. VS POD results: which (L, steps) the MPS check reaches (`VSから職場へ_ハバード検算_2026-11-11.zip`; the values zip
   stays sealed).
2. U value(s), dt, steps, L, devices and days (proposal after item 1).
3. Observable and verdicts (section 6), and whether the ruler enters a verdict or stays beside (paper 8 kept it
   beside).
4. Paper 8 first: A1 and A2 of `notes/paper8/review_workplace_2026-11-11.md`.

## Related work to cite and position against (home, 2026-11-11 06:15 CET; abstracts read, full texts not)

- Phasecraft + Google Quantum AI, arXiv:2510.26845: 2D Fermi-Hubbard dynamics on Willow, up to 6x6 (72 qubits),
  second-order Trotter up to 3 steps; post-selection on fermion number, TFLO (training on the U = 0 free-fermion
  circuit), shot reweighting (MESR), GPR smoothing, twirling, DD; checks by statevector (4x4), FLO at U = 0, Majorana
  propagation, TDVP chi 2048. Closest to part B. Their U = 0 circuit is used to correct; ours is kept beside, never to
  correct, and our sizes stay inside the classical check.
- Phasecraft + Quantinuum, arXiv:2510.26300: 2D Fermi-Hubbard on H2 (56 qubits, 7x4 torus, pi flux), 4 second-order
  steps; twirling, TFLO, GPR; claims beyond exact classical simulation (TDVP, Majorana propagation compared).
- Google Quantum AI, arXiv:2010.07965: 1D Fermi-Hubbard, 8 sites on 16 qubits; post-selection on particle number,
  averaging over 16 qubit assignments, Floquet calibration, spin echoes, rescaling by a damping model.
- Part A: Tindall, Fishman, Stoudenmire, Sels, PRX Quantum (2024), arXiv:2306.14887 (tensor-network simulation of the
  Eagle kicked Ising experiment). Also to check and cite: Begusic and Chan (Pauli-path simulation of the same
  experiment), Anand et al. (Berkeley, classical benchmarking of ZNE beyond exact verification).
- Analog Fermi-Hubbard simulators (fermionic atoms in optical lattices, e.g. Greiner at Harvard, Bloch at MPQ) for the
  introduction only; to check before citing. Schwinger (Martinez et al. 2016, CERN QTI) is out of paper 9.

## Owner's decisions, 2026-11-11 17:00 JST (home)

- Hubbard declaration range: the workplace proposal accepted (L = 20 and 30, 2 / 4 / 6 steps, U = 4; 8 steps as the
  edge; U = 0 ruler and per-site charge check beside; answers recomputed by the declaration's script and sealed, the POD
  values as an independent second computation). Still to settle before the declaration: whether the U = 0 ruler keeps
  cancelling CZ pairs so that its CZ count and layers match U > 0.
- psf-os exact_tn: the gate-order light cone balloons when commuting diagonal gates are written edge by edge (home
  check: refused at 2^83 for Z_106 at 8 steps in plain edge order; agrees with reach_tn to 1.7e-14 with colour-layer
  order). A commuting-run cone is not scheduled (owner: no time); callers order diagonal layers by colour.
