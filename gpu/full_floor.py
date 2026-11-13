"""Whole-device readout record for the quirk ledger (home, 2026-11-13; prereg/full_floor_2026-11-13.md).

Two circuits on every working qubit of the device (failed qubits left out): all qubits measured as prepared (|0...0>,
the floor) and after one X on each (|1...1>). No two-qubit gate. 4000 shots. Scored per physical qubit: floor
1 - z0 (0 -> 1 readout and idle) and 1 + z1 (1 -> 0 readout and decay). The record is beside every verdict and is
never used to correct; it is for the fair check of the quirk ledger (notes/quirk_rank_2026-11-13: a ledger that knows
only the qubits a day's jobs used cannot tell whether a re-ranked chain avoided the weak qubits).

usage: PYTHONPATH=<psf-os>:<notebook> python gpu/full_floor.py build DEV OUT ANS   (ANS: an empty marker file, kept
       so gpu/night.py treats this job like the others)
       PYTHONPATH=... python gpu/full_floor.py score OUT ANS   (writes OUT/full_floor.json)
"""
import json
import os
import sys

import numpy as np


def circuits(dev):
    from qiskit import QuantumCircuit
    qs = [q for q in range(dev.num_qubits) if dev.qubit_ok(q)]
    out = []
    for ones in (False, True):
        c = QuantumCircuit(dev.num_qubits, len(qs))
        if ones:
            for q in qs:
                c.x(q)
        c.barrier(qs)
        for k, q in enumerate(qs):
            c.measure(q, k)
        out.append(c)
    return qs, out


def build(dev_dir, out, ans):
    from psf_os import device as Dv, job as J
    from psf_os.user2d import _record
    for p in (out, ans):
        if os.path.exists(p):
            raise SystemExit(f"STOP: {p} exists")
    dev = Dv.Device.load(dev_dir)
    qs, cs = circuits(dev)
    runs = os.path.join(out, "runs")
    os.makedirs(runs)
    m = {q: q for q in qs}
    _record(dev, runs, "pff_zero", "user", "full_floor", [cs[0]], [dict(input="z0", setting="z")], qs, m,
            dict(tag="zero"), 4000, True)
    _record(dev, runs, "pff_one", "user", "full_floor", [cs[1]], [dict(input="z1", setting="z")], qs, m,
            dict(tag="one"), 4000, True)
    man = J.assemble(dev, runs, os.path.join(out, "job"), max_seconds=20)
    json.dump(dict(device=dev.name, qubits=len(qs), failed=sorted(set(range(dev.num_qubits)) - set(qs)),
                   circuits=len(man["pubs"]), qpu_seconds_model=man["qpu_seconds_model"]),
              open(os.path.join(out, "build.json"), "w"), indent=1)
    json.dump(dict(job=os.path.basename(out), answers="none: a measurement record, no verdict"), open(ans, "w"))
    json.dump(dict(device=dev.name, circuits=len(man["pubs"])), open(os.path.join(out, "report.json"), "w"))
    print(f"{dev.name}: {len(qs)} working qubits, {len(man['pubs'])} circuits, {man['qpu_seconds_model']} s")


def score(out, ans):
    from psf_os import job as J
    from psf_os.kim import z_values
    read = J.read(os.path.join(out, "job"), os.path.join(out, "runs"))
    res = dict(qubits={})
    for name, (rec, cc) in read.items():
        p = rec["points"][0]
        z, se = z_values(cc[(p["input"], "z")], len(rec["labels"]))
        for q, v in zip(rec["labels"], z):
            res["qubits"].setdefault(str(q), {})["floor0" if p["input"] == "z0" else "floor1"] = (
                float(1 - v) if p["input"] == "z0" else float(1 + v))
    f0 = np.array([v["floor0"] for v in res["qubits"].values()])
    f1 = np.array([v["floor1"] for v in res["qubits"].values()])
    res.update(qubits_measured=len(f0), floor0_median=float(np.median(f0)), floor1_median=float(np.median(f1)))
    json.dump(res, open(os.path.join(out, "full_floor.json"), "w"), indent=1, sort_keys=True)
    print(f"{len(f0)} qubits: 1 - z(|0>) median {np.median(f0):.4f}, worst {f0.max():.3f}; "
          f"1 + z(|1>) median {np.median(f1):.4f}, worst {f1.max():.3f}")


if __name__ == "__main__":
    {"build": lambda: build(*sys.argv[2:5]), "score": lambda: score(*sys.argv[2:4])}[sys.argv[1]]()
