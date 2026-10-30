"""Test 2 (2026-10-30; home's instruction 指示書_非可積分ミラー): does the rule's lead survive when the kicked-Ising ring is
made non-integrable? A mirror (echo) circuit with a longitudinal field hz, read like noise wall probe P1.

    python -m toqb.kising_echo build FETCH RUNS --arm fold:rule --n 20 --L 12 --hz 0.1 [--h 0.6] [--shots 500]
    python -m toqb.kising_echo rehearse RUNS [--lstar fold:rule=56.5 fold:zipcyc=15.4 qiskit:2:blind:template=26.4]
    python -m toqb.kising_echo standin RUNS OUT.json [--T 64] [--n 20]      (the twin: TOQB's stand-in, T1 / T2 / ZZ)
    python -m toqb.kising_echo score JOB RUNS [--out-name echo_score.json]

The step. S = (RX(2h) Z RZ(2 hz))^{(x)n} CZ_ring (operator order: the CZ ring first). hz = 0 is toqb.kising's free-
fermion step; hz != 0 breaks integrability. RZ(2 hz) commutes with the CZ ring and only shifts the Euler angle lam of
RX(2h) Z = e^{ia} RZ(phi) RY(theta) RZ(lam) to lam' = lam + 2 hz, so the two-qubit structure does not depend on hz
and a placement comparison sees only the change of integrability. With A = RZ(phi) RY(theta), B = RZ(lam') CZ_ring:
S = A B.

The mirror. L steps forward, then a flip W = X^{(x)n}, then L steps of S'^{-1} with S' = W S W:
    U = S'^{-L} W S^L = W S^{-L} W W S^L = W,
so the noiseless output is the input with every bit flipped, at any n and hz (no state vector needed at n = 36).
W S W is S with every angle negated (X RY(t) X = RY(-t), X RZ(t) X = RZ(-t), and W CZ_ring W = (-1)^n CZ_ring), so
S'^{-1} = CZ_ring RZ(lam') . RY(theta) RZ(phi) (time order: RZ(phi), RY(theta), RZ(lam'), the CZ ring).

Why the flip (a change from the instruction's barrier, to be confirmed by home / the owner): TOQB's ring parser
(`fold.read_ring`) drops barriers, and in the model_circuit form the single-qubit gates between two CZ rings are
merged. Without W the block at the turn is A^{-1} RZ(-lam') A ... = a diagonal, and CZ RZ CZ cancels to RZ, so a
compiler may collapse the whole echo. With W the merged block at the turn is RZ(lam') A'^{-1} W A, which contains X:
it does not commute with CZ and nothing cancels. Acceptance (from the instruction, unchanged): the compiled circuit
must have exactly 2L x (the arm's two-qubit gates for one ring layer); a record that fails is invalid.

Circuit form: `task_loop.model_circuit` with 2L layers. The single-qubit block V_k between CZ ring k and k + 1 (V_0
before the first, V_2L after the last) is written V_k = RZ(a_k) RY(b_k) RZ(c_k): c_k moves back across CZ ring k into
layer k's RZ slot, b_k is layer k + 1's first RY, a_k its RZ (c_0 acts on a basis state and a_2L before a Z
measurement, both dropped). Layer 1's first RY is the input RY(pi bit).

Reading (as P1). Inputs |0..0>, |1..1>, Neel, anti-Neel (z_j = 1 - 2 bit_j); every qubit read in Z. Per input
    m = sum_j (-z_j) <Z_j>   (weight 1; the expected output is the flipped input),   m2 = sum_j z_j z_j+1 <Z_j Z_j+1>,
both n without noise. Relaxation toward |0> and readout asymmetry add a first-order term proportional to sum_j z_j,
which cancels in the sum over the four inputs. Each record carries its own readout reference (X on the measured
physical qubits, as toqb.kising_charge.reference_circuit), so
    rho_E(D) = [sum_inputs m]_D / [sum_inputs m]_ref,   D = 2L the echo's full depth.
L* is toqb.kising_charge.decay_length over D (the same "steps" as the noise wall).
"""
from __future__ import annotations

import json
import os
import sys
import time

import numpy as np

from toqb import kising as K
from toqb import kising_charge as KC

INPUTS = KC.INPUTS


# ------------------------------------------------------------------------------------------------ the circuit

def _rz(t):
    return np.diag([np.exp(-0.5j * t), np.exp(0.5j * t)])


def _ry(t):
    return np.array([[np.cos(t / 2), -np.sin(t / 2)], [np.sin(t / 2), np.cos(t / 2)]], dtype=complex)


_X = np.array([[0, 1], [1, 0]], dtype=complex)


def step_angles(h, hz):
    theta, phi, lam = K.step_euler(h)
    return theta, phi, lam + 2 * hz


def blocks(L, h, hz):
    """The 2L + 1 single-qubit blocks V_0 .. V_2L (2x2, the same on every qubit) around the 2L CZ rings."""
    theta, phi, lamp = step_angles(h, hz)
    A = _rz(phi) @ _ry(theta)
    Api = _ry(theta) @ _rz(phi)  # A'^{-1}, A' = W A W = RZ(-phi) RY(-theta)
    R = _rz(lamp)
    return [R] + [R @ A] * (L - 1) + [R @ Api @ _X @ A] + [R @ Api] * (L - 1) + [np.eye(2, dtype=complex)]


def _zyz(V):
    from qiskit.synthesis import OneQubitEulerDecomposer
    t, p, l = OneQubitEulerDecomposer("ZYZ").angles(V)  # V = e^{ia} RZ(p) RY(t) RZ(l)
    return float(p), float(t), float(l)  # (a, b, c)


def angles(bits, n, L, h, hz):
    """The model_circuit angle list (2L layers) of the echo on input `bits`."""
    if L < 1:
        raise ValueError("L >= 1")
    V = [_zyz(B) for B in blocks(L, h, hz)]
    D = 2 * L
    rz_slot = [0.0] * (D + 1)  # 1-based layers
    for k in range(1, D + 1):
        rz_slot[k] += V[k - 1][0] + V[k][2]  # a_{k-1} + c_k
    a = []
    for k in range(1, D + 1):
        b_prev = V[k - 1][1]
        if k == 1:
            a += [np.pi * bits[q] for q in range(n)]
            for _ in range(n):
                a += [b_prev, rz_slot[1]]
        else:
            a += [b_prev] * n
            for _ in range(n):
                a += [0.0, rz_slot[k]]
    a += [V[D][1]] * n
    return a


def circuit(bits, n, L, h, hz):
    from toqb import task_loop as TL
    return TL.model_circuit(angles(bits, n, L, h, hz), n, 2 * L)


def q2_count(c):
    return sum(1 for i in c.data if len(i.qubits) == 2 and i.operation.name not in ("barrier", "measure"))


def per_layer_q2(arm, n, seed=0):
    """The arm's two-qubit gates for one ring layer: a one-layer model circuit with generic angles, compiled."""
    from toqb import task_loop as TL
    rng = np.random.default_rng(seed)
    ang = list(rng.uniform(-1, 1, len(TL.angle_list(np.zeros(TL.n_params(n, 1)), np.zeros(n), n, 1, 1.0))))
    return q2_count(arm.compile(TL.model_circuit(ang, n, 1)))


# ------------------------------------------------------------------------------------------------ estimation

def _z(bits_key, n):
    k = bits_key.replace(" ", "")
    return np.array([1 - 2 * int(k[-1 - q]) for q in range(n)])


def input_values(counts, zin, flipped, n):
    """(m, var m, m2, var m2) of one circuit's counts: m = sum_j s_j Z_j with s = -z (echo) or z (reference),
    m2 = sum_j z_j z_j+1 Z_j Z_j+1."""
    s = -zin if flipped else zin
    w2 = zin * np.roll(zin, -1)
    vals, vals2, cnt = [], [], []
    for key, c in counts.items():
        z = _z(key, n)
        vals.append(float(np.sum(s * z)))
        vals2.append(float(np.sum(w2 * z * np.roll(z, -1))))
        cnt.append(c)
    vals, vals2, cnt = np.array(vals), np.array(vals2), np.array(cnt, float)
    N = cnt.sum()

    def mv(v):
        m = float(np.sum(v * cnt) / N)
        return m, (float(np.sum(cnt * (v - m) ** 2) / (N - 1)) / N if N > 1 else float("nan"))
    m, vm = mv(vals)
    m2, vm2 = mv(vals2)
    return m, vm, m2, vm2


def estimate(cell_counts, n):
    """cell_counts: {(input, "echo" | "ref"): counts}. rho_E (weight 1) and rho_E2 (weight 2) with SE."""
    num = vnum = den = vden = num2 = vnum2 = den2 = vden2 = 0.0
    per = {}
    for i in INPUTS:
        zin = 1 - 2 * np.array(KC.input_bits(i, n))
        m, vm, m2, vm2 = input_values(cell_counts[(i, "echo")], zin, True, n)
        r, vr, r2, vr2 = input_values(cell_counts[(i, "ref")], zin, False, n)
        num, vnum, den, vden = num + m, vnum + vm, den + r, vden + vr
        num2, vnum2, den2, vden2 = num2 + m2, vnum2 + vm2, den2 + r2, vden2 + vr2
        per[i] = dict(m=m, ref=r)
    rho, se = KC.ratio(num, vnum, den, vden)
    rho2, se2 = KC.ratio(num2, vnum2, den2, vden2)
    return dict(rho4=rho, se4=se, rho_w2=rho2, se_w2=se2, per_input=per)


# ------------------------------------------------------------------------------------------------ build

def cmd_build(argv):
    import argparse
    p = argparse.ArgumentParser(prog="kising_echo build")
    p.add_argument("fetch")
    p.add_argument("out")
    p.add_argument("--arm", required=True)
    p.add_argument("--n", type=int, required=True)
    p.add_argument("--L", type=int, required=True, help="steps one way; the echo's full depth is 2L")
    p.add_argument("--hz", type=float, required=True)
    p.add_argument("--h", type=float, default=0.6)
    p.add_argument("--shots", type=int, default=500)
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
    D = 2 * a.L
    name = f"kecho_n{a.n}_D{D}_hz{a.hz:g}_h{a.h:g}-{a.arm.replace(':', '_')}"
    os.makedirs(a.out, exist_ok=True)
    jf, qf = os.path.join(a.out, name + ".json"), os.path.join(a.out, name + ".qpy")
    for f in (jf, qf):
        if os.path.exists(f):
            print(f"STOP: {f} exists: a run never overwrites another", file=sys.stderr)
            return 2
    t0 = time.perf_counter()
    task = dict(n=a.n, layers=D, enc=float(np.pi / 2))
    pr = dict(traj=0, seed=7, shots=a.shots, reps=200, level=0.99)
    plan = dict(name=f"echo hz: {name}", device="file:" + tfile, verify=False, task=task, predict=pr,
                standin=dict(t12=0.3, over=0.01, zz_hz=1e4, seed=20261017))
    R = S2.Runner(plan, a.arm)
    cs, points = [], []
    for i in INPUTS:
        cs.append(R.arm.compile(circuit(KC.input_bits(i, a.n), a.n, a.L, a.h, a.hz)))
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
    rec = dict(kind="s2rc", lam_test=True, echo_test=True, arm=a.arm, seed=0, plan=plan["name"], task=task,
               predict=pr, standin=plan["standin"], verify=False, device=plan["device"],
               target_sha256=fj["target_sha256"], version=R.arm.version(), final_mean=[], loops=0, started=S._cest(),
               echo=dict(h=a.h, hz=a.hz, L_half=a.L, D=D, inputs=list(INPUTS), turn="flip W = X^n",
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
    print(f"{name}: {len(cs)} circuits (4 echo + 4 references), {q2} two-qubit gates = {D} x {per}: "
          f"{'ACCEPTED' if accepted else 'REJECTED (two-qubit count ' + str(q2s) + ')'}, {d * 1e6:.2f} us; valid {rec['valid']}")
    return 0 if rec["valid"] else 2


# ------------------------------------------------------------------------------------------------ score

def judge(cells, ref="fold:rule"):
    """Rule A (draft): per (hz, n, D) and other arm X, the rule against X at 2 SE (WIN / LOSS / TIE), judged when
    either arm's rho exceeds 2 SE (else NOT JUDGED: both at the noise floor). Rule B (draft): per (hz, n), kappa of
    fold:zipcyc (L*_rule / L*_zipcyc) inside [3.3, 3.9]."""
    duels = []
    key = {}
    for c in cells:
        key.setdefault((c["hz"], c["n"], c["L"]), {})[c["arm"]] = c
    for (hz, n, D), g in sorted(key.items()):
        if ref not in g:
            continue
        r = g[ref]
        for arm, c in sorted(g.items()):
            if arm == ref:
                continue
            se = float(np.hypot(r["se4"], c["se4"]))
            d = r["rho4"] - c["rho4"]
            judged = r["rho4"] > 2 * r["se4"] or c["rho4"] > 2 * c["se4"]
            v = ("NOT JUDGED" if not judged else ("WIN" if d > 2 * se else ("LOSS" if d < -2 * se else "TIE")))
            duels.append(dict(hz=hz, n=n, D=D, arm=arm, diff=d, se=se, verdict=v))
    walls = {}
    rule_b = []
    for hz in sorted({c["hz"] for c in cells}):
        w = KC.wall([c for c in cells if c["hz"] == hz], ref=ref)
        walls[str(hz)] = w
        for x in w["relative"]:
            if x["arm"] == "fold:zipcyc" and x.get("kappa") is not None:
                lo, hi = 3.3, 3.9
                rule_b.append(dict(hz=hz, n=x["n"], kappa=x["kappa"], se=x["se_kappa"],
                                   verdict="INSIDE" if lo <= x["kappa"] <= hi else ("BELOW" if x["kappa"] < lo else "ABOVE")))
    return dict(duels=duels, walls=walls, rule_B=rule_b)


def cmd_score(argv):
    import argparse
    p = argparse.ArgumentParser(prog="kising_echo score")
    p.add_argument("job")
    p.add_argument("runs")
    p.add_argument("--out-name", default="echo_score.json")
    a = p.parse_args(argv)
    out = os.path.join(a.job, a.out_name)
    if os.path.exists(out):
        raise SystemExit(f"STOP: {out} exists")
    man = json.load(open(os.path.join(a.job, "manifest.json")))
    raw = json.load(open(os.path.join(a.job, "raw_counts.json")))
    rows = {r["pub"]: r["counts"] for r in raw["rows"]}
    cells, invalid = [], []
    for cid, c in enumerate(man["cells"]):
        rf = os.path.join(a.runs, c["name"] + ".json")
        if KC.sha256_file(rf) != c["run_sha256"]:
            raise SystemExit(f"STOP: {rf} differs from the manifest")
        rec = json.load(open(rf))
        if not rec.get("echo_test"):
            continue
        if not rec.get("valid"):
            invalid.append(c["name"])
            continue
        n = rec["task"]["n"]
        cc = {}
        for k, pub in enumerate(man["pubs"]):
            if pub["cell"] == cid:
                pt = rec["points"][pub["point"]]
                cc[(pt["input"], pt["setting"])] = rows[k]
        est = estimate(cc, n)
        cells.append(dict(name=c["name"], arm=rec["arm"], n=n, L=rec["echo"]["D"], hz=rec["echo"]["hz"],
                          q2=rec.get("q2"), us=rec.get("us"), **est))
    res = dict(cells=cells, invalid=invalid, **judge(cells))
    json.dump(res, open(out, "w"), indent=1, default=str)
    for c in cells:
        print(f"{c['name']}: rho_E {c['rho4']:.4f} +- {c['se4']:.4f}; weight 2 {c['rho_w2']:.4f} +- {c['se_w2']:.4f}")
    for d in res["duels"]:
        print(f"hz {d['hz']:g} n {d['n']} D {d['D']}: rule vs {d['arm']}: {d['diff']:+.4f} +- {d['se']:.4f} {d['verdict']}")
    for b in res["rule_B"]:
        print(f"rule B hz {b['hz']:g} n {b['n']}: kappa zipcyc {b['kappa']:.2f} +- {b['se']:.2f} {b['verdict']}")
    if invalid:
        print("invalid records (acceptance failed): " + ", ".join(invalid))
    return 0


# ------------------------------------------------------------------------------------------------ rehearse / twin

def se_model(rho, n, shots):
    """Shot-noise SE of rho_E with four inputs of `shots` shots, the n Z_j taken independent: var(m) ~ n (1 - rho^2)
    / shots per input, the reference near 1 (variance neglected)."""
    return float(np.sqrt(4 * n * max(1 - rho * rho, 0.0) / shots) / (4 * n))


def cmd_rehearse(argv):
    """Before any device: per record, rho_E = exp(-D / L*) at an assumed L* per arm, its shot-noise SE and whether the
    cell is above 2 SE (judgeable). The default L* are the 2026-10-29 marrakesh n = 20 values (records)."""
    import argparse
    import glob
    p = argparse.ArgumentParser(prog="kising_echo rehearse")
    p.add_argument("runs")
    p.add_argument("--lstar", nargs="*", default=["fold:rule=56.5", "fold:zipcyc=15.1", "qiskit:2:blind:template=26.4"])
    a = p.parse_args(argv)
    ls = {kv.split("=")[0]: float(kv.split("=")[1]) for kv in a.lstar}
    for f in sorted(glob.glob(os.path.join(a.runs, "kecho_*.json"))):
        r = json.load(open(f))
        n, D, S = r["task"]["n"], r["echo"]["D"], r["predict"]["shots"]
        Ls = ls.get(r["arm"])
        rho = float(np.exp(-D / Ls)) if Ls else float("nan")
        se = se_model(rho, n, S) if Ls else float("nan")
        print(f"{os.path.basename(f)[:-5]}: q2 {r['q2']} ({'accepted' if r['echo']['accepted'] else 'REJECTED'}), "
              f"assumed L* {Ls}: rho_E {rho:.4f}, SE {se:.4f}, {'above' if rho > 2 * se else 'below'} 2 SE")
    return 0


def z_all(eng, pl, A, T, seed):
    """Per circuit, the trajectory mean of <Z> on every measured clbit (readout included): (len(A), clbits)."""
    meas = sorted(pl.meas, key=lambda m: m[1])
    P = A.shape[0]
    cp, ct = eng._chunks(P, T, pl.n)
    acc = np.zeros((P, len(meas)))
    k = 0
    for i in range(0, P, cp):
        for j in range(0, T, ct):
            t = min(ct, T - j)
            psi, _ = eng.run(pl, A[i:i + cp], t, seed * 1009 + k)
            k += 1
            for col, (q, cl, p01, p10) in enumerate(meas):
                p1 = eng._p1(psi, pl.n, q)
                p1 = np.asarray(p1.get() if hasattr(p1, "get") else p1, dtype=float).reshape(-1, t)
                z = 1 - 2 * p1
                acc[i:i + cp, col] += ((1 - p01 - p10) * z + (p10 - p01)).sum(axis=1)
            del psi
    return acc / T


def cmd_standin(argv):
    """The twin rehearsal (pod; home's instruction: rule and zipcyc at n = 20): every record's 8 circuits on TOQB's
    stand-in (toqb.s2r.StandIn: T1, T2 and static ZZ, by trajectories), rho_E from the trajectory means (no shots)."""
    import argparse
    import glob
    from qiskit import qpy
    from toqb import s2r as S
    from toqb import traj2 as T2
    p = argparse.ArgumentParser(prog="kising_echo standin")
    p.add_argument("runs")
    p.add_argument("out")
    p.add_argument("--T", type=int, default=64)
    p.add_argument("--n", type=int, default=20)
    p.add_argument("--seed", type=int, default=20261030)
    a = p.parse_args(argv)
    if os.path.exists(a.out):
        raise SystemExit(f"STOP: {a.out} exists")
    st = None
    eng = T2.Engine()
    res = []
    for f in sorted(glob.glob(os.path.join(a.runs, "kecho_*.json"))):
        r = json.load(open(f))
        if r["task"]["n"] != a.n or not r.get("valid"):
            continue
        if st is None:
            st = S.StandIn(**r["standin"])
        cs = qpy.load(open(os.path.join(a.runs, r["export"]["qpy"]), "rb"))
        t0 = time.perf_counter()
        zs = []
        for c in cs:
            rr, _nm = st.prepared(c)
            pl = T2.plan(c, rr, st.target, over=st.params["over"])
            zs.append(z_all(eng, pl, pl.angles(c)[None, :], a.T, a.seed)[0])
        n = r["task"]["n"]
        num = den = 0.0
        for k, pt in enumerate(r["points"][:4]):
            zin = 1 - 2 * np.array(KC.input_bits(pt["input"], n))
            num += float(np.sum(-zin * zs[k]))
            den += float(np.sum(zin * zs[4 + k]))
        rho = num / den
        res.append(dict(name=os.path.basename(f)[:-5], arm=r["arm"], n=n, D=r["echo"]["D"], hz=r["echo"]["hz"],
                        rho_E=rho, T=a.T, q2=r["q2"], us=r["us"], wall_s=time.perf_counter() - t0))
        print(f"{res[-1]['name']}: twin rho_E {rho:.4f} (T {a.T}), {res[-1]['wall_s']:.0f} s", flush=True)
    by = {}
    for x in res:
        by.setdefault((x["arm"], x["hz"]), []).append(x)
    lst = {}
    for (arm, hz), g in sorted(by.items()):
        g = sorted(g, key=lambda v: v["D"])
        Ds = [v["D"] for v in g]
        rh = [v["rho_E"] for v in g]
        se = [max(0.02, 1 / np.sqrt(a.T)) for _ in g]  # trajectory spread is not tracked; a fixed nominal SE
        Lst, _ = KC.decay_length(Ds, rh, se)
        lst[f"{arm} hz={hz:g}"] = Lst
        print(f"{arm} hz {hz:g}: L* (twin) {Lst}")
    json.dump(dict(records=res, L_star=lst), open(a.out, "w"), indent=1, default=str)
    return 0


def main(argv):
    cmds = dict(build=cmd_build, score=cmd_score, rehearse=cmd_rehearse, standin=cmd_standin)
    if not argv or argv[0] not in cmds:
        print(__doc__)
        return 2
    return cmds[argv[0]](argv[1:])


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
