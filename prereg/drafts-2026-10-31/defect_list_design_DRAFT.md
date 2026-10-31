# A defect list for quantum placement: memtest and a bad-block list (DESIGN DRAFT, home, 2026-10-31; not declared)

**Status.** Design and a working prototype (`toqb/defect_list.py`, `tests/test_defect_list.py`), replayed on the
device records of 30-31 October (`results/defect-list-replay-2026-10-31/`). No device run. Every parameter below is a
draft for the owner; nothing is fixed.

## 1. The model: what an operating system does with bad memory

| layer | in a computer | for a quantum device | today |
|---|---|---|---|
| hardware self-correction | ECC memory; SSD/HDD remap bad sectors to spares | quantum error correction | not available (vendors aim at 2029) |
| vendor self-report | SMART | the device's calibration (error rates, T1/T2, readout) | available; it did **not** show the 30 October defect |
| user-side test | memtest, badblocks | the rule's own mirror echo, read per ring site (Paper 5, P3) | built (about 40 s of QPU per device for four ring sizes) |
| bad list | Linux HWPOISON / `badram`, Windows `badmemorylist`, a file system's bad clusters | a dated per-device list of dead paths | prototype (this draft) |
| allocate around it | the allocator never hands out a listed page | the placement skips outlines that contain a listed path | prototype (`place`, `mask`) |
| retire on repetition | pages with repeated correctable errors are taken offline early | a path is listed after it is dead in at least 2 jobs | prototype |
| expiry | (memory defects are permanent) | a listing lapses unless seen again (defects may drift) | prototype; the expiry is open (the 3-day test sets it) |

## 2. Why the list holds paths, not qubits

On ibm_kingston (30 October) 17 of the 18 qubits of the dead run at n = 40 were healthy on another ring of the same
day (3-7, 17, 27 on the n = 20 ring; 27-29 and 49-53 on the n = 36 ring; 49-55, 59 on the n = 72 ring). The 18th,
qubit 38, was on no other ring, and it sits at the centre of the run. A memory-style ban
of qubits would have banned healthy qubits and would not describe the effect. By Lemma 2 of Paper 5 a single local
fault in a D = 24 echo reaches at most 12 sites each way, so the source most likely sits near the **centre** of a dead
run. The list therefore records the centre path (4 qubits, in ring order) of each dead run; placement avoids outlines
that contain that path.

## 3. The pipeline

1. **Scan** (user-side test): the rule's echo at D = 24 (hz 0, or averaged over hz), per ring site; dead run = at
   least `min_len` = 3 consecutive sites with signal below `thr` = 0.12 (minority rate 0.44).
2. **Ingest**: one observation per job and ring size: the ring, its dead runs, their centre paths, the job's
   submission time (`defect_list ingest`).
3. **Retire / expire**: sightings whose centre paths share at least 2 qubits are one entry; its path is the part
   common to all sightings. LISTED when seen in >= 2 jobs and last seen within the expiry (draft: 7 days); CANDIDATE
   after one job; EXPIRED after the expiry. A healthy ring through a listed path is reported as a contradiction
   (`defect_list status`).
4. **Allocate**: the rule's own placement (`fold.fold_place`: the shortest outline in the fixed order, working
   elements only) with one more condition: no listed path (`defect_list place`). For the unchanged build tools,
   `defect_list mask` writes a copy of the day's fetch with the middle coupler of each listed path marked failed; on
   the replay both give the same rings at n = 20, 36, 40 and 72.
5. **Verify**: the next scan checks the new ring; its observation enters the list like any other.

**Category.** The list comes from the user's own runs, not from the vendor's calibration, and it changes the
placement. It is therefore neither the map-free standard nor map-aware placement: a third category, *self-checked*,
always labelled as such. The map-free rule stays the standard and the reference.

## 4. Replay on 30-31 October (post hoc; `results/defect-list-replay-2026-10-31/`)

- Observations: kingston (test 2, test 3E, rule-only rerun, options test off), marrakesh (test 2, test 3E), fez
  (31 October).
- **LISTED (kingston):** centre [28, 29, 38, 49] (3 jobs; the n = 40 run of Paper 5), [11, 10, 9] and [87, 86, 85]
  (2 jobs each; the n = 72 runs). No contradiction: no healthy kingston ring passes through any of them.
- **CANDIDATE:** fez [6, 7, 17, 27], [26, 27, 28, 29], [63, 56] (one job); marrakesh [27, 28] (one job; one
  contradiction: marrakesh's healthy n = 36 ring passes 27-28) and [96, 103, 104].
- **Placement on kingston with the list:** n = 20 and 36 unchanged (no listed path on them); n = 40 skips 2 outlines
  and takes `band (0,1) 3 ((0,1),(0,3),(0,3))`, which leaves the run at 30-31-32-33-39-53 instead of 29-38-49; n = 72
  skips 38 outlines. The avoiding n = 40 echo was built from the masked fetch and passed the two-qubit acceptance
  (960 = 24 x 40).

## 5. An observation that limits the "chip, not circuit" reading (post hoc)

Some dead runs recur at the same ring positions on different chips with the same circuit:

- n = 72 (the same ring on all three devices): a dead run covering ring positions 57-64 in all four runs (kingston
  56-2 and 57-2 across the wrap, marrakesh 51-64, fez 49-68).
- n = 40 (the same ring on kingston and marrakesh): positions 0-17 on kingston, 3-10 on marrakesh.
- n = 20 (the same circuit on all three): dead only on fez.

So the dead runs depend on the chip (n = 20), but partly also on the position in the circuit. The idle time per site
of the compiled circuits is uniform (0.0-0.3 us of 5.15 us), so idling does not explain the recurrence. Paper 5
version 1.1 says "the dead runs follow the chip, not the circuit"; a precise wording is "depend on the chip, and
some positions recur across chips". A correction in its next version is proposed to the owner; not tested further
here.

## 6. Costs and limits

- The scan costs QPU time on every use (about 10 s per device and size at 1000 shots); the list saves it only if
  defects persist for days.
- Avoiding a path may move the ring onto another bad path: the list improves only by scanning again.
- The list cannot help a quantity that needs every qubit of a large ring if fresh defects appear anywhere on it.
- Whether defects persist, drift or move is the open question; the draft declaration
  `defect_days_DRAFT.md` asks it together with whether avoidance helps.
