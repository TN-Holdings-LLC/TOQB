"""Build the combined job of the 3D device test (draft prereg/drafts-2026-11-06/os3d_device_DRAFT.md, step 1;
offline, no IBM): arm A = psf-os grid3d v3 fold, arm B = Qiskit SABRE seed 0, t = 1, 2, 3, each with its floor and
mirror, plus one ring sentinel, in one job folder. Reads only the device record (coupling graph, failed marks).

Record names keep arm and depth apart (p2d_g3d_t1, p2d_sabre_t1, each with _floor and _mirror), as calib_beside.py
and result2d expect. The exact answers go to ANSWERS_OUT only (to be sealed: commit its sha256 first, the file after
the verdicts); nothing else written here contains them.

usage: python gpu/os3d_compare_build.py DEVICE_RECORD OUT_DIR ANSWERS_OUT [--ts 1,2,3] [--theta 0.8] [--shots 4000]
"""
import argparse
import hashlib
import json
import os

import numpy as np

L, M, N = 4, 2, 2


def sabre(dev, rc, logical, seed=0):
    """SABRE layout and routing on the record's coupling graph without failed elements, seed 0 only; RZZ(+-pi/2) as
    one CZ (the identity grid3d uses); basis cz/rz/sx/x. Returns (compiled, phys) with phys[s] the qubit of site s."""
    from qiskit import transpile
    from qiskit.transpiler import CouplingMap
    from psf_os.compile import measured_qubits, rzz_exact
    bad = set(dev.failed_qubits)
    badc = {frozenset(c) for c in dev.failed_couplers}
    edges = [(a, b) for a, b in dev.couplers if a not in bad and b not in bad and frozenset((a, b)) not in badc]
    cm = CouplingMap([list(e) for e in edges] + [[b, a] for a, b in edges])
    qc = logical.copy()
    qc.measure_all()
    routed = transpile(qc, coupling_map=cm, basis_gates=["rzz", "swap", "rx", "measure"], optimization_level=1,
                       layout_method="sabre", routing_method="sabre", seed_transpiler=seed)
    routed = rzz_exact(routed)
    c = transpile(routed, coupling_map=cm, basis_gates=["cz", "rz", "sx", "x", "measure"], optimization_level=1,
                  routing_method="none", layout_method="trivial", seed_transpiler=seed)
    mq = measured_qubits(c)
    return c, [int(mq[s]) for s in range(logical.num_qubits)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("device")
    ap.add_argument("out")
    ap.add_argument("answers_out")
    ap.add_argument("--ts", default="1,2,3")
    ap.add_argument("--theta", type=float, default=0.8)
    ap.add_argument("--shots", type=int, default=4000)
    ap.add_argument("--max-seconds", type=float, default=60)
    ap.add_argument("--dry-clifford-sentinel", action="store_true",
                    help="offline dry runs only: the Clifford echo sentinel, so the local simulator can run the job")
    a = ap.parse_args()
    for p in (a.out, a.answers_out):
        if os.path.exists(p):
            raise SystemExit(f"STOP: {p} exists")
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
    preps = {}
    for t in ts:  # everything is prepared and accepted before anything is written
        preps[f"g3d_t{t}"] = ("A v3 fold", G.prepare(dev, L, M, N, t, a.theta, layout="fold", rc=rc))
        cu, phys = sabre(dev, rc, G.logical(L, M, N, t, a.theta))
        cf, cmir = U.floor_of(cu), G.mirror_of_compiled(rc, cu, phys)
        preps[f"sabre_t{t}"] = ("B SABRE seed 0", dict(
            cu=cu, cf=cf, cm=cmir, cz=Mi.cz_count(cu), cz_layers=cu.depth(lambda i: len(i.qubits) == 2), phys=phys,
            used=sorted({cu.find_bit(q).index for i in cu.data if i.operation.name == "cz" for q in i.qubits}
                        | set(phys)),
            checks=G.accept(cu, cf, cmir, phys), grid3d=dict(L=L, M=M, N=N, t=t, theta=a.theta, sabre_seed=0)))
    runs = os.path.join(a.out, "runs")
    os.makedirs(runs)
    for tag, (arm, pr) in preps.items():
        G.write_records(dev, runs, tag, pr, a.shots, L, M, N, extra=dict(grid3d=pr["grid3d"], compare_arm=arm))
    ring = 40
    mq = measured_qubits(rc.compile(C.model_circuit(list(np.zeros(C.n_model_angles(ring, 1))), ring, 1)))
    sentinel.build(dev, runs, [int(mq[j]) for j in range(ring)], a.shots, rc,
                   spec=dict(kind="echo_clifford", D=24) if a.dry_clifford_sentinel else None)
    man = J.assemble(dev, runs, os.path.join(a.out, "job"), max_seconds=a.max_seconds)
    answers = {tag: G.exact(L, M, N, pr["grid3d"]["t"], a.theta) for tag, (_, pr) in preps.items()}
    os.makedirs(os.path.dirname(os.path.abspath(a.answers_out)), exist_ok=True)
    with open(a.answers_out, "w") as f:
        json.dump(answers, f, indent=1, sort_keys=True)
    ans_sha = hashlib.sha256(open(a.answers_out, "rb").read()).hexdigest()
    gh = GH.qpy_hash(os.path.join(a.out, "job", "circuits.qpy"))
    rep = dict(device=dev.name, lattice=[L, M, N], theta=a.theta, ts=ts, shots=a.shots, circuits=len(man["pubs"]),
               qpu_seconds_model=man["qpu_seconds_model"], gate_hash=gh, answers_sha256=ans_sha,
               arms={tag: dict(arm=arm, cz=pr["cz"], cz_layers=pr["cz_layers"], qubits_used=len(pr["used"]),
                               mapping={str(s): q for s, q in enumerate(pr["phys"])}, checks=pr["checks"],
                               **{k: v for k, v in pr["grid3d"].items() if k not in ("L", "M", "N", "theta")})
                     for tag, (arm, pr) in preps.items()},
               job=os.path.join(a.out, "job"), runs=runs)
    json.dump(rep, open(os.path.join(a.out, "report.json"), "w"), indent=1)
    for tag, r in rep["arms"].items():
        print(f"{tag:10} {r['arm']:15} CZ {r['cz']:4} layers {r['cz_layers']:4} qubits {r['qubits_used']}")
    print(f"circuits {rep['circuits']}  model {rep['qpu_seconds_model']:.1f} s  gates {gh['gate_sha256'][:12]}  "
          f"answers sha256 {ans_sha}")


if __name__ == "__main__":
    main()
