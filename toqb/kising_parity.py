"""Test 3's size probe (2026-10-30; owner's request "measure the size limit as L* measured the depth limit"): the global
parity P = X_1 X_2 ... X_n of the kicked-Ising ring (J = pi/4), conserved by every step for even n.

    python -m toqb.kising_parity build FETCH RUNS --arm fold:rule --n 20 --L 4 [--h 0.6] [--shots 1000]
    python -m toqb.kising_parity rehearse RUNS --vstar fold:rule=170,fold:zipcyc=47,qiskit:2:blind:template=45
    python -m toqb.kising_parity score JOB RUNS [--vstar-pred ARM=V,...] [--band 0.2] [--out-name parity_score.json]

Why P is conserved. Conjugation by the CZ ring maps X_j to Z_{j-1} X_j Z_{j+1}; over the ring every Z appears twice,
so the product of the X_j is unchanged; the single-qubit rotations of a step map the product to itself up to a sign
that the circuit's Euler form absorbs. Checked on the circuit itself by statevector: <P> is exact and the same at every
L (tests, n = 6, 7, 8). The probe uses even n only, so that |-..-> has P = +1 and the four inputs pair as below.

What it measures. P has weight n. Under uniform depolarizing noise p per qubit per step it decays as
(1 - 4p/3)^(n L): the decay depends on the product n L, the circuit's "volume". The readable volume V* is the n L at
which the parity ratio falls to 1/e. The weight-2 charge of noise wall stage 1 decays as (1 - 4p/3)^(2 L), so under the
same model V* = 2 L*: the device's charge decay length of 2026-10-29 predicts V* before any parity is measured. Where
the noise is not uniform the two can differ (the charge averages its sites, the parity multiplies them; dephasing
damps X but not ZZ); the declared band covers a +-20 % rate scatter only.

Circuit. The `toqb.kising` step in `task_loop.model_circuit` order, all L steps (as `toqb.kising_charge`). Inputs are
X-basis product states prepared by the first layer's RY(+-pi/2): |+..+>, |-..-> (P = +1 for even n), |-+..+> and
|+-..-> (P = -1). The readout rotation is H A (A the step's last rotations), so every qubit is measured in X and the
parity of the measured bits is P. One template per (n, L).

Readout reference (per record, on the physical qubits the compiled circuit measures): half-filled bit strings (Neel,
anti-Neel, and each with its first bit flipped: two parities of each sign) prepared with X gates and read at once.
All-0 and all-1 references would weigh an asymmetric readout (1 read as 0 more often) at its extremes, while the
circuit's outputs are spread over many bit strings.

Estimates. num = [P(++) + P(--) - P(-+) - P(+-)] / 4 from the circuits; den = the same signed mean of the references;
rho_P = num / den (1 noiselessly), SE by the delta method (per shot P = +-1, so var = (1 - <P>^2) / S). Additive
readout biases cancel in the signed means; the multiplicative readout loss cancels in the ratio to first order.
V* per (arm, n): a one-parameter fit rho_P = exp(-n L / V*) over the record's L (toqb.kising_charge.decay_length on
n L). Nothing here connects to IBM.
"""
from __future__ import annotations

import json
import os
import sys
import time

import numpy as np

from toqb import kising as K
from toqb import kising_charge as KC

INPUTS = ("plus", "minus", "minus_plus", "plus_minus")
SIGN = {"plus": 1, "minus": 1, "minus_plus": -1, "plus_minus": -1}
REFS = ("neel", "antineel", "neel_f", "antineel_f")


def input_signs(name, n):
    """+1 for |+>, -1 for |->, per qubit."""
    if name == "plus":
        return [1] * n
    if name == "minus":
        return [-1] * n
    if name == "minus_plus":
        return [-1] + [1] * (n - 1)
    if name == "plus_minus":
        return [1] + [-1] * (n - 1)
    raise ValueError(name)


def ref_bits(name, n):
    """Half-filled bit strings, so that a readout that favours 0 over 1 weighs both alike (the circuit's outputs are
    spread over many bit strings): Neel 0101.., anti-Neel 1010.., and each with its first bit flipped."""
    neel = [q % 2 for q in range(n)]
    if name == "neel":
        return neel
    if name == "antineel":
        return [1 - b for b in neel]
    if name == "neel_f":
        return [1 - neel[0]] + neel[1:]
    if name == "antineel_f":
        return [neel[0]] + [1 - b for b in neel[1:]]
    raise ValueError(name)


def ref_sign(name, n):
    return (-1) ** sum(ref_bits(name, n))


def _x_readout_angles(h):
    """(c, g): RZ(c) then RY(g) equals H A up to a final RZ (A = RZ(phi) RY(theta), the step's last rotations)."""
    from qiskit.synthesis import OneQubitEulerDecomposer
    theta, phi, _ = K.step_euler(h)

    def rz(t):
        return np.diag([np.exp(-1j * t / 2), np.exp(1j * t / 2)])

    def ry(t):
        return np.array([[np.cos(t / 2), -np.sin(t / 2)], [np.sin(t / 2), np.cos(t / 2)]])
    Hm = np.array([[1, 1], [1, -1]]) / np.sqrt(2)
    t, p, l = OneQubitEulerDecomposer("ZYZ").angles(Hm @ rz(phi) @ ry(theta))
    return float(l), float(t)


def angles(signs, n, L, h):
    """The model_circuit angle list (L >= 1): X-basis input, all L steps, every qubit read in X."""
    if L < 1:
        raise ValueError("L >= 1; L = 0 is the per-record readout reference")
    theta, phi, lam = K.step_euler(h)
    c, g = _x_readout_angles(h)
    a = []
    for k in range(L):
        last = k == L - 1
        if k == 0:
            a += [signs[q] * np.pi / 2 for q in range(n)]
            for q in range(n):
                a += [0.0, lam + (c if last else 0.0)]
        else:
            a += [theta] * n
            for q in range(n):
                a += [0.0, phi + lam + (c if last else 0.0)]
    a += [g] * n
    return a


def circuit(signs, n, L, h):
    from toqb import task_loop as TL
    return TL.model_circuit(angles(signs, n, L, h), n, L)


def parity_value(counts, n):
    """<prod_q (1 - 2 b_q)> over the first n clbits (key's rightmost character is clbit 0) and its shot variance."""
    S = sum(counts.values())
    m = 0.0
    for k, v in counts.items():
        bits = k.replace(" ", "")[::-1][:n]
        m += v * (-1) ** bits.count("1")
    m /= S
    return m, (1 - m * m) / S


def estimate(cell_counts, n):
    """cell_counts: {name: counts} for INPUTS and REFS. Returns rho_P, its SE, num, den."""
    vals = {k: parity_value(cell_counts[k], n) for k in INPUTS + REFS}
    num = sum(SIGN[i] * vals[i][0] for i in INPUTS) / 4
    vnum = sum(vals[i][1] for i in INPUTS) / 16
    den = sum(ref_sign(r, n) * vals[r][0] for r in REFS) / 4
    vden = sum(vals[r][1] for r in REFS) / 16
    rho, se = KC.ratio(num, vnum, den, vden)
    return dict(rho=rho, se=se, num=num, den=den, P={k: vals[k][0] for k in INPUTS + REFS})


def vstar_fit(cells):
    """V* per (arm, n): decay_length over n L. cells: dicts with arm, n, L, rho, se."""
    by = {}
    for c in cells:
        by.setdefault((c["arm"], c["n"]), []).append(c)
    out = []
    for (arm, n), g in sorted(by.items()):
        g = sorted(g, key=lambda c: c["L"])
        V, se = KC.decay_length([n * c["L"] for c in g], [c["rho"] for c in g], [c["se"] for c in g])
        out.append(dict(arm=arm, n=n, Ls=[c["L"] for c in g], V_star=V, se=se))
    return out


def judge(fits, pred, band=0.2):
    """Declared rule: V* inside [pred (1 - band), pred (1 + band)] widened by 2 SE -> INSIDE, else BELOW / ABOVE."""
    out = []
    for f in fits:
        p = pred.get(f["arm"])
        if p is None or f["V_star"] is None:
            continue
        lo, hi = p * (1 - band) - 2 * f["se"], p * (1 + band) + 2 * f["se"]
        out.append(dict(arm=f["arm"], n=f["n"], V_star=f["V_star"], se=f["se"], pred=p, lo=lo, hi=hi,
                        verdict="INSIDE" if lo <= f["V_star"] <= hi else ("BELOW" if f["V_star"] < lo else "ABOVE")))
    return out


def _parse_map(s):
    return {k: float(v) for k, v in (x.split("=") for x in s.split(","))} if s else {}


def cmd_build(argv):
    import argparse
    p = argparse.ArgumentParser(prog="kising_parity build")
    p.add_argument("fetch")
    p.add_argument("out")
    p.add_argument("--arm", required=True)
    p.add_argument("--n", type=int, required=True)
    p.add_argument("--L", type=int, required=True)
    p.add_argument("--h", type=float, default=0.6)
    p.add_argument("--shots", type=int, default=1000)
    a = p.parse_args(argv)
    if a.n % 2:
        print("STOP: n must be even (the four inputs pair parities +1 and -1 only for even n)", file=sys.stderr)
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
    name = f"kparity_n{a.n}_L{a.L}_h{a.h:g}-{a.arm.replace(':', '_')}"
    os.makedirs(a.out, exist_ok=True)
    jf, qf = os.path.join(a.out, name + ".json"), os.path.join(a.out, name + ".qpy")
    for f in (jf, qf):
        if os.path.exists(f):
            print(f"STOP: {f} exists: a run never overwrites another", file=sys.stderr)
            return 2
    t0 = time.perf_counter()
    task = dict(n=a.n, layers=a.L, enc=float(np.pi / 2))
    pr = dict(traj=0, seed=7, shots=a.shots, reps=200, level=0.99)
    plan = dict(name=f"test 3 parity: {name}", device="file:" + tfile, verify=False, task=task, predict=pr,
                standin=dict(t12=0.3, over=0.01, zz_hz=1e4, seed=20261017))
    R = S2.Runner(plan, a.arm)
    cs, points = [], []
    for i in INPUTS:
        cs.append(R.arm.compile(circuit(input_signs(i, a.n), a.n, a.L, a.h)))
        points.append(dict(input=i, sign=SIGN[i]))
    meas0 = None
    for r in REFS:
        rc, meas = KC.reference_circuit(cs[0], ref_bits(r, a.n))
        meas0 = meas
        cs.append(rc)
        points.append(dict(input=r, sign=ref_sign(r, a.n)))
    for c in cs[:len(INPUTS)]:
        mm = {c.find_bit(x.clbits[0]).index: c.find_bit(x.qubits[0]).index for x in c.data if x.operation.name == "measure"}
        if mm != meas0:
            print("STOP: the compiled circuits of one record measure on different qubits", file=sys.stderr)
            return 2
    d, q2 = R.arm.duration(cs[0], (a.n, a.L))
    labels = np.ones(len(cs), dtype=int)
    p1 = np.full(len(cs), 0.5)
    rec = dict(kind="s2rc", lam_test=True, parity_test=True, arm=a.arm, seed=0, plan=plan["name"], task=task,
               predict=pr, standin=plan["standin"], verify=False, device=plan["device"],
               target_sha256=fj["target_sha256"], version=R.arm.version(), final_mean=[], loops=0, started=S._cest(),
               parity=dict(h=a.h, J="pi/4", inputs=list(INPUTS), refs=list(REFS),
                           measured_qubits={str(k): v for k, v in sorted(meas0.items())}),
               points=points, inputs=[[0] * a.n for _ in points], noiseless_z=[float(p_["sign"]) for p_ in points],
               twin=None, q2=int(q2), us=round(d * 1e6, 3), active=int(active(cs[0])))
    rec["prediction"] = predict_job(p1, labels, a.shots, pr["reps"], pr["level"], pr["seed"] + 1)
    rec["prediction_shots_only"] = predict_job(p1, labels, a.shots, pr["reps"], pr["level"], pr["seed"] + 1)
    rec["prediction"]["twin_p1"] = [float(x) for x in p1]
    rec["test_labels"] = [int(v) for v in labels]  # placeholders: only so that assemble can read the record
    from qiskit import qpy
    with open(qf, "wb") as f:
        qpy.dump(list(cs), f)
    rec["export"] = dict(qpy=os.path.basename(qf), circuits=len(cs), sha256=KC.sha256_file(qf))
    rec.update(wall_s=time.perf_counter() - t0, structural_fail=R.arm.structural_fail,
               on_failed_ops=R.arm.on_failed_ops, ended=S._cest())
    rec["valid"] = not R.arm.structural_fail and not R.arm.on_failed_ops
    json.dump(rec, open(jf, "w", encoding="utf-8"))
    print(f"{name}: {len(cs)} circuits (4 + 4 references), {q2} two-qubit gates, {d * 1e6:.2f} us; valid {rec['valid']}")
    return 0 if rec["valid"] else 2


def cmd_rehearse(argv):
    """Before any device: per record, rho_P = exp(-n L / V*) at the declared V* per arm, and its shot-noise SE
    (readout loss not included)."""
    import argparse
    import glob
    p = argparse.ArgumentParser(prog="kising_parity rehearse")
    p.add_argument("runs")
    p.add_argument("--vstar", required=True, help="ARM=V,...")
    a = p.parse_args(argv)
    V = _parse_map(a.vstar)
    for f in sorted(glob.glob(os.path.join(a.runs, "kparity_*.json"))):
        r = json.load(open(f))
        n, L, S = r["task"]["n"], r["task"]["layers"], r["predict"]["shots"]
        v = V.get(r["arm"])
        rho = float(np.exp(-n * L / v)) if v else float("nan")
        se = float(np.sqrt(2 * (1 - rho * rho) / S) / 2) if v else float("nan")
        print(f"{os.path.basename(f)[:-5]:44s} predicted rho_P {rho:.4f}, SE about {se:.4f} ({S} shots); "
              f"{r['q2']} two-qubit gates, {r['us']} us")
    return 0


def cmd_score(argv):
    import argparse
    p = argparse.ArgumentParser(prog="kising_parity score")
    p.add_argument("job")
    p.add_argument("runs")
    p.add_argument("--vstar-pred", default="", help="declared V* per arm, ARM=V,...")
    p.add_argument("--band", type=float, default=0.2)
    p.add_argument("--judged-n", default="20,36", help="the n judged by the declared rule; others reported")
    p.add_argument("--kappa", type=float, nargs=2, default=[3.3, 3.9], help="zipcyc's declared kappa range (P-B)")
    p.add_argument("--out-name", default="parity_score.json")
    a = p.parse_args(argv)
    man = json.load(open(os.path.join(a.job, "manifest.json")))
    raw = json.load(open(os.path.join(a.job, "raw_counts.json")))
    rows = {r["pub"]: r["counts"] for r in raw["rows"]}
    cells = []
    for cid, c in enumerate(man["cells"]):
        rf = os.path.join(a.runs, c["name"] + ".json")
        if KC.sha256_file(rf) != c["run_sha256"]:
            raise SystemExit(f"STOP: {rf} differs from the manifest")
        rec = json.load(open(rf))
        if not rec.get("parity_test"):
            continue
        n, L = rec["task"]["n"], rec["task"]["layers"]
        cc = {}
        for k, pub in enumerate(man["pubs"]):
            if pub["cell"] == cid:
                cc[rec["points"][pub["point"]]["input"]] = rows[k]
        est = estimate(cc, n)
        cells.append(dict(name=c["name"], arm=rec["arm"], n=n, L=L, q2=rec.get("q2"), us=rec.get("us"), **est))
    fits = vstar_fit(cells)
    judged_n = {int(x) for x in a.judged_n.split(",") if x}
    verdicts = [v for v in judge(fits, _parse_map(a.vstar_pred), a.band) if v["n"] in judged_n]
    # P-B: zipcyc's kappa = V*_rule / V*_zipcyc inside [k_lo, k_hi] widened by 2 SE (judged n only)
    fd = {(f["arm"], f["n"]): f for f in fits}
    kap = []
    for n in sorted(judged_n):
        r, z = fd.get(("fold:rule", n)), fd.get(("fold:zipcyc", n))
        if not r or not z or r["V_star"] is None or z["V_star"] is None:
            continue
        k = r["V_star"] / z["V_star"]
        sk = k * float(np.hypot(r["se"] / r["V_star"], z["se"] / z["V_star"]))
        kap.append(dict(n=n, kappa=k, se=sk, verdict="INSIDE" if a.kappa[0] - 2 * sk <= k <= a.kappa[1] + 2 * sk
                        else ("BELOW" if k < a.kappa[0] else "ABOVE")))
    duel = []
    keyn = {}
    for c in cells:
        keyn.setdefault((c["n"], c["L"]), {})[c["arm"]] = c
    for (n, L), g in sorted(keyn.items()):
        if "fold:rule" not in g:
            continue
        r = g["fold:rule"]
        for other in sorted(x for x in g if x != "fold:rule"):
            o = g[other]
            d = r["rho"] - o["rho"]
            se = float(np.hypot(r["se"], o["se"]))
            duel.append(dict(n=n, L=L, other=other, diff=d, se=se,
                             verdict="WIN" if d > 2 * se else ("LOSS" if d < -2 * se else "TIE")))
    for c in sorted(cells, key=lambda c: (c["n"], c["arm"], c["L"])):
        print(f"{c['name']:44s} rho_P {c['rho']:.4f} +- {c['se']:.4f} (num {c['num']:.4f}, ref {c['den']:.4f}) | "
              f"{c['q2']} two-qubit gates, {c['us']} us")
    for f in fits:
        v = "n/a" if f["V_star"] is None else f"{f['V_star']:.1f} +- {f['se']:.1f}"
        print(f"V* {f['arm']} n {f['n']}: {v} (fit over n L, L = {f['Ls']})")
    for v in verdicts:
        print(f"V* {v['arm']} n {v['n']}: {v['V_star']:.1f} +- {v['se']:.1f}, declared {v['pred']:.1f} "
              f"(band [{v['lo']:.1f}, {v['hi']:.1f}]): {v['verdict']}")
    for x in kap:
        print(f"P-B n {x['n']}: kappa zipcyc {x['kappa']:.2f} +- {x['se']:.2f}: {x['verdict']}")
    for x in duel:
        print(f"n {x['n']} L {x['L']}: fold:rule - {x['other']}: {x['diff']:+.4f} +- {x['se']:.4f}: {x['verdict']}")
    out = os.path.join(a.job, a.out_name)
    if os.path.exists(out):
        print(f"{out} exists; not written")
    else:
        json.dump(dict(cells=cells, fits=fits, verdicts=verdicts, kappa=kap, duels=duel), open(out, "w"),
                  default=lambda o: o.tolist() if hasattr(o, "tolist") else str(o))
    return 0


def main(argv):
    cmds = dict(build=cmd_build, rehearse=cmd_rehearse, score=cmd_score)
    if not argv or argv[0] not in cmds:
        print(__doc__)
        return 2
    return cmds[argv[0]](argv[1:])


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
