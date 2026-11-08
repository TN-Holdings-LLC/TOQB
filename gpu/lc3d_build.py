"""Build one device job of the light-cone test on 4 x 2 x 2 (3D Heisenberg XXX, owner 2026-11-08 21:25 JST "進めて"):
the all-up state with one spin flipped at site SOURCE, evolved by the line layout (gpu/heis3d.py physical_line, with
rule A) for t = 1 .. T steps of dt; and, at every place and depth, the same circuit without the flip (the all-up state
is an eigenstate of XXX, so its exact <Z> is +1 everywhere: what the device shows there is the background that noise
makes). Every line translation that fits, in its fixed order, up to --k candidates; each arm with its floor and
mirror; one ring sentinel. The place is chosen afterwards by its own t = 1 mirrors (rule "top", gpu/lc3d_score.py).
Exact answers: the logged Trotter product of each arm from its start state (full statevector, 16 sites).

usage: PYTHONPATH=<psf-os>:<TOQB>/gpu python gpu/lc3d_build.py DEV OUT ANSWERS_OUT [--dt 0.05] [--ts 1,2,3,4,5,6]
       [--source 1,0,0] [--k 4] [--shots 4000] [--max-seconds 300] [--dry-clifford-sentinel]
"""
import argparse
import hashlib
import json
import os

import numpy as np

import heis3d as H

L, M, N = 4, 2, 2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("device")
    ap.add_argument("out")
    ap.add_argument("answers_out")
    ap.add_argument("--dt", type=float, default=0.05)
    ap.add_argument("--ts", default="1,2,3,4,5,6")
    ap.add_argument("--source", default="1,0,0")
    ap.add_argument("--k", type=int, default=4)
    ap.add_argument("--shots", type=int, default=4000)
    ap.add_argument("--max-seconds", type=float, default=300)
    ap.add_argument("--dry-clifford-sentinel", action="store_true")
    a = ap.parse_args()
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
    src = tuple(int(v) for v in a.source.split(","))
    s0 = list(G.sites(L, M, N)).index(src)
    runs = os.path.join(a.out, "runs")
    os.makedirs(runs)
    cands, avoid = [], []
    while len(cands) < a.k:
        try:
            qc, placed, used, log, where = H.physical_line(dev, 1, a.dt, 1.0, avoid=avoid, flips=[s0])
        except G.Refused:
            break
        cands.append(dict(index=len(cands), r0=where["r0"], c0=where["c0"], bridges=where["bridges"],
                          avoid=list(avoid)))
        avoid.append((where["r0"], where["c0"]))
    if not cands:
        raise SystemExit(f"NOT RUN: no line translation fits on {dev.name}")
    arms, answers = {}, {}
    for c in cands:
        for head, flips in (("lc", [s0]), ("lz", [])):
            for t in ts:
                qc, placed, used, log, where = H.physical_line(dev, t, a.dt, 1.0, avoid=c["avoid"], flips=flips)
                assert (where["r0"], where["c0"]) == (c["r0"], c["c0"])
                phys = [placed[s] for s in range(L * M * N)]
                full = QuantumCircuit(dev.num_qubits)
                full.compose(qc, qubits=list(range(qc.num_qubits)), inplace=True)
                cu = rc.pm.run(U.with_measure(full, phys))
                cf = U.floor_of(cu)
                cm = G.mirror_of_compiled(rc, cu, phys)
                G.accept(cu, cf, cm, phys)
                prep = dict(cu=cu, cf=cf, cm=cm, cz=Mi.cz_count(cu), phys=phys)
                tag = f"{head}{c['index']}_t{t}"
                G.write_records(dev, runs, tag, prep, a.shots, L, M, N,
                                extra=dict(lc3d=dict(dt=a.dt, t=t, source=list(src) if flips else None, **where),
                                           compare_arm=f"light cone candidate {c['index']}"
                                                       + (" (flip)" if flips else " (no flip)")))
                arms[tag] = dict(candidate=c["index"], t=t, flip=bool(flips), cz=prep["cz"],
                                 cz_layers=cu.depth(lambda i: len(i.qubits) == 2), r0=c["r0"], c0=c["c0"],
                                 mapping={str(s): q for s, q in enumerate(phys)}, bonds=len(log))
                answers[tag] = H.exact_from_log_flips(L, M, N, log, a.dt, 1.0, flips)
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
    rep = dict(device=dev.name, model="heisenberg light cone", lattice=[L, M, N], dt=a.dt, ts=ts, source=list(src),
               source_site=s0, shots=a.shots, layout="line",
               candidates=[{x: c[x] for x in ("index", "r0", "c0", "bridges")} for c in cands], arms=arms,
               circuits=len(man["pubs"]), qpu_seconds_model=man["qpu_seconds_model"], gate_hash=gh,
               answers_sha256=ans_sha, job=os.path.join(a.out, "job"), runs=runs)
    json.dump(rep, open(os.path.join(a.out, "report.json"), "w"), indent=1)
    for c in cands:
        print(f"candidate {c['index']}: r0 {c['r0']} c0 {c['c0']} bridges {c['bridges']}")
    print(f"circuits {rep['circuits']}  model {rep['qpu_seconds_model']:.1f} s  gates {gh['gate_sha256'][:12]}  "
          f"answers sha256 {ans_sha}")


if __name__ == "__main__":
    main()
