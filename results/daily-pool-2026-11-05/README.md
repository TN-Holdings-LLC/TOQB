# Daily pool of 2026-11-05 (task T): sealed exact answers, values not in git

- **Pool:** `daily/pool.py` (D01-D32 in a fixed order; FX-A, FX-B candidates for the fixed problem; S01-S06 scale
  problems on B102, not computed yet). Circuits with measurements in `circuits/<ID>.qpy` and `<ID>.qasm` (OpenQASM 3):
  anyone can recompute the answers exactly from them.
- **Answers:** exact statevector (`gpu/daily_answers.py`): P32 and C33 on the whole patch, B42 and B72 from each
  qubit's light cone (largest 29 and 31). One H100 80 GB, 2026-11-05 01:49-02:04 CET (`gpu/daily_pod.sh`, kit
  91fa9fd). No approximation, no randomness.
- **Sealed (addendum A):** the values are not committed. `sha256.txt` lists the SHA-256 of each
  `sealed/<ID>.json` (D01-D32, FX-B) and of `answers.json`, each written as
  `json.dumps(obj, sort_keys=True, separators=(",", ":"))` plus one newline. `sealed/` and `answers.json` are in
  `.gitignore` and are handed over apart from the bundle. `progress.txt` is the pod log without the lines that carry
  values (`daily/seal.py redact`).
- **Checks (`checks.json`), all passed:** K1 GPU = CPU light cones (P32, B42, B72 t 1-3; C33 t 1-4) max 3.6e-06; K2
  single = double (P32 whole patch D13, D09, D21, D08; the five largest cones of D12, D19, D28, D23; C33 at N 25)
  max 6.8e-06; K3 theta = 0 and Clifford points max 6.1e-07, F3 dual-unitary point N 25 double 2.1e-14, N 33 single
  1.1e-05 (tolerance 1e-4); K4 FX-A against the answer sealed on 2026-11-04 (`results/bank-2026-11-04/pod/du_bank`)
  2.5e-06.
- **Before the handoff (`handoff_check.json`, `daily/handoff_check.py`):**
  - independent CPU check (balls of radius t - 1, Aer statevector; C33 by MPS) of D01, D02, D03, D09, D13, D17, D18,
    D21, D26: max 4.7e-06. C33 only at t 8 (D01): t 10 by MPS took over an hour on the laptop and was left out;
  - `psf-os run2d`, one job per problem (D01-D32, FX-A, FX-B): FakeKingston and the 11-04 marrakesh and fez records
    accept all 34 (CZ as the problems need, e.g. D13 128, D04 192, D01 272; time model 10.8 s per job with its ring
    sentinel, 6.35 s for the three circuits user, floor, mirror); FakeFez and FakeMarrakesh refuse all 34 (no
    qualifying copy; the reasons are kept);
  - the compiled circuits (FakeKingston) without noise against the sealed answers: D13, D21, D01 whole (Aer MPS),
    D17, D03, D07, FX-B by light cones (Aer statevector): max 4.7e-06.
  - S01-S06 (B102) were not sent through run2d (they move to another day); B102 has 2 copies on every device, 1
    qualifying on the 11-04 fez record, none on marrakesh or the fake devices.
- **The pod's first run** stopped in K2 on a memory error of the script (the 64 GB double-precision state was still
  referenced); fixed in 91fa9fd and run again from the start. Its logs are kept with the pod logs.

## Proposals (the pool itself is unchanged)

1. **The fake devices refuse everything but FakeKingston.** FakeFez and FakeMarrakesh have no qualifying copy of
   any patch (each copy touches a coupler marked failed or a qubit next to one). If home's dry runs use a fake device,
   FakeKingston (or the device records of 11-04) is the one that lets every problem through.
2. **B102 has two copies only**, and on the 11-04 records one qualifies on fez and none on marrakesh. The scale
   problems S01-S06 would be refused on marrakesh as it was on 11-04; a narrower block (columns 0-7, more copies)
   would place more often.
3. **F3 at N = 33 in single precision** drifts by up to about 1e-5 by t 8 (K3) and the norm by up to 3.1e-05 (D27, t 20); far
   below a device's error, but the K3 tolerance for N = 33 single precision had to be 1e-4, not 1e-5.
4. **Five problems are marked as easy to guess** by the rule fixed before the answers were seen (|M| >= 0.9 or
   |M| <= 0.05 at the problem's t); they stay in the pool. Their IDs are in the report.
