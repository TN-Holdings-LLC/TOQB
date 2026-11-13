"""Regression: rebuild the declared jobs of 11-11 and 11-12 on the very device records they were built from, with the
current psf-os, without and with the sentinel fallback, and compare the circuits with the recorded job's by psf-os's
gate hash (psf_os.gatehash: the gate list itself; the QPY bytes, circuits_sha256, change with the Qiskit version, as
recorded 2026-11-05) and, beside, by circuits_sha256 (workplace, 2026-11-13). Then try the same builders on the three ibm_marrakesh records of 11-12.
usage: PYTHONPATH=<psf-os>:<lab-notebook> python regress.py WORK_DIR"""
import json
import os
import subprocess
import sys

NB = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
G = os.path.join(NB, "gpu")
RES = os.path.join(NB, "results")
JOBS = [
    ("hubbard-2026-11-11", "ibm_fez", ["hub_build.py", "{dev}", "{out}", RES + "/hubbard-2026-11-11/answers/hub_answers_home.json",
                                       "{ans}", "--L", "20", "30", "--steps", "2", "4", "6"]),
    ("hubbard-big-2026-11-11", "ibm_fez", ["hub_build.py", "{dev}", "{out}", RES + "/hubbard-big-2026-11-11/answers/hub_answers_big.json",
                                           "{ans}", "--L", "45", "60", "--steps", "2", "4"]),
    ("hub-dt-2026-11-12", "ibm_fez", ["hub_dt.py", "build", "{dev}", "{out}", RES + "/hub-dt-2026-11-12/answers", "{ans}"]),
    ("ohm-2026-11-12", "ibm_fez", ["ohm_build.py", "{dev}", "{out}", RES + "/ohm-2026-11-12/answers/ohm_answers.json", "{ans}"]),
    ("ohm-kingston-2026-11-12", "ibm_kingston", ["ohm_build.py", "{dev}", "{out}", RES + "/ohm-2026-11-12/answers/ohm_answers.json", "{ans}"]),
    ("xx91-2026-11-12", "ibm_fez", ["ffxx91.py", "{dev}", "{out}", "{ans}", "--steps", "2,4,8,12,16,20"]),
]


def run(args, cwd):
    p = subprocess.run([sys.executable] + args, cwd=cwd, capture_output=True, text=True)
    return p.returncode, (p.stdout + p.stderr).strip().splitlines()[-1:]


def main(work):
    os.makedirs(work, exist_ok=True)
    rows = []
    for res, devname, cmd in JOBS:
        dev = os.path.join(RES, res, "fetch_in", devname, "dev")
        from psf_os import gatehash
        want = json.load(open(os.path.join(RES, res, devname, "job", "manifest.json")))["circuits_sha256"]
        qf = os.path.join(RES, res, devname, "job", "circuits.qpy")
        if not os.path.exists(qf) and os.path.exists(qf + ".gz"):
            import gzip, shutil
            qf2 = os.path.join(work, res + "_recorded.qpy")
            with gzip.open(qf + ".gz") as fi, open(qf2, "wb") as fo:
                shutil.copyfileobj(fi, fo)
            qf = qf2
        want_g = gatehash.qpy_hash(qf)["gate_sha256"]
        for fb in (None, "same_qubits"):
            tag = f"{res}_{devname}_{fb or 'none'}"
            out, ans = os.path.join(work, tag), os.path.join(work, tag + "_ans")
            args = [os.path.join(G, cmd[0])] + [a.format(dev=dev, out=out, ans=ans) for a in cmd[1:]]
            if fb:
                args += ["--sentinel-fallback", fb]
            code, tail = run(args, work)
            got = json.load(open(os.path.join(out, "job", "manifest.json")))["circuits_sha256"] if code == 0 else None
            got_g = gatehash.qpy_hash(os.path.join(out, "job", "circuits.qpy"))["gate_sha256"] if code == 0 else None
            rows.append(dict(job=res, device=devname, fallback=fb, built=code == 0, same_gates=got_g == want_g,
                             gate_hash=(got_g or "")[:16], recorded_gate_hash=want_g[:16], same_qpy_bytes=got == want,
                             tail=tail))
            print(json.dumps(rows[-1]), flush=True)
    for res, cmd in (("ohm-2026-11-12", JOBS[3][2]), ("ohm-kingston-2026-11-12", JOBS[4][2]), ("xx91-2026-11-12", JOBS[5][2]),
                     ("hubbard-2026-11-11", JOBS[0][2])):
        dev = os.path.join(RES, res, "fetch_in", "ibm_marrakesh", "dev")
        for fb in (None, "same_qubits"):
            tag = f"marrakesh_{res}_{fb or 'none'}"
            out, ans = os.path.join(work, tag), os.path.join(work, tag + "_ans")
            args = [os.path.join(G, cmd[0])] + [a.format(dev=dev, out=out, ans=ans) for a in cmd[1:]]
            if fb:
                args += ["--sentinel-fallback", fb]
            code, tail = run(args, work)
            b = json.load(open(os.path.join(out, "build.json"))) if code == 0 else {}
            rows.append(dict(job=res, device="ibm_marrakesh", fallback=fb, built=code == 0, tail=tail,
                             circuits=b.get("circuits"), seconds=b.get("qpu_seconds_model"),
                             sentinel_fallback=b.get("sentinel_fallback")))
            print(json.dumps(rows[-1]), flush=True)
    json.dump(rows, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "regress.json"), "w"), indent=1)


if __name__ == "__main__":
    main(sys.argv[1])
