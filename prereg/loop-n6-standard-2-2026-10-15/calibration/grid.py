import json, sys, itertools
from multiprocessing import Pool
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
import numpy as np
from calib import run
plan = json.load(open(os.path.join(ROOT, "plan_loop_pilot_n6_s11.json"))); task = plan["task"]
START = 901
def one(args):
    cfg, nseeds, cps = args
    o = run(cfg, list(range(START, START + nseeds)), task, set(cps))
    return dict(cfg=cfg, **{str(k): dict(mean=round(float(v.mean()), 3), p25=round(float(np.percentile(v, 25)), 3),
                                        ge70=round(float((v >= 0.7).mean()), 2)) for k, v in o.items()})
if __name__ == "__main__":
    spec = json.loads(open(sys.argv[1]).read()); START = spec.get("start", 901)
    jobs = [(dict(iterations=spec["iterations"], batch=b, a=a, c=c, A=spec.get("A", 2)), spec["seeds"], spec["cps"])
            for b in spec["batch"] for a in spec["a"] for c in spec["c"]]
    with Pool(2) as p:
        for r in p.imap(one, jobs):
            c = r["cfg"]; print(c["batch"], c["a"], c["c"], " ".join(f"{k}:{r[k]['mean']}/{r[k]['p25']}/{r[k]['ge70']}" for k in map(str, spec["cps"])), flush=True)
            open(sys.argv[2], "a").write(json.dumps(r) + "\n")
