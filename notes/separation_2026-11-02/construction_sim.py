"""Construction for the separation note (notes/separation_2026-11-02): two device states with the same calibration-type
numbers and different best placements, checked in Aer.

SIMULATION ONLY. Nothing here is a device result. The device is IBM's FakeKingston coupling graph (fake elements as
qiskit-ibm-runtime ships them); the noise is planted by this script.

The planted noise acts only when couplers are driven in the same ring layer:
  after a CZ on the planted coupler e, if a coupler at distance one from e (disjoint from e, joined to it by one
  coupler of the device) also carries a CZ in the same ring layer, an extra ZZ error acts on e.
"Same ring layer" is read from the compiled circuit by occurrence: the k-th CZ on a coupler belongs to layer k (each
ring coupler carries exactly one CZ per ring layer; asserted). Two models of the extra error, both fixed before any
run and not tuned:
  coherent  RZZ(theta), theta = pi/8, run as a statevector (n = 20 rings, the scan's own echo at h = 0.6);
  pauli     ZZ with probability p = 0.15 (the value of psf-os test T3), run on the stabilizer method with the echo at
            its Clifford point h = pi/4 (as T3), so that the n = 40 and n = 72 rings can be simulated.
State B is the same device with no planted error. Every circuit with no CZ at distance one from e in the same layer is
left exactly unchanged, so any measurement made on e alone returns the same counts in A and B (V1).

The planted coupler is fixed by rule, not chosen to mimic a device observation: ring positions 12 and 13 of the
standard n = 20 ring (the positions psf-os test T3 plants at on the n = 40 ring); on FakeKingston that is (43, 42), which lies on the
standard n = 20, 40 and 72 rings. On the device (ibm_kingston, 30 Oct to 1 Nov 2026) those qubits were healthy.

Checks (in order of how sure they are to pass):
  V1  calibration-type numbers are unchanged: a mirror benchmark of the CZ on e alone gives identical counts in A
      and B; the same benchmark with a distance-one coupler driven in the same layer does not (scope of the note).
  V2  the ring echo dies in A: a dead run (a_j < 0.12 on 3 or more sites) covers e on the standard rings.
  V3  psf-os finds and avoids it: two scans list the path; the ring placed around the registry has no dead run.
      Only existing psf-os functions are used (scan_job, scan_ingest, registry, plan, score, sentinel.verdict).
  V4  frame flip (coherent model, n = 20): the echo with a local frame flip at ring position 12, at 13, and the
      global flip (all even positions); all three were fixed before running and are all reported.

Usage:  PYTHONPATH=<psf-os> python construction_sim.py WORK_DIR OUT_JSON
"""
import json
import math
import os
import shutil
import sys
import time

import numpy as np

from psf_os import device as Dv
from psf_os import job as J
from psf_os import plan as P
from psf_os import registry as R
from psf_os import scan as S
from psf_os import sentinel as Se
from psf_os import sim

THETA = math.pi / 8
P_ERR = 0.15
SEED = 20261102
BANNER = "SIMULATION with a planted same-layer error on FakeKingston -- not a device result"


# ------------------------------------------------------------------------------------------------ the planted state A

def distance_one(dev, e):
    """Couplers disjoint from e and joined to it by one working coupler of the device."""
    edges = {tuple(sorted(c)) for c in dev.working_couplers()}
    a, b = e
    nbr = {q for (x, y) in edges for q in (x, y) if {x, y} & {a, b}} - {a, b}
    return {f for f in edges if not (set(f) & {a, b}) and set(f) & nbr}


def layer_index(circ):
    """For each CZ instruction (by position): (coupler, k) where k counts that coupler's earlier CZs."""
    seen, out = {}, {}
    for idx, ins in enumerate(circ.data):
        if ins.operation.name == "cz":
            c = tuple(sorted(circ.find_bit(q).index for q in ins.qubits))
            out[idx] = (c, seen.get(c, 0))
            seen[c] = seen.get(c, 0) + 1
    return out, seen


def with_same_layer_error(circ, e, adj, model):
    """The circuit with the extra error after each CZ on e whose layer also drives a coupler in `adj`.
    Returns (circuit, number of inserted errors)."""
    from qiskit import QuantumCircuit
    from qiskit_aer.noise import pauli_error
    e = tuple(sorted(e))
    idx, seen = layer_index(circ)
    by_layer = {}
    for c, k in idx.values():
        by_layer.setdefault(k, set()).add(c)
    out = QuantumCircuit(*circ.qregs, *circ.cregs, name=circ.name)
    inserted = 0
    for i, ins in enumerate(circ.data):
        out.append(ins.operation, [out.qubits[circ.find_bit(q).index] for q in ins.qubits],
                   [out.clbits[circ.find_bit(c).index] for c in ins.clbits])
        if i in idx and idx[i][0] == e and by_layer[idx[i][1]] & adj:
            qa, qb = out.qubits[e[0]], out.qubits[e[1]]
            if model == "coherent":
                out.rzz(THETA, qa, qb)
            else:
                out.append(pauli_error([("ZZ", P_ERR), ("II", 1 - P_ERR)]).to_instruction(), [qa, qb])
            inserted += 1
    return out, inserted


def run_one(c, shots, seed, e=None, adj=None, model=None):
    """Counts of one circuit in state A (e given) or B (e None). Clifford circuits on the stabilizer method,
    others as a statevector of the active qubits."""
    from qiskit_aer import AerSimulator
    cc = sim.to_clifford_gates(c)
    inserted = 0
    if model == "pauli":
        if cc is None:
            raise ValueError("the pauli model needs a Clifford circuit")
        cc, inserted = with_same_layer_error(cc, e, adj, "pauli")
        res = AerSimulator(method="stabilizer").run(cc, shots=shots, seed_simulator=seed).result()
        return dict(res.get_counts(0)), inserted
    if model == "coherent":
        c, inserted = with_same_layer_error(c, e, adj, "coherent")
        if inserted:
            cc = None  # RZZ(pi/8) is not Clifford: statevector below
    if cc is not None:
        res = AerSimulator(method="stabilizer").run(cc, shots=shots, seed_simulator=seed).result()
        return dict(res.get_counts(0)), inserted
    run_c, act = sim.compact(c)
    if len(act) > sim.MAX_STATEVECTOR:
        raise ValueError(f"{len(act)} active qubits: too many for a statevector")
    res = AerSimulator(method="statevector").run(run_c, shots=shots, seed_simulator=seed).result()
    return dict(res.get_counts(0)), inserted


def submit(job_dir, seed, e=None, adj=None, model=None):
    """As psf_os.sim.submit (same files, same format), with the planted state A when e is given."""
    from qiskit import qpy
    man = json.load(open(os.path.join(job_dir, "manifest.json")))
    circs = qpy.load(open(os.path.join(job_dir, "circuits.qpy"), "rb"))
    for c in circs:  # each CZ coupler of a ring circuit carries the same number of CZs (one per ring layer)
        _, seen = layer_index(c)
        if seen and len(set(seen.values())) != 1:
            raise RuntimeError(f"{c.name}: couplers carry different numbers of CZs {sorted(set(seen.values()))}")
    rows, ins = [], 0
    for k, c in enumerate(circs):
        counts, n_ins = run_one(c, man["shots"], seed + k, e, adj, model)
        rows.append(dict(pub=k, counts=counts))
        ins += n_ins
    label = f"local-{model or 'clean'}-{seed}"
    t = sim._stamp()
    json.dump(dict(job_id=label, submitted=t, local=True, backend=man["fetch"]["backend"],
                   simulator=f"aer same-layer {model or 'none'}"), open(os.path.join(job_dir, "submission.json"), "w"))
    json.dump(dict(fetched=t, job_id=label, status="DONE (local)", rows=rows),
              open(os.path.join(job_dir, "raw_counts.json"), "w"))
    return ins


# ------------------------------------------------------------------------------------------------ V1

def mirror_benchmark(nq, pairs, m, seed):
    """m layers of (random single-qubit Clifford on every qubit of `pairs`, one CZ per pair), then the inverse of the
    whole sequence; ideal output all zeros. On the full device register (physical qubit labels)."""
    from qiskit import QuantumCircuit
    from qiskit.quantum_info import random_clifford
    qs = sorted({q for p in pairs for q in p})
    rng = np.random.default_rng(seed)
    fw = QuantumCircuit(nq, nq)
    for _ in range(m):
        for q in qs:
            fw.compose(random_clifford(1, seed=int(rng.integers(1 << 30))).to_circuit(), [q], inplace=True)
        for a, b in pairs:
            fw.cz(a, b)
    qc = fw.compose(fw.inverse())
    for q in qs:  # measure the benchmarked qubits only (clbit = physical qubit)
        qc.measure(q, q)
    return qc


def v1(dev, e, adj, f, shots=4000):
    rows = []
    for label, pairs in (("e alone (calibration-type)", [e]), (f"e with {list(f)} in the same layer", [e, f])):
        for m in (2, 8, 32):
            qc = mirror_benchmark(dev.num_qubits, pairs, m, SEED + m)
            row = dict(benchmark=label, m=m)
            for model in ("pauli", "coherent"):
                ca, ins = run_one(qc, shots, SEED + m, e, adj, model)
                cb, _ = run_one(qc, shots, SEED + m)
                ok = lambda cnt: sum(v for k, v in cnt.items()  # noqa: E731
                                     if all(k.replace(" ", "")[::-1][q] == "0" for q in e)) / shots
                row[model] = dict(inserted=ins, success_A=ok(ca), success_B=ok(cb), identical_counts=ca == cb)
            rows.append(row)
    return rows


# ------------------------------------------------------------------------------------------------ V2, V3, V4

def rings_and_signals(job_dir, runs, D=24):
    prof, *_ = S.job_profiles(job_dir, runs, D=D)
    return {n: (list(map(int, ph)), [float(x) for x in a]) for n, (ph, a) in prof.items()}


def on_ring(ring, e):
    n = len(ring)
    return any({ring[j], ring[(j + 1) % n]} == set(e) for j in range(n))


def dead_cover(ring, a, e):
    runs = S.dead_runs(np.asarray(a))
    n = len(ring)
    out = []
    for s0, L0 in runs:
        qs = [ring[(s0 + t) % n] for t in range(L0)]
        out.append(dict(start=s0, length=L0, qubits=qs, covers_e=set(e) <= set(qs),
                        mean=float(np.mean([a[(s0 + t) % n] for t in range(L0)]))))
    return out


def scans(dev, e, adj, model, spec, sizes, work, now):
    """Two scans in state A, ingested; returns registry path, per-scan profiles, LISTED entries."""
    base, profs = None, []
    for k in (1, 2):
        s = P.scan_job(dev, os.path.join(work, f"scan{k}"), sizes=sizes, spec=spec)
        submit(s["job"], SEED + 100 * k, e, adj, model)
        profs.append(rings_and_signals(s["job"], s["runs"]))
        reg, _ = P.scan_ingest(dev.name, s["job"], s["runs"], base, f"scan{k}")
        base = os.path.join(work, f"registry_{k}.json")
        R.save(reg, base)
    reg = R.load(base)
    listed = [dict(path=x["centre"], status=x["status"]) for x in R.entries(reg["observations"], now=now)]
    return base, profs, listed


def user_echo(dev, job, reg_path, work, now, e, adj, model, sentinel_spec):
    out = {}
    for arm in ("standard", "avoiding"):
        d = os.path.join(work, f"{arm}_{job['kind']}_n{job['n']}")
        if arm == "standard":
            rep = P.plan(dev, job, R.empty(), d, now, standard=True)
        else:
            rep = P.plan(dev, job, R.load(reg_path), d, now, sentinel_spec=sentinel_spec)
        uj = rep["user_job"]
        submit(uj["job"], SEED + 7, e, adj, model)
        (sc,) = J.score(uj["job"], uj["runs"]).values()
        row = dict(ring=sc["ring"], e_on_ring=on_ring(sc["ring"], e), usable=sc["usable"], n=sc["n"],
                   mean_all=float(np.mean(sc["a"])), dead=sc["dead"], masked=rep["masked_couplers"])
        usable_sites = S.usable(np.asarray(sc["a"]))
        row["mean_usable"] = float(np.mean([sc["a"][j] for j in usable_sites])) if usable_sites else None
        if arm == "avoiding":
            row["sentinel"] = Se.verdict(uj["job"], uj["runs"])["status"]
        out[arm] = row
    return out


def v4(dev, e, adj, ring20, work):
    """Coherent model, n = 20 echo (h = 0.6, D = 24) on the standard ring with no flip and with three fixed flips."""
    pos = [j for j in range(20) if {ring20[j], ring20[(j + 1) % 20]} == set(e)][0]
    variants = [("no flip", None), (f"flip at {pos}", [pos]), (f"flip at {pos + 1}", [pos + 1]),
                ("global flip (even positions)", list(range(0, 20, 2)))]
    rows = []
    for label, flip in variants:
        runs = os.path.join(work, "v4", label.replace(" ", "_").replace("(", "").replace(")", ""), "runs")
        job = dict(kind="echo", n=20, D=24, h=0.6, hz=0.0, shots=1000)
        if flip:
            job["flip"] = flip
        J.build(dev, job, runs)
        jd = os.path.join(os.path.dirname(runs), "job")
        J.assemble(dev, runs, jd)
        res = {}
        for state, kw in (("A", dict(e=e, adj=adj, model="coherent")), ("B", {})):
            jd_s = jd + "_" + state
            shutil.copytree(jd, jd_s)
            submit(jd_s, SEED + 40, **kw)
            (sc,) = J.score(jd_s, runs).values()
            seg = [j % 20 for j in range(pos - 2, pos + 4)]
            res[state] = dict(usable=sc["usable"], mean_all=float(np.mean(sc["a"])),
                              near_e=[round(sc["a"][j], 3) for j in seg], dead=sc["dead"])
        rows.append(dict(variant=label, flip=flip, **res))
    return rows


def main(work, out_json):
    t0 = time.time()
    os.makedirs(work, exist_ok=False)
    print(BANNER)
    dev = Dv.fetch_fake("FakeKingston")
    now = P.now_cet()
    probe = P.scan_job(dev, os.path.join(work, "probe"), sizes=(20,))
    rec = [json.load(open(os.path.join(probe["runs"], x))) for x in os.listdir(probe["runs"]) if x.endswith(".json")][0]
    ring20 = [int(rec["echo"]["measured_qubits"][str(j)]) for j in range(20)]
    e = tuple(sorted((ring20[12], ring20[13])))
    adj = distance_one(dev, e)
    f = sorted(adj)[0]
    print(f"device {dev.name}: {len(dev.couplers)} couplers, {len(dev.failed_couplers)} failed; planted coupler e = {e}; "
          f"distance-one couplers {sorted(adj)}")
    res = dict(banner=BANNER, device=dev.name, e=list(e), distance_one=[list(x) for x in sorted(adj)],
               theta=THETA, p=P_ERR, seed=SEED)

    res["V1"] = v1(dev, e, adj, f)
    for r in res["V1"]:
        print("V1", r["benchmark"], "m =", r["m"], {k: r[k] for k in ("pauli", "coherent")})

    # coherent model, n = 20, the scan's own echo (h = 0.6)
    wc = os.path.join(work, "coherent")
    reg_c, prof_c, listed_c = scans(dev, e, adj, "coherent", None, (20,), wc, now)
    ring, a = prof_c[0][20]
    res["V2_coherent"] = dict(n=20, ring=ring, e_on_ring=on_ring(ring, e), a_scan1=a,
                              dead=dead_cover(ring, a, e), usable=len(S.usable(np.asarray(a))))
    res["V3_coherent"] = dict(listed=listed_c,
                              user=user_echo(dev, dict(kind="echo", n=20, D=24, h=0.6, hz=0.0, shots=1000), reg_c, wc,
                                             now, e, adj, "coherent", None))
    print("V2 coherent n=20:", res["V2_coherent"]["dead"], "usable", res["V2_coherent"]["usable"])
    print("V3 coherent:", listed_c, {k: (v["usable"], v["e_on_ring"]) for k, v in res["V3_coherent"]["user"].items()})

    # pauli model, n = 20, 40, 72, the echo at its Clifford point
    wp = os.path.join(work, "pauli")
    spec = dict(kind="echo_clifford", D=24, shots=1000)
    reg_p, prof_p, listed_p = scans(dev, e, adj, "pauli", spec, (20, 40, 72), wp, now)
    res["V2_pauli"] = {}
    for n, (ring, a) in sorted(prof_p[0].items()):
        res["V2_pauli"][n] = dict(ring=ring, e_on_ring=on_ring(ring, e), a_scan1=a, dead=dead_cover(ring, a, e),
                                  usable=len(S.usable(np.asarray(a))))
        print(f"V2 pauli n={n}:", res["V2_pauli"][n]["dead"], "usable", res["V2_pauli"][n]["usable"])
    res["V3_pauli"] = dict(listed=listed_p, user={})
    for n in (40, 72):
        res["V3_pauli"]["user"][n] = user_echo(dev, dict(kind="echo_clifford", n=n, D=24, shots=1000), reg_p,
                                               os.path.join(wp, f"u{n}"), now, e, adj, "pauli",
                                               dict(kind="echo_clifford", D=24))
        print(f"V3 pauli n={n}:", {k: (v["usable"], v["e_on_ring"], v.get("sentinel"))
                                   for k, v in res["V3_pauli"]["user"][n].items()})
    print("listed (pauli):", listed_p)

    res["V4"] = v4(dev, e, adj, ring20, work)
    for r in res["V4"]:
        print("V4", r["variant"], "A:", r["A"]["usable"], r["A"]["near_e"], "B:", r["B"]["usable"], r["B"]["near_e"])

    res["seconds"] = round(time.time() - t0, 1)
    json.dump(res, open(out_json, "w"), indent=1, default=str)
    print(f"done in {res['seconds']} s. {BANNER}.")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
