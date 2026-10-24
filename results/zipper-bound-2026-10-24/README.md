# Is the zipper the least? n = 10 (and 12, running) by exhaustive search (analysis only; 2026-10-24)

`bound_rs/` is a Rust port of `results/zipper-P1-2026-10-22/bound.py` (same moves, costs, start layouts and IDA*
bound). It reproduces bound.py's n = 4, 6, 8 results (6, 11, 16 CZ per layer). `zipper_bound N LIMIT`; output as
printed in `nN.txt` (cloud container, 2 CPUs).

- **n = 10:** the least is 21 CZ per layer = 5n/2 - 4, found from the zipper's start layout (0, 1, 2, 9, 8, 3, 4, 7,
  6, 5); no start layout reaches 20 or fewer. 12 s.
- **Limit of the claim (unchanged from bound.py):** the search starts from every layout of minimum total ring length
  (256 at n = 10), not from longer layouts; within that class the zipper is optimal for n = 4, 6, 8 and 10.
