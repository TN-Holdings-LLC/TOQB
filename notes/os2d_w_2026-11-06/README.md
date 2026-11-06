# 2D OS fixes and additions (home's task W, 2026-11-06; workplace; not declared)

Constraint kept: `psf_os/user2d.py` and `psf_os/compile.py` unchanged (git diff empty). Every change is a new module,
a new option, or an error message. Proof that run2d builds the same circuits: `reproduce.py --gate-hash` rebuilt the
four run2d results of 11-04 / 11-05 from their committed device records and user circuits (Qiskit 2.6.1 here, 2.5.2
when they were built) and every compiled circuit has the same gates (4 of 4 GATES SAME); `reproduce.py` 9 of 9 SAME.

| item | what changed | what did not | for the daily record it needs |
|---|---|---|---|
| W1 flags (`psf_os/report2d.py`, `result2d --extended`) | new: unreadable (floor < 0.3), rule R (P6's formula, now in psf-os), the circuit's neighbours of both, M with and without them (and M_exact over the same qubits) | `user2d.card` and every verdict; the plain `result2d` output | nothing to report it; a declaration change only if a flag is to enter a verdict |
| W2 retention (same module) | retention, normalised error, per-qubit slope, MSE after one scale, CZ layers, decay per layer: identical to `gpu/daily_score.py` (checked on 11-05, both devices, to 1e-15); notes on the mirror and on the absolute criterion | daily_score.py (still the declared scorer) | none (report only); daily_score could call report2d later (a scorer change, owner) |
| W3 ring sentinel (`psf_os/ring2d.py`, prototype) | analysis: fez's ring DEAD in all 7 fez jobs (11-03 to 11-05), always the same stretch 67-66-65-64-63-56-43-42-41 (+47, 57, 36, 21 sometimes); marrakesh CLEAN in all 3. The stretch overlaps P6's patch at 36, 41, 42, 43, 47. Proposal A (report only, no circuit change): judge the sentinel beside a ledger of known-dead qubits (`verdict_beside_ledger`; prospectively, from earlier days only, 11-05 would read CLEAN with 9 known qubits set aside). Proposal B (circuit change): mask the stretch for the ring: through the registry it also moves the user (P32 (0,0) -> (4,0); B72, B102 refused on fez) and the ring still runs along part of it; a ring-only mask needs a new builder | the sentinel circuits and verdict as declared | A: a declaration change of how the sentinel is read; B: a new builder and a declaration change of the circuits |
| W4 gate hash (`psf_os/gatehash.py`, `psf-os gatehash`, `reproduce.py --gate-hash`) | a hash over (name, qubits, clbits, angles rounded to 1e-10), canonical JSON; the same across QPY versions (tested with two QPY versions: bytes differ, hash equal) | the manifest's `circuits_sha256` (kept; not replaced) | none to use it; writing it into the manifest would change job.py's output (owner) |
| W5 time model | `run2d` checks the time model before writing anything (a refusal in user2d left a half-written --out) and names a usable `--max-seconds`; job.assemble's refusal also gives the numbers | the model itself; the default 60 s | none (refusals only) |
| W5 shots per record (proposal only) | not built. job.assemble requires one shots value; the IBM side already sends per-pub shots (`sampler.run([(c, None, shots)])`); a manifest list `pub_shots` and the time model summed per circuit would allow it, with a uniform job unchanged byte for byte | | job.py and ibm.py changes (owner) |

## Found on the way (beyond the task)

- `run2d_stdout.json` and `report.json` in the committed records carry the absolute --out path of the machine that
  built them (`/tmp/claude-0/work/toqb/...`). No user name, but a local path in a record; calling run2d with a
  relative --out avoids it (no code change made, since report.json is written by user2d).
- On a good day rule R's floor line (median - 0.05 when the MAD is small) drops about 4 of 32-33 qubits and, with
  their neighbours, flags about 10: M without them moved by 0.002-0.024 on 11-05 (`cards_summary.md`). The flags are
  a report; they should not be read as a correction.
- The 11-05 fez floors were all above 0.5 (no qubit unreadable); the floor of -0.003 home mentioned was in the twirl
  exploration, whose records use their own names and are not read by `result2d`.

## Files

- psf-os: `psf_os/report2d.py`, `psf_os/gatehash.py`, `psf_os/ring2d.py`, `psf_os/cli.py` (result2d --extended,
  gatehash, run2d's early time check), `psf_os/job.py` (refusal message), tests `test_report2d.py` (6),
  `test_ring2d.py` (2), `test_cli_w5.py` (1).
- TOQB: `reproduce.py --gate-hash`; `notes/os2d_w_2026-11-06/cards/*.json` (extended cards of 11-04 / 11-05),
  `cards_summary.md`, `ring2d_fez.json`.
