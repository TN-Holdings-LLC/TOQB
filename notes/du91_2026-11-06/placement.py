"""Task X1 (DRAFT): can the 51 / 71 / 91-site chains be placed by translation on the device records we have?
Device records: the folders' device.json, or a job manifest's device (geometry and failed elements only).
usage: PYTHONPATH=<psf-os>:. python notes/du91_2026-11-06/placement.py OUT.json"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
from daily import du91 as X  # noqa: E402
from psf_os import device as D  # noqa: E402
from psf_os import lattice2d as L  # noqa: E402

RECORDS = [
    ("2026-11-05 daily", "results/daily/2026-11-05/ibm_marrakesh/dev/device.json"),
    ("2026-11-05 daily", "results/daily/2026-11-05/ibm_fez/dev/device.json"),
    ("2026-11-05 twirl", "results/twirl-explore-2026-11-05/ibm_marrakesh/dev/device.json"),
    ("2026-11-05 twirl", "results/twirl-explore-2026-11-05/ibm_fez/dev/device.json"),
    ("2026-11-04 practice", "results/practice-2026-11-04/dev/device.json"),
    ("2026-11-04 practice", "results/practice-fez-2026-11-04/dev/device.json"),
    ("2026-11-04 p6", "results/p6-device-2026-11-04/V/job/manifest.json"),
    ("2026-11-04 p6", "results/p6-marrakesh-2026-11-04/V/job/manifest.json"),
    ("2026-11-03 kim-e K", "results/kim-e-2026-11-03/K/V/job/manifest.json"),
]


def load(path):
    d = json.load(open(path))
    return D.Device(**(d["device"] if "device" in d and isinstance(d["device"], dict) else d))


def main(out):
    res = []
    for label, path in RECORDS:
        dev = load(path)
        row = dict(record=label, device=dev.name, failed_qubits=dev.failed_qubits,
                   failed_couplers=dev.failed_couplers, widths={})
        for n in X.WIDTHS:
            copies = {}
            for sh in X.SHAPES:
                try:
                    ch = X.snake(n, sh)
                except ValueError as e:
                    copies[sh[0]] = f"does not fit: {e}"
                    continue
                cs = L.copies(dev, X.edges(ch), ch)
                ok = [(dr, dc) for dr, dc, m in cs if not L.check(dev, X.edges(ch), m)]
                copies[sh[0]] = dict(copies=len(cs), qualifying=ok)
            p = X.place(dev, n)
            row["widths"][str(n)] = dict(per_shape=copies, chosen=None if p["shape"] is None else
                                         dict(shape=p["shape"], drow=p["drow"], dcol=p["dcol"]))
            print(label, dev.name, n, {k: (v if isinstance(v, str) else f"{len(v['qualifying'])}/{v['copies']}")
                                        for k, v in copies.items()},
                  "->", None if p["shape"] is None else (p["shape"], p["drow"], p["dcol"]), flush=True)
        res.append(row)
    json.dump(res, open(out, "w"), indent=1)


if __name__ == "__main__":
    main(sys.argv[1])
