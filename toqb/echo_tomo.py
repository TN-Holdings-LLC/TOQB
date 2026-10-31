"""Where did the echo's signal go? (2026-10-31, stage 1 of the coherent-error test; design draft, not declared)

The rule's mirror echo returns the flipped input; read in Z only, a site whose Bloch vector was rotated into the X-Y
plane looks the same as a site whose signal was lost. Here the echo circuits of toqb.kising_echo are read in three
bases. For each ring site j and echo input i the expected output is -z_in,j along Z, so the sign-aligned vector

    v_j = mean over the 4 inputs of (-z_in,j) * (<X_j>, <Y_j>, <Z_j>)

is (0, 0, 1) without noise. A coherent single-qubit rotation keeps |v_j| and tilts it; loss (decoherence, randomising
errors) shrinks |v_j|. Read at several depths in Z, a rotation that grows with depth makes v_z change sign; loss does
not.

    python -m toqb.echo_tomo build FETCH RUNS --n 40 --L 12 [--hz 0] [--shots 1000] --basis X|Y|Z
    python -m toqb.echo_tomo score JOB RUNS --block 38,49,... --segment 3,4,... [--other 3,...] --out F

`build` makes the Z record with toqb.kising_echo (the identical circuit) and, for X or Y, a copy whose echo circuits
get a basis change before every measurement (X: RZ(pi/2) SX RZ(pi/2), i.e. H; Y: SX RZ(pi/2), i.e. H S^dagger); the
reference circuits stay in Z. Two-qubit gates are unchanged.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile

import numpy as np

from toqb import kising_charge as KC

NAME = re.compile(r"kecho_n(\d+)_D(\d+)_hz([0-9.]+)_h([0-9.]+)-(.+?)(?:_b([XYZ]))?$")


def with_basis(circ, basis):
    """The circuit with a basis change on every measured qubit just before its measurement (X or Y); Z unchanged."""
    if basis == "Z":
        return circ
    import numpy as _np
    from qiskit import QuantumCircuit
    out = QuantumCircuit(*circ.qregs, *circ.cregs, name=circ.name)
    for i in circ.data:
        if i.operation.name == "measure":
            q = out.qubits[circ.find_bit(i.qubits[0]).index]
            if basis == "X":
                out.rz(_np.pi / 2, q)
                out.sx(q)
                out.rz(_np.pi / 2, q)
            elif basis == "Y":
                out.sx(q)
                out.rz(_np.pi / 2, q)
            else:
                raise ValueError(basis)
        out.append(i.operation, [out.qubits[circ.find_bit(q).index] for q in i.qubits],
                   [out.clbits[circ.find_bit(c).index] for c in i.clbits])
    return out


def cmd_build(argv):
    import argparse
    from qiskit import qpy
    p = argparse.ArgumentParser(prog="echo_tomo build")
    p.add_argument("fetch")
    p.add_argument("runs")
    p.add_argument("--n", type=int, required=True)
    p.add_argument("--L", type=int, required=True)
    p.add_argument("--hz", type=float, default=0.0)
    p.add_argument("--h", type=float, default=0.6)
    p.add_argument("--shots", type=int, default=1000)
    p.add_argument("--basis", choices=["X", "Y", "Z"], required=True)
    p.add_argument("--arm", default="fold:rule")
    a = p.parse_args(argv)
    base = f"kecho_n{a.n}_D{2 * a.L}_hz{a.hz:g}_h{a.h:g}-{a.arm.replace(':', '_')}"
    if a.basis == "Z":
        r = subprocess.run([sys.executable, "-m", "toqb.kising_echo", "build", a.fetch, a.runs, "--arm", a.arm, "--n",
                            str(a.n), "--L", str(a.L), "--hz", str(a.hz), "--h", str(a.h), "--shots", str(a.shots)],
                           capture_output=True, text=True)
        print((r.stdout + r.stderr).strip().splitlines()[-1])
        return r.returncode
    name = f"{base}_b{a.basis}"
    jo, qo = (os.path.join(a.runs, name + e) for e in (".json", ".qpy"))
    for f in (jo, qo):
        if os.path.exists(f):
            print(f"STOP: {f} exists", file=sys.stderr)
            return 2
    with tempfile.TemporaryDirectory() as tmp:
        r = subprocess.run([sys.executable, "-m", "toqb.kising_echo", "build", a.fetch, tmp, "--arm", a.arm, "--n",
                            str(a.n), "--L", str(a.L), "--hz", str(a.hz), "--h", str(a.h), "--shots", str(a.shots)],
                           capture_output=True, text=True)
        if r.returncode:
            print(r.stdout + r.stderr, file=sys.stderr)
            return r.returncode
        rec = json.load(open(os.path.join(tmp, base + ".json")))
        cs = qpy.load(open(os.path.join(tmp, base + ".qpy"), "rb"))
        new = [with_basis(c, a.basis) if pt["setting"] == "echo" else c for c, pt in zip(cs, rec["points"])]
        os.makedirs(a.runs, exist_ok=True)
        with open(qo, "wb") as f:
            qpy.dump(new, f)
        rec["plan"] = rec["plan"] + f" (echo read in {a.basis})"
        rec["echo"] = dict(rec["echo"], basis=a.basis, source_qpy_sha256=rec["export"]["sha256"])
        rec["export"] = dict(qpy=os.path.basename(qo), circuits=len(new), sha256=KC.sha256_file(qo))
        json.dump(rec, open(jo, "w", encoding="utf-8"))
    print(f"{name}: {len(new)} circuits; echo circuits read in {a.basis}; valid {rec['valid']}")
    return 0 if rec["valid"] else 2


# ------------------------------------------------------------------------------------------------ scoring

def _pm(counts, n):
    """Per bit (clbit index) <(-1)^b> and its shot-noise SE from one counts dict."""
    m, N = np.zeros(n), 0.0
    for key, k in counts.items():
        b = key.replace(" ", "")
        m += k * np.array([1 - 2 * int(b[n - 1 - j]) for j in range(n)])
        N += k
    m /= N
    return m, np.sqrt(np.maximum(1 - m ** 2, 0) / N)


def aligned(counts_by_input, n):
    """Sign-aligned component a_j = mean over inputs of (-z_in,j) <P_j> and its SE (P the record's basis)."""
    a, v = np.zeros(n), np.zeros(n)
    for i in KC.INPUTS:
        zin = 1 - 2 * np.array(KC.input_bits(i, n))
        m, se = _pm(counts_by_input[i], n)
        a += -zin * m / 4
        v += se ** 2 / 16
    return a, np.sqrt(v)


def connected(counts_by_input, n):
    """Per ring pair (j, j+1 mod n): mean over the inputs of |<P_j P_j+1> - <P_j><P_j+1>| (P the record's basis)."""
    c = np.zeros(n)
    for i in KC.INPUTS:
        Z, w = [], []
        for key, k in counts_by_input[i].items():
            b = key.replace(" ", "")
            Z.append([1 - 2 * int(b[n - 1 - j]) for j in range(n)])
            w.append(k)
        Z, w = np.array(Z, float), np.array(w, float)
        w /= w.sum()
        m = w @ Z
        for j in range(n):
            jj = (j + 1) % n
            c[j] += abs(float(w @ (Z[:, j] * Z[:, jj]) - m[j] * m[jj])) / len(KC.INPUTS)
    return c


def read_job(job, runs):
    """{(n, D, basis): (phys, a, se, corr)} for every echo record of the job (corr: connected pair correlations)."""
    import gzip
    man = json.load(open(os.path.join(job, "manifest.json")))
    p = os.path.join(job, "raw_counts.json")
    raw = json.load(open(p)) if os.path.exists(p) else json.load(gzip.open(p + ".gz"))
    rows = {r["pub"]: r["counts"] for r in raw["rows"]}
    out = {}
    for cid, c in enumerate(man["cells"]):
        m = NAME.match(c["name"])
        if not m:
            continue
        rf = os.path.join(runs, c["name"] + ".json")
        if KC.sha256_file(rf) != c["run_sha256"]:
            raise SystemExit(f"STOP: {rf} differs from the manifest")
        rec = json.load(open(rf))
        n, D, basis = rec["task"]["n"], rec["echo"]["D"], rec["echo"].get("basis", "Z")
        if (n, D, basis) in out:
            raise SystemExit(f"STOP: two records for n {n} D {D} basis {basis}")
        cc = {}
        for k, pub in enumerate(man["pubs"]):
            if pub["cell"] == cid:
                pt = rec["points"][pub["point"]]
                if pt["setting"] == "echo":
                    cc[pt["input"]] = rows[k]
        mq = rec["echo"]["measured_qubits"]
        a, se = aligned(cc, n)
        out[(n, D, basis)] = ([int(mq[str(j)]) for j in range(n)], a, se, connected(cc, n))
    return out


def bloch(data, n, D):
    """Per site (vx, vy, vz), |v| and the transverse fraction |v_xy| / |v|, at (n, D) if all three bases were read."""
    if not all((n, D, b) in data for b in "XYZ"):
        return None
    phys = data[(n, D, "Z")][0]
    if any(data[(n, D, b)][0] != phys for b in "XY"):
        raise SystemExit(f"STOP: the X, Y and Z records of n {n} D {D} are on different rings")
    vx, vy, vz = (data[(n, D, b)][1] for b in "XYZ")
    r = np.sqrt(vx ** 2 + vy ** 2 + vz ** 2)
    tf = np.sqrt(vx ** 2 + vy ** 2) / np.maximum(r, 1e-12)
    return dict(phys=phys, vx=vx, vy=vy, vz=vz, r=r, transverse=tf)


def verdict_length(r_seg, r_rest, keep=0.8, lost=0.5):
    """KEPT: the segment's single-site vector length is >= keep x the rest's (the signal was turned, a per-site
    counter-rotation could bring it back); SHRUNK: < lost x the rest's; otherwise MIXED."""
    if r_seg < lost * r_rest:
        return "SHRUNK"
    if r_seg >= keep * r_rest:
        return "KEPT"
    return "MIXED"


def crossings(vals, ses, k=2.0):
    """Signs of the values that are beyond k SE, in depth order, with repeats merged (e.g. '+-+')."""
    out = ""
    for v, s in zip(vals, ses):
        t = "+" if v > k * s else "-" if v < -k * s else ""
        if t and (not out or out[-1] != t):
            out += t
    return out


def verdict_depth(vals, ses):
    """OSCILLATES: + then - then + again over depth (a turning that comes back: a periodic coherent error);
    CROSSES ONCE: + then - (turned past zero, not back within the depths read); STARTS INVERTED: the first value
    beyond 2 SE is already negative; NO CROSSING otherwise."""
    p = crossings(vals, ses)
    if p.startswith("-"):
        return "STARTS INVERTED"
    if "+-+" in p:
        return "OSCILLATES"
    if "+-" in p:
        return "CROSSES ONCE"
    return "NO CROSSING"


def verdict_corr(c_seg, c_rest_pairs, k=3.0):
    """ENTANGLED: the segment's mean connected correlation exceeds the mean of the rest's pairs by more than k x their
    spread / sqrt(#rest pairs) and by at least 0.05; NOT SEEN otherwise."""
    r = np.asarray(c_rest_pairs, float)
    se = float(np.std(r, ddof=1) / np.sqrt(len(r))) if len(r) > 1 else 0.0
    return "ENTANGLED" if c_seg > r.mean() + max(k * se, 0.05) else "NOT SEEN"


def sign_change(depths, vals, ses):
    """(validation helper) OSCILLATES if the values reach both > +2 SE and < -2 SE over the depths, else MONOTONE."""
    pos = any(v > 2 * s for v, s in zip(vals, ses))
    neg = any(v < -2 * s for v, s in zip(vals, ses))
    return "OSCILLATES" if pos and neg else "MONOTONE"


def defect_present(phys, a, path, thr=0.12, min_len=3, need=2, rel=None):
    """True if a dead run (>= min_len consecutive ring sites below thr, cyclic) holds >= need qubits of path. With
    `rel`, the line is max(thr, rel x the ring's median) (a weak run, toqb.safe_loop's rule)."""
    from toqb import defect_list as DL
    if rel is not None:
        thr = max(thr, rel * float(np.median(a)))
    for st, ln in DL.dead_runs(np.asarray(a), thr=thr, min_len=min_len):
        q = {phys[(st + t) % len(phys)] for t in range(ln)}
        if len(q & set(path)) >= need:
            return True
    return False


def _sites(phys, qs):
    return [j for j, q in enumerate(phys) if q in qs]


def _pairs(phys, qs, inside=True):
    n = len(phys)
    if inside:
        return [j for j in range(n) if phys[j] in qs and phys[(j + 1) % n] in qs]
    return [j for j in range(n) if phys[j] not in qs and phys[(j + 1) % n] not in qs]


def cmd_score(argv):
    import argparse
    p = argparse.ArgumentParser(prog="echo_tomo score")
    p.add_argument("job")
    p.add_argument("runs")
    p.add_argument("--block", required=True, help="judged block: physical qubits, comma separated")
    p.add_argument("--segment", required=True, help="the whole dead run (the rest = the ring minus this)")
    p.add_argument("--other", default="", help="reported block")
    p.add_argument("--path", default="28,29,38,49", help="listed path for the precondition")
    p.add_argument("--weak-rel", type=float, default=None, help="precondition on a weak run (line max(0.12, rel x median))")
    p.add_argument("--n", type=int, default=40)
    p.add_argument("--control-n", type=int, default=20)
    p.add_argument("--D", type=int, default=24)
    p.add_argument("--D-tomo", type=int, default=12)
    p.add_argument("--out", required=True)
    a = p.parse_args(argv)
    if os.path.exists(a.out):
        raise SystemExit(f"STOP: {a.out} exists")
    ints = lambda t: {int(x) for x in t.split(",") if x}  # noqa: E731
    blk, seg, oth, path = ints(a.block), ints(a.segment), ints(a.other), ints(a.path)
    data = read_job(a.job, a.runs)
    res = dict(block=sorted(blk), segment=sorted(seg), other=sorted(oth), path=sorted(path), cells={})
    for (n, D, b), (phys, v, se, c) in sorted(data.items()):
        res["cells"][f"n{n}_D{D}_{b}"] = dict(phys=phys, a=[float(x) for x in v], se=[float(x) for x in se],
                                              corr=[float(x) for x in c])
    # P0: the defect is there today (Z, D = 24, the declared dead-run rule)
    phys, v, se, _ = data[(a.n, a.D, "Z")]
    res["P0"] = present = defect_present(phys, v, path, rel=a.weak_rel)
    kind = "a dead run" if a.weak_rel is None else f"a weak run (line max(0.12, {a.weak_rel:g} x median))"
    print(f"P0 n {a.n} D {a.D}: {kind} holds >= 2 of {sorted(path)}: {'PRESENT' if present else 'ABSENT'}")
    if not present:
        print("the defect is absent: nothing is judged (all values are reported in the output file)")
    # J1: the block's Z signal over depth (primary)
    zs = sorted(D for (n, D, b) in data if n == a.n and b == "Z")
    blocks = [("block", blk)] + ([("other", oth)] if oth else []) + [("rest", None)]
    res["depth"] = {}
    for name, qs in blocks:
        vals, ses = [], []
        for D in zs:
            ph, v, se, _ = data[(a.n, D, "Z")]
            g = _sites(ph, qs) if qs is not None else [j for j, q in enumerate(ph) if q not in seg]
            vals.append(float(np.mean(v[g])))
            ses.append(float(np.sqrt(np.sum(se[g] ** 2)) / len(g)))
        res["depth"][name] = dict(depths=zs, a=vals, se=ses, signs=crossings(vals, ses), verdict=verdict_depth(vals, ses))
        print(f"{'J1' if name == 'block' else '  '} {name} a over D: "
              + ", ".join(f"{D}: {x:+.3f}" for D, x in zip(zs, vals)) + f" -> {res['depth'][name]['verdict']}")
    # J2: single-site vector length at D-tomo (and at D, reported)
    res["length"] = {}
    for D in sorted({a.D_tomo, a.D}):
        bl = bloch(data, a.n, D)
        if bl is None:
            continue
        g, rr = _sites(bl["phys"], blk), [j for j, q in enumerate(bl["phys"]) if q not in seg]
        rg, rr_ = float(np.mean(bl["r"][g])), float(np.mean(bl["r"][rr]))
        e = dict(r_block=rg, r_rest=rr_, transverse_block=float(np.mean(bl["transverse"][g])),
                 transverse_rest=float(np.mean(bl["transverse"][rr])), verdict=verdict_length(rg, rr_),
                 v_block=[float(np.mean(bl[k][g])) for k in ("vx", "vy", "vz")])
        if oth:
            go = _sites(bl["phys"], oth)
            e["r_other"] = float(np.mean(bl["r"][go]))
        res["length"][f"D{D}"] = e
        print(f"{'J2' if D == a.D_tomo else '  '} D {D}: |v| block {rg:.3f}, rest {rr_:.3f}; mean v block "
              f"({e['v_block'][0]:+.3f}, {e['v_block'][1]:+.3f}, {e['v_block'][2]:+.3f}); transverse block "
              f"{e['transverse_block']:.2f}, rest {e['transverse_rest']:.2f} -> {e['verdict']}")
    # J3: connected neighbour correlations in X, Y, Z at D-tomo (and at D, reported)
    res["corr"] = {}
    for D in sorted({a.D_tomo, a.D}):
        for b in "XYZ":
            if (a.n, D, b) not in data:
                continue
            ph, _, _, c = data[(a.n, D, b)]
            ib, rp = _pairs(ph, blk), _pairs(ph, seg, inside=False)
            cb = float(np.mean(c[ib]))
            res["corr"][f"D{D}_{b}"] = dict(block=cb, rest=float(np.mean(c[rp])), rest_sd=float(np.std(c[rp], ddof=1)),
                                            k_block=len(ib), k_rest=len(rp), verdict=verdict_corr(cb, c[rp]))
        row = [f"{b} {res['corr'][f'D{D}_{b}']['block']:.3f}/{res['corr'][f'D{D}_{b}']['rest']:.3f}"
               for b in "XYZ" if f"D{D}_{b}" in res["corr"]]
        vs = [res["corr"][f"D{D}_{b}"]["verdict"] for b in "XYZ" if f"D{D}_{b}" in res["corr"]]
        if vs:
            res["corr"][f"D{D}"] = "ENTANGLED" if "ENTANGLED" in vs else "NOT SEEN"
            print(f"{'J3' if D == a.D_tomo else '  '} D {D} connected pair correlation block/rest: " + "; ".join(row)
                  + f" -> {res['corr'][f'D{D}']}")
    # control: the healthy ring
    for D in sorted({a.D_tomo, a.D}):
        cb = bloch(data, a.control_n, D)
        if cb is not None:
            res.setdefault("control", {})[f"D{D}"] = dict(r=float(np.mean(cb["r"])),
                                                         transverse=float(np.mean(cb["transverse"])))
            print(f"   control n {a.control_n} D {D}: |v| {np.mean(cb['r']):.3f}, transverse {np.mean(cb['transverse']):.2f}")
    for D in sorted(D for (n, D, b) in data if n == a.control_n and b == "Z"):
        ph, v, se, c = data[(a.control_n, D, "Z")]
        res.setdefault("control_Z", {})[f"D{D}"] = dict(a=float(np.mean(v)), corr=float(np.mean(c)))
        print(f"   control n {a.control_n} D {D} Z: a {np.mean(v):+.3f}, connected ZZ {np.mean(c):.3f}")
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
