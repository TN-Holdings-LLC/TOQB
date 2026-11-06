"""Replay of the 11-06 marrakesh faults in a simulator (not declared, not a device result): would the v3.1 job's own
probes have passed the bad translation over, and what would the judged arm have read?

Fault model (stated here, chosen to resemble what the device showed; not read from any calibration):
  everywhere: 2-qubit depolarizing 0.005 on CZ, 1-qubit 0.0002 on sx/x, readout 0.015 (as sim3d's uniform model);
  q29: amplitude damping 0.04 after every 1-qubit gate on it (a fast-relaxing qubit; |0> floor stays at +1);
  coupler 48-49: 2-qubit depolarizing 0.05 (CZ error 0.052 on 11-06).
Probes: counts (1000 shots) -> psf_os.grid3d.probe_choose. Arms: mean over 300 trajectories of the exact <Z>.

usage: python replay_1106.py PSF_OS JOB_DIR(the v3.1 build: report.json, job, runs) ANSWERS.json OUT.json
"""
import json
import os
import sys

import numpy as np


def noise_for(act, faults=True):
    from qiskit_aer.noise import NoiseModel, amplitude_damping_error, depolarizing_error
    loc = {q: i for i, q in enumerate(act)}
    nm = NoiseModel()
    nm.add_all_qubit_quantum_error(depolarizing_error(0.005, 2), ["cz"])
    nm.add_all_qubit_quantum_error(depolarizing_error(0.0002, 1), ["sx", "x"])
    if faults:
        if 29 in loc:
            nm.add_quantum_error(amplitude_damping_error(0.04), ["sx", "x", "rz"], [loc[29]])
        if 48 in loc and 49 in loc:
            for pair in ([loc[48], loc[49]], [loc[49], loc[48]]):
                nm.add_quantum_error(depolarizing_error(0.05, 2), ["cz"], pair)
    return nm


def main():
    psf, run, answers, out = sys.argv[1:5]
    sys.path.insert(0, psf)
    from qiskit import qpy
    from qiskit.quantum_info import Pauli
    from qiskit_aer import AerSimulator
    from psf_os import grid3d as G
    from psf_os import job as J
    from psf_os import sim as Sm
    rep = json.load(open(os.path.join(run, "report.json")))
    man = json.load(open(os.path.join(run, "job", "manifest.json")))
    circs = qpy.load(open(os.path.join(run, "job", "circuits.qpy"), "rb"))
    names = [man["cells"][p["cell"]]["name"] for p in man["pubs"]]
    ans = json.load(open(answers))
    pr = 0.015
    res = {}
    for faults in ((False, True) if len(sys.argv) < 6 else (sys.argv[5] == 'faults',)):
        rows = []
        for k, (c, nm_) in enumerate(zip(circs, names)):
            if nm_.startswith("probe"):
                cc, act = Sm.compact(c)
                r = AerSimulator(method="statevector", noise_model=noise_for(act, faults), fusion_enable=not faults).run(
                    cc, shots=1000, seed_simulator=7 + k).result().get_counts(0)
                # readout error as a classical flip per bit
                rng = np.random.default_rng(k)
                flipped = {}
                for key, v in r.items():
                    for _ in range(v):
                        bits = [b if rng.random() > pr else ("1" if b == "0" else "0") for b in key]
                        kk = "".join(bits)
                        flipped[kk] = flipped.get(kk, 0) + 1
                rows.append(dict(pub=k, counts=flipped))
            else:
                rows.append(dict(pub=k, counts={"0" * c.num_clbits: 1}))
        tmp = os.path.join(os.path.dirname(os.path.abspath(out)), f"_replay_job_{int(faults)}")
        os.makedirs(tmp, exist_ok=True)
        for f in ("manifest.json", "circuits.qpy"):
            if not os.path.exists(os.path.join(tmp, f)):
                os.symlink(os.path.abspath(os.path.join(run, "job", f)), os.path.join(tmp, f))
        json.dump(dict(job_id="replay", submitted="-", local=True, backend=rep["device"]),
                  open(os.path.join(tmp, "submission.json"), "w"))
        json.dump(dict(fetched="-", job_id="replay", status="DONE", rows=rows),
                  open(os.path.join(tmp, "raw_counts.json"), "w"))
        ch = G.probe_choose(tmp, os.path.join(run, "runs"))
        chosen = ch["chosen"] if ch["chosen"] is not None else 0
        arms = {}
        for tag in [f"g3d0_t{t}" for t in rep["ts"]] + [f"g3d{chosen}_t{t}" for t in rep["ts"]] + \
                   [f"hex_t{t}" for t in rep["ts"]]:
            if tag in arms:
                continue
            k = names.index(f"p2d_{tag}")
            c = circs[k]
            rec = json.load(open(os.path.join(run, "runs", f"p2d_{tag}.json")))
            cc, act = Sm.compact(c)
            loc = {q: i for i, q in enumerate(act)}
            body = cc.remove_final_measurements(inplace=False)
            mapping = rec["mapping"]
            labels = rec["labels"]
            for lab in labels:
                body.save_expectation_value(Pauli("Z"), [loc[int(mapping[str(lab)])]], label=f"z{lab}")
            d = AerSimulator(method="statevector", noise_model=noise_for(act, faults), fusion_enable=not faults).run(
                body, shots=300, seed_simulator=11).result().data()
            z = np.array([float(np.real(d[f"z{lab}"])) * (1 - 2 * pr) for lab in labels])
            ex = np.array([ans[tag][str(lab)] for lab in labels])
            arms[tag] = dict(mse=float(np.mean((z - ex) ** 2)), M=float(z.mean()), M_exact=float(ex.mean()),
                             retention=float(z.mean() / ex.mean()) if abs(ex.mean()) >= 0.1 else None)
        res["faults" if faults else "uniform"] = dict(chosen=ch["chosen"], probe=[{x: r[x] for x in (
            "index", "r0", "c0", "low") if x in r} | dict(min_floor=r.get("min_floor"), max_floor1=r.get("max_floor1"))
            for r in ch["candidates"]], arms=arms)
        print("faults" if faults else "uniform", "chosen", ch["chosen"], "lines", round(ch["line0"], 3),
              round(ch["line1"], 3), [(r["index"], round(r.get("min_floor", 0), 3), round(r.get("max_floor1", 0), 3),
                                       r["low"]) for r in ch["candidates"]], flush=True)
        for tag, a in arms.items():
            print(f"   {tag:9} MSE {a['mse']:.4f}  M {a['M']:+.3f}/{a['M_exact']:+.3f}  retention "
                  f"{a['retention'] if a['retention'] is None else round(a['retention'], 3)}")
    json.dump(res, open(out, "w"), indent=1)


if __name__ == "__main__":
    main()
