"""Review checks of psf_os.grid3d (workplace, 2026-11-06; home's 06l item 4). Not declared; no device.

1. FOLD_SCHEDULES: the positions each fixed schedule makes every value visit, from the identity and from the reversed
   start, the swap count, and the end permutation (must be the reversal of the start).
2. schedule(): which schedule the fold picks for N = 2, 3, 4 (first fit over the fixed tuple; no score, no search).
3. Every two-qubit gate of the placed circuit is on a coupler of the record (fits() checks failed couplers only).

usage: python check_fold.py PSF_OS_CHECKOUT DEVICE_RECORD
"""
import sys

sys.path.insert(0, sys.argv[1])
from psf_os import device as Dv  # noqa: E402
from psf_os import grid3d as G  # noqa: E402


def visits(sch, start):
    perm = list(start)
    seen = {x: {perm.index(x)} for x in range(4)}
    for rnd in sch:
        for i in rnd:
            perm[i], perm[i + 1] = perm[i + 1], perm[i]
        for x in range(4):
            seen[x].add(perm.index(x))
    common = set.intersection(*seen.values())
    return sorted(common), sum(len(r) for r in sch), tuple(perm)


print("1. FOLD_SCHEDULES")
for k, sch in enumerate(G.FOLD_SCHEDULES):
    for start in ((0, 1, 2, 3), (3, 2, 1, 0)):
        pos, sw, end = visits(sch, start)
        print(f"   schedule {k} start {start}: every value visits {pos}, {sw} swaps, ends {end}, "
              f"reversed {end == tuple(reversed(start))}")

dev = Dv.Device.load(sys.argv[2])
native = {frozenset(c) for c in dev.couplers}
print("2./3. placement on", dev.name)
for (L, M, N, t) in [(4, 2, 2, 1), (4, 2, 2, 2), (4, 2, 2, 3), (4, 3, 2, 1), (4, 2, 3, 2), (4, 3, 3, 2),
                     (4, 6, 2, 2), (4, 3, 4, 2)]:
    qc, placed, used, passes, info = G.physical(dev, L, M, N, t, 0.8, layout="fold", info=True)
    pairs = {frozenset(qc.find_bit(q).index for q in ins.qubits) for ins in qc.data if len(ins.qubits) == 2}
    off = sorted(sorted(p) for p in pairs - native)
    print(f"   {L}x{M}x{N} t{t}: {info}, passes {passes}, two-qubit pairs {len(pairs)}, not couplers {off}")
