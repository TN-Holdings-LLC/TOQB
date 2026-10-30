"""Per-site reading of mirror-echo cells (2026-10-30 evening, the options test): for each measured qubit j, the raw
echo signal a_j = mean over the 4 inputs of <s_j Z_j>, with s = -z_in (the echo returns the flipped input), so
a_j = 1 for a perfect echo and 0 for a random bit. A declared set of sites is compared between jobs that differ only
in SamplerV2 options. Nothing here reads the calibration.

    python -m toqb.echo_sites compare --runs RUNS --cell NAME --segment 3,4,... \\
        --job off=JOB_OFF --job dd=JOB_DD --job twirl=JOB_TW --base off --out F
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

from toqb import kising_charge as KC


def site_signal(counts_by_input, n):
    """(a, se): per-site signal and its shot-noise SE over the 4 inputs, from {input: counts}."""
    a, v = np.zeros(n), np.zeros(n)
    for i in KC.INPUTS:
        zin = 1 - 2 * np.array(KC.input_bits(i, n))
        c = counts_by_input[i]
        N = float(sum(c.values()))
        m = np.zeros(n)
        for key, k in c.items():
            b = key.replace(" ", "")
            m += k * np.array([1 - 2 * int(b[n - 1 - j]) for j in range(n)])
        m = -zin * m / N
        a += m / 4
        v += (1 - m ** 2) / N / 16
    return a, np.sqrt(v)


def group(a, se, idx):
    idx = list(idx)
    return float(np.mean(a[idx])), float(np.sqrt(np.sum(se[idx] ** 2)) / len(idx))


def cell_counts(job, runs, name):
    man = json.load(open(os.path.join(job, "manifest.json")))
    raw = json.load(open(os.path.join(job, "raw_counts.json")))
    rows = {r["pub"]: r["counts"] for r in raw["rows"]}
    cid = [k for k, c in enumerate(man["cells"]) if c["name"] == name][0]
    rf = os.path.join(runs, name + ".json")
    if KC.sha256_file(rf) != man["cells"][cid]["run_sha256"]:
        raise SystemExit(f"STOP: {rf} differs from the manifest of {job}")
    rec = json.load(open(rf))
    out = {}
    for k, p in enumerate(man["pubs"]):
        if p["cell"] == cid:
            pt = rec["points"][p["point"]]
            if pt["setting"] == "echo":
                out[pt["input"]] = rows[k]
    mq = rec["echo"]["measured_qubits"]
    return out, [int(mq[str(j)]) for j in range(len(mq))], rec["task"]["n"]


def cmd_compare(argv):
    import argparse
    p = argparse.ArgumentParser(prog="echo_sites compare")
    p.add_argument("--runs", required=True)
    p.add_argument("--cell", required=True)
    p.add_argument("--segment", default="")
    p.add_argument("--job", action="append", required=True, help="LABEL=JOB")
    p.add_argument("--base", required=True)
    p.add_argument("--out", required=True)
    a = p.parse_args(argv)
    if os.path.exists(a.out):
        raise SystemExit(f"STOP: {a.out} exists")
    seg = {int(x) for x in a.segment.split(",") if x}
    res = {}
    for lj in a.job:
        lab, job = lj.split("=", 1)
        cc, phys, n = cell_counts(job, a.runs, a.cell)
        s, se = site_signal(cc, n)
        inseg = [j for j, q in enumerate(phys) if q in seg]
        rest = [j for j, q in enumerate(phys) if q not in seg]
        res[lab] = dict(phys=phys, a=[float(x) for x in s], se=[float(x) for x in se], segment_on_ring=[phys[j] for j in inseg],
                        all=group(s, se, range(n)), seg=group(s, se, inseg) if inseg else None,
                        rest=group(s, se, rest) if rest else None)
    base = res[a.base]
    verdicts = {}
    for lab, r in res.items():
        if lab == a.base:
            continue
        v = {}
        for part in ("seg", "rest", "all"):
            if r[part] is None or base[part] is None:
                continue
            d = r[part][0] - base[part][0]
            e = float(np.hypot(r[part][1], base[part][1]))
            v[part] = dict(diff=d, se=e, verdict="HELPS" if d > 2 * e else "HURTS" if d < -2 * e else "NO EFFECT")
        if r["seg"] is not None and r["rest"] is not None:
            v["recovered"] = bool(r["seg"][0] >= 0.8 * r["rest"][0])
        verdicts[lab] = v
    json.dump(dict(cell=a.cell, segment=sorted(seg), base=a.base, jobs=res, verdicts=verdicts), open(a.out, "w"), indent=1)
    for lab, r in res.items():
        f = lambda g: "n/a" if g is None else f"{g[0]:.3f} +- {g[1]:.3f}"
        print(f"{a.cell} [{lab}]: all {f(r['all'])}; segment {f(r['seg'])}; rest {f(r['rest'])}")
    for lab, v in verdicts.items():
        print(f"{lab} vs {a.base}: " + "; ".join(f"{k} {x['diff']:+.3f} +- {x['se']:.3f} {x['verdict']}"
                                             for k, x in v.items() if isinstance(x, dict))
              + (f"; segment recovered: {v['recovered']}" if "recovered" in v else ""))
    return 0


def main(argv):
    if not argv or argv[0] != "compare":
        print(__doc__)
        return 2
    return cmd_compare(argv[1:])


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
