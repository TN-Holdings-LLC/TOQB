"""Build one job for the next 3D device test (draft prereg/drafts-2026-11-06/os3d_v31_DRAFT.md; offline, no IBM).

One job, nothing searched, no search arm (owner 2026-11-06: the formula-against-search question is settled):
  * probes: for the first k qualifying fold translations (fixed order) the |0> floor and the |1> floor at the deepest
    t of every touched qubit (psf_os.grid3d.probe_records);
  * 3D arms g3d<i>_t<t>: the 4 x 2 x 2 kicked Ising, grid3d fold v3.1, at candidate i's translation, t in ts, each with
    floor and mirror (every candidate is in the job; the scorer judges the one the probes choose);
  * 2D arms hex_t<t>: 16 sites of the device's own lattice (one hexagon of 12 and two tails of 2; 16 edges), the same
    step, written as a user circuit on labels and placed by psf-os (user2d, translation), floor and mirror;
  * one ring sentinel.
The exact answers go to ANSWERS_OUT only (sha256 printed for the seal).

usage: python gpu/os3d_v31_build.py DEVICE_RECORD OUT ANSWERS_OUT [--k 4] [--ts 1,2,3] [--theta 0.8] [--shots 4000]
"""
import argparse
import hashlib
import json
import os
import shutil
import tempfile

import numpy as np

L, M, N = 4, 2, 2
HEX = [3, 4, 5, 6, 7, 17, 27, 26, 25, 24, 23, 16]   # row 0 cols 3-7, bridge 17, row 1 cols 7-3, bridge 16
TAILS = [(7, 8), (8, 9), (27, 28), (28, 29)]


def hex_patch():
    sites = HEX + [8, 9, 28, 29]
    return sites, [(HEX[i], HEX[(i + 1) % 12]) for i in range(12)] + TAILS


def hex_circuit(t, theta):
    from qiskit import QuantumCircuit
    sites, edges = hex_patch()
    qc = QuantumCircuit(max(sites) + 1)
    for _ in range(t):
        for a, b in edges:
            qc.rzz(-np.pi / 2, a, b)
        for q in sites:
            qc.rx(theta, q)
    return qc


def hex_exact(t, theta):
    """{str(label): exact <Z>} for the patch's labels."""
    from qiskit import QuantumCircuit
    from qiskit.quantum_info import Statevector
    sites, edges = hex_patch()
    idx = {q: i for i, q in enumerate(sites)}
    qc = QuantumCircuit(len(sites))
    for _ in range(t):
        for a, b in edges:
            qc.rzz(-np.pi / 2, idx[a], idx[b])
        for q in sites:
            qc.rx(theta, idx[q])
    p = Statevector(qc).probabilities()
    k = np.arange(len(p))
    return {str(q): float(np.sum(p * (1 - 2 * ((k >> idx[q]) & 1)))) for q in sites}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("device")
    ap.add_argument("out")
    ap.add_argument("answers_out")
    ap.add_argument("--k", type=int, default=4)
    ap.add_argument("--ts", default="1,2,3")
    ap.add_argument("--theta", type=float, default=0.8)
    ap.add_argument("--shots", type=int, default=4000)
    ap.add_argument("--max-seconds", type=float, default=120)
    ap.add_argument("--probe-t", type=int, default=None, help="probe depth (default: the deepest t, as on 11-07)")
    ap.add_argument("--dry-clifford-sentinel", action="store_true")
    a = ap.parse_args()
    for p in (a.out, a.answers_out):
        if os.path.exists(p):
            raise SystemExit(f"STOP: {p} exists")
    from qiskit import qpy
    from psf_os import circuits as C
    from psf_os import device as Dv
    from psf_os import gatehash as GH
    from psf_os import grid3d as G
    from psf_os import job as J
    from psf_os import sentinel
    from psf_os import user2d as U
    from psf_os.compile import RuleCompiler, measured_qubits
    dev = Dv.Device.load(a.device)
    rc = RuleCompiler(dev)
    ts = [int(v) for v in a.ts.split(",")]
    runs = os.path.join(a.out, "runs")
    os.makedirs(runs)
    cands = G.probe_records(dev, runs, L, M, N, a.probe_t or max(ts), a.theta, k=a.k, shots=a.shots, excited=True,
                            rc=rc)  # one shot count per job
    arms, answers = {}, {}
    for c in cands:
        for t in ts:
            pr = G.prepare(dev, L, M, N, t, a.theta, layout="fold", rc=rc, avoid=[tuple(v) for v in c["avoid"]])
            assert (pr["where"]["r0"], pr["where"]["c0"]) == (c["r0"], c["c0"])
            tag = f"g3d{c['index']}_t{t}"
            G.write_records(dev, runs, tag, pr, a.shots, L, M, N, extra=dict(grid3d=pr["grid3d"],
                                                                             compare_arm=f"3D candidate {c['index']}"))
            arms[tag] = dict(kind="3D", candidate=c["index"], t=t, cz=pr["cz"], cz_layers=pr["cz_layers"],
                             r0=c["r0"], c0=c["c0"], fold_version=pr["where"]["fold_version"],
                             mapping={str(s): q for s, q in enumerate(pr["phys"])})
            answers[tag] = G.exact(L, M, N, t, a.theta)
    with tempfile.TemporaryDirectory() as d:
        items = []
        for t in ts:
            f = os.path.join(d, f"hex_t{t}.qpy")
            with open(f, "wb") as fh:
                qpy.dump(hex_circuit(t, a.theta), fh)
            items.append((f"hex_t{t}", U.load(f)))
        U.build_batch(dev, items, os.path.join(d, "b"), shots=a.shots, max_seconds=10 ** 6)
        rep2 = json.load(open(os.path.join(d, "b", "report.json")))
        for f in os.listdir(os.path.join(d, "b", "runs")):
            if f.startswith("p2d_hex_t"):
                shutil.copy(os.path.join(d, "b", "runs", f), os.path.join(runs, f))
    for t in ts:
        rec = json.load(open(os.path.join(runs, f"p2d_hex_t{t}.json")))
        arms[f"hex_t{t}"] = dict(kind="2D", t=t, cz=rec.get("cz"), mapping=rec["mapping"],
                                 copy=rep2.get("items", {}).get(f"hex_t{t}", {}).get("copy"))
        answers[f"hex_t{t}"] = hex_exact(t, a.theta)
    ring = 40
    mq = measured_qubits(rc.compile(C.model_circuit(list(np.zeros(C.n_model_angles(ring, 1))), ring, 1)))
    sentinel.build(dev, runs, [int(mq[j]) for j in range(ring)], a.shots, rc,
                   spec=dict(kind="echo_clifford", D=24) if a.dry_clifford_sentinel else None)
    man = J.assemble(dev, runs, os.path.join(a.out, "job"), max_seconds=a.max_seconds)
    os.makedirs(os.path.dirname(os.path.abspath(a.answers_out)), exist_ok=True)
    with open(a.answers_out, "w") as f:
        json.dump(answers, f, indent=1, sort_keys=True)
    ans_sha = hashlib.sha256(open(a.answers_out, "rb").read()).hexdigest()
    gh = GH.qpy_hash(os.path.join(a.out, "job", "circuits.qpy"))
    rep = dict(device=dev.name, ts=ts, theta=a.theta, shots=a.shots,
               candidates=[{x: c[x] for x in ("index", "r0", "c0", "used")} for c in cands], arms=arms,
               circuits=len(man["pubs"]), qpu_seconds_model=man["qpu_seconds_model"], gate_hash=gh,
               answers_sha256=ans_sha, job=os.path.join(a.out, "job"), runs=runs)
    json.dump(rep, open(os.path.join(a.out, "report.json"), "w"), indent=1)
    for c in cands:
        print(f"candidate {c['index']}: r0 {c['r0']} c0 {c['c0']}")
    for tag, r in arms.items():
        print(f"{tag:9} {r['kind']} CZ {r['cz']}" + (f" layers {r['cz_layers']}" if "cz_layers" in r else ""))
    print(f"circuits {rep['circuits']}  model {rep['qpu_seconds_model']:.1f} s  gates {gh['gate_sha256'][:12]}  "
          f"answers sha256 {ans_sha}")


if __name__ == "__main__":
    main()
