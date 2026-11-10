"""Which sites ever stand on each bridge position during one step of the 4 x M x 2 line schedule (bridges {1,5},{3,7})."""
import sys
sys.path.insert(0, "/mnt/c/Users/Administrator/Desktop/psf_zero_project/ising_line_2026-11-08")
import ising_line as IL
start, ops = IL.schedule_for([(3, 7), (1, 5)])
for rev in (False, True):
    arr = list(start); seq = ops if not rev else list(reversed(ops))
    if rev:   # the reversed step starts from the end arrangement of the forward step
        for k, e in ops:
            if k != "U":
                arr[e], arr[e + 1] = arr[e + 1], arr[e]
    vis = {p: set() for p in (1, 3, 5, 7)}
    snap = [list(arr)]
    for k, e in seq:
        if k != "U":
            arr[e], arr[e + 1] = arr[e + 1], arr[e]
        snap.append(list(arr))
    for a in snap:
        for p in vis:
            vis[p].add(IL.NAMES[a[p]])
    print(("reversed" if rev else "forward ") + " step: " + "  ".join(f"pos {p}: {sorted(v)}" for p, v in vis.items()))
