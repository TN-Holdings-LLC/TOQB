"""Regression of psf-os's entrance (psf_os.entrance, 2026-11-13): the declared jobs of 11-11 and 11-12 built through
the entrance from their logical circuits alone, on the very device records they were built from, compared with the
recorded job by psf-os's gate hash (psf_os.gatehash; the QPY bytes change with the Qiskit version) and the answers
written by label compared with the recorded answers file (workplace, 2026-11-13; desk only, no device).
The entrance is called with the declared builders' settings (shots, max_seconds; mirror "compiled" is the entrance's
default and what the builders patched in; no sentinel fallback, no twin, no special).
3D (added 2026-11-13g): the declared kicked-Ising 3D jobs (os3d-physA-2026-11-07 j1 / j2 on ibm_fez, os3d-kingston-top-
2026-11-07 mid / big on ibm_kingston): every 3D arm (user, floor, mirror) rebuilt through the entrance from
grid3d.logical(4, M, N, t, theta) at the arm's recorded translation (at3d) and fold version, and every 2D arm (hex
patch on labels, user2d's own mirror) through the entrance, compared record by record by gate hash with the recorded
runs. The probes and the sentinel of those jobs are made by the builder (gpu/os3d_v31_build.py), not by the entrance.
usage: PYTHONPATH=<psf-os>:<lab-notebook> python regress_entrance.py WORK_DIR [job ...]   (jobs: hubbard xx91 ohm
       ohm-kingston hubbard-big 3d; default all but 3d)"""
import gzip
import json
import os
import shutil
import sys
import time

NB = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.join(NB, "gpu"))
RES = os.path.join(NB, "results")


def hubbard(Ls, steps, ans_file):
    import hub_build as HB
    vals = json.load(open(ans_file))
    items, ans = [], {}
    for L in Ls:
        for s in steps:
            for arm in ("U4", "U0"):
                t = f"L{L}_s{s}_{arm}"
                items.append((t, HB.logical(L, s, arm)))
                ans[t] = vals[t]
    return items, ans


def xx91():
    import ff_xx as F
    import ffxx91 as X
    items, ans = [], {}
    for th in (0.7853981633974483, 1.5707963267948966):
        for s in (2, 4, 8, 12, 16, 20):
            t = X.tag(91, th, s)
            items.append((t, F.circuit(91, s, th, measure=False)))
            ans[t] = [float(z) for z in F.z_exact(91, s, th)]
    return items, ans


def ohm():
    import ohm_answers as OA
    A = json.load(open(os.path.join(RES, "ohm-2026-11-12", "answers", "ohm_answers.json")))
    meta, vals = A["meta"], A["z"]
    strs = OA.strings(meta["N"], meta["K"], meta["m"], meta["seed"])
    items, ans = [], {}
    for arm in OA.ARMS:
        for t in meta["cycles"]:
            for name, bits in strs:
                tg = OA.tag(arm, t, name)
                items.append((tg, OA.circuit(meta["N"], t, arm, bits)))
                ans[tg] = vals[tg]
    return items, ans


JOBS = {
    "hubbard": ("hubbard-2026-11-11", "ibm_fez", lambda: hubbard((20, 30), (2, 4, 6),
                RES + "/hubbard-2026-11-11/answers/hub_answers_home.json"), 4000, 60, "hub_ibm_fez_ans.json"),
    "xx91": ("xx91-2026-11-12", "ibm_fez", xx91, 4000, 160, "xx91_ibm_fez_ans.json"),
    "ohm": ("ohm-2026-11-12", "ibm_fez", ohm, 1000, 160, "ohm_ibm_fez_ans.json"),
    "ohm-kingston": ("ohm-kingston-2026-11-12", "ibm_kingston", ohm, 1000, 160, "ohm_ibm_kingston_ans.json"),
    "hubbard-big": ("hubbard-big-2026-11-11", "ibm_fez", lambda: hubbard((45, 60), (2, 4),
                    RES + "/hubbard-big-2026-11-11/answers/hub_answers_big.json"), 4000, 60, "hubB_ibm_fez_ans.json"),
}


def recorded_qpy(res, devname, work):
    qf = os.path.join(RES, res, devname, "job", "circuits.qpy")
    if not os.path.exists(qf) and os.path.exists(qf + ".gz"):
        q2 = os.path.join(work, f"{res}_{devname}_recorded.qpy")
        with gzip.open(qf + ".gz") as fi, open(q2, "wb") as fo:
            shutil.copyfileobj(fi, fo)
        qf = q2
    return qf


JOBS3D = [("os3d-physA-2026-11-07", "j1_4x4x3"), ("os3d-physA-2026-11-07", "j2_4x2x2"),
          ("os3d-kingston-top-2026-11-07", "mid_4x4x3"), ("os3d-kingston-top-2026-11-07", "big_4x6x3")]


def main3d(work):
    import glob
    import os3d_v31_build as HX
    from psf_os import device as Dv
    from psf_os import entrance as E
    from psf_os import gatehash
    from psf_os import grid3d as G
    rows = []
    for res, job in JOBS3D:
        t0 = time.time()
        dev = Dv.Device.load(os.path.join(RES, res, "dev"))
        runs = os.path.join(RES, res, job, "runs")
        recs = sorted(glob.glob(os.path.join(runs, "p2d_*.json")))
        same = differ = 0
        bad = []
        for f in recs:
            r = json.load(open(f))
            tag = r.get("tag")
            if f.endswith(("_floor.json", "_mirror.json")):
                continue
            out = os.path.join(work, f"e3d_{res}_{job}_{tag}")
            if "grid3d" in r:
                g = r["grid3d"]
                qc = G.logical(4, g["M"], g["N"], g["t"], g["theta"])
                E.build(dev, [(tag, qc)], out, shots=r.get("shots", 4000), max_seconds=10 ** 6,
                        fold=g.get("fold_version", "v3.1"), at3d=[(g["r0"], g["c0"])])
            else:  # the 2D hex arm: written on labels, user2d's own mirror
                t, th = r.get("t"), None
                import re
                m = re.match(r"hex_(?:th(\d\d)_)?t(\d+)$", tag)
                th = int(m.group(1)) / 10 if m.group(1) else 0.8
                qc = HX.hex_circuit(int(m.group(2)), th)
                E.build(dev, [(tag, qc)], out, shots=r.get("shots", 4000), max_seconds=10 ** 6, mirror="logical")
            for suf in ("", "_floor", "_mirror"):
                a = gatehash.qpy_hash(os.path.join(runs, f"p2d_{tag}{suf}.qpy"))["gate_sha256"]
                b = gatehash.qpy_hash(os.path.join(out, "runs", f"p2d_{tag}{suf}.qpy"))["gate_sha256"]
                if a == b:
                    same += 1
                else:
                    differ += 1
                    bad.append(tag + suf)
        rows.append(dict(job="3d", result=res, part=job, device=dev.name, records_same=same, records_differ=differ,
                         differ=bad[:10], wall_s=round(time.time() - t0, 1)))
        print(json.dumps(rows[-1]), flush=True)
    return rows


def main(work, names):
    from psf_os import device as Dv
    from psf_os import entrance as E
    from psf_os import gatehash
    os.makedirs(work, exist_ok=True)
    rows = []
    if "3d" in names:
        rows += main3d(work)
        names = [n for n in names if n != "3d"]
    for name in names:
        res, devname, make, shots, maxs, ans_name = JOBS[name]
        t0 = time.time()
        dev = Dv.Device.load(os.path.join(RES, res, "fetch_in", devname, "dev"))
        items, ans = make()
        out, ans_out = os.path.join(work, f"entrance_{name}"), os.path.join(work, f"entrance_{name}_ans.json")
        b = E.build(dev, items, out, answers=ans, answers_out=ans_out, shots=shots, max_seconds=maxs)
        got = gatehash.qpy_hash(os.path.join(out, "job", "circuits.qpy"))["gate_sha256"]
        want = gatehash.qpy_hash(recorded_qpy(res, devname, work))["gate_sha256"]
        rec_ans = json.load(open(os.path.join(RES, res, "answers", ans_name)))
        rec_ans = rec_ans.get("z", rec_ans)
        new_ans = json.load(open(ans_out))
        rec_build = json.load(open(os.path.join(RES, res, devname, "build.json")))
        rows.append(dict(job=name, result=res, device=devname, same_gates=got == want, gate_hash=got[:16],
                         recorded_gate_hash=want[:16], same_answers_by_label=new_ans == rec_ans,
                         families=[(g["family"], g["n"], g["placement"].get("rule"), g["placement"].get("shape"))
                                   for g in b["groups"]],
                         circuits=b["circuits"], recorded_circuits=rec_build.get("circuits"),
                         seconds=b["qpu_seconds_model"], recorded_seconds=rec_build.get("qpu_seconds_model"),
                         wall_s=round(time.time() - t0, 1)))
        print(json.dumps(rows[-1]), flush=True)
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "regress_entrance.json")
    old = json.load(open(path)) if os.path.exists(path) else []
    keep = [r for r in old if r["job"] not in names and not (r["job"] == "3d" and any(x["job"] == "3d" for x in rows))]
    json.dump(keep + rows, open(path, "w"), indent=1)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2:] or list(JOBS))
