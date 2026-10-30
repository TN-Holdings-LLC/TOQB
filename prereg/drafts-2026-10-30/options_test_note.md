# Options test on ibm_kingston (home, FIXED 2026-10-30 15:20 CET on the owner's go, before any fetch): do dynamical decoupling or gate twirling bring the dead sites back

**Why.** On ibm_kingston today, at n = 40 the rule's echo had the same 18 dead sites in two runs (3-7, 17, 27-29, 38,
49-55, 59; `rerun-rule-only/posthoc_live_sites/`). Read after the runs: their signed per-site signal is about 0 on
3-29 and negative (-0.15 to -0.30, the echo returns the wrong bit more often than the right one) on 38-59, which points
to a coherent error. Both runs had dynamical decoupling and twirling off. Both options read nothing from the
calibration and act the same on every qubit, so they fit the map-free standard as job options.

**Design (owner's go 2026-10-30 23:16 JST).**
- ibm_kingston, a new fetch after this note. `fold:rule` only. The mirror echo of test 2 at n = 20 (control, no dead
  sites today) and n = 40; hz = 0; one-way L = 12 (D = 24); h = 0.6; 4 inputs and 4 references; **1000 shots**.
  2 cells, 16 circuits, built once (`gpu/options_test.sh`).
- The same circuits are assembled into three jobs and submitted one after the other, each with one SamplerV2 setting
  (`s2rc_device submit --dd / --twirl`): **off** (the standard: no DD, no twirling); **dd** (dynamical decoupling,
  XY4, twirling off); **twirl** (gate twirling on, measure twirling off, DD off). Time model 7.9 s per job, 23.8 s
  in all.
- Map-free placement as always. If the day's n = 40 ring is not today's ring, the segment is its members on the ring.

**Reading.** Per measured qubit j, the raw signal a_j = mean over the 4 inputs of <s_j Z_j>, s = -z_in (1 = perfect,
0 = random, negative = the wrong bit more often), with its shot-noise SE (`toqb/echo_sites.py`). Segment G = the 18
qubits above; R = the rest of the n = 40 ring. For each job, the means of a over G, over R and over all sites.

**Judged (n = 40), for dd and for twirl, each against off.**
- **G (the dead sites):** HELPS if mean_G(option) - mean_G(off) > 2 SE (combined), HURTS if below -2 SE, else NO
  EFFECT.
- **Recovered:** mean_G(option) >= 0.8 mean_R(option).
- **R (the live sites):** the same HELPS / HURTS / NO EFFECT, to see whether the option costs the healthy part.

**Reported, not judged.** The same three numbers at n = 20 (control); the sub-blocks 3-29 and 38-59; rho_E per job;
the billed seconds; the fetch's time and calibration time. If off does not show the dead sites again, the verdicts
are still computed and reported with that note. Nothing read from these numbers changes this note.
