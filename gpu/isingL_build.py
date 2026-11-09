"""Build one device job comparing psf-os's Ising line layout with the fold v3.1 at the same places (owner 2026-11-09
09:30 JST "両方"; the line ported to psf-os 0fb4512, grid3d layout "line", at=[(r0, c0)]).

Per lattice (4 x 2 x 2 and 4 x 3 x 2 by default): the fold's translations in psf-os's fixed order that fit, up to k;
at each, the kicked Ising circuit (RZZ(-pi/2) on every edge, then RX(theta) on every site, t steps) in the fold v3.1
and in the line layout placed on the fold's own qubits (at=[(r0, c0)]); each arm with its floor and mirror; one ring
sentinel per job. The Ising bonds commute, so the exact answer does not depend on the layout: psf_os.grid3d.exact.
The place is chosen afterwards by its two t = 1 mirrors (rule "top", gpu/isingL_score.py).

usage: PYTHONPATH=<psf-os>:<TOQB>/gpu python gpu/isingL_build.py DEV OUT ANSWERS_OUT [--lattices 2,2:4,3,2:2]
       [--theta 0.6] [--ts 1,2,3,4] [--shots 4000] [--max-seconds 300] [--dry-clifford-sentinel]
"""
import argparse
import hashlib
import json
import os

import numpy as np

L = 4


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("device")
    ap.add_argument("out")
    ap.add_argument("answers_out")
    ap.add_argument("--lattices", default="2,2:4,3,2:2", help="M,N:k list")
    ap.add_argument("--theta", type=float, default=0.6)
    ap.add_argument("--ts", default="1,2,3,4")
    ap.add_argument("--shots", type=int, default=4000)
    ap.add_argument("--max-seconds", type=float, default=300)
    ap.add_argument("--dry-clifford-sentinel", action="store_true")
    a = ap.parse_args()
    for p in (a.out, a.answers_out):
        if os.path.exists(p):
            raise SystemExit(f"STOP: {p} exists")
    from psf_os import circuits as C
    from psf_os import device as Dv
    from psf_os import gatehash as GH
    from psf_os import grid3d as G
    from psf_os import job as J
    from psf_os import sentinel
    from psf_os.compile import RuleCompiler, measured_qubits
    dev = Dv.Device.load(a.device)
    rc = RuleCompiler(dev)
    ts = [int(v) for v in a.ts.split(",")]
    items = a.lattices.split(",")
    lattices = []
    for i in range(0, len(items), 2):
        m, rest = items[i], items[i + 1]
        n_, k = rest.split(":")
        lattices.append((int(m), int(n_), int(k)))
    runs = os.path.join(a.out, "runs")
    os.makedirs(runs)
    arms, answers, cands_all = {}, {}, {}
    for M, N, k in lattices:
        lat = f"{L}x{M}x{N}"
        cands, avoid = [], []
        while len(cands) < k:
            try:
                qc, placed, used, passes, where = G.physical(dev, L, M, N, 1, a.theta, layout="fold", info=True,
                                                             avoid=avoid)
            except G.Refused:
                break
            cands.append(dict(index=len(cands), r0=where["r0"], c0=where["c0"]))
            avoid.append((where["r0"], where["c0"]))
        cands_all[lat] = cands
        for c in cands:
            for lay, head in (("fold", "f"), ("line", "l")):
                for t in ts:
                    prep = G.prepare(dev, L, M, N, t, a.theta, layout=lay, rc=rc, at=[(c["r0"], c["c0"])])
                    assert (prep["where"]["r0"], prep["where"]["c0"]) == (c["r0"], c["c0"]), prep["where"]
                    tag = f"q{M}{N}{head}{c['index']}_t{t}"
                    G.write_records(dev, runs, tag, prep, a.shots, L, M, N,
                                    extra=dict(isingL=dict(prep["where"], theta=a.theta, t=t, asked=lay),
                                               compare_arm=f"{lat} candidate {c['index']} ({lay})"))
                    arms[tag] = dict(lattice=[L, M, N], candidate=c["index"], layout=lay, t=t, cz=prep["cz"],
                                     cz_layers=prep["cz_layers"], r0=c["r0"], c0=c["c0"],
                                     used=len(prep["used"]), mapping={str(s): q for s, q in enumerate(prep["phys"])})
                    answers[tag] = G.exact(L, M, N, t, a.theta)
    if not arms:
        raise SystemExit(f"NOT RUN: no fold translation fits on {dev.name}")
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
    rep = dict(device=dev.name, model="kicked ising", theta=a.theta, ts=ts, shots=a.shots, candidates=cands_all,
               arms=arms, circuits=len(man["pubs"]), qpu_seconds_model=man["qpu_seconds_model"], gate_hash=gh,
               answers_sha256=ans_sha, job=os.path.join(a.out, "job"), runs=runs)
    json.dump(rep, open(os.path.join(a.out, "report.json"), "w"), indent=1)
    for lat, cs in cands_all.items():
        print(lat, "candidates", [(c["r0"], c["c0"]) for c in cs])
    for tag, r in sorted(arms.items()):
        if r["candidate"] == 0:
            print(f"{tag:10} CZ {r['cz']:4} layers {r['cz_layers']:3} qubits {r['used']}")
    print(f"circuits {rep['circuits']}  model {rep['qpu_seconds_model']:.1f} s  gates {gh['gate_sha256'][:12]}  "
          f"answers sha256 {ans_sha}")


if __name__ == "__main__":
    main()
