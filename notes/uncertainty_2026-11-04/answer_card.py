"""After-the-fact example (not declared) of the proposed answer card for a P5 job: for each theta and t, the measured
magnetisation with 2 SE of shot noise (chance), next to the bias indicators of the same job: the theta = 0 floor at that
t, the sentinel's verdict, and (where answers exist) the exact value. The card changes no verdict.

usage: PYTHONPATH=<psf-os>:<TOQB> python answer_card.py RESULT_DIR OUT_JSON      (RESULT_DIR holds V/, answers_*)
"""
import json
import os
import sys

import numpy as np

from psf_os import kim as K
from psf_os import sentinel


def main(d, outp):
    jd, runs = os.path.join(d, "V", "job"), os.path.join(d, "V", "runs")
    sc = K.score(jd, runs)
    cpu = json.load(open(os.path.join(d, "answers_cpu.json")))
    pod = json.load(open(os.path.join(d, "answers_pod", "answers_C.json")))
    ans_cpu = cpu["answers"]["b"] if "lattices" in cpu else cpu["answers"]
    cells = {round(s["theta"], 6): s for s in sc.values()}
    floor = {r["t"]: float(np.mean(r["z"])) for r in cells[0.0]["rows"]}
    card = dict(sentinel=sentinel.verdict(jd, runs)["status"], floor=floor, rows=[])
    for th in sorted(k for k in cells if k != 0.0):
        key = f"{th:.6f}"
        for r in cells[th]["rows"]:
            t = r["t"]
            z, se = np.array(r["z"]), np.array(r["se"])
            ex = (pod.get(key, {}).get(str(t)) or ans_cpu.get(key, {}).get(str(t)) or {}).get("z")
            row = dict(theta=th, t=t, M=float(z.mean()), two_se=float(2 * np.sqrt((se ** 2).sum()) / len(z)),
                       floor=floor.get(t))
            if ex is not None:
                idx = [i for i, v in enumerate(ex) if v is not None]
                m_ans = float(np.mean([z[i] for i in idx]))
                two_se_ans = float(2 * np.sqrt(sum(se[i] ** 2 for i in idx)) / len(idx))
                e = float(np.mean([ex[i] for i in idx]))
                row.update(answered=len(idx), M_answered=m_ans, two_se_answered=two_se_ans, M_exact=e,
                           dev=m_ans - e, dev_in_se=(m_ans - e) / (two_se_ans / 2))
            card["rows"].append(row)
    json.dump(card, open(outp, "w"), indent=1)
    print(f"sentinel {card['sentinel']}; floor {dict((t, round(v, 3)) for t, v in floor.items())}")
    print("| theta | t | M answered +- 2 SE | exact | difference | difference / SE | floor at t |")
    for r in card["rows"]:
        if "M_exact" in r:
            print(f"| {r['theta']} | {r['t']} | {r['M_answered']:.3f} +- {r['two_se_answered']:.3f} | {r['M_exact']:.3f} | "
                  f"{r['dev']:+.3f} | {r['dev_in_se']:+.0f} | {r['floor'] if r['floor'] is None else round(r['floor'], 3)} |")


if __name__ == "__main__":
    main(*sys.argv[1:3])
