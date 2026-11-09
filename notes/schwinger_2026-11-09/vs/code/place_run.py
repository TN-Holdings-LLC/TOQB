"""Chains (du91's shape rule first, psf_os.chain.place (rule C) only if no shape fits), user circuits as QPY, run2d.

usage: python place_run.py WORK_DIR DEV_ROOT TOQB_DIR OUT.json [N,N..] [steps,..] [param names]
       run2d is started in WORK_DIR with --out given relative to it.
"""
import json, os, subprocess, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import schwinger as S

work, devroot, toqb, out = sys.argv[1:5]
NS = [int(x) for x in sys.argv[5].split(",")] if len(sys.argv) > 5 else list(S.NS)
STEPS = [int(x) for x in sys.argv[6].split(",")] if len(sys.argv) > 6 else list(S.STEPS)
PN = sys.argv[7].split(",") if len(sys.argv) > 7 else [p[0] for p in S.PARAMS]
sys.path.insert(0, os.path.join(toqb, "daily")); sys.path.insert(0, os.path.join(toqb, "gpu"))
import du91
from psf_os import device as Dv, chain as C
DEVS = os.environ.get("DEVS", "ibm_fez,ibm_kingston,ibm_marrakesh").split(",")
os.makedirs(os.path.join(work, "circuits"), exist_ok=True)
res = json.load(open(out)) if os.path.exists(out) else {}


def chain_for(dev, n):
    r = du91.place(dev, n)
    if r["shape"] is not None:
        sh = [s for s in du91.SHAPES if s[0] == r["shape"]][0]
        return dict(rule="shape " + r["shape"], chain=du91.snake(n, sh), copy=[r["drow"], r["dcol"]])
    c = C.place(dev, n)
    return dict(rule="C", chain=c["chain"], start=c["start"], steps=c["steps"])


from qiskit import qpy
from concurrent.futures import ThreadPoolExecutor
import threading
LOCK = threading.Lock()
jobs = []
for dn in DEVS:
    dev = Dv.Device.load(os.path.join(devroot, dn))
    for n in NS:
        pl = chain_for(dev, n)
        for pn in PN:
            p = [x for x in S.PARAMS if x[0] == pn][0]
            for st in STEPS:
                key = f"{dn}/N{n}_{pn}_s{st}"
                if key in res and res[key]["returncode"] == 0:
                    continue
                cid = f"N{n}_{pn}_s{st}_{dn}"
                qc = S.trotter(n, st, p, chain=pl["chain"])
                with open(os.path.join(work, "circuits", cid + ".qpy"), "wb") as f:
                    qpy.dump(qc, f)
                jobs.append((dn, n, st, key, cid, pl))


def job(args):
    dn, n, st, key, cid, pl = args
    if True:
        if True:
            if True:
                rel = os.path.join("run2d", dn, cid)
                t0 = time.time()
                if os.path.exists(os.path.join(work, rel)) and not os.path.exists(os.path.join(work, rel, "report.json")):
                    rel += "_r2"  # an interrupted earlier invocation left the folder; run2d never overwrites
                if os.path.exists(os.path.join(work, rel, "report.json")):
                    pr = subprocess.CompletedProcess([], 0, "", "")  # finished by the interrupted invocation
                else:
                    pr = subprocess.run([sys.executable, "-m", "psf_os", "run2d", "--device", os.path.join(devroot, dn),
                                         "--circuit", os.path.join("circuits", cid + ".qpy"), "--out", rel, "--shots",
                                         "4000"], capture_output=True, text=True, cwd=work)
                r = dict(rule=pl["rule"], chain=pl["chain"], returncode=pr.returncode, seconds=round(time.time() - t0, 1),
                         dir=rel)
                if pr.returncode == 0:
                    rp = json.load(open(os.path.join(work, rel, "report.json")))
                    with open(os.path.join(work, rel, "runs", "p2d_user.qpy"), "rb") as f:
                        cq = qpy.load(f)[0]
                    r.update(cz=rp["cz"], cz_ideal=S.cz_ideal(n, st), copy=rp["copy"], checks=rp["checks"],
                             cz_layers=cq.depth(filter_function=lambda i: i.operation.name == "cz"),
                             depth=cq.depth(), qpu_seconds_model=rp["qpu_seconds_model"])
                else:
                    r.update(refused=(pr.stderr.strip().splitlines() or [""])[-1][:300])
                with LOCK:
                    res[key] = r
                    print(key, r.get("cz"), r.get("cz_layers"), r.get("copy"), r["rule"], r.get("refused", ""), r["seconds"], "s", flush=True)
                    json.dump(res, open(out, "w"), indent=1)


with ThreadPoolExecutor(int(os.environ.get("WORKERS", "6"))) as ex:
    list(ex.map(job, jobs))
print(len(jobs), "jobs done")
