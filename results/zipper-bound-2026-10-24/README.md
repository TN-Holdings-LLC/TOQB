# Is the zipper the least? n = 10, 12 and 14 by exhaustive search (analysis only; 2026-10-24, n = 14 2026-10-25)

`bound_rs/` is a Rust port of `results/zipper-P1-2026-10-22/bound.py` (same moves, costs, start layouts and IDA*
bound). It reproduces bound.py's n = 4, 6, 8 results (6, 11, 16 CZ per layer). `zipper_bound N LIMIT`; output as
printed in `nN.txt` (cloud container, 2 CPUs).

- **n = 10:** the least is 21 CZ per layer = 5n/2 - 4, found from the zipper's start layout (0, 1, 2, 9, 8, 3, 4, 7,
  6, 5); no start layout reaches 20 or fewer. 12 s.
- **n = 12:** the least is 26 CZ per layer = 5n/2 - 4, again from the zipper's start layout (0, 1, 2, 11, 10, 3, 4,
  9, 8, 5, 6, 7); none of the 1,024 start layouts reaches 25 or fewer. 18 min 38 s.
- **n = 14 (2026-10-25):** the least is 31 CZ per layer = 5n/2 - 4; none of the 4,096 start layouts reaches 30 or
  fewer. `n14.txt`, every shard's output in `n14_shards.tgz` (SHA-256 fac4107e…). Run on a CPU pod (AMD EPYC 9575F,
  32 vCPU, 30 workers) with `run_bound14_pod.sh` and the shard option of `bound_rs` (`de3640b`): 64 shards, 45 min,
  11.3 CPU hours.
- **Only the zipper and its mirror image reach the least**, at n = 10, 12 and 14 alike: at n = 14 the start layouts
  (0, 1, 2, 13, 12, 3, 4, 11, 10, 5, 6, 9, 8, 7) (the zipper's) and (0, 13, 12, 1, 2, 11, 10, 3, 4, 9, 8, 5, 6, 7) (its
  reflection i -> n - i); every other start layout needs more.
- **Limit of the claim (unchanged from bound.py):** the search starts from every layout of minimum total ring length
  (256 at n = 10), not from longer layouts; within that class the zipper is optimal for n = 4, 6, 8, 10, 12 and 14. Whether 5n/2 - 4 is a lower bound for
  every start layout and every even n is not shown by any search here.

## Every start layout, n = 4, 6, 8 and 10 (2026-10-25)

`ZB_ALL=1 zipper_bound N LIMIT [k/K]` searches every layout of the n ring nodes on the line, one per class under the
ring's symmetries (rotation and reflection of the labels) and the line's reflection, instead of the minimum-length
layouts only. Output in `all/` (cloud container, 2 CPUs; n = 10 in two shards).

| n | start layouts (classes) | least extra / CZ per layer | start layouts reaching it | search below it |
|---|---|---|---|---|
| 4 | 3 | 2 / 6 | 1: (0, 1, 2, 3) | nothing at extra 1 (`allm4.txt`) |
| 6 | 38 | 5 / 11 | 1: (0, 1, 2, 5, 4, 3) | nothing at extra 4 (`allm6.txt`) |
| 8 | 1,320 | 8 / 16 | 1: (0, 1, 2, 7, 6, 3, 4, 5) | nothing at extra 7 (`allm8.txt`) |
| 10 | 91,296 | 11 / 21 | 1: (0, 1, 2, 9, 8, 3, 4, 7, 6, 5) | none of the other 91,295 reaches 11 or less |

For n = 4 to 10, **5n/2 - 4 is the least over every start layout**, and the zipper's start layout is the only one
(up to symmetry) that reaches it. The restriction to minimum-length layouts removed no better schedule here. Still a
search, not a proof: n >= 12 over every layout, and every even n, are not shown.

## Towards a proof (2026-10-25; work in progress, nothing proven)

The cost of a schedule is s + 3t (s CZ+SWAP blocks, t plain SWAPs). The bound 5n/2 - 4 CZ per layer (extra 3n/2 - 4)
follows for every even n from two statements:

- **L1.** Every schedule needs t >= n/2 - 2 plain SWAPs.
- **L2.** A schedule with exactly t = n/2 - 2 needs s >= 2 CZ+SWAP blocks.

Then t >= n/2 - 1 costs at least 3n/2 - 3, and t = n/2 - 2 costs at least 3(n/2 - 2) + 2 = 3n/2 - 4; the zipper has
t = n/2 - 2 and s = 2 (as found by the searches at n = 10 and 12).

**Checked exactly, not proven:** `hstar/` computes the exact cost-to-go from every state (every layout, every set of
done edges) by a reverse Dijkstra, with the move costs as arguments (`hstar N CZSWAP_COST SWAP_COST`). Output in
`hstar/frontier.txt`: with CZ+SWAP free and SWAP 1, the least is n/2 - 2 (L1); with costs 1 and 20, the least is
20 (n/2 - 2) + 2 (L1 and L2 together); with costs 1 and 3, the least is 3n/2 - 4; for n = 4, 6 and 8, over every start
layout.

**More checks (2026-10-25, later).** `hstar/frontier.txt` now covers n = 4 to 9, odd n included (n = 9 in the cloud
container, about 6 min per cost setting), and the relaxed problem (`HSTAR_RELAX=1`: ring neighbours adjacent on the
line may swap at cost 0 without a CZ):

| n | least extra cost (costs 1, 3) | least plain SWAPs t (CZ+SWAP free) | same, relaxed | costs 1, 20 |
|---|---|---|---|---|
| 4 | 2 | 0 | 0 | 2 = 20*0 + 2 |
| 5 | 4 | 1 | 1 | 21 = 20*1 + 1 |
| 6 | 5 | 1 | 1 | 22 = 20*1 + 2 |
| 7 | 7 | 2 | 2 | 41 = 20*2 + 1 |
| 8 | 8 | 2 | 2 | 42 = 20*2 + 2 |
| 9 | 10 | 3 | (not run) | 61 = 20*3 + 1 |

So for every n from 4 to 9: t >= floor((n - 3)/2) plain SWAPs; at that count at least 2 CZ+SWAP blocks for even n and
1 for odd n; the least extra cost is floor((3n - 7)/2), i.e. 5n/2 - 4 CZ per layer for even n and (5n - 7)/2 for odd n
(9, 14 and 19 at n = 5, 7 and 9: the target for a zipper of odd n). The relaxed problem gives the same t up to n = 8:
L1 does not depend on the CZ+SWAP blocks needing an undone edge; it is a statement about orders alone.

**A structural fact behind L1.** A CZ+SWAP exchanges two ring neighbours, so it changes the relative order on the
line of that pair only. The relative order of any two nodes that are not ring neighbours changes only by plain SWAPs,
one pair per SWAP. L1 is therefore a statement about orders: making every ring edge adjacent at some time forces at
least floor((n - 3)/2) such pairs to change order. Not yet shown. Tried and too weak: per edge, the count of
crossings with edges at ring distance 2 or more must reach 0 at some time; one plain SWAP can lower up to four such
counts, and the bound this gives is far below n/2. No published result on this problem was found (closest: circular sorting,
Adin, Alon and Roichman).
