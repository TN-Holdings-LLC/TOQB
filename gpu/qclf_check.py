"""Noiseless check of a classifier job (gpu/qclf_build.py) before any run: every compiled circuit checked (or the
first K points), reduced to its active qubits and run as an exact statevector (Aer, no noise, no shots); its per-bit <Z> must equal the task's
noiseless feature (sealed answers file, read locally only); each floor and mirror must read all zeros.

usage: PYTHONPATH=<psf-os>:<TOQB> python gpu/qclf_check.py OUT ANSWERS.json [--points K]   (writes OUT/check.json)
"""
import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from toqb import qelm as Q  # noqa: E402


_SIM = None


def _prepared(c):
    mm = Q.measured_map(c)
    body = c.remove_final_measurements(inplace=False)
    act = sorted({body.find_bit(q).index for i in body.data for q in i.qubits} | set(mm.values()))
    pos = {q: k for k, q in enumerate(act)}
    cc = _on(body, act)
    keys = sorted(mm)
    cc.save_probabilities([pos[mm[k]] for k in keys])  # index bit j <-> keys[j]
    return cc, keys


def z_batch(circuits, chunk=30):
    """Per measured bit <Z> of each compiled circuit, exact: Aer's statevector on the active qubits (no noise, no
    shots), all bits of a circuit from one probability vector; circuits run in chunks."""
    global _SIM
    from qiskit_aer import AerSimulator
    if _SIM is None:
        _SIM = AerSimulator(method="statevector", max_parallel_experiments=2, max_parallel_threads=2)
    out = []
    for s0 in range(0, len(circuits), chunk):
        prep = [_prepared(c) for c in circuits[s0:s0 + chunk]]
        res = _SIM.run([cc for cc, _ in prep], shots=1).result()
        for e, (_, keys) in enumerate(prep):
            p = np.asarray(res.data(e)["probabilities"])
            m = len(keys)
            t = p.reshape([2] * m)  # axis i is bit m - 1 - i
            z = {}
            for j, k in enumerate(keys):
                ax = m - 1 - j
                z[k] = 1 - 2 * float(t.sum(axis=tuple(i for i in range(m) if i != ax))[1])
            out.append(z)
    return out


def z_by_clbit(c):
    return z_batch([c])[0]


def _on(body, act):
    from qiskit import QuantumCircuit
    pos = {q: k for k, q in enumerate(act)}
    c = QuantumCircuit(len(act))
    for i in body.data:
        if i.operation.name in ("barrier", "delay"):
            continue
        c.append(i.operation, [pos[body.find_bit(q).index] for q in i.qubits])
    return c


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("answers")
    ap.add_argument("--points", type=int, default=None, help="check the first K points of each arm only")
    a = ap.parse_args()
    from qiskit import qpy
    rep = json.load(open(os.path.join(a.out, "report.json")))
    ans = json.load(open(a.answers))
    F = np.array(ans["features"])
    ntr = len(ans["y_train"])
    po = rep.get("points_override")
    if po:
        F = np.vstack([F[:po], F[ntr:ntr + po]])
    n = rep["n"]
    runs = os.path.join(a.out, "runs")
    res = dict(arms={})
    for arm, r in rep["arms"].items():
        tag = r["tag"]
        cs = qpy.load(open(os.path.join(runs, f"q_{tag}.qpy"), "rb"))
        K = min(len(cs) // 3, a.points or len(cs) // 3)
        worst = 0.0
        for i, z in enumerate(z_batch(cs[:3 * K])):
            p, b = divmod(i, 3)
            worst = max(worst, max(abs(z[q] - F[p, b * n + q]) for q in range(n)))
        ctrl = {}
        for kind in ("floor", "mirror"):
            cc = qpy.load(open(os.path.join(runs, f"q_{tag}_{kind}.qpy"), "rb"))
            ctrl[kind] = max(abs(1 - v) for z in z_batch(cc) for v in z.values())
        ok = worst < 1e-9 and ctrl["floor"] < 1e-9 and ctrl["mirror"] < 1e-9
        res["arms"][arm] = dict(points_checked=K, worst_feature_diff=worst, floor_worst=ctrl["floor"],
                                mirror_worst=ctrl["mirror"], ok=bool(ok))
        print(f"{arm:26} points {K}: worst |<Z> - f0| {worst:.2e}; floor {ctrl['floor']:.2e}; mirror "
              f"{ctrl['mirror']:.2e}: {'PASS' if ok else 'FAIL'}")
    res["ok"] = all(v["ok"] for v in res["arms"].values())
    json.dump(res, open(os.path.join(a.out, "check.json"), "w"), indent=1)
    return 0 if res["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
