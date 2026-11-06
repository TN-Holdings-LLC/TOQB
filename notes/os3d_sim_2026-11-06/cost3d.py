"""CZ count and CZ layers (compile only, no noise): grid3d v1 (521ac5b), v2 (rows), v3 (fold, L = 4) and SABRE
(seeds 0..4, best and median) on one device record. usage: python cost3d.py PSF_OS DEVICE_RECORD OUT.json"""
import json
import sys

import numpy as np


def main():
    psf, devdir, out = sys.argv[1:4]
    sys.path.insert(0, psf)
    sys.path.insert(0, __file__.rsplit("/", 1)[0])
    import sim3d as S
    from psf_os import device as Dv
    from psf_os import grid3d as G
    from psf_os import mirror2d as Mi
    from psf_os.compile import RuleCompiler
    dev = Dv.Device.load(devdir)
    rc = RuleCompiler(dev)
    G1 = S.load_v1()
    lay = lambda c: c.depth(lambda i: len(i.qubits) == 2)
    rows = []
    for (L, M, N) in ((4, 2, 2), (4, 3, 2), (4, 2, 3), (4, 4, 2), (4, 3, 3), (4, 2, 4), (4, 6, 2), (4, 3, 4), (8, 2, 2)):
        n = L * M * N
        for t in (1, 2):
            r = dict(size=f"{L}x{M}x{N}", t=t)
            for name, fn in (("v1", lambda: G1.physical(dev, L, M, N, t, 0.8)),
                             ("v2", lambda: G.physical(dev, L, M, N, t, 0.8, layout="rows")),
                             ("v3", lambda: G.physical(dev, L, M, N, t, 0.8, layout="fold"))):
                try:
                    qc, placed, used, _ = fn()
                    c = S.compile_grid(dev, rc, qc, placed, n, name != "v1")
                    r[name] = (Mi.cz_count(c), lay(c))
                except Exception as e:  # noqa: BLE001
                    r[name] = None
            sab = []
            for seed in range(5):
                c = S.compile_sabre(dev, G.logical(L, M, N, t, 0.8), seed)
                sab.append((Mi.cz_count(c), lay(c)))
            sab.sort()
            r["sabre_best"], r["sabre_median"] = sab[0], sab[2]
            rows.append(r)
            print(r, flush=True)
    json.dump(rows, open(out, "w"), indent=1)


if __name__ == "__main__":
    main()
