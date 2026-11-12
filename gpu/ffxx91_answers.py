"""Placement-free answers of the XX 91-qubit depth scan (home, 2026-11-12), so that one hash can be declared before
the device is known. The build (gpu/ffxx91.py) writes the same values keyed by the chain's device labels; `check`
shows that a build's answer file is the logical file laid on its chain (chain position k <-> label labels[k]).
usage: python gpu/ffxx91_answers.py logical OUT [--n 91] [--steps 2,4,8,12,16,20]
       python gpu/ffxx91_answers.py check LOGICAL BUILD_ANSWERS BUILD_JSON
Prints hashes and differences only, never answer values.
"""
import argparse
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ff_xx as F  # noqa: E402
from ffxx91 import tag  # noqa: E402

THETAS = (0.7853981633974483, 1.5707963267948966)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    lo = sub.add_parser("logical")
    lo.add_argument("out")
    lo.add_argument("--n", type=int, default=91)
    lo.add_argument("--steps", default="2,4,8,12,16,20")
    ch = sub.add_parser("check")
    ch.add_argument("logical")
    ch.add_argument("build_answers")
    ch.add_argument("build_json")
    a = ap.parse_args()
    if a.cmd == "logical":
        out = {tag(a.n, th, s): [float(z) for z in F.z_exact(a.n, s, th)]
               for th in THETAS for s in map(int, a.steps.split(","))}
        json.dump(out, open(a.out, "w"), indent=1, sort_keys=True)
        print("logical answers sha256", hashlib.sha256(open(a.out, "rb").read()).hexdigest())
        return
    lg = json.load(open(a.logical))
    ba = json.load(open(a.build_answers))
    b = json.load(open(a.build_json))
    n = len(next(iter(lg.values())))
    labels = b["chains"][str(n)]["labels"]
    worst = 0.0
    if set(lg) != set(ba):
        raise SystemExit(f"FAIL: tags differ: {sorted(set(lg) ^ set(ba))}")
    for t in lg:
        worst = max(worst, max(abs(lg[t][k] - ba[t][str(q)]) for k, q in enumerate(labels)))
    print(f"{'PASS' if worst == 0.0 else 'FAIL'}: build answers equal the logical answers on the chain (worst {worst:.1e})")


if __name__ == "__main__":
    main()
