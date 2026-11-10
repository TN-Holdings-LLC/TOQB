"""Build one device job of the paper 3 follow-up classifier (owner 2026-11-10): arm A fold:rule, arm B Qiskit level 2
seed 0 blind (SABRE layout and routing, no map: toqb.task_loop 'qiskit:2:blind:template', as 10-30), each compiled
from the day's psf-os device record (geometry and failed marks only: toqb.devices 'psfos:'), on the task of
gpu/qclf_task.py. Per arm: (128 + 200) x 3 circuits (point-major, basis-minor, as 10-30) and psf-os's own checks on
point 0's three circuits (floor: the compiled circuit without its non-diagonal single-qubit gates; mirror: the
compiled body, its inverse, the same measurement); one ring sentinel per job (psf-os). Rule G as 10-30: one measured
map per arm, no failed element; else STOP (nothing written).

usage: PYTHONPATH=<psf-os>:<TOQB> python gpu/qclf_build.py DEV_DIR TASK_DIR OUT [--shots 250] [--max-seconds 240]
       [--points K (tests only)] [--dry-clifford-sentinel]
"""
import argparse
import hashlib
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from toqb import qelm as Q  # noqa: E402

ARMS = (("fold:rule", "a_rule"), ("qiskit:2:blind:template", "b_sabre"))


def sha256(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def mirror_of(c):
    """Body, inverse, the same measurement; translated to the native basis without moving any gate."""
    from qiskit import QuantumCircuit
    from qiskit.circuit.equivalence_library import SessionEquivalenceLibrary as SEL
    from qiskit.transpiler import PassManager
    from qiskit.transpiler.passes import BasisTranslator
    mm = Q.measured_map(c)
    body = c.remove_final_measurements(inplace=False)
    m = body.compose(body.inverse())
    m = PassManager([BasisTranslator(SEL, ["cz", "rz", "sx", "x"])]).run(m)
    out = QuantumCircuit(c.num_qubits, c.num_clbits)
    out.compose(m, qubits=range(c.num_qubits), inplace=True)
    for k in sorted(mm):
        out.measure(mm[k], k)
    return out


def write_record(runs, name, role, circuits, points, shots, extra):
    from qiskit import qpy
    for k, c in enumerate(circuits):
        c.name = f"{name}-{k}"
    jf, qf = os.path.join(runs, name + ".json"), os.path.join(runs, name + ".qpy")
    for f in (jf, qf):
        if os.path.exists(f):
            raise SystemExit(f"STOP: {f} exists")
    with open(qf, "wb") as f:
        qpy.dump(list(circuits), f)
    rec = dict(kind="qclf", psfos_role=role, points=points, shots=shots, valid=True,
               export=dict(qpy=os.path.basename(qf), circuits=len(circuits), sha256=sha256(qf)), **extra)
    json.dump(rec, open(jf, "w"), indent=1)
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dev_dir")
    ap.add_argument("task_dir")
    ap.add_argument("out")
    ap.add_argument("--shots", type=int, default=Q.SHOTS)
    ap.add_argument("--max-seconds", type=float, default=240)
    ap.add_argument("--points", type=int, default=None, help="tests only: the first K training and K test points")
    ap.add_argument("--dry-clifford-sentinel", action="store_true")
    a = ap.parse_args()
    if os.path.exists(a.out):
        raise SystemExit(f"STOP: {a.out} exists")
    from psf_os import circuits as C
    from psf_os import device as Dv
    from psf_os import gatehash as GH
    from psf_os import job as J
    from psf_os import sentinel
    from psf_os.compile import RuleCompiler, measured_qubits
    from psf_os.mirror2d import cz_count
    from psf_os.user2d import floor_of
    dev = Dv.Device.load(a.dev_dir)
    task = json.load(open(os.path.join(a.task_dir, "task.json")))
    n, L, enc = task["n"], task["L"], task["enc"]
    X = np.array(task["X"])
    ntr = task["n_train"]
    if a.points:
        X = np.vstack([X[:a.points], X[ntr:ntr + a.points]])
    spec = "psfos:" + os.path.abspath(a.dev_dir)
    built, report = [], dict(device=dev.name, task_sha256=sha256(os.path.join(a.task_dir, "task.json")),
                             answers_sha256=task["answers_sha256"], n=n, L=L, shots=a.shots, points_override=a.points,
                             arms={})
    for arm, tag in ARMS:
        cs, maps, A = Q.build_features(arm, spec, X, n, L, enc)
        ok_g = len(maps) == 1 and not A.structural_fail and not A.on_failed_ops
        if not ok_g:
            raise SystemExit(f"STOP: rule G fails for {arm} on {dev.name} (maps {len(maps)}, structural "
                             f"{A.structural_fail}, failed ops {A.on_failed_ops}): nothing written")
        mm = Q.measured_map(cs[0])
        floors = [floor_of(c) for c in cs[:3]]
        mirrors = [mirror_of(c) for c in cs[:3]]
        czu = [cz_count(c) for c in cs[:3]]
        checks = dict(floor_diagonal=all(i.operation.name in ("cz", "rz", "barrier", "measure", "delay")
                                         for f in floors for i in f.data),
                      floor_cz=[cz_count(f) for f in floors] == czu,
                      mirror_cz=[cz_count(m) for m in mirrors] == [2 * v for v in czu],
                      mirror_measures=all(Q.measured_map(m) == mm for m in mirrors),
                      mirror_native=all(i.operation.name in ("cz", "rz", "sx", "x", "barrier", "measure")
                                        for m in mirrors for i in m.data))
        if not all(checks.values()):
            raise SystemExit(f"STOP: {arm}: control acceptance failed {checks}")
        built.append((arm, tag, cs, floors, mirrors, mm))
        report["arms"][arm] = dict(tag=tag, circuits=len(cs), cz_per_circuit=czu[0], measured_qubits={
            str(k): v for k, v in sorted(mm.items())}, rule_G="PASS", controls=checks)
    runs = os.path.join(a.out, "runs")
    os.makedirs(runs)
    pts = [dict(input=f"p{k // 3}", setting=Q.BASES[k % 3]) for k in range(3 * len(X))]
    for arm, tag, cs, floors, mirrors, mm in built:
        common = dict(arm=arm, task=dict(n=n, layers=L, enc=enc), measured_qubits={str(k): v for k, v in mm.items()})
        write_record(runs, f"q_{tag}", "user", cs, pts, a.shots, dict(common, qclf_arm=True))
        write_record(runs, f"q_{tag}_floor", "floor", floors, pts[:3], a.shots, common)
        write_record(runs, f"q_{tag}_mirror", "mirror", mirrors, pts[:3], a.shots, common)
    rc = RuleCompiler(dev)
    ring = 40
    mq = measured_qubits(rc.compile(C.model_circuit(list(np.zeros(C.n_model_angles(ring, 1))), ring, 1)))
    sentinel.build(dev, runs, [int(mq[j]) for j in range(ring)], a.shots, rc,
                   spec=dict(kind="echo_clifford", D=24) if a.dry_clifford_sentinel else None)
    man = J.assemble(dev, runs, os.path.join(a.out, "job"), max_seconds=a.max_seconds)
    gh = GH.qpy_hash(os.path.join(a.out, "job", "circuits.qpy"))
    report.update(circuits=len(man["pubs"]), qpu_seconds_model=man["qpu_seconds_model"], gate_hash=gh)
    json.dump(report, open(os.path.join(a.out, "report.json"), "w"), indent=1)
    for arm, r in report["arms"].items():
        q = sorted(r["measured_qubits"].values())
        print(f"{arm:26} {r['circuits']} circuits, CZ {r['cz_per_circuit']} per circuit, qubits {q[:4]}... G PASS")
    print(f"circuits {report['circuits']}  model {report['qpu_seconds_model']} s  gates {gh['gate_sha256'][:12]}  "
          f"answers sha256 {task['answers_sha256']}")


if __name__ == "__main__":
    main()
