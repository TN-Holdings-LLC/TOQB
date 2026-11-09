"""Readability under the fixed uniform noise model only (depolarizing 0.005 on cz, 0.0002 on sx and x, readout 0.015 as
a factor 1 - 2 p on every <Z>; not fitted to any device). For each compiled circuit (fez, parameter set M1): the MSE of
the noisy reading against the exact Trotter output, and the MSE of the guess "nothing happened" (the bare vacuum,
Z_n = -(-1)^n) against the same. Writes only these MSEs and their ratio (no answer value).

usage: python noise_est.py WORK_DIR RUN2D.json OUT.json [params]
"""
import json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import schwinger as S
from qiskit import QuantumCircuit, qpy
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, depolarizing_error

work, run2d, out = sys.argv[1:4]
pn = sys.argv[4] if len(sys.argv) > 4 else "M1"
R = json.load(open(run2d))
P = {p[0]: p for p in S.PARAMS}
nm = NoiseModel()
nm.add_all_qubit_quantum_error(depolarizing_error(0.005, 2), ["cz"])
nm.add_all_qubit_quantum_error(depolarizing_error(0.0002, 1), ["sx", "x"])
RO = 1 - 2 * 0.015
sim = AerSimulator(method="density_matrix", noise_model=nm)
res = json.load(open(out)) if os.path.exists(out) else {}
for key, r in sorted(R.items(), key=lambda kv: (int(kv[0].split("/N")[1].split("_")[0]), kv[0])):
    dn, cid = key.split("/")
    if dn != "ibm_fez" or f"_{pn}_" not in cid or r["returncode"] != 0 or key in res:
        continue
    n, st = int(cid.split("_")[0][1:]), int(cid.split("_")[2][1:])
    with open(os.path.join(work, r.get("dir", os.path.join("run2d", dn, cid + "_" + dn)), "runs", "p2d_user.qpy"), "rb") as f:
        cq = qpy.load(f)[0]
    used = sorted({cq.find_bit(q).index for i in cq.data for q in i.qubits})
    idx = {p: k for k, p in enumerate(used)}
    body, site = QuantumCircuit(len(used)), {}
    for ins in cq.data:
        qs = [idx[cq.find_bit(q).index] for q in ins.qubits]
        if ins.operation.name == "measure":
            site[cq.find_bit(ins.clbits[0]).index] = qs[0]
        elif ins.operation.name not in ("barrier", "delay"):
            body.append(ins.operation, qs)
    body.save_density_matrix()
    rho = sim.run(body).result().data()["density_matrix"]
    pr = np.real(np.diag(np.asarray(rho)))
    zk = [RO * float(sum(pr[i] * (1 - 2 * ((i >> site[k]) & 1)) for i in range(len(pr)))) for k in range(n)]
    zn = [None] * n
    for k, s_ in enumerate(S.site_of_clbit(n, st, r["chain"])):
        zn[s_ - 1] = zk[k]
    ze = S.z_sites(S.trotter(n, st, P[pn]), n, st)
    zv = [-(-1) ** s for s in range(1, n + 1)]
    mse_noisy = float(np.mean([(a - b) ** 2 for a, b in zip(zn, ze)]))
    mse_vac = float(np.mean([(a - b) ** 2 for a, b in zip(zv, ze)]))
    res[key] = dict(n=n, steps=st, cz=r["cz"], cz_layers=r["cz_layers"], mse_noisy=mse_noisy, mse_vacuum_guess=mse_vac,
                    ratio=mse_noisy / mse_vac if mse_vac > 0 else None)
    print(key, f"cz {r['cz']} noisy {mse_noisy:.4f} vacuum-guess {mse_vac:.4f}", flush=True)
    json.dump(res, open(out, "w"), indent=1)
