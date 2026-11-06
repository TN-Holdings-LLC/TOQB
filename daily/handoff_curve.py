"""Task Y step 4: the chosen curveball problems (results/daily-pool-2026-11-05/curveball_selection.json) before they go
home, no device:

  circuits  each chosen problem's circuit with its measurements as RESULTS/circuits/<ID>.qpy and <ID>.qasm (OpenQASM 3).
  run2d     (PC) every chosen circuit through `psf-os run2d`, one job each, on the 11-05 device records (marrakesh, fez)
            and FakeKingston (graph and failed marks only); `--out` is given as a path relative to the working folder
            (the run is started in SCRATCH_DIR). CZ count, copy, time model, or the refusal as given.
  noiseless (pod, GPU) the user circuit as built (daily/pool.py) against the released answers: P32 from the whole 2^32
            state, B72 from each qubit's light cone; and the compiled circuit of the first accepting device the same
            way where its cones stay at most 26 qubits (P32 compiled: whole state).

usage: python daily/handoff_curve.py circuits RESULTS_DIR SELECTION.json
       python daily/handoff_curve.py run2d SELECTION.json SCRATCH_DIR OUT.json
       python daily/handoff_curve.py noiseless SELECTION.json RELEASED_DIR SCRATCH_DIR OUT.json [cupy|numpy]
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "gpu"))
sys.path.insert(0, os.path.join(HERE, ".."))

from daily import pool as P  # noqa: E402

TOQB = os.path.abspath(os.path.join(HERE, ".."))
DEVICES = {"marrakesh_11-05": os.path.join(TOQB, "results/daily/2026-11-05/ibm_marrakesh/dev"),
           "fez_11-05": os.path.join(TOQB, "results/daily/2026-11-05/ibm_fez/dev"), "fake_FakeKingston": None}
SHOTS = 4000
MAX_COMPILED_CONE = 26


def chosen(selection):
    return [c["id"] for c in json.load(open(selection))["chosen"] if c["id"]]


def circuits(results, selection):
    from qiskit import qasm3, qpy
    d = os.path.join(results, "circuits")
    os.makedirs(d, exist_ok=True)
    ids = chosen(selection)
    for pid in ids:
        qc = P.problem_circuit(pid)
        qc.name = pid
        with open(os.path.join(d, pid + ".qpy"), "wb") as f:
            qpy.dump(qc, f)
        open(os.path.join(d, pid + ".qasm"), "w", newline="\n").write(qasm3.dumps(qc))
    return ids


def run2d(selection, scratch, out):
    from qiskit import qpy
    from psf_os import device as Dv
    from psf_os import job as J
    from daily import handoff_check as H
    os.makedirs(scratch, exist_ok=True)
    ids = chosen(selection)
    os.makedirs(os.path.join(scratch, "circuits"), exist_ok=True)
    for pid in ids:
        with open(os.path.join(scratch, "circuits", pid + ".qpy"), "wb") as f:
            qpy.dump(P.problem_circuit(pid), f)
    rep = {}
    for dname, ddir in DEVICES.items():
        if ddir is None:
            ddir = os.path.join(scratch, "dev_" + dname)
            if not os.path.exists(os.path.join(ddir, "device.json")):
                Dv.fetch_fake(dname.split("_", 1)[1]).save(ddir)
        dev = Dv.Device.load(ddir)
        res = dict(device=dev.name, copies=H.copies(dev), problems={})
        for pid in ids:
            rel = os.path.join("run2d", dname, pid)  # relative to scratch, the working folder of the run
            t0 = time.time()
            p = subprocess.run([sys.executable, "-m", "psf_os", "run2d", "--device", ddir, "--circuit",
                                os.path.join("circuits", pid + ".qpy"), "--out", rel, "--shots", str(SHOTS)],
                               capture_output=True, text=True, cwd=scratch)
            r = dict(returncode=p.returncode, seconds_wall=round(time.time() - t0, 1))
            if p.returncode == 0:
                rp = json.load(open(os.path.join(scratch, rel, "report.json")))
                r.update(cz=rp["cz"], cz_ideal=P.cz_ideal(*P.entry(pid)[1:5]), copy=rp["copy"],
                         passed_over=len(rp["passed_over"]), circuits=rp["circuits"],
                         qpu_seconds_model_job=rp["qpu_seconds_model"],
                         qpu_seconds_model_three=round(J.qpu_seconds(3, SHOTS), 2), checks=rp["checks"])
            else:
                r.update(refused=(p.stderr.strip().splitlines() or [""])[-1])
            res["problems"][pid] = r
            print(f"run2d {dname} {pid}: " + (f"cz {r['cz']} (ideal {r['cz_ideal']}) copy {r['copy']} job "
                                              f"{r['qpu_seconds_model_job']} s" if p.returncode == 0 else
                                              f"REFUSED {r['refused'][:120]}"), flush=True)
        rep[dname] = res
    json.dump(rep, open(out, "w"), indent=1)
    return rep


def noiseless(selection, released, scratch, out, backend="cupy"):
    import qiskit
    import daily_answers as A
    from daily import handoff_check as H
    rep = {}
    for pid in chosen(selection):
        rel = json.load(open(os.path.join(released, pid + ".json")))
        ans = {int(k): v for k, v in rel["values"].items()}
        pa = P.entry(pid)[2]
        qc = P.problem_circuit(pid)
        if pa in A.FULL:
            got = A.full({0: qc}, backend, "single")["values"][0]
            how = "built circuit, whole state"
        else:
            got = A.cones(qc, backend, "single")["values"]
            how = "built circuit, light cones"
        r = dict(built=dict(method=how, compared=len(ans), max_diff=float(max(abs(got[q] - ans[q]) for q in ans))))
        ok = [d for d in DEVICES if os.path.exists(os.path.join(scratch, "run2d", d, pid, "report.json"))]
        if ok:
            cq, m = H._compiled(scratch, ok[0], pid)
            c, idx = H._compact(cq)
            meas = c.copy()
            meas.add_register(qiskit.ClassicalRegister(len(m)))
            labels = sorted(m)
            for k, q in enumerate(labels):
                meas.measure(idx[m[q]], k)
            if pa in A.FULL:
                g2 = A.full({0: meas}, backend, "single")["values"][0]
                how2 = "compiled circuit, whole state"
            else:
                g2 = A.cones(meas, backend, "single", max_qubits=MAX_COMPILED_CONE)["values"]
                how2 = f"compiled circuit, light cones up to {MAX_COMPILED_CONE}"
            done = [q for q in labels if g2[idx[m[q]]] is not None]
            r["compiled"] = dict(device=ok[0], method=how2, compared=len(done), qubits=len(labels),
                                 max_diff=float(max(abs(g2[idx[m[q]]] - ans[q]) for q in done)) if done else None)
        rep[pid] = r
        print(f"noiseless {pid}: built {r['built']['max_diff']:.2e}"
              + (f", compiled ({r['compiled']['device']}, {r['compiled']['compared']} of {r['compiled']['qubits']}) "
                 f"{r['compiled']['max_diff']:.2e}" if "compiled" in r and r["compiled"]["max_diff"] is not None else ""),
              flush=True)
        json.dump(rep, open(out, "w"), indent=1)
    return rep


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "circuits":
        print(circuits(sys.argv[2], sys.argv[3]))
    elif cmd == "run2d":
        run2d(sys.argv[2], sys.argv[3], sys.argv[4])
    elif cmd == "noiseless":
        noiseless(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], *(sys.argv[6:7] or ["cupy"]))
    else:
        raise SystemExit(__doc__)
