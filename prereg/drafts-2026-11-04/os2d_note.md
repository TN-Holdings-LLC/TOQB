# OS2D: the 2D OS core on a device: general placement and the user's own circuit as a mirror sentinel (drafted at the workplace, fixed at home, 2026-11-04)

Status: drafted by the workplace (4c2a5a2, `os2d_note_DRAFT.md`), fixed at home after the owner's go of 2026-11-04
(with the answer card added to the reported items). Builder `gpu/os2d_device.py` and scorer `gpu/os2d_score.py`; the
scorer was written before any device run and checked on synthetic counts only. Sent on the same day as P6's job, as a
separate job, after it (owner, 2026-11-04). psf-os 58b1423 (the workplace commit of this draft:
lattice2d.py, mirror2d.py; ising2d.place now goes through lattice2d with P6's six copies, result unchanged by test).

**Why.** psf-os checks 2D lattices with a ring echo, which does not cross the lattice's edges, and fez (stage E) showed
faults psf-os did not see. Two pieces of the 2D OS core are tried here: (G) placement of any edge set by translation
(`psf_os.lattice2d`), and (H) a sentinel made of the user's own circuit, U then U^dagger (`psf_os.mirror2d`), which
returns to |0...0> on every qubit and so needs no classical answer.

**Limit, stated first.** A mirror cancels some errors, coherent ones in particular (a static ZZ is cancelled exactly by
a frame flip in a mirror circuit; psf-os repair notes). A clean mirror does not show the problem's answer is right; a
failing mirror shows that something on those qubits loses the signal. This test asks whether the mirror's flags point
at the qubits where the problem (with exact answers) goes wrong.

## Device and placement

As P6's declaration (`prereg/drafts-2026-11-04/p6_device_note.md`): the least-queued of ibm_fez, ibm_marrakesh,
ibm_kingston read right before the fetch (ties: marrakesh, fez, kingston); the registry's mask on kingston; placement
`ising2d.place` (= `lattice2d.place` restricted to P6's six copies in their order; no search; reasons recorded); if no
copy qualifies, the next device by queue, and if none, no job.

## The job (one job, 4000 shots, no mitigation, options off, "stay", `psf-os submit`)

| cells | t | circuits | CZ per circuit |
|---|---|---|---|
| P6 problem, theta_x 0.53 | 1..5 | 5 | 76 t |
| readout floor, theta_x 0 | 1, 5 | 2 | 76, 380 |
| mirror of the theta_x 0.53 circuit (U, barrier, U^dagger) | 3, 5 | 2 | 456, 760 (acceptance: exactly twice U's count) |
| ring sentinel (echo D = 24, n = 40) | | 4 | |

13 circuits, 17.5 s by the time model (dry run on FakeKingston: copy (0, 0)). Answers: P6's CPU answers t <= 5
(`results/p6-answers-2026-11-04/answers_cpu.json`, sealed in f183ca5); floor and mirror: 1 exactly.

**The barrier is not optional.** Without it, the level-1 pass manager removed every CZ of a 6-qubit mirror (56 -> 0
in `tests/test_mirror2d.py`): U and U^dagger cancel at the join. The acceptance check (twice U's CZ count) guards it.

## The flag rule (fixed here)

For each qubit q: z0_q = mean <Z_q> over the floor cells, zm_q = mean <Z_q> over the mirror cells, d_q = z0_q - zm_q.
Flag q if d_q > median(d) + max(5 x 1.4826 x MAD(d), 0.05) (rule R's form: the healthy majority sets the line; 0.05
is the declared magnetisation line). An edge is flagged when both ends are. Subtracting the floor keeps a pure readout
fault (low z0 and low zm) from being blamed on the circuit; rule R handles readout separately.

## Judged (questions fixed in advance)

1. **Q1 — do the flags locate the problem's errors?** On the P6 problem cells (t = 1..5, all 35 qubits answered):
   MSE of the flagged qubits / MSE of the rest. **LOCATES** if the ratio is 2 or more, **DOES NOT LOCATE** below 2,
   **NOT TESTED** if no qubit is flagged.
2. **Q2 — does dropping the flagged qubits help?** MSE without them / MSE of all: **HELPS** at most 0.8, **NO EFFECT**
   between 0.8 and 1.25, **HURTS** at 1.25 or more; NOT TESTED if none is flagged.
3. **Ring sentinel:** CLEAN expected; reported if not.

## Reported, not judged

- P6 at t = 1..5: READS and AGREES as in P6's declaration, **with 2 SE (shot noise) of the magnetisation beside each
  t's difference** (new in this draft; the verdict is unchanged).
- **The answer card** (`prereg/drafts-2026-11-04/answer_card_DRAFT.md`, owner 2026-11-04: adopted for reports): beside
  each reported magnetisation, the value +- 2 SE (chance), and where answered the difference and difference / SE, the
  theta_x = 0 floor of the same t, and the sentinels' verdicts (bias indicators). A difference within the line but many
  SE away is written as within the line, but a bias. No verdict changes.
- The flagged qubits and edges, d, the line; the mirror signal at t = 3 and 5 separately; the floor; rule R's drops (as
  a comparison of the two checks).
- Whether the flagged set overlaps IBM's failed marks or the suspect rule's ends (expected: no, those are excluded by
  placement).

## Power, honestly

On a copy chosen to avoid failed and suspect elements, the mirror may flag nothing (NOT TESTED), and at t <= 5 the
problem's errors may be too small for Q1 to separate groups. A NOT TESTED result is a result: it says the placement
left nothing the mirror could find. The next step would then be a device or day with known faults, which cannot be
chosen without reading a map; the owner decides.

## A tighter READS (a proposal only; the declared rule is unchanged)

READS today asks MSE <= half the answer's mean square; with answers near 0.8 the line is about 0.3, which says the
signal is there, not that it is accurate. One tighter form: READS if the MSE is at most c times the shot-noise
variance expected at the measured values (mean of (1 - z_q^2) / shots), for a fixed c (for example 10). With 4000
shots that is about 1e-3: a real accuracy test, which today's devices may fail at depth. Another: READS on the floor-
normalised values (z_q / z0_q). Either would be fixed with the owner before a declaration, not applied to past runs.

## Dry run and checks (workplace)

- `tests/test_lattice2d.py` (psf-os): copies on FakeMarrakesh are real edges; the general enumeration of P6's pattern
  gives exactly its six copies in order; P6's placement equals the declared implementation on the fake snapshots, on
  the 3 Nov marks of fez and kingston (with and without the registry mask), and on 200 random sets of marks.
- `tests/test_mirror2d.py`: mirrors return every shot to |0...0> in simulation (6 qubits, t = 1 and 3); CZ exactly
  doubled; the P6 mirror build is accepted at t = 3, 5; the flag rule finds planted drops and does not blame a low
  readout.
- `gpu/os2d_score.py` on synthetic counts (two planted bad qubits, 23 and 44): flags [23, 44], Q1 LOCATES, Q2 HELPS.
