"""Pre-run check of an Ohm job (gpu/ohm_build.py), noiseless, on the job's own compiled circuits (workplace,
2026-11-12; the form of gpu/hub_check.py). Each compiled user circuit is reduced to its N chain qubits in chain order
and simulated without noise: Aer's matrix-product-state method (no truncation) up to --aer-cycles cycles, quimb's
CircuitMPS on merged two-qubit blocks (bond cap --chi) above. Its per-qubit <Z> must equal the answers (by chain
label) within 1e-6; its mirror must read all zeros (1e-6). Also: A1 and A2 equal in CZ count and CZ depth for every
cycle count and string. Prints differences only, never answer values.
usage: PYTHONPATH=<psf-os>:<TOQB> python gpu/ohm_check.py OUT ANSWERS_BY_LABEL.json [--aer-cycles 3] [--chi 2048]
       [--only TAG ...] [--mirrors all|first:N]   (writes OUT/check.json)
"""
import argparse
import ast
import json
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import hub_check as HK  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("answers")
    ap.add_argument("--aer-cycles", type=int, default=3)
    ap.add_argument("--chi", type=int, default=2048)
    ap.add_argument("--only", nargs="*", default=None)
    ap.add_argument("--mirrors", default="all", help="all, or first:N (the mirrors of the first N strings per arm and t)")
    a = ap.parse_args()
    b = json.load(open(os.path.join(a.out, "build.json")))
    ans = json.load(open(a.answers))["z"]
    runs = os.path.join(a.out, "runs")
    chain = b["chain"]["labels"]
    lim = None if a.mirrors == "all" else int(a.mirrors.split(":")[1])
    res, ok = {}, True
    t_all = time.time()
    for tag in sorted(b["cz"]):
        if a.only and tag not in a.only:
            continue
        arm, tt, name = tag.split("_")
        t = int(tt[1:])
        rec = json.load(open(os.path.join(runs, f"p2d_{tag}.json")))
        m = rec["mapping"] if isinstance(rec["mapping"], dict) else ast.literal_eval(rec["mapping"])
        phys = [int(m[str(q)]) for q in chain]
        sim = HK.z_of if t <= a.aer_cycles else (lambda qc: HK.z_quimb(qc, a.chi))
        t0 = time.time()
        z, method = sim(HK.reduced(HK.load(os.path.join(runs, f"p2d_{tag}.qpy")), phys))
        e = np.array([ans[tag][str(q)] for q in chain])
        r = dict(cz=b["cz"][tag], cz_depth=b["cz_depth"][tag], method=method, worst=float(np.abs(z - e).max()))
        good = r["worst"] < 1e-6
        k = int(name[1:])
        if lim is None or k < lim:
            zm, _ = sim(HK.reduced(HK.load(os.path.join(runs, f"p2d_{tag}_mirror.qpy")), phys))
            r["mirror_worst"] = float(np.abs(zm - 1.0).max())
            good &= r["mirror_worst"] < 1e-6
        r["ok"], r["seconds"] = bool(good), round(time.time() - t0, 1)
        ok &= good
        res[tag] = r
        print(f"{tag}: CZ {r['cz']} depth {r['cz_depth']}; {method}: worst {r['worst']:.1e}"
              + (f", mirror {r['mirror_worst']:.1e}" if "mirror_worst" in r else ", mirror not simulated")
              + f" {'PASS' if good else 'FAIL'} ({r['seconds']} s)", flush=True)
    for tag in list(res):
        if tag.startswith("A1_") and "A2_" + tag[3:] in res:
            t2 = "A2_" + tag[3:]
            same = (res[tag]["cz"], res[tag]["cz_depth"]) == (res[t2]["cz"], res[t2]["cz_depth"])
            ok &= same
            if not same:
                print(f"{tag[3:]}: A1 / A2 CZ {res[tag]['cz']} / {res[t2]['cz']}, depth {res[tag]['cz_depth']} / "
                      f"{res[t2]['cz_depth']} DIFFER")
    res["ALL"] = "PASS" if ok else "FAIL"
    res["seconds"] = round(time.time() - t_all, 1)
    json.dump(res, open(os.path.join(a.out, "check.json"), "w"), indent=1)
    print("ALL", res["ALL"], f"({res['seconds']} s)")


if __name__ == "__main__":
    main()
