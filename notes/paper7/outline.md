# Paper 7 outline (DRAFT, workplace, 2026-11-06; task V): a user's 2D circuits through an OS that reads no map

Status: skeleton for home. Numbers are not typed here; they come from `notes/paper7/tables.py` (out/tables.md, .tex)
and grow with the daily record. Every claim points to a committed record. After-the-fact numbers are marked "after the
fact". The text is finished at home.

**Working title:** *Exact answers, no map, no mitigation: user-written 2D circuits through a placement-only OS on IBM
Heron r2 devices.*

**Central question:** a user writes, in plain Qiskit, a 2D circuit whose answer is known exactly. The OS places it by
translation without reading any calibration-quality number, adds its own controls, and runs it with no error
mitigation. How close does the answer come, and how is that shown honestly?

**Not claimed (stated in the abstract and the conclusion):** quantum advantage. Every answer is computed exactly on a
classical machine (light cones of at most 33 qubits; P32 and C33 as whole states). No correction is claimed to work.

## Framing (owner / home, 2026-11-06, from the Zenodo counts of papers 1-6)

Paper 3 (a pitfall in comparisons, useful to other researchers) drew the most readers. Two parts of paper 7 are of
that kind and go to the front (abstract, introduction, first figures), ahead of our own device numbers:
1. **The bias of an absolute criterion, in both directions** (section 6): a DIFFERS can keep as much signal as an
   AGREES; a small-answer problem can AGREE while losing much. Any benchmark scored by |M - M_exact| <= c has it.
2. **Anyone can check every number** (section 8): `reproduce.py` re-scores every result from committed raw counts;
   answers sealed by hash before the run; job IDs for IBM.
The order of sections stays (methods before results); only the abstract, the introduction and figure 4 lead with these.
The counts behind this choice are small (tens of views per paper, repeat views possible): a hint, not evidence.

## Sections

1. **Introduction: the no-map policy.**
   - Placement reads the coupling graph and the failed / masked elements only; no quality numbers, no search, no
     selection by simulation (papers 5 and 6 policy, carried to 2D).
   - From paper 6 (10.5281/zenodo.23883938, the ring's self-check layer, 1D) to the 2D user entrance `psf-os run2d`.
   - Sources: psf-os README (a766073); `prereg/drafts-2026-11-04/os2d_note.md`.
2. **The OS's 2D layer.**
   - Placement by translation (`lattice2d.place`: the first qualifying copy in a fixed order; psf-os 58b1423);
     refusal with reasons when none qualifies.
   - Controls in the same job: floor (the circuit without non-diagonal one-qubit gates), mirror (U U^dagger; a fault
     locator, not an error measure), ring sentinel. Answer card per tag (user2d, a07cd76).
   - `rzz(+-pi/2)` written exactly as one CZ and two RZ (psf-os ac84182): CZ halved for P4/P5. Evidence: the CZ counts
     of the practice circuits before and after ac84182 (`results/practice-2026-11-04/README.md`, "CZ counts").
3. **Problems and answers.**
   - The problems follow published experiments: P4, the dual-unitary kicked Ising chain (arXiv 2411.00765); P5, the
     utility experiment's form (Kim et al., Nature 618, 500 (2023)); P6, the Qedma QESEM tutorial; the daily pool
     D02- and the hard problems H01-H03 (`daily/pool.py`).
   - Sealing: hashes committed before the values (12164be -> 50e412e for the daily pool).
   - Two independent computations per pool: GPU state vectors / light cones with checks K1-K4, and a CPU recomputation
     by another method (`results/daily-pool-2026-11-05/README.md`, `handoff_check.json`).
4. **Result 1: the practice problems (2026-11-04, 22 circuits x 2 devices).** Table (a).
   - Declared: READS 22/22 on both; AGREES 19/22 (marrakesh), 18/22 (fez); BEATS 19/22, 20/22.
   - P5 theta 0.4 misses by the same -0.04 to -0.07 on both devices (a systematic loss; answers near 1, the all-1 guess
     hard to beat).
   - Records: `results/practice-2026-11-04` (fb6e5dc), `results/practice-fez-2026-11-04` (87ca8dc).
5. **Result 2: the daily record (from 2026-11-05).** Tables (b) and (c).
   - Fixed FX-A: day-to-day and device-to-device spread (first points: 11-04 and 11-05 within 0.002 per device).
   - New problems in pool order; every night and device a row, failures included (`results/daily/RECORD.md`; standing
     rules `prereg/daily/standing_rules.md`, f54f3d9).
6. **Verdict and retention** (`notes/reporting/verdict_and_retention.md`, 904caa4).
   - The declared verdict first; retention R and normalised error beside it on every row; the absolute criterion's bias
     shown in both directions (D02 DIFFERS while keeping 0.82-0.86; FX-A AGREES while keeping 0.73 on fez).
   - Decay per CZ layer differs by family (D02 0.004-0.005, FX-A 0.007-0.013): no single device-health number.
7. **Negative result: correction.** Table (d).
   - Floor and mirror correction, declared (11-04): HELPS on both devices, but AGREES only partly; over-corrects at
     theta_x 0.8 on fez; leaves -0.13 to -0.15 on marrakesh (`results/corr-2026-11-04`, `results/corr-marrakesh-2026-11-04`).
   - After the fact (05b): the loss the mirror does not see sits next to the qubits rule R drops; synthetic noise shows
     why a mirror misses or doubles some errors (`notes/s1_2026-11-05`).
   - Twirl exploration (11-05, **not declared**): any frame randomisation cost D02 0.06-0.09 of raw signal; FX-A stayed
     over-corrected (`results/twirl-explore-2026-11-05`). A mirror-based correction is problem-dependent here.
8. **Reproduction.** `reproduce.py` (cb364e0: 9 of 9 re-scored the same from committed raw counts), the software
   versions (`results/ENVIRONMENT.md`, 6c51cec), three levels (re-score; recompute answers; rerun on a device).
9. **Limits.** Two devices (kingston's queue kept it out), few days, good hours of the day (floors 0.95-0.97);
   P6's outside comparison: our unmitigated gaps were larger than the tutorial's unmitigated ones on 11-04 (0.159 /
   0.210 / 0.201 against 0.091 / 0.139 / 0.180 at t 5 / 7 / 9; their gate implementation and shots not stated;
   `results/p6-device-2026-11-04/README.md`, 735226d); B72 / B102 problems placeable on fez only on the 11-05 records.
10. **Discussion: distance to the wall (an estimate, not a measurement).** `notes/paper7/wall_distance.md` (owner
    11-06: chemistry only through this number, no chemistry run on a device). With gamma fitted to our records, the
    FeMoco resource estimates (Lee et al. 2021; Reiher et al. 2017) would need, uncorrected, a gamma 5.5-13.4 orders of
    magnitude smaller; error correction changes the conclusion entirely.
11. **Conclusion.** What the record shows and does not; no advantage; no working correction yet.

## To fill as the record grows

- Tables (b), (c): every night (rerun `python notes/paper7/tables.py`).
- The hard problems H01-H03 (owner, 11-06): answers sealed 11-06; their rows go into (b) with a note of their size.
- Phase floor and neighbour rule: only if the owner runs them (drafts).
