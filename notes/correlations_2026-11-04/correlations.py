"""After-the-fact analysis (not declared, nothing judged): connected correlations C_ij = <Z_i Z_j> - <Z_i><Z_j> of P5's
lattice circuit at lattice distance 1, 2, 3, measured (from the existing counts) against exact (statevector of the
union of the two causal cones, when it has at most MAXQ qubits), and the correlation floor from the theta = 0 cells
(raw <Z_i Z_j>, ideal 1; it carries the readout error of both qubits).

usage: PYTHONPATH=<psf-os>:<TOQB> python correlations.py OUT_JSON [MAXQ]
"""
import collections
import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor

import numpy as np

from psf_os import job as J
from psf_os import kim as K

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
JOBS = [("kingston B (stage B)", "results/kim-lattice-2026-11-03", ""),
        ("kingston b (stage C/D)", "results/kim-cd-2026-11-03", "b"),
        ("kingston c (stage C/D, theta 0 floor)", "results/kim-cd-2026-11-03", "c"),
        ("kingston K (stage E)", "results/kim-e-2026-11-03/K", "e"),
        ("fez X (stage E)", "results/kim-e-2026-11-03/X", "e")]
THETAS = (0.4, 0.8, 1.0)


def pm1(counts, n):
    keys = list(counts)
    w = np.array([counts[k] for k in keys], dtype=float)
    z = np.array([[1 - 2 * int(k.replace(" ", "")[-1 - j]) for j in range(n)] for k in keys], dtype=float)
    return z, w


def pairs_by_distance(qubits, edges, dmax=3):
    out = {d: [] for d in range(1, dmax + 1)}
    for i, a in enumerate(qubits):
        dist = {a: 0}
        fr = [a]
        adj = collections.defaultdict(list)
        for x, y in edges:
            adj[x].append(y)
            adj[y].append(x)
        for d in range(1, dmax + 1):
            fr = [y for x in fr for y in adj[x] if y not in dist]
            for y in fr:
                dist[y] = d
        for b, d in dist.items():
            if d >= 1 and b > a:
                out[d].append((a, b))
    return out


def exact_pair(args):
    qubits, edges, a, b, theta, t, maxq = args
    from qiskit import QuantumCircuit
    from qiskit.quantum_info import Pauli
    from qiskit_aer import AerSimulator
    ua = set(K.ball(edges, a, max(t - 1, 0)))
    ub = set(K.ball(edges, b, max(t - 1, 0)))
    u = sorted(ua | ub)
    if len(u) > maxq:
        return None
    s = set(u)
    ue = [e for e in edges if e[0] in s and e[1] in s]
    idx = {p: k for k, p in enumerate(u)}
    qc = QuantumCircuit(len(u))
    for op in K.ops(u, ue, theta, t):
        if op[0] == "cz":
            qc.cz(idx[op[1]], idx[op[2]])
        else:
            getattr(qc, op[0])(op[1], idx[op[2]])
    n = len(u)

    def P(qs):
        lab = ["I"] * n
        for q in qs:
            lab[n - 1 - idx[q]] = "Z"
        return Pauli("".join(lab))
    qc.save_expectation_value(P([a, b]), list(range(n)), label="zz")
    qc.save_expectation_value(P([a]), list(range(n)), label="za")
    qc.save_expectation_value(P([b]), list(range(n)), label="zb")
    d = AerSimulator(method="statevector", precision="double").run(qc).result().data(0)
    return float(d["zz"] - d["za"] * d["zb"]), len(u)


def main(outp, maxq=22):
    res = {}
    for name, d, tag in JOBS:
        jd, runs = os.path.join(ROOT, d, "V", "job"), os.path.join(ROOT, d, "V", "runs")
        for cell, (rec, cc) in J.read(jd, runs).items():
            if rec.get("psfos_job", {}).get("kind") != "kim_lattice" or rec["psfos_job"].get("tag", "") != tag:
                continue
            theta = float(rec["psfos_job"]["theta"])
            if not (theta == 0.0 or any(abs(theta - x) < 1e-9 for x in THETAS)):
                continue
            qubits, edges = rec["qubits"], [tuple(e) for e in rec["edges"]]
            n = len(qubits)
            pos = {q: k for k, q in enumerate(qubits)}
            pairs = pairs_by_distance(qubits, edges)
            for p in rec["points"]:
                t = p["t"]
                if t == 0:
                    continue
                z, w = pm1(cc[(p["input"], "z")], n)
                N = w.sum()
                m1 = (w @ z) / N
                for dist, pl in pairs.items():
                    ia = np.array([pos[a] for a, _ in pl])
                    ib = np.array([pos[b] for _, b in pl])
                    zz = (w @ (z[:, ia] * z[:, ib])) / N
                    conn = zz - m1[ia] * m1[ib]
                    key = f"{name} | theta {theta:g} | t {t} | d {dist}"
                    row = dict(job=name, theta=theta, t=t, d=dist, pairs=len(pl),
                               raw_zz_mean=float(zz.mean()), conn_mean=float(conn.mean()),
                               conn_abs_mean=float(np.abs(conn).mean()))
                    if theta != 0.0 and t <= 5:
                        args = [(qubits, edges, a, b, theta, t, maxq) for a, b in pl]
                        with ProcessPoolExecutor(2) as ex:
                            got = list(ex.map(exact_pair, args, chunksize=8))
                        ok = [k for k, g in enumerate(got) if g is not None]
                        if ok:
                            ex_c = np.array([got[k][0] for k in ok])
                            me = conn[ok]
                            row.update(answered=len(ok), exact_conn_mean=float(ex_c.mean()),
                                       exact_conn_abs_mean=float(np.abs(ex_c).mean()),
                                       meas_conn_mean_answered=float(me.mean()),
                                       mean_abs_diff=float(np.abs(me - ex_c).mean()),
                                       ratio_measured_to_exact=float(me.mean() / ex_c.mean()) if abs(ex_c.mean()) > 1e-6 else None,
                                       union_max=max(got[k][1] for k in ok))
                        else:
                            row.update(answered=0)
                    res[key] = row
                    print(key, {k: (round(v, 4) if isinstance(v, float) else v) for k, v in row.items()
                                if k not in ("job", "theta", "t", "d")}, flush=True)
    json.dump(res, open(outp, "w"), indent=1)


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 22)
