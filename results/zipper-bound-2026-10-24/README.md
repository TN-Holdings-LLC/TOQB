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
