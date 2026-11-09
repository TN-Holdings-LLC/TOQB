# Paper 8 outline (DRAFT, workplace, 2026-11-10; handover 11-09 item 4; skeleton for home and the owner)

Status: skeleton only. Numbers are not typed here as results; every claim points to a committed record, and the
tables are to be generated from those records by `notes/paper8/tables.py` (to be written, in the form of
`notes/paper7/tables.py`: committed records in, tables.md / tables.tex / tables.json out, nothing typed by hand).
Every device result named below re-scores to the same numbers from its committed raw counts (`reproduce.py`, 21 of 21
at TOQB 114c8f9). After-the-fact numbers are marked "after the fact". Author: TN Holdings.

**Working title:** *Wider and deeper without mitigation: IBM's dual-unitary chain at 91 qubits, and 3D lattices
through a placement-only OS.*

**Central question:** paper 7 carried user-written 2D circuits through an OS that reads no map. Does the same policy
(placement by fixed rules from the coupling graph and failed elements only, own controls in the job, no mitigation,
answers sealed before the run) carry to (a) a wider chain that no fixed shape can hold and (b) three-dimensional
lattices that heavy-hex cannot embed?

**Not claimed:** quantum advantage (every answer is computed classically); that any mitigation works; that a layout is
"better" in general (comparisons are per place and day, with the measure fixed in advance).

## Sections

1. **Introduction.** From paper 7 (doi:10.5281/zenodo.24046673: 2D entrance, daily record, du51 / du71) to wider and
   deeper. The no-map policy, unchanged; what is new: rule C, the 3D layer, the place rule "top", nMSE.
2. **The dual-unitary chain at N = 91 (headline).**
   - Placement: no fixed shape fits on the day's records; rule C (`psf_os.chain`, adopted 11-06 as not a search on the
     ground of reproducibility: fixed neighbour order, first fit, step count recorded). Record: 1,665 steps on
     marrakesh. Sources: `prereg/du91_2026-11-09.md`, `results/du91-2026-11-09/`, `notes/chain_detour_2026-11-06/`.
   - Checks before the run: the noiseless light-cone check of the run2d-compiled 91-qubit chain on the marrakesh record of
     11-05, t 4 and 8 (`notes/chain_detour_2026-11-06/README.md`, the same failed marks and 1,665 steps), and the h = 0
     stabilizer check (`notes/du71_2026-11-07/README.md`).
   - Verdicts as declared (READS; decay rate against cos 2h for three h; readable depth). Widths 51 / 71 / 91 side by
     side (Table 1), 51 and 71 from paper 7.
   - After the fact: the scatter of the fit is several times the shot noise (`notes/du91_2026-11-09`); h = 0.15 is
     slower than cos 2h in all three widths, with the ruler (h = 0) in a different job each time. Stated as an open
     point, with the remedy (the ruler in every job) as the next declaration.
3. **The 3D layer of the OS.**
   - Layouts: fold v3.1 (and v3.2 carry), line (Ising: `psf_os/grid3d_line.py`, 4x2x2 and 4x3x2; Heisenberg:
     `gpu/heis3d.py`). Fixed schedules found offline and kept as constants; translations in a fixed order.
   - Place choice: the gate (probes) worked at 16 sites and stopped every place at 48 and 72 sites; the owner's rule
     "top" (the place whose own t = 1 mirror is highest is judged; probe marks recorded beside). Sources:
     `prereg/os3d_gate_2026-11-07.md`, `prereg/os3d_mid_kingston_top_2026-11-07.md`, `results/os3d-*-2026-11-07`.
   - Report beside, never used: the calibration of the elements each arm used (`gpu/calib_beside.py`).
4. **Physics A: kicked Ising on 3D lattices** (`results/os3d-physA-2026-11-07`, fez; 4x4x3 and 4x2x2; theta 0.4 /
   0.6 / 0.8; t 1-3): READS at every theta and t; retention; bulk against surface (Table 2).
5. **Physics B: Heisenberg XXX 4x2x2** (`results/os3d-heisB-2026-11-08`, fez): READS, DIFFERS; Neel retention by t
   (Table 3).
6. **Layouts compared on the same places** (heisE: marrakesh and kingston, 11-08; `results/os3d-heisE*`).
   - CZ of the transport: old -> carry -> line (Table 4, from the builds).
   - Declared verdicts on retention; then the main measure changed to nMSE (`notes/reporting/layout_comparison_metric.md`)
     with the reason: noise that slows the exchange can raise an order parameter's retention. The two runs keep their
     declared verdicts; the nMSE comparison is reported after the fact (Table 5), including the place where the
     declared expectation failed (kingston t 4).
   - Ising line (`prereg/isingL_2026-11-09.md`): built, checked noiselessly; device result if run before submission.
7. **New problem: pair creation in the Schwinger model** (`prereg/schw_2026-11-09.md`, `results/schw-2026-11-09`,
   marrakesh; Martinez et al. 2016 form; N 6 and 8; three parameter sets; 1 / 2 / 5 steps). READS, BEATS (against the
   vacuum and all-zero guesses), AGREES on nu; the charge sum Sum Z (exactly 0) recorded raw as a check, never used to
   correct (Table 6). Candidate selection and the readout-order point (answers per label) from `notes/schwinger_2026-11-09`.
8. **Light cone in 3D, retried on a device** (`prereg/lc3d_2026-11-09.md`, `results/lc3d-2026-11-09`): fronts DIFFER
   (late), the shape of the spread matches; the earlier estimate that had dropped it (`notes/lc3d_2026-11-08`) beside.
9. **The simulator and the device** (`notes/os3d_sim_2026-11-07/realsim.py --expect`): Ising close, Heisenberg
   optimistic on retention, layout differences close (Table 7). The model is never fitted to the device.
10. **Limits and lessons (kept as results).**
    - Two mirrors (twirled): not added (`notes/two_mirrors_2026-11-08`), including a withdrawn hypothesis.
    - Three mirrors: usable at t = 1 only; the product rule fails with depth under gate-local noise alone
      (`notes/three_mirrors_2026-11-09`).
    - The retention bias that led to nMSE; the fit scatter at N = 91; h = 0.15; a declared expectation that failed.
11. **Reproducibility.** `reproduce.py` (raw counts -> the same scores; declared scorers unchanged, older scorer
    versions taken from the history where a scorer has grown); answers sealed by hash before each run; job IDs.

## Tables (numbering as in paper 7: one generator, one caption per table, a common footnote on the source records)

| Table | Content | Records |
|---|---|---|
| 1 | du51 / du71 / du91: device, rule (shape / C), CZ at t = 24, READS, k - cos 2h per h, readable depth | `results/du51-2026-11-07`, `du71-2026-11-07`, `du91-2026-11-09` |
| 2 | physA: theta x t, M / exact, retention, verdicts; bulk and surface | `results/os3d-physA-2026-11-07` |
| 3 | heisB: t, Neel retention, MSE, verdicts | `results/os3d-heisB-2026-11-08` |
| 4 | CZ per layout and t (old, carry, line; fold v3.1, line for Ising) | the builds' report.json |
| 5 | heisE: per place and t, retention difference and nMSE (after the fact) | `results/os3d-heisE*-2026-11-08` |
| 6 | Schwinger: N, set, steps, CZ, READS, BEATS, nu AGREES, Sum Z | `results/schw-2026-11-09` |
| 7 | Simulator against device (Ising, Heisenberg) | `notes/os3d_sim_2026-11-07`, the device scores |

## Open before writing

- The owner's go for this skeleton (handover 11-09: proposed, no answer yet).
- Whether the N = 91 rerun (ruler in every job) and isingL come before the paper.
- `notes/paper8/tables.py` (next workplace task if wanted).
