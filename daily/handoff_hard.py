"""Checks of the hard problems H01-H03 before they go home (task W, as task T's section 6), no device:

  run2d     (PC) every H circuit through `psf-os run2d`, one job each, on the 11-05 device records (marrakesh, fez) and
            FakeKingston (its graph and failed marks only): CZ count, copy, time model, or the refusal as given; and
            the copies of each patch. Writes OUT/run2d_hard.json and keeps the compiled user circuits.
  noiseless (pod, GPU) the compiled user circuit of the first device that accepted it, without noise, against the
            raw answers: every qubit, by gpu/daily_answers.py on the compiled gates themselves (sx, x, rz, cz on the
            active qubits; H03 the whole 2^32 state, H01 and H02 each qubit's light cone in the compiled circuit).

usage: python daily/handoff_hard.py run2d OUT_DIR SCRATCH_DIR
       python daily/handoff_hard.py noiseless SCRATCH_DIR ANSWERS_HARD.json OUT.json [cupy|numpy]
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "gpu"))
sys.path.insert(0, os.path.join(HERE, ".."))

from daily import pool as P  # noqa: E402

IDS = [e[0] for e in P.HARD]
DEVICES = {"marrakesh_11-05": "results/daily/2026-11-05/ibm_marrakesh/dev",
           "fez_11-05": "results/daily/2026-11-05/ibm_fez/dev", "fake_FakeKingston": None}


def run2d(out, scratch):
    from daily import handoff_check as H
    from psf_os import device as Dv
    devdirs = {}
    for d, p in DEVICES.items():
        if p is None:
            p = os.path.join(scratch, "dev_" + d)
            if not os.path.exists(os.path.join(p, "device.json")):
                Dv.fetch_fake(d.split("_", 1)[1]).save(p)
        devdirs[d] = p
    r = H.run2d(scratch, devdirs, ids=IDS)
    os.makedirs(out, exist_ok=True)
    json.dump(r, open(os.path.join(out, "run2d_hard.json"), "w"), indent=1)
    return r


def noiseless(scratch, answers, out, backend="cupy"):
    import numpy as np
    import daily_answers as A
    from daily import handoff_check as H
    ans = json.load(open(answers))
    rep = {}
    for pid in IDS:
        ok = [d for d in DEVICES if os.path.exists(os.path.join(scratch, "run2d", d, pid, "report.json"))]
        if not ok:
            rep[pid] = dict(skipped="refused on every device")
            continue
        qc, m = H._compiled(scratch, ok[0], pid)
        c, idx = H._compact(qc)
        meas = c.copy()
        meas.add_register(__import__("qiskit").ClassicalRegister(len(m)))
        labels = sorted(m)
        for k, q in enumerate(labels):
            meas.measure(idx[m[q]], k)
        if P.entry(pid)[2] in A.FULL:
            got = A.full({0: meas}, backend, "single")["values"][0]
            how = "compiled circuit, whole state"
        else:
            got = A.cones(meas, backend, "single")["values"]
            how = "compiled circuit, light cone of every qubit"
        sealed = {int(k): v for k, v in ans[pid]["values"].items()}
        d = max(abs(got[idx[m[q]]] - sealed[q]) for q in labels)
        rep[pid] = dict(device=ok[0], method=how, qubits=len(labels), cz=int(sum(1 for i in c.data if i.operation.name == "cz")),
                        max_diff=float(d), ok=bool(d <= 1e-4))
        print(f"noiseless {pid} ({ok[0]}): {how}, {len(labels)} qubits, max |compiled - answer| {d:.2e}", flush=True)
        del got
    json.dump(rep, open(out, "w"), indent=1)
    return rep


if __name__ == "__main__":
    if sys.argv[1] == "run2d":
        run2d(sys.argv[2], sys.argv[3])
    elif sys.argv[1] == "noiseless":
        noiseless(sys.argv[2], sys.argv[3], sys.argv[4], *(sys.argv[5:6] or ["cupy"]))
    else:
        raise SystemExit(__doc__)
