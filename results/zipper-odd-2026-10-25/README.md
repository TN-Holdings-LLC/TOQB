# The zipper for odd n (analysis only; 2026-10-25)

The zipper ring schedule (TOQB `toqb/ring_zip.py`, PSF-Zero a24 with `PSF_RING_ZIP=1`) is defined for even n only.
`zip_any.py` extends it to every n >= 4 by formula, with no search:

- the same start order: 0, 1, 2, n-1, n-2, 3, 4, n-3, n-4, 5, ... (pairs from the two arcs, alternating);
- round A: CZ on positions (1,2), (3,4), ...;
- round B: CZ + SWAP at the left end (0,1) only (even n: also at the right end);
- round C: plain SWAPs on positions (2,3), (4,5), ...: (n - 3)/2 of them (even n: n/2 - 2);
- round D: CZ on positions (1,2), (3,4), ...;
- odd layers run the rounds backwards, as for even n.

CZ per layer for odd n: n + 1 + 3 (n - 3)/2 = **(5n - 7)/2** (9, 14, 19, 24 at n = 5, 7, 9, 11). For even n the
function returns exactly `ring_rounds_zip`'s rounds (checked for n = 4 to 40), so nothing changes there.

**Checks.**

- `check41.txt` (`python zip_any.py 41`): for every n from 4 to 41, one layer built on the line equals the ring's CZ
  layer on the start positions followed by a permutation (Clifford equality, Qiskit), the layer followed by itself
  backwards is the identity, and the CZ count (an end block CZ + SWAP counted as 2) is 5n/2 - 4 (even) or
  (5n - 7)/2 (odd).
- **It is the least known.** `odd5.txt` ... `odd11.txt`: IDA* from every start layout of minimum ring length
  (`zipper_bound N (3n-7)/2`, bound_rs `de3640b`) reaches (3n - 7)/2 extra only from the zipper's start and its
  images under the ring's and the line's symmetries, and the schedule it prints is this one (one end block, then the
  middle SWAPs). The exact cost-to-go over every
  state (`results/zipper-bound-2026-10-24/hstar`) gives the same least for n = 5, 7 and 9 from every start layout.
  As for even n, this is a search result, not a proof for every n.

**In the compilers (owner, 2026-10-25: "a change of specification is fine").** PSF-Zero `fab3602`: AI front end a25
(item 49) and `rust/psfbind` ring r3 build this schedule for odd n with `PSF_RING_ZIP=1`; every other output is a24's,
bit for bit (PSF-Zero `patches/psf_ai_compile_a25_2026-10-25/check_a25_result.txt`). TOQB's default front end is a25
from this commit on (`toqb/task_loop.py`); `tests/test_a25_odd_zip.py`: the `psfai:template_zip` arm on the marrakesh
snapshot builds n = 5, 7, 9, 11 at L = 2, 4 with (5n - 7)/2 CZ per layer and the logical model's P(1) (statevector,
to 1e-9). TOQB's own `ring_zip.py` (the prototype's copy, report only) stays even-only. Not run on a device.
