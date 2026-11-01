"""QCA test (2026-11-01, OS plan M3): a forward-only Clifford computation with a known answer on the rule's ring.

n layers of (H on every qubit, then CZ on every ring coupler) is the identity on an n-ring (its symplectic matrix has
order n; checked by stabilizer simulation for n = 20, 40 on the four inputs). It is not a mirror: no layer is undone
by a later one. The output must equal the input bit by bit.

    python -m toqb.qca_test build FETCH RUNS --arm fold:rule --n 40 [--shots 1000]
    python -m toqb.qca_test score JOB RUNS --out F [--segment ...]
"""
from __future__ import annotations

import json
import os
import sys
import time

import numpy as np

from toqb import kising_charge as KC
from toqb.kising_echo import per_layer_q2, q2_count

INPUTS = KC.INPUTS


def circuit(bits, n):
    from qiskit import QuantumCircuit
    qc = QuantumCircuit(n)
    for q, b in enumerate(bits):
        if b:
            qc.x(q)
    for _ in range(n):
        for q in range(n):
            qc.h(q)
        for q in range(n):
            qc.cz(q, (q + 1) % n)
    qc.measure_all()
    return qc


def cmd_build(argv):
    """The QCA circuit (n layers of H on every qubit then the CZ ring; identity on an n-ring) on 4 inputs and their
    4 readout references, compiled by the arm; acceptance as in the echo (n CZ per layer)."""
    import argparse
    p = argparse.ArgumentParser(prog="qca_test build")
    p.add_argument("fetch")
    p.add_argument("out")
    p.add_argument("--arm", required=True)
    p.add_argument("--n", type=int, required=True)
    p.add_argument("--shots", type=int, default=1000)
    a = p.parse_args(argv)
    if a.n % 2:
        print("STOP: n must be even (Neel inputs)", file=sys.stderr)
        return 2
    from toqb import s2r as S
    from toqb import s2r2 as S2
    from toqb.fold_lam import active
    from toqb.s2rc import predict_job
    tfile = os.path.abspath(os.path.join(a.fetch, "target.pkl"))
    fj = json.load(open(os.path.join(a.fetch, "fetch.json"), encoding="utf-8"))
    if KC.sha256_file(tfile) != fj["target_sha256"]:
        print("STOP: target.pkl differs from fetch.json's hash", file=sys.stderr)
        return 2
    D = a.n
    name = f"kqca_n{a.n}_D{D}-{a.arm.replace(':', '_')}"
    os.makedirs(a.out, exist_ok=True)
    jf, qf = os.path.join(a.out, name + ".json"), os.path.join(a.out, name + ".qpy")
    for f in (jf, qf):
        if os.path.exists(f):
            print(f"STOP: {f} exists: a run never overwrites another", file=sys.stderr)
            return 2
    t0 = time.perf_counter()
    task = dict(n=a.n, layers=D, enc=float(np.pi / 2))
    pr = dict(traj=0, seed=7, shots=a.shots, reps=200, level=0.99)
    plan = dict(name=f"qca: {name}", device="file:" + tfile, verify=False, task=task, predict=pr,
                standin=dict(t12=0.3, over=0.01, zz_hz=1e4, seed=20261017))
    R = S2.Runner(plan, a.arm)
    cs, points = [], []
    for i in INPUTS:
        cs.append(R.arm.compile(circuit(KC.input_bits(i, a.n), a.n)))
        points.append(dict(input=i, setting="echo"))
    meas0 = None
    for i in INPUTS:
        rc, meas = KC.reference_circuit(cs[0], KC.input_bits(i, a.n))
        meas0 = meas
        cs.append(rc)
        points.append(dict(input=i, setting="ref"))
    for c in cs[:len(INPUTS)]:
        mm = {c.find_bit(x.clbits[0]).index: c.find_bit(x.qubits[0]).index for x in c.data if x.operation.name == "measure"}
        if mm != meas0:
            print("STOP: the compiled circuits of one record measure on different qubits", file=sys.stderr)
            return 2
    per = per_layer_q2(R.arm, a.n)
    q2s = [q2_count(c) for c in cs[:len(INPUTS)]]
    accepted = all(q == D * per for q in q2s)
    d, q2 = R.arm.duration(cs[0], (a.n, D))
    labels = np.ones(len(cs), dtype=int)
    p1 = np.full(len(cs), 0.5)
    rec = dict(kind="s2rc", lam_test=True, qca_test=True, arm=a.arm, seed=0, plan=plan["name"], task=task,
               predict=pr, standin=plan["standin"], verify=False, device=plan["device"],
               target_sha256=fj["target_sha256"], version=R.arm.version(), final_mean=[], loops=0, started=S._cest(),
               echo=dict(D=D, inputs=list(INPUTS), circuit="n x (H on all, CZ ring): identity on the n-ring",
                         measured_qubits={str(k): v for k, v in sorted(meas0.items())},
                         q2_per_layer=per, q2_circuits=q2s, accepted=bool(accepted)),
               points=points, inputs=[KC.input_bits(p_["input"], a.n) for p_ in points],
               noiseless_z=[0.0] * len(points), twin=None, q2=int(q2), us=round(d * 1e6, 3), active=int(active(cs[0])))
    rec["prediction"] = predict_job(p1, labels, a.shots, pr["reps"], pr["level"], pr["seed"] + 1)
    rec["prediction_shots_only"] = predict_job(p1, labels, a.shots, pr["reps"], pr["level"], pr["seed"] + 1)
    rec["prediction"]["twin_p1"] = [float(x) for x in p1]
    rec["test_labels"] = [int(v) for v in labels]  # placeholders, only so that assemble can read the record
    from qiskit import qpy
    with open(qf, "wb") as f:
        qpy.dump(list(cs), f)
    rec["export"] = dict(qpy=os.path.basename(qf), circuits=len(cs), sha256=KC.sha256_file(qf))
    rec.update(wall_s=time.perf_counter() - t0, structural_fail=R.arm.structural_fail,
               on_failed_ops=R.arm.on_failed_ops, ended=S._cest())
    rec["valid"] = bool(accepted and not R.arm.structural_fail and not R.arm.on_failed_ops)
    json.dump(rec, open(jf, "w", encoding="utf-8"))
    print(f"{name}: {len(cs)} circuits (4 inputs + 4 references), {q2} two-qubit gates = {D} x {per}: "
          f"{'ACCEPTED' if accepted else 'REJECTED (two-qubit count ' + str(q2s) + ')'}, {d * 1e6:.2f} us; valid {rec['valid']}")
    return 0 if rec["valid"] else 2



def site_signal(counts_by_input, n):
    """a_j = mean over the inputs of <z_in,j Z_j> (1: every shot returns the input bit; 0: random; < 0: flipped),
    and its shot-noise SE."""
    a, v = np.zeros(n), np.zeros(n)
    for i in INPUTS:
        zin = 1 - 2 * np.array(KC.input_bits(i, n))
        c = counts_by_input[i]
        N = float(sum(c.values()))
        m = np.zeros(n)
        full = 0
        for key, k in c.items():
            b = key.replace(" ", "")
            m += k * np.array([1 - 2 * int(b[n - 1 - j]) for j in range(n)])
        m /= N
        a += zin * m / len(INPUTS)
        v += (1 - m ** 2) / N / len(INPUTS) ** 2
    return a, np.sqrt(v)


def full_match(counts_by_input, n):
    """Fraction of shots, over the inputs, that return the whole input string."""
    hit = tot = 0
    for i in INPUTS:
        want = "".join(str(b) for b in reversed(KC.input_bits(i, n)))
        c = counts_by_input[i]
        hit += sum(k for key, k in c.items() if key.replace(" ", "") == want)
        tot += sum(c.values())
    return hit / tot


def read(job, runs):
    import gzip
    man = json.load(open(os.path.join(job, "manifest.json")))
    p = os.path.join(job, "raw_counts.json")
    raw = json.load(open(p)) if os.path.exists(p) else json.load(gzip.open(p + ".gz"))
    rows = {r["pub"]: r["counts"] for r in raw["rows"]}
    out = {}
    for cid, c in enumerate(man["cells"]):
        rf = os.path.join(runs, c["name"] + ".json")
        if KC.sha256_file(rf) != c["run_sha256"]:
            raise SystemExit(f"STOP: {rf} differs from the manifest")
        rec = json.load(open(rf))
        if not rec.get("qca_test"):
            continue
        cc = {rec["points"][pub["point"]]["input"]: rows[k] for k, pub in enumerate(man["pubs"])
              if pub["cell"] == cid and rec["points"][pub["point"]]["setting"] == "echo"}
        mq = rec["echo"]["measured_qubits"]
        out[c["name"]] = (rec["task"]["n"], [int(mq[str(j)]) for j in range(rec["task"]["n"])], cc)
    return out


def cmd_score(argv):
    import argparse
    from toqb import defect_list as DL
    p = argparse.ArgumentParser(prog="qca_test score")
    p.add_argument("job")
    p.add_argument("runs")
    p.add_argument("--out", required=True)
    a = p.parse_args(argv)
    if os.path.exists(a.out):
        raise SystemExit(f"STOP: {a.out} exists")
    res = {}
    for name, (n, phys, cc) in sorted(read(a.job, a.runs).items()):
        s, se = site_signal(cc, n)
        dead = DL.dead_runs(s, 0.12, 3)
        usable = DL.usable(s, 0.12, 3)
        res[name] = dict(n=n, phys=phys, a=[float(x) for x in s], se=[float(x) for x in se],
                         mean=float(np.mean(s)), mean_se=float(np.sqrt(np.sum(se ** 2)) / n),
                         usable=len(usable), dead=[[phys[(st + t) % n] for t in range(ln)] for st, ln in dead],
                         per_bit=float((1 + np.mean(s)) / 2), full=full_match(cc, n))
        r = res[name]
        print(f"{name}: mean signal {r['mean']:+.3f} +- {r['mean_se']:.3f} (per-bit right {r['per_bit']:.3f}); usable "
              f"{r['usable']}/{n}; whole string {r['full']:.4f}; dead runs {r['dead'] or 'none'}")
    json.dump(res, open(a.out, "w"), indent=1)
    return 0


def main(argv):
    cmds = dict(build=cmd_build, score=cmd_score)
    if not argv or argv[0] not in cmds:
        print(__doc__)
        return 2
    return cmds[argv[0]](argv[1:])


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
