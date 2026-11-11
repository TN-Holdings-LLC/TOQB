# Paper 8 draft 3: workplace read-through (2026-11-11; handover 11-10 item 1)

Checked: the TeX source at TOQB 290d045 against `out/tables.json` / `out/tables.md` (regenerated from the records: equal
to the committed ones) and the results' own README / BUILD files. The draft is not changed here except the table
captions (point B1, a mechanical fix in `tables.py`). Wording is for home and the owner.

## A. Statements that the records contradict (fix before release)

**A1. Section 2.1, "On the records of 7 to 9 November no fixed chain shape of daily/du91 fits 91 sites on any of the
three devices."** Two committed fez records of 7 November fit shape S3 (`daily.du91.place`):
`results/daily/2026-11-07/ibm_fez/dev` and `results/os3d-v31-2026-11-07/ibm_fez/dev` (failed qubit 72 only). The later
fez records of 7 November (failed 72 and 148) and every record of 8 and 9 read here fit no shape. Suggested:
"On ibm_fez a fixed shape (S3) fitted 91 sites on the records of 7 November until qubit 148 was marked failed; on the
records of 8 and 9 November no fixed shape fits on any of the three devices."

**A2. Section 6.4 and the abstract, Ising line against fold.** "The prediction (line closer everywhere) held on
4x2x2" and the abstract's "came closer to the exact answer on 4x2x2" go beyond Table 9: at 4x2x2 place 0, line was
farther at t = 2, 3, 4 (+0.0060, +0.0297, +0.0454, all resolved); line was closer at the judged place 3 (t 3, 4
resolved), at place 1 at every t (all resolved) and at place 2 from t = 3. Suggested: "held at the judged 4x2x2 place
(and at place 1, and at place 2 from t = 3), not at place 0, where line was farther from t = 2"; abstract: "came closer to the exact answer at the judged
4x2x2 place but farther on 4x3x2". Worth checking against prereg/isingL_2026-11-09.md, which place the prediction
named.

## B. Presentation

**B1. Double table numbers (fixed here).** Every appendix table printed as "Table 1: Table 1. ..." (the caption text
carried its own number and LaTeX added another). `tables.py` now drops the leading "Table N." from the LaTeX caption
only (tables.md unchanged); regenerated `out/tables.tex`; the source compiles (latexmk, no undefined references) and
prints "Table 1: The dual-unitary chain ...". The table order is unchanged, so the text's Table 1-10 still match.

**B2. Reference 1** names "IBM Quantum" as the author of arXiv:2411.00765; give the authors and title as published
(not checked here: no access to the outside sources beyond the records).

**B3. Open items already known:** PENDING commit hashes (Data and code); the contact address (handover 11-08 item 6:
`contact.love.os.architect@` or `love.os.architect@`); the GitHub URLs of TOQB and psf-os (not checked from the
workplace); the header comment (lines 1-6) still carries the DRAFT 1 / 2 notes and a stray "Was:".

**B4. Small consistency point.** Section 2.2 gives the sentinels of the marrakesh run (A DEAD, B CLEAN); section 2.4 does
not give those of the fez run (both DEAD, `results/night-2026-11-10/du91r/README.md`).

## C. Checked and equal to the records

Abstract and conclusion; 2.2 (MSE 0.0393 / 0.699, k and cos 2h, depth 24); 2.4 (MSE 0.2872 / 0.7595, k, depth 24 and 16
for h 0.10, ruler ratio 0.9982 +- 0.0015, +0.0037, series 0.04-0.11 at t 20-24); figure 1 caption range +0.0017 to
+0.0045; 3.2 (kingston 0.92 / 0.95 / 0.95 and smallest MSE sum of five; 4x6x3 0.88 / 0.88 / 0.86; mid: |1> floor marks on
every fez place, qubits 27, 63, 103, 126 shared); 4 (CZ up to 1464, retention 0.733-0.834, 4x2x2 READS t 1-6, bulk 0.68-0.73
against surface 0.74-0.83 at t 3); 5 (0.72 / 0.62 / 0.51 / 0.53, 176-692 CZ); 6.1 (Table 4; 41.6 % at t 4); 6.2 (both judged
places, resolved t 2-3 on marrakesh); 6.3 (28 of 32 counted from Table 5); 6.4 numbers at the judged places, 46 % fewer CZ,
all 8 cells of 4x3x2 farther; 7 (16 / 18 / 14 of 18, N 8 step 5 M1 and M3 at 420 CZ, Sum Z +0.115 to +0.612, 3 (N - 1));
8 (fronts, 2.1-3.9, 0.76-0.43, TVD 0.025-0.144); 9 (564 / 705 / 690 CZ, 0.61, 7-9 %, parity 0.50 / 0.12 / about 0, 17 values);
10 (Ising mean 0.987, 0.929-1.025; Heisenberg 1.15-1.28); limits (marrakesh 14 failed qubits on 10 November).

## D. Not checked here

3.2 "the gate alone would have refused it and every other place" (kingston); 9 "small mid-range values are near zero in
every product, as predicted"; limits: the kingston cluster that left only the weight-10 cone clear.
