"""Estimating lam without simulation (2026-10-26; prereg/drafts-2026-10-26/esp_check_note.md):

    python -m toqb.esp_est OUT.jsonl --cells n:L:arm ... | --n ... --L ... --arms ...

For each cell: model 0 of fold_lam (seed 1000 n + L), its first input, compiled by the arm for snapshot:marrakesh;
E1 = product of (1 - error) over every gate with an error in the Target (cz, sx, x, ...) and the read-out of clbit 0's
qubit; E2 = the same over clbit 0's backward light cone. The Target's errors evaluate, they choose nothing.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np


def estimates(c, target):
    ins = [(i.operation.name, tuple(c.find_bit(q).index for q in i.qubits), [c.find_bit(b).index for b in i.clbits])
           for i in c.data]
    def err(name, qs):
        if name not in target.operation_names:
            return 0.0
        p = target[name].get(qs)
        if p is None and len(qs) == 2:
            p = target[name].get(qs[::-1])
        return 0.0 if p is None or p.error is None else float(p.error)
    mq = [qs[0] for nm, qs, cl in ins if nm == "measure" and cl and cl[0] == 0][0]
    ro = err("measure", (mq,))
    e1, e2, cone = 1.0 - ro, 1.0 - ro, {mq}
    for nm, qs, cl in ins:
        if nm in ("measure", "barrier", "delay"):
            continue
        e1 *= 1.0 - err(nm, qs)
    seen_measure = False
    for nm, qs, cl in reversed(ins):
        if nm == "measure":
            continue
        if nm in ("barrier", "delay"):
            continue
        if set(qs) & cone:
            e2 *= 1.0 - err(nm, qs)
            cone |= set(qs)
    return e1, e2, mq, len(cone)


def main(argv):
    out = argv[0]
    if os.path.exists(out):
        print(f"STOP: {out} exists", file=sys.stderr)
        return 2
    opts = {"--n": [], "--L": [], "--arms": [], "--cells": []}
    key = None
    for a in argv[1:]:
        if a in opts:
            key = a
        else:
            opts[key].append(a)
    cells = [tuple(c.split(":", 2)) for c in opts["--cells"]]
    cells += [(n, L, a) for n in opts["--n"] for L in opts["--L"] for a in opts["--arms"]]
    from toqb import s2r2 as S2
    from toqb import task_loop as TL
    for n, L, arm in cells:
        n, L = int(n), int(L)
        rng = np.random.default_rng(1000 * n + L)
        theta = rng.uniform(-1, 1, TL.n_params(n, L))
        x = rng.uniform(-1, 1, (24, n))[0]
        plan = dict(name="esp", device="snapshot:marrakesh", verify=False, task=dict(n=n, layers=L, enc=float(np.pi / 2)),
                    predict=dict(traj=8, seed=1), standin=dict(t12=0.3, over=0.01, zz_hz=1e4, seed=20261017))
        row = dict(n=n, L=L, arm=arm)
        try:
            R = S2.Runner(plan, arm)
            c = R.compile(theta, x)
            d, q2 = R.arm.duration(c, (n, L))
            e1, e2, mq, cone = estimates(c, R.device.target)
            row.update(E1=round(e1, 5), E2=round(e2, 5), readout_q=mq, cone=cone, q2=int(q2), us=round(d * 1e6, 3))
        except Exception as exc:
            row["error"] = f"{type(exc).__name__}: {exc}"[:300]
        with open(out, "a", encoding="utf-8") as f:
            f.write(json.dumps(row) + "\n")
        print(json.dumps(row), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
