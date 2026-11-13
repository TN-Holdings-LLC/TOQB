"""Regression of psf-os's entrance (psf_os.entrance, 2026-11-13): the declared jobs of 11-11 and 11-12 built through
the entrance from their logical circuits alone, on the very device records they were built from, compared with the
recorded job by psf-os's gate hash (psf_os.gatehash; the QPY bytes change with the Qiskit version) and the answers
written by label compared with the recorded answers file (workplace, 2026-11-13; desk only, no device).
The entrance is called with the declared builders' settings (shots, max_seconds; mirror "compiled" is the entrance's
default and what the builders patched in; no sentinel fallback, no twin, no special).
usage: PYTHONPATH=<psf-os>:<lab-notebook> python regress_entrance.py WORK_DIR [job ...]   (jobs: hubbard xx91 ohm
       ohm-kingston hubbard-big; default all)"""
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


def main(work, names):
    from psf_os import device as Dv
    from psf_os import entrance as E
    from psf_os import gatehash
    os.makedirs(work, exist_ok=True)
    rows = []
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
    keep = [r for r in old if r["job"] not in names]
    json.dump(keep + rows, open(path, "w"), indent=1)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2:] or list(JOBS))
