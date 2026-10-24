"""Circuit cost against size, compile only (flow A of 2026-10-24; report, no simulation, no claim):

    python -m toqb.scale_cost OUT.json [--n 10 12 14] [--L 16 24 32] [--device snapshot:marrakesh]

For each n, L and arm (item 31 `psfai:template`, the zipper `psfai:template_zip`, Qiskit
`qiskit:2:target:template`), compiles one model circuit of TOQB's ring classifier with random angles and records
the compiled CZ count, the scheduled duration on the device's Target, the number of active qubits, and the compile
time. Needs $PSF_ZERO_REPO (and $PSF_COMPILE_FILE, $PSF_AI_FILE as for every TOQB loop).
"""
from __future__ import annotations

import json
import os
import sys
import time

import numpy as np

from toqb import s2r as S
from toqb import task_loop as TL
from toqb.devices import get_device

ARMS = ("psfai:template", "psfai:template_zip", "qiskit:2:target:template")


def active_qubits(qc):
    return len({qc.find_bit(q).index for ins in qc.data if ins.operation.name not in ("barrier", "delay")
                for q in ins.qubits})


def main(argv):
    argv = list(argv)
    if not argv or argv[0].startswith("--"):
        print(__doc__)
        return 1
    out = argv.pop(0)
    if os.path.exists(out):
        print(f"STOP: {out} exists: an output is never overwritten", file=sys.stderr)
        return 2
    opts = {"--n": [10, 12, 14], "--L": [16, 24, 32], "--device": ["snapshot:marrakesh"]}
    key = None
    for a in argv:
        if a in opts:
            key, opts[a] = a, []
        else:
            opts[key].append(a)
    ns, Ls, dev = [int(v) for v in opts["--n"]], [int(v) for v in opts["--L"]], opts["--device"][0]
    device = get_device(dev)
    rng = np.random.default_rng(20261024)
    rows = []
    for spec in ARMS:
        arm = S.Arm(spec, device)
        for n in ns:
            for L in Ls:
                theta = rng.uniform(-1, 1, TL.n_params(n, L))
                x = rng.uniform(-1, 1, n)
                qc = TL.model_circuit(TL.angle_list(theta, x, n, L, np.pi / 2), n, L)
                t = time.perf_counter()
                try:
                    c = arm.compile(qc)
                    d, q2 = arm.duration(c, (n, L))
                    row = dict(arm=spec, n=n, L=L, q2=int(q2), duration_us=round(d * 1e6, 3), active=active_qubits(c),
                               compile_s=round(time.perf_counter() - t, 2), ok=True)
                except Exception as exc:  # recorded, not hidden
                    row = dict(arm=spec, n=n, L=L, ok=False, error=f"{type(exc).__name__}: {exc}"[:300])
                rows.append(row)
                print(json.dumps(row), flush=True)
    json.dump(dict(device=dev, arms=list(ARMS), rows=rows), open(out, "w"), indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
