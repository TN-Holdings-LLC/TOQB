"""Exploratory (owner, 2026-11-05 evening: "no record needed; fix the correction as well as possible, check it, then
test D02 on the device to see if the direction is right"). Not declared, not part of the daily record.

One job per device with, for each user circuit (D02 and FX-A as the control):
  raw      the compiled circuit, readout-twirled                          (K_R instances)
  tw       the compiled circuit with every CZ Pauli-twirled, readout-twirled (K instances)
  floor    the compiled circuit without non-diagonal one-qubit gates, readout-twirled (K_R)
  mraw     the compiled mirror U, barrier, U^dagger, readout-twirled       (K_R)
  mtw      the compiled mirror with every CZ Pauli-twirled, readout-twirled (K)
  floor2   the floor of the compiled mirror (the mirror's depth), readout-twirled (K_R)
Twirl tables are fixed (no random numbers): CZ number g, instance k -> Pauli pair index (7 g + 3 k + 1) mod 16.
Readout twirl: qubit j of instance k gets an X before its measurement if (j + k) is odd; the bit is flipped back.

The correction (scored by `score`): rule R on the floor; guard: floor < 0.3 -> unreadable; per qubit
z_corr = z_tw / (F_q * g), g = exp(median over kept q of 0.5 ln(m_q / F2_q)) (mirror at depth 2t over the floor at 2t),
for the twirled pair (tw, mtw) and for the untwirled pair (raw, mraw) side by side.

usage: PYTHONPATH=<psf-os ac84182>:<TOQB> python gpu/twirl_explore.py build DEV_DIR CIRCUITS_DIR OUT_DIR ID [ID ...]
       PYTHONPATH=... python gpu/twirl_explore.py score OUT_DIR ANSWERS.json
"""
import json
import os
import sys

import numpy as np

K, K_R, SHOTS = 8, 4, 1000
PAULIS = [(a, b) for a in "IXYZ" for b in "IXYZ"]


def _apply_pauli(out, p, q):
    if p == "X":
        out.x(q)
    elif p == "Z":
        out.rz(np.pi, q)
    elif p == "Y":
        out.rz(np.pi, q)
        out.x(q)


def twirl(compiled, k):
    """Every CZ (a, b) -> (Pa x Pb) CZ (Pa' x Pb'), Pa' = Pa Z^[Pb has X], Pb' = Pb Z^[Pa has X]: the same unitary up
    to a global phase. Then one-qubit runs are merged (rz, sx, x); the CZ count is unchanged."""
    from qiskit.transpiler import PassManager
    from qiskit.transpiler.passes import Optimize1qGatesDecomposition
    out = compiled.copy_empty_like()
    g = 0
    for ins in compiled.data:
        if ins.operation.name == "cz":
            a, b = ins.qubits
            pa, pb = PAULIS[(7 * g + 3 * k + 1) % 16]
            _apply_pauli(out, pa, a)
            _apply_pauli(out, pb, b)
            out.append(ins.operation, ins.qubits, ins.clbits)
            _apply_pauli(out, pa, a)
            _apply_pauli(out, pb, b)
            if pb in "XY":
                out.rz(np.pi, a)
            if pa in "XY":
                out.rz(np.pi, b)
            g += 1
        else:
            out.append(ins.operation, ins.qubits, ins.clbits)
    return PassManager([Optimize1qGatesDecomposition(basis=["rz", "sx", "x"])]).run(out)


def flips(n, k):
    return [int((j + k) % 2 == 1) for j in range(n)]


def readout_twirl(c, k):
    """An X before the measurement of clbit j when flips[j]; the clbit is flipped back in scoring."""
    out = c.copy_empty_like()
    meas = [(ins.qubits, ins.clbits) for ins in c.data if ins.operation.name == "measure"]
    body = [ins for ins in c.data if ins.operation.name != "measure"]
    for ins in body:
        out.append(ins.operation, ins.qubits, ins.clbits)
    fl = flips(len(meas), k)
    for (qs, cs) in meas:
        j = c.find_bit(cs[0]).index
        if fl[j]:
            out.x(qs[0])
    for (qs, cs) in meas:
        out.measure(qs[0], cs[0])
    return out


def build(dev_dir, circ_dir, out, ids):
    from psf_os import device as Dv
    from psf_os import job as J
    from psf_os import lattice2d as L
    from psf_os import mirror2d as M
    from psf_os import user2d as U
    from psf_os.compile import RuleCompiler, rzz_exact
    if os.path.exists(out):
        raise SystemExit(f"STOP: {out} exists")
    dev = Dv.Device.load(dev_dir)
    rc = RuleCompiler(dev)
    runs = os.path.join(out, "runs")
    os.makedirs(runs)
    rep = {}
    for pid in ids:
        qc = U.load(os.path.join(circ_dir, f"{pid}.qpy"))
        labels, edges, logical = U.analyse(qc, dev)
        dr, dc, m, reasons = L.place(dev, edges, labels)
        phys = [m[q] for q in labels]
        u = rzz_exact(U.relabel(logical, m, dev.num_qubits))
        cu = rc.pm.run(U.with_measure(u, phys))
        cm = rc.pm.run(M.mirror(u, phys))
        cz = M.cz_count(cu)
        sets = {
            "raw": [readout_twirl(cu, k) for k in range(K_R)],
            "tw": [readout_twirl(twirl(cu, k), k) for k in range(K)],
            "floor": [readout_twirl(U.floor_of(cu), k) for k in range(K_R)],
            "mraw": [readout_twirl(cm, k) for k in range(K_R)],
            "mtw": [readout_twirl(twirl(cm, k), k) for k in range(K)],
            "floor2": [readout_twirl(U.floor_of(cm), k) for k in range(K_R)],
        }
        for role, cs in sets.items():
            want = 2 * cz if role in ("mraw", "mtw", "floor2") else cz
            got = [M.cz_count(c) for c in cs]
            if any(x != want for x in got):
                raise SystemExit(f"STOP: {pid} {role}: CZ {got}, expected {want}")
            U._record(dev, runs, f"x_{pid}_{role}", role, f"x_{role}", cs,
                      [dict(input=f"k{k}", setting="z") for k in range(len(cs))], labels=labels, mapping=m,
                      extra=dict(pid=pid, edges=[list(e) for e in edges], cz=want), shots=SHOTS, valid=True)
        rep[pid] = dict(copy=dict(drow=dr, dcol=dc), cz=cz, labels=labels)
    man = J.assemble(dev, runs, os.path.join(out, "job"), max_seconds=40)
    rep.update(device=dev.name, circuits=len(man["pubs"]), qpu_seconds_model=man["qpu_seconds_model"])
    json.dump(rep, open(os.path.join(out, "report.json"), "w"), indent=1)
    print(json.dumps({k: v for k, v in rep.items() if k not in ids}),
          {p: (rep[p]["copy"], rep[p]["cz"]) for p in ids})
    return rep


def z_of(counts, n, k):
    """<Z_j> for clbit j, readout twirl of instance k undone."""
    fl = flips(n, k)
    tot = sum(counts.values())
    z = np.zeros(n)
    for bits, c in counts.items():
        b = bits.replace(" ", "")[::-1]
        z += c * np.array([1 - 2 * (int(b[j]) ^ fl[j]) for j in range(n)])
    return z / tot


def read(out):
    from psf_os import job as J
    got = {}
    for name, (rec, cc) in J.read(os.path.join(out, "job"), os.path.join(out, "runs")).items():
        if not rec.get("psfos_job", {}).get("kind", "").startswith("x_"):
            continue
        n = len(rec["labels"])
        zs = [z_of(cc[(f"k{k}", "z")], n, k) for k in range(len(rec["points"]))]
        got.setdefault(rec["pid"], dict(labels=rec["labels"], edges=rec["edges"]))[rec["psfos_role"]] = np.mean(zs, 0)
    return got


def correct(d, ans, guard=0.3):
    lab = d["labels"]
    idx = [i for i, q in enumerate(lab) if str(q) in ans]
    a = np.array([ans[str(lab[i])] for i in idx])
    F, F2 = d["floor"][idx], d["floor2"][idx]
    med = np.median(F)
    mad = np.median(np.abs(F - med))
    keep = (F >= med - max(5 * 1.4826 * mad, 0.05)) & (F >= guard) & (F2 >= 0.05)
    res = {}
    for name, val in (("raw", d["raw"]), ("tw", d["tw"])):
        res[name] = val[idx]
    for name, zk, mk in (("corr_raw", "raw", "mraw"), ("corr_tw", "tw", "mtw")):
        m = d[mk][idx]
        rate = 0.5 * np.log(np.clip(m / np.maximum(F2, 0.05), 1e-3, 1.0))
        g = float(np.exp(np.median(rate[keep])))
        res[name] = d[zk][idx] / (F * g)
        res[name + "_g"] = g
    res["floor_only_tw"] = d["tw"][idx] / F
    out = {}
    for name in ("raw", "tw", "floor_only_tw", "corr_raw", "corr_tw"):
        v = res[name]
        sel = keep if name.startswith(("corr", "floor")) else np.ones(len(a), bool)
        out[name] = dict(diff=float(v[sel].mean() - a[sel].mean()), mse=float(np.mean((v[sel] - a[sel]) ** 2)),
                         n=int(sel.sum()))
    out["g_raw"], out["g_tw"] = res["corr_raw_g"], res["corr_tw_g"]
    out["dropped"] = [lab[idx[i]] for i in range(len(idx)) if not keep[i]]
    return out


def score(out, answers):
    ans = json.load(open(answers))
    got = read(out)
    res = {pid: correct(d, ans[pid]) for pid, d in got.items()}
    json.dump(res, open(os.path.join(out, "scores.json"), "w"), indent=1)
    for pid, r in res.items():
        print(pid, "dropped", r["dropped"], f"| gate/run raw {r['g_raw']:.3f} tw {r['g_tw']:.3f}")
        for name in ("raw", "tw", "floor_only_tw", "corr_raw", "corr_tw"):
            x = r[name]
            print(f"   {name:14} diff {x['diff']:+.3f}  MSE {x['mse']:.4f}  ({x['n']} q)")
    return res


if __name__ == "__main__":
    if sys.argv[1] == "build":
        build(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5:])
    else:
        score(sys.argv[2], sys.argv[3])
