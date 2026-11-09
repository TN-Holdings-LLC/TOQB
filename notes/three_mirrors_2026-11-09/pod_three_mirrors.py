"""Three mirrors on a many-core machine (POD): the same readings as three_mirrors.py, split into chunks of
trajectories run in parallel (one Aer thread per process), combined per circuit. Same criteria (three_mirrors.py).

usage: PYTHONPATH=<psf-os>:. python pod_three_mirrors.py DEVICE_RECORD OUT.json
           [--layouts line,fold] [--ts 1,2,3,4] [--zetas 0,0.005,0.01,0.02] [--traj 2000] [--chunk 100] [--procs 64]
"""
import argparse
import json
import os
import time
from multiprocessing import get_context

import numpy as np

import three_mirrors as T


def _task(args):
    key, circ, couplers, zeta, traj, seed = args
    from qiskit.quantum_info import SparsePauliOp
    from qiskit_aer import AerSimulator
    nm, _ = T.noise()
    body, site = T.compact(circ, couplers, zeta)
    n = body.num_qubits
    op = SparsePauliOp.from_sparse_list([("Z", [site[k]], 1.0 / len(site)) for k in site], num_qubits=n)
    body.save_expectation_value(op, list(range(n)), label="m", pershot=True)
    sim = AerSimulator(noise_model=nm, method="statevector", seed_simulator=seed, max_parallel_threads=1)
    vals = np.real(np.array(sim.run(body, shots=traj).result().data()["m"]))
    return key, vals.tolist()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("device")
    ap.add_argument("out")
    ap.add_argument("--layouts", default="line,fold")
    ap.add_argument("--theta", type=float, default=0.6)
    ap.add_argument("--ts", default="1,2,3,4")
    ap.add_argument("--zetas", default="0,0.005,0.01,0.02")
    ap.add_argument("--traj", type=int, default=2000)
    ap.add_argument("--chunk", type=int, default=100)
    ap.add_argument("--procs", type=int, default=os.cpu_count())
    a = ap.parse_args()
    from psf_os import device as Dv
    from psf_os import grid3d as G
    from psf_os import mirror2d as Mi
    from psf_os.compile import RuleCompiler
    dev = Dv.Device.load(a.device)
    rc = RuleCompiler(dev)
    _, pr = T.noise()
    ro = 1 - 2 * pr
    meta, tasks = {}, []
    zetas = [float(v) for v in a.zetas.split(",")]
    for layout in a.layouts.split(","):
        for t in (int(v) for v in a.ts.split(",")):
            qc, placed, used, _, where = G.physical(dev, 4, 2, 2, t, a.theta, layout=layout, info=True)
            phys = [placed[s] for s in range(16)]
            bridges = sorted(set(used) - set(phys))
            cu = T.compiled(dev, rc, qc, phys)
            rp, bp = T.parts(cu, set(bridges))
            circs = dict(F=T.mirror(rc, cu, phys), L=T.mirror(rc, rp, phys), Rt=T.mirror(rc, bp, phys),
                         R=T.readout_only(dev, phys))
            meta[(layout, t)] = dict(where=where, bridges=bridges, cz={k: Mi.cz_count(v) for k, v in circs.items()})
            for z in zetas:
                for k, c in circs.items():
                    if k == "R" and z > 0:
                        continue  # the readout-only circuit has no two-qubit layer: the same at every zeta
                    for i in range(a.traj // a.chunk):
                        tasks.append(((layout, t, z, k), c, dev.couplers, z, a.chunk, 1000 * i + 11))
    t0 = time.time()
    vals = {}
    with get_context("fork").Pool(a.procs) as pool:
        for key, v in pool.imap_unordered(_task, tasks, chunksize=1):
            vals.setdefault(key, []).extend(v)
    rows = []
    for (layout, t), m in meta.items():
        for z in zetas:
            r = {}
            for k in ("F", "L", "Rt", "R"):
                v = np.array(vals[(layout, t, z if k != "R" else 0.0, k)])
                r[k] = (float(v.mean()) * ro, float(v.std(ddof=1) / np.sqrt(len(v))) * ro)
            F, L, Rt, R = (r[k][0] for k in ("F", "L", "Rt", "R"))
            sF, sL, sRt, sR = (r[k][1] for k in ("F", "L", "Rt", "R"))
            delta = F - L * Rt / R
            se = float(np.sqrt(sF ** 2 + (Rt / R * sL) ** 2 + (L / R * sRt) ** 2 + (L * Rt / R ** 2 * sR) ** 2))
            rows.append(dict(layout=m["where"]["layout"], r0=m["where"]["r0"], c0=m["where"]["c0"], t=t, zeta=z,
                             traj=a.traj, cz=m["cz"], bridges=m["bridges"], F=F, L=L, Rt=Rt, R=R,
                             se=dict(F=sF, L=sL, Rt=sRt, R=sR), delta=delta, delta_se=se))
            print(f"{layout:4} t{t} zeta {z:<6} CZ F {m['cz']['F']:4} L {m['cz']['L']:4} Rt {m['cz']['Rt']:4}  F {F:.4f} "
                  f"L {L:.4f} Rt {Rt:.4f} R {R:.4f}  delta {delta:+.4f} +- {se:.4f} ({delta / se:+.1f} SE)", flush=True)
    json.dump(dict(rows=rows, seconds=round(time.time() - t0, 1), procs=a.procs, tasks=len(tasks)), open(a.out, "w"),
              indent=1)
    print(f"{len(tasks)} tasks, {a.procs} processes, {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
