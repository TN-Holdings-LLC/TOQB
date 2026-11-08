"""C baseline: CZ of psf-os's Ising fold (v3.1 merge=True, v3.2 merge='carry') per lattice, RuleCompiler with
rzz_exact (grid3d.prepare), on the fez record; t = 1, 2 (per-step cost = difference)."""
import sys
from psf_os import device as Dv, grid3d as G
from psf_os.compile import RuleCompiler
dev = Dv.Device.load(sys.argv[1]); rc = RuleCompiler(dev)
for (M, N) in ((2, 2), (3, 2), (2, 3), (2, 4), (4, 3), (6, 3)):
    row = []
    for merge in (True, "carry"):
        try:
            c = [G.prepare(dev, 4, M, N, t, 0.6, layout="fold", rc=rc, merge=merge)["cz"] for t in (1, 2)]
            w = G.prepare(dev, 4, M, N, 1, 0.6, layout="fold", rc=rc, merge=merge)["where"]
            row.append(f"{'v3.1' if merge is True else 'v3.2'}: t1 {c[0]} t2 {c[1]} (step {c[1] - c[0]}) at r0 {w.get('r0')} c0 {w.get('c0')}")
        except Exception as e:
            row.append(f"{merge}: {type(e).__name__} {str(e)[:80]}")
    print(f"4x{M}x{N}: " + " | ".join(row), flush=True)
