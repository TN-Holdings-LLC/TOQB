"""Build one device job of the 3D Heisenberg (XXX) Trotter evolution on the folded layout (draft B; owner 2026-11-07
22:51 JST "OK" to dt = 0.05): every fold translation that fits, in psf-os's fixed order, up to --k, as a candidate;
each candidate at t = 1 .. 4 with its floor and mirror; one ring sentinel. The place is chosen afterwards by its own
t = 1 mirror (rule "top", `gpu/heis3d_score.py`). Exact answers: the logged Trotter product of each arm (the order of
bonds is the layout's), full statevector (4 x 2 x 2 = 16 sites).

usage: PYTHONPATH=<psf-os>:<TOQB>/gpu python gpu/heis3d_build.py DEV OUT ANSWERS_OUT [--dt 0.05] [--delta 1]
       [--ts 1,2,3,4] [--k 4] [--lattice 2,2] [--shots 4000] [--max-seconds 300] [--dry-clifford-sentinel] [--carry]

--carry (2026-11-08): the x-bonds ride on the swaps of their columns (gpu/heis3d.py FoldHeis, carry); 24 CZ fewer
per step at 4 x 2 x 2. Not declared for a device run yet.
"""
import argparse
import hashlib
import json
import os

import numpy as np

import heis3d as H

L = 4


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("device")
    ap.add_argument("out")
    ap.add_argument("answers_out")
    ap.add_argument("--dt", type=float, default=0.05)
    ap.add_argument("--delta", type=float, default=1.0)
    ap.add_argument("--ts", default="1,2,3,4")
    ap.add_argument("--k", type=int, default=4)
    ap.add_argument("--lattice", default="2,2")
    ap.add_argument("--shots", type=int, default=4000)
    ap.add_argument("--max-seconds", type=float, default=300)
    ap.add_argument("--dry-clifford-sentinel", action="store_true")
    ap.add_argument("--carry", action="store_true")
    a = ap.parse_args()
    M, N = (int(v) for v in a.lattice.split(","))
    if L * M * N > 24:
        raise SystemExit("STOP: the exact answers here use the full statevector (at most 24 sites)")
    for p in (a.out, a.answers_out):
        if os.path.exists(p):
            raise SystemExit(f"STOP: {p} exists")
    from qiskit import QuantumCircuit
    from psf_os import circuits as C
    from psf_os import device as Dv
    from psf_os import gatehash as GH
    from psf_os import grid3d as G
    from psf_os import job as J
    from psf_os import mirror2d as Mi
    from psf_os import sentinel
    from psf_os import user2d as U
    from psf_os.compile import RuleCompiler, measured_qubits
    dev = Dv.Device.load(a.device)
    rc = RuleCompiler(dev)
    ts = [int(v) for v in a.ts.split(",")]
    runs = os.path.join(a.out, "runs")
    os.makedirs(runs)
    cands, avoid = [], []
    while len(cands) < a.k:
        try:
            qc, placed, used, log, where = H.physical(dev, M, N, 1, a.dt, a.delta, avoid=avoid, carry=a.carry)
        except G.Refused:
            break
        cands.append(dict(index=len(cands), r0=where["r0"], c0=where["c0"], layout=where["layout"], used=used,
                          avoid=list(avoid)))
        avoid.append((where["r0"], where["c0"]))
    if not cands:
        raise SystemExit(f"NOT RUN: no fold translation fits on {dev.name}")
    arms, answers = {}, {}
    for c in cands:
        for t in ts:
            qc, placed, used, log, where = H.physical(dev, M, N, t, a.dt, a.delta, avoid=c["avoid"], carry=a.carry)
            assert (where["r0"], where["c0"]) == (c["r0"], c["c0"])
            n = L * M * N
            phys = [placed[s] for s in range(n)]
            full = QuantumCircuit(dev.num_qubits)
            full.compose(qc, qubits=list(range(qc.num_qubits)), inplace=True)
            cu = rc.pm.run(U.with_measure(full, phys))
            cf = U.floor_of(cu)
            cm = G.mirror_of_compiled(rc, cu, phys)
            G.accept(cu, cf, cm, phys)
            prep = dict(cu=cu, cf=cf, cm=cm, cz=Mi.cz_count(cu), phys=phys)
            tag = f"h3d{c['index']}_t{t}"
            G.write_records(dev, runs, tag, prep, a.shots, L, M, N,
                            extra=dict(heis3d=dict(dt=a.dt, delta=a.delta, t=t, **where),
                                       compare_arm=f"3D Heisenberg candidate {c['index']}"))
            arms[tag] = dict(kind="3D", candidate=c["index"], t=t, cz=prep["cz"],
                             cz_layers=cu.depth(lambda i: len(i.qubits) == 2), r0=c["r0"], c0=c["c0"],
                             mapping={str(s): q for s, q in enumerate(phys)}, bonds=len(log))
            answers[tag] = H.exact_from_log(L, M, N, log, a.dt, a.delta)
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
    rep = dict(device=dev.name, model="heisenberg", lattice=[L, M, N], dt=a.dt, delta=a.delta, ts=ts, shots=a.shots,
               carry=a.carry,
               candidates=[{x: c[x] for x in ("index", "r0", "c0", "layout", "used")} for c in cands], arms=arms,
               circuits=len(man["pubs"]), qpu_seconds_model=man["qpu_seconds_model"], gate_hash=gh,
               answers_sha256=ans_sha, job=os.path.join(a.out, "job"), runs=runs)
    json.dump(rep, open(os.path.join(a.out, "report.json"), "w"), indent=1)
    for c in cands:
        print(f"candidate {c['index']}: r0 {c['r0']} c0 {c['c0']} ({c['layout']})")
    for tag, r in arms.items():
        ms = H.staggered(answers[tag], L, M, N)
        print(f"{tag:9} CZ {r['cz']} layers {r['cz_layers']}  exact m_s {ms:+.4f}")
    print(f"circuits {rep['circuits']}  model {rep['qpu_seconds_model']:.1f} s  gates {gh['gate_sha256'][:12]}  "
          f"answers sha256 {ans_sha}")


if __name__ == "__main__":
    main()
