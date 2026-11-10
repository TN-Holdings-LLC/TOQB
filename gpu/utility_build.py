"""Build one device job reproducing observables of IBM's 2023 utility experiment raw (Kim et al., Nature 618, 500;
home, 2026-11-10; to be declared before any run).

Circuit, as published: |0...0> on Eagle's 127-qubit heavy-hex graph, t steps of R_X(theta_h) on every qubit then
R_ZZ(-pi/2) on every edge (each R_ZZ(-pi/2) = RZ(-pi/2) x RZ(-pi/2) then one CZ, checked to 4e-16; all ZZ commute);
theta_h = k pi / 32, k = 0..16. Observables: Z_106 after 4 steps (Fig. 2), the weight-10 product after 5 steps
(Fig. 3), the weight-17 product after 5 steps (Fig. 3) and the Fig. 4a product (Y and Z exchanged) after 5 steps and
one more R_X layer.

Placement (no quality number): Eagle's graph embeds in Heron r2's in two ways (rustworkx VF2, fixed order). For each
observable, the first embedding whose backward light cone (all qubits within t edges of the observable's support,
and every edge touching them) contains no failed qubit or coupler of the day's record; with none, the observable is
not built on that device. Gates on failed elements are left out; they lie outside the cone, so the observable's exact
value is the published circuit's. Every circuit carries the whole embedded circuit otherwise (not the cone alone).
Measured: the observable's qubits only, in its basis (X: H; Y: Sdg H). Each circuit has its floor (no non-diagonal
single-qubit gate) and its mirror (body, inverse, the same measurement), per observable at k = 8; one ring sentinel.

usage: PYTHONPATH=<psf-os>:<TOQB> python gpu/utility_build.py DEV_DIR OUT ANSWERS_OUT SEALED_DIR [--shots 4000]
       [--max-seconds 150] [--obs z106_t4,w10_t5,w17_t5,w17b_t5x]
SEALED_DIR holds the exact values (w10_t5.jsonl, w17_t5.jsonl, w17b_t5x.jsonl; Z_106 is computed here by
utility_exact.tn_value); ANSWERS_OUT gets {tag: value}, and its sha256 is printed.
"""
import argparse
import hashlib
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import utility_exact as UE  # noqa: E402
import utility_tn as UT  # noqa: E402

KS = range(17)


def embeddings(dev_json, eagle_edges):
    import rustworkx as rx
    g = rx.PyGraph()
    g.add_nodes_from(range(dev_json["num_qubits"]))
    g.add_edges_from_no_data(sorted({tuple(sorted(map(int, e))) for e in dev_json["couplers"]}))
    e = rx.PyGraph()
    e.add_nodes_from(range(127))
    e.add_edges_from_no_data(eagle_edges)
    out = []
    for m in rx.vf2_mapping(g, e, subgraph=True, induced=False, id_order=True):   # heron -> eagle
        inv = {v: k for k, v in m.items()}
        if frozenset(inv.values()) not in {frozenset(x.values()) for x in out}:
            out.append(inv)                                                          # eagle -> heron
    return out, e


def cone(obs, t, eg):
    import rustworkx as rx
    D = rx.distance_matrix(eg)
    qs = {q for q in range(127) if min(D[q][s] for s in obs) <= t}
    return qs, {(a, b) for a, b in eg.edge_list() if a in qs or b in qs}


def circuit(inv, eagle_edges, failed_q, failed_e, theta, t, obs, extra_rx, width):
    """The embedded circuit on device qubits, gates on failed elements left out, the observable measured."""
    from qiskit import QuantumCircuit
    keep_q = [q for q in range(127) if inv[q] not in failed_q]
    keep_e = [(a, b) for a, b in eagle_edges
              if inv[a] not in failed_q and inv[b] not in failed_q and tuple(sorted((inv[a], inv[b]))) not in failed_e]
    qc = QuantumCircuit(width, len(obs))
    for _ in range(t):
        for q in keep_q:
            qc.rx(theta, inv[q])
        for a, b in keep_e:
            qc.rz(-math.pi / 2, inv[a])
            qc.rz(-math.pi / 2, inv[b])
            qc.cz(inv[a], inv[b])
    if extra_rx:
        for q in keep_q:
            qc.rx(theta, inv[q])
    for k, q in enumerate(sorted(obs)):
        p = inv[q]
        if obs[q] == "X":
            qc.h(p)
        elif obs[q] == "Y":
            qc.sdg(p)
            qc.h(p)
        qc.measure(p, k)
    return qc


def native(qc):
    from qiskit.transpiler import PassManager
    from qiskit.transpiler.passes import BasisTranslator, Optimize1qGatesDecomposition
    from qiskit.circuit.equivalence_library import SessionEquivalenceLibrary as SEL
    basis = ["cz", "rz", "sx", "x"]
    return PassManager([BasisTranslator(SEL, basis), Optimize1qGatesDecomposition(basis=basis)]).run(qc)


def exact_value(name, k, sealed):
    obs, t, ex = UT.OBS[name]
    if name == "z106_t4":
        return UE.tn_value(obs, UE.eagle_edges(), k * math.pi / 32, t, ex)[0]
    for line in open(os.path.join(sealed, name + ".jsonl")):
        r = json.loads(line)
        if r.get("k") == k:
            return r["re"]
    raise KeyError((name, k))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dev_dir")
    ap.add_argument("out")
    ap.add_argument("answers_out")
    ap.add_argument("sealed_dir")
    ap.add_argument("--shots", type=int, default=4000)
    ap.add_argument("--max-seconds", type=float, default=150)
    ap.add_argument("--obs", default="z106_t4,w10_t5,w17_t5,w17b_t5x")
    a = ap.parse_args()
    for p in (a.out, a.answers_out):
        if os.path.exists(p):
            raise SystemExit(f"STOP: {p} exists")
    from psf_os import circuits as C
    from psf_os import device as Dv
    from psf_os import gatehash as GH
    from psf_os import job as J
    from psf_os import sentinel
    from psf_os.compile import RuleCompiler, measured_qubits
    from psf_os.mirror2d import cz_count
    from psf_os.user2d import floor_of
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from qclf_build import mirror_of, write_record
    dev = Dv.Device.load(a.dev_dir)
    dj = json.load(open(os.path.join(a.dev_dir, "device.json")))
    fq = {int(q) for q in dj["failed_qubits"]}
    fe = {tuple(sorted(map(int, e))) for e in dj["failed_couplers"]}
    ee = UE.eagle_edges()
    embs, eg = embeddings(dj, ee)
    chosen, answers, rep = {}, {}, dict(device=dev.name, embeddings=len(embs), observables={})
    for name in a.obs.split(","):
        obs, t, ex = UT.OBS[name]
        cq, ce = cone(obs, t, eg)
        pick = None
        for i, inv in enumerate(embs):
            if not any(inv[q] in fq for q in cq) and not any(tuple(sorted((inv[x], inv[y]))) in fe for x, y in ce):
                pick = i
                break
        rep["observables"][name] = dict(embedding=pick, cone_qubits=len(cq))
        if pick is not None:
            chosen[name] = pick
    if not chosen:
        raise SystemExit(f"NOT RUN: no observable's cone avoids the failed elements on {dev.name}")
    runs = os.path.join(a.out, "runs")
    os.makedirs(runs)
    for name, i in chosen.items():
        obs, t, ex = UT.OBS[name]
        inv = embs[i]
        cs, pts = [], []
        for k in KS:
            c = native(circuit(inv, ee, fq, fe, k * math.pi / 32, t, obs, ex, dev.num_qubits))
            cs.append(c)
            pts.append(dict(input=f"k{k:02d}", setting=name))
            answers[f"{name}_k{k:02d}"] = exact_value(name, k, a.sealed_dir)
        mid = cs[8]
        fl, mi = floor_of(mid), mirror_of(mid)
        meas = {str(j): inv[q] for j, q in enumerate(sorted(obs))}
        common = dict(observable=name, embedding=i, eagle_support=sorted(obs), measured_qubits=meas, t=t,
                      extra_rx=ex)
        write_record(runs, f"u_{name}", "user", cs, pts, a.shots, common)
        write_record(runs, f"u_{name}_floor", "floor", [fl], [dict(input="k08", setting=name)], a.shots, common)
        write_record(runs, f"u_{name}_mirror", "mirror", [mi], [dict(input="k08", setting=name)], a.shots, common)
        rep["observables"][name].update(cz_per_circuit=cz_count(cs[0]), circuits=len(cs), measured=meas,
                                        mirror_cz=cz_count(mi))
    rc = RuleCompiler(dev)
    ring = 40
    mq = measured_qubits(rc.compile(C.model_circuit(list(np.zeros(C.n_model_angles(ring, 1))), ring, 1)))
    sentinel.build(dev, runs, [int(mq[j]) for j in range(ring)], a.shots, rc)
    man = J.assemble(dev, runs, os.path.join(a.out, "job"), max_seconds=a.max_seconds)
    os.makedirs(os.path.dirname(os.path.abspath(a.answers_out)), exist_ok=True)
    with open(a.answers_out, "w") as f:
        json.dump(answers, f, indent=1, sort_keys=True)
    sha = hashlib.sha256(open(a.answers_out, "rb").read()).hexdigest()
    gh = GH.qpy_hash(os.path.join(a.out, "job", "circuits.qpy"))
    rep.update(circuits=len(man["pubs"]), qpu_seconds_model=man["qpu_seconds_model"], gate_hash=gh, answers_sha256=sha,
               shots=a.shots)
    json.dump(rep, open(os.path.join(a.out, "report.json"), "w"), indent=1)
    for name, r in rep["observables"].items():
        print(f"{name:9} embedding {r['embedding']}  cone {r['cone_qubits']}"
              + (f"  CZ {r['cz_per_circuit']} per circuit" if r["embedding"] is not None else "  NOT BUILT (cone hits a failed element)"))
    print(f"circuits {rep['circuits']}  model {rep['qpu_seconds_model']} s  answers sha256 {sha}")


if __name__ == "__main__":
    main()
