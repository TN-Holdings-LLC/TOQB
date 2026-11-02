# Separation note: calibration-only placement against self-measuring placement (workplace, 2026-11-02)

Status: **draft, not declared.** A TOQB note, not a paper. Whether any of it goes into Paper 6 is decided later by home
and the owner. **Every number here is from an Aer simulation, not a device result.**

| file | content |
|---|---|
| `separation_note.tex`, `.pdf` | the note (4 pages): terms, a two-point lower bound (near-trivial, stated only to fix terms), the self-measuring upper bound with its assumptions A1-A4, the construction (the centre), what neither proves, relation to the kingston observation |
| `construction_sim.py` | the construction in Aer on FakeKingston: an extra ZZ error on one coupler that acts only when a coupler at distance one is driven in the same ring layer; checks V1-V4 |
| `out/construction_result.json` | all numbers the note quotes (keys named in the tex `% src:` comments) |
| `out/construction_run.txt` | the run's printed output (188 s on a 2-core machine) |

Run (psf-os at eb20501, unchanged; qiskit 2.6.1, qiskit-aer 0.18.2):

```bash
PYTHONPATH=<psf-os> python notes/separation_2026-11-02/construction_sim.py WORK_DIR out.json
```

Fixed before the run and not tuned: planted coupler (42, 43) = positions 12-13 of the standard n = 20 ring (the
positions psf-os test T3 plants at on the n = 40 ring); coherent RZZ(pi/8); Pauli ZZ probability 0.15 (T3's value); seed 20261102; the three V4 flips
(position 12, position 13, all even positions).

Results in one line each (details in the note, Table 1):

- V1: a benchmark of the planted coupler alone gets 0 inserted errors and counts identical to the clean state (m = 2,
  8, 32, both models); with a distance-one coupler driven in the same layer it sees the error (Pauli 0.74625 / 0.2685 /
  0.24975, coherent 0.8755 / 0.1745 / 0.0250 of 4000 shots, clean 1.000).
- V2: Pauli model, a 16-site dead run over the coupler at n = 20, 40, 72; coherent model (n = 20), a 3-site dead run at
  mean 0.10, ring mean 0.39.
- V3: listed after two scans; usable sites 24 -> 40 (n = 40) and 56 -> 72 (n = 72), sentinel CLEAN; coherent n = 20:
  usable 20 -> 20 but ring mean 0.40 -> 1.00 (the 3 sites sat just under the line; the same circuit was flagged in 3 of
  4 runs).
- V4: local frame flips at either end of the coupler, and the global flip, cancel the coherent error exactly (every
  site 1.000); on the device the repair was partial.
