# Defect list, replayed on the device records of 30-31 October (post hoc; no device run)

Prototype `toqb/defect_list.py` (design: `prereg/drafts-2026-10-31/defect_list_design_DRAFT.md`), draft parameters:
dead run = at least 3 consecutive ring sites with echo signal below 0.12 at D = 24 (averaged over the hz present);
centre path = the 4 middle qubits of a run; sightings sharing 2 qubits merge; LISTED after 2 jobs; expiry 7 days.

- `observations.json`: one observation per job and ring size (kingston: test 2, test 3E, rule-only rerun, options
  test off; marrakesh: test 2, test 3E; fez: 31 October), with the ring, its dead runs and their centre paths.
- `status.txt`: the list at 2026-10-31 12:00. LISTED on kingston: [28, 29, 38, 49] (3 jobs), [11, 10, 9] and
  [87, 86, 85] (2 jobs each), no contradiction. CANDIDATE: fez [6, 7, 17, 27], [26, 27, 28, 29], [63, 56];
  marrakesh [27, 28] (one contradiction: its healthy n = 36 ring passes 27-28), [96, 103, 104].
- `place_kingston.txt`: the rule's placement on the 30 October 14:02 kingston fetch with the list. n = 20 and 36
  unchanged; n = 40 skips 2 outlines (the 30 October ring among them) and takes
  `band (0,1) 3 ((0,1),(0,3),(0,3))`; n = 72 skips 38 outlines.
- `fetch_masked_kingston.json`: the same fetch masked by the list (middle couplers (9, 10), (29, 38), (85, 86) marked
  failed); the unchanged fold:rule build places the same rings as `place` at n = 20, 36, 40 and 72, and the avoiding
  n = 40 echo passed the two-qubit acceptance (960 = 24 x 40).

Read with care: 17 of the 18 qubits of kingston's n = 40 run were healthy on other rings that day (the 18th, qubit 38,
was on no other ring and sits at the run's centre), so the list holds paths, not qubits. Some runs recur at the same
ring positions on several chips with the same circuit (n = 72, positions 57-64 on all three devices), so the runs
depend on the chip and partly on the position in the circuit.
