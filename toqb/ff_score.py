"""Score of the frame-flip test (2026-10-31): per record the sign-aligned Z signal per ring site (toqb.echo_tomo
.aligned), then the block's mean against the same ring's rest, with and without the frame flip.

    python -m toqb.ff_score JOB RUNS --block 38,49,... --segment 3,4,... --out F
"""
import json
import os
import re
import sys

import numpy as np

from toqb import echo_tomo as ET
from toqb import kising_charge as KC

NAME = re.compile(r"kecho_n(\d+)_D(\d+)_hz([0-9.]+)_h([0-9.]+)-fold_rule(_ff)?$")


def read(job, runs):
    import gzip
    man = json.load(open(os.path.join(job, "manifest.json")))
    p = os.path.join(job, "raw_counts.json")
    raw = json.load(open(p)) if os.path.exists(p) else json.load(gzip.open(p + ".gz"))
    rows = {r["pub"]: r["counts"] for r in raw["rows"]}
    out = {}
    for cid, c in enumerate(man["cells"]):
        m = NAME.match(c["name"])
        if not m:
            continue
        rf = os.path.join(runs, c["name"] + ".json")
        if KC.sha256_file(rf) != c["run_sha256"]:
            raise SystemExit(f"STOP: {rf} differs from the manifest")
        rec = json.load(open(rf))
        n, D, ff = rec["task"]["n"], rec["echo"]["D"], bool(rec["echo"].get("frame_flip"))
        cc = {rec["points"][pub["point"]]["input"]: rows[k] for k, pub in enumerate(man["pubs"])
              if pub["cell"] == cid and rec["points"][pub["point"]]["setting"] == "echo"}
        a, se = ET.aligned(cc, n)
        mq = rec["echo"]["measured_qubits"]
        out[(n, D, ff)] = ([int(mq[str(j)]) for j in range(n)], a, se)
    return out


def mean_se(a, se, idx):
    return float(np.mean(a[idx])), float(np.sqrt(np.sum(se[idx] ** 2)) / len(idx))


def verdict(d, se):
    return "HELPS" if d > 2 * se else "HURTS" if d < -2 * se else "NO EFFECT"


def main(argv):
    import argparse
    p = argparse.ArgumentParser(prog="ff_score")
    p.add_argument("job")
    p.add_argument("runs")
    p.add_argument("--block", required=True)
    p.add_argument("--segment", required=True)
    p.add_argument("--n", type=int, default=40)
    p.add_argument("--D", type=int, default=24)
    p.add_argument("--control-n", type=int, default=20)
    p.add_argument("--out", required=True)
    a = p.parse_args(argv)
    if os.path.exists(a.out):
        raise SystemExit(f"STOP: {a.out} exists")
    blk = {int(x) for x in a.block.split(",")}
    seg = {int(x) for x in a.segment.split(",")}
    data = read(a.job, a.runs)
    res = dict(block=sorted(blk), segment=sorted(seg), cells={})
    for (n, D, ff), (phys, v, se) in sorted(data.items()):
        g = [j for j, q in enumerate(phys) if q in blk]
        r = [j for j, q in enumerate(phys) if q not in seg]
        row = dict(phys=phys, a=[float(x) for x in v], se=[float(x) for x in se], all=mean_se(v, se, list(range(n))))
        if g:
            row["block"], row["rest"] = mean_se(v, se, g), mean_se(v, se, r)
        res["cells"][f"n{n}_D{D}_{'ff' if ff else 'off'}"] = row
        line = f"n {n} D {D} {'FF ' if ff else 'off'}: all {row['all'][0]:+.3f}"
        if g:
            line += f"; block {row['block'][0]:+.3f} +- {row['block'][1]:.3f}; rest {row['rest'][0]:+.3f}"
        print(line)
    for D in sorted({D for (n, D, ff) in data if n == a.n}):
        off, on = res["cells"].get(f"n{a.n}_D{D}_off"), res["cells"].get(f"n{a.n}_D{D}_ff")
        if not (off and on):
            continue
        d = on["block"][0] - off["block"][0]
        s = float(np.hypot(on["block"][1], off["block"][1]))
        rec = on["block"][0] >= 0.8 * on["rest"][0]
        e = dict(diff=d, se=s, verdict=verdict(d, s), recovered=bool(rec),
                 rest_diff=on["rest"][0] - off["rest"][0], rest_se=float(np.hypot(on["rest"][1], off["rest"][1])))
        res[f"J_D{D}"] = e
        print(f"{'J' if D == a.D else ' '} n {a.n} D {D}: block FF - off {d:+.3f} +- {s:.3f} -> {e['verdict']}; "
              f"recovered (block >= 0.8 x rest with FF): {'YES' if rec else 'NO'}; rest FF - off {e['rest_diff']:+.3f}")
    off, on = res["cells"].get(f"n{a.control_n}_D{a.D}_off"), res["cells"].get(f"n{a.control_n}_D{a.D}_ff")
    if off and on:
        d, s = on["all"][0] - off["all"][0], float(np.hypot(on["all"][1], off["all"][1]))
        res["control"] = dict(diff=d, se=s, verdict=verdict(d, s))
        print(f"  control n {a.control_n} D {a.D}: FF - off {d:+.3f} +- {s:.3f} -> {res['control']['verdict']}")
    json.dump(res, open(a.out, "w"), indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
