# ibm_kingston, rule "top" (stop removed): 4 x 4 x 3 and 4 x 6 x 3 from one record (2026-11-07 daytime JST;
prereg/os3d_mid_kingston_top_2026-11-07.md, prereg/os3d_big_kingston_top_2026-11-07.md)

- Pushes: b55f4a7 (4 x 4 x 3, rule top), then abb4ef1 (adds 4 x 6 x 3). A fetch `fetch2/` (04:30 CET) came after
  b55f4a7 but before abb4ef1 and is not used; a fetch at 04:28 CET came before b55f4a7 and is not used either.
  Used: `fetch3/` (queue read 04:32:58 CET: marrakesh 2, fez 0, kingston 1; kingston fetched 04:33:13 CET).
- Record: failed qubits 112, 113, 121, 146; couplers 112-113, 121-122, 130-131, 145-146, 146-147.
- 4 x 4 x 3 (`mid_4x4x3/`): candidates 0-4 (r0 0 c0 0, r0 0 c0 4, r0 1 c0 0, r0 1 c0 4, r0 2 c0 0); 73 circuits,
  84.5 s by the model, gates 6d4cfde9c210, answers 346cc34a... (k = 5, as sealed).
- 4 x 6 x 3 (`big_4x6x3/`): candidate 0 (r0 0, c0 0); 25 circuits, 30.9 s, gates c8742871856d (the same circuits as
  the 04:03 CET kingston job: same record of failures), answers 7d874e25... (k = 1, as sealed).
- Stabilizer check on this record: every place of both sizes, t = 1-3, deviation 0.
