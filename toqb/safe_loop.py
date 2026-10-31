"""Safe-ring loop (2026-10-31): scan, list, avoid, scan again, until the rule's rings are verified clean.

The defect list of toqb.defect_list lists a path only after it is dead (< 0.12) in two jobs. On 31 October a weak
stretch on the n = 72 ring placed around that list (signal 0.10-0.18 against a ring median of about 0.4) slipped
through and the ring read about 4 layers less deep than n = 20. This module is the strict variant:

- a site is *weak* if its echo signal at D = 24 is below max(thr, rel x the ring's median) (default 0.12, 0.5);
- a weak run is at least `min_len` consecutive weak ring sites (cyclic); its centre path (4 qubits) is listed at once
  (one sighting is enough);
- a ring is SAFE when it has no weak run and its readable depth L* reaches the same job's n = 20 control within
  2 combined SE.

    python -m toqb.safe_loop scan OUT.json --obs DEVICE:JOB:RUNS[:LABEL] ... [--base LIST.json]
    python -m toqb.safe_loop mask FETCH LIST.json OUT_FETCH
    python -m toqb.safe_loop judge JOB RUNS --list LIST.json --out RESULT.json --next NEXT_LIST.json

Nothing here reads a calibration number; the list comes only from the user's own runs.
"""
from __future__ import annotations

import json
import math
import os
import pickle
import sys

import numpy as np

from toqb import defect_list as DL
from toqb import kising_charge as KC


def weak_runs(a, thr=0.12, rel=0.5, min_len=3):
    """Runs of at least min_len consecutive ring sites (cyclic) below max(thr, rel x median(a))."""
    a = np.asarray(a, float)
    line = max(thr, rel * float(np.median(a)))
    return DL.dead_runs(a, line, min_len), line


def scan_job(device, job, runs, label, thr=0.12, rel=0.5, min_len=3, width=4):
    """One entry per ring size of the job: the ring, the weak line, the weak runs and their centre paths."""
    prof, job_id, backend, when = DL.job_profiles(job, runs)
    if backend and backend != device:
        raise ValueError(f"{job}: submitted to {backend}, not {device}")
    out = []
    for n, (phys, a) in sorted(prof.items()):
        rs, line = weak_runs(a, thr, rel, min_len)
        out.append(dict(device=device, job=job_id, label=label, submitted=when, n=n, ring=list(phys),
                        median=float(np.median(a)), line=line,
                        weak=[dict(start=s, length=L, qubits=[phys[(s + t) % n] for t in range(L)],
                                   centre=list(DL.centre_path(phys, s, L, width)),
                                   mean=float(np.mean([a[(s + t) % n] for t in range(L)]))) for s, L in rs]))
    return out


def paths_of(lst, device):
    """The listed paths of a device, without duplicates (a path and its reverse are the same)."""
    seen, out = set(), []
    for p in lst["paths"]:
        if p["device"] != device:
            continue
        key = min(tuple(p["path"]), tuple(reversed(p["path"])))
        if key not in seen:
            seen.add(key)
            out.append(tuple(p["path"]))
    return out


def add_paths(lst, scans, overlap=2):
    """A new list: the old paths plus the centre path of every weak run in the scans (one sighting is enough). A centre
    sharing at least `overlap` qubits with a path already listed on the device is the same defect seen again (a run's
    ends move by a site or two) and is not added, so one defect masks one coupler."""
    new = dict(params=lst["params"], paths=list(lst["paths"]), scans=list(lst.get("scans", [])) + scans)
    for s in scans:
        for w in s["weak"]:
            if not any(p["device"] == s["device"] and len(set(p["path"]) & set(w["centre"])) >= overlap
                       for p in new["paths"]):
                new["paths"].append(dict(device=s["device"], path=w["centre"], source=f"{s['label']} n {s['n']}",
                                         mean=w["mean"], length=w["length"]))
    return new


def depth_verdicts(echo_score, hz="0.0", control=20):
    """Per n: L*, SE and REACHED / SHORTER against the control's L* (2 combined SE), from kising_echo's walls."""
    w = echo_score["walls"][hz]
    f = {x["n"]: (x["L_star"], x["se"]) for x in w["fits"]}
    if control not in f or f[control][0] is None:
        return {}
    l0, s0 = f[control]
    out = {}
    for n, (L, se) in sorted(f.items()):
        if n == control:
            continue
        ok = L is not None and L >= l0 - 2 * math.sqrt(se ** 2 + s0 ** 2)
        out[n] = dict(L_star=L, se=se, L_star_control=l0, se_control=s0, depth="REACHED" if ok else "SHORTER")
    return out


def main(argv):
    import argparse
    p = argparse.ArgumentParser(prog="safe_loop")
    sp = p.add_subparsers(dest="cmd", required=True)
    s1 = sp.add_parser("scan")
    s1.add_argument("out")
    s1.add_argument("--obs", nargs="+", required=True)
    s1.add_argument("--base", default=None)
    s1.add_argument("--seed-defect-list", default=None, help="toqb.defect_list file: its LISTED paths seed the list")
    s1.add_argument("--now", default=None)
    s1.add_argument("--thr", type=float, default=0.12)
    s1.add_argument("--rel", type=float, default=0.5)
    s1.add_argument("--min-len", type=int, default=3)
    s2 = sp.add_parser("mask")
    s2.add_argument("fetch")
    s2.add_argument("list")
    s2.add_argument("out_fetch")
    s3 = sp.add_parser("judge")
    s3.add_argument("job")
    s3.add_argument("runs")
    s3.add_argument("--list", required=True)
    s3.add_argument("--out", required=True)
    s3.add_argument("--next", required=True)
    s3.add_argument("--device", default="ibm_kingston")
    s3.add_argument("--label", default=None)
    a = p.parse_args(argv)

    if a.cmd == "scan":
        if os.path.exists(a.out):
            raise SystemExit(f"STOP: {a.out} exists")
        params = dict(thr=a.thr, rel=a.rel, min_len=a.min_len)
        if a.base:
            lst = json.load(open(a.base))
            if lst["params"] != params:
                raise SystemExit("STOP: the base list was made with other parameters")
        else:
            lst = dict(params=params, paths=[], scans=[])
        if a.seed_defect_list:
            import datetime as dt
            d = json.load(open(a.seed_defect_list))
            now = dt.datetime.fromisoformat(a.now) if a.now else None
            for e in DL.entries(d["observations"], now=now):
                if e["status"] == "LISTED":
                    lst["paths"].append(dict(device=e["device"], path=e["centre"],
                                             source=f"defect list {os.path.basename(a.seed_defect_list)}"))
        scans = []
        for it in a.obs:
            parts = it.split(":")
            scans += scan_job(parts[0], parts[1], parts[2], parts[3] if len(parts) > 3 else parts[1],
                              a.thr, a.rel, a.min_len)
        new = add_paths(lst, scans)
        json.dump(new, open(a.out, "w"), indent=1)
        for s in scans:
            print(f"{s['label']} n {s['n']}: median {s['median']:.2f}, weak line {s['line']:.2f}; weak runs "
                  + ("; ".join(f"{w['length']} sites {w['qubits']} (mean {w['mean']:.2f})" for w in s["weak"]) or "none"))
        for pth in new["paths"]:
            print(f"listed {pth['device']} {pth['path']} ({pth['source']})")
        return 0

    if a.cmd == "mask":
        if os.path.exists(a.out_fetch):
            raise SystemExit(f"STOP: {a.out_fetch} exists")
        fj = json.load(open(os.path.join(a.fetch, "fetch.json")))
        target = pickle.load(open(os.path.join(a.fetch, "target.pkl"), "rb"))
        lst = json.load(open(a.list))
        paths = paths_of(lst, fj["backend"])
        t2, masked = DL.mask_target(target, paths)
        os.makedirs(a.out_fetch)
        tp = os.path.join(a.out_fetch, "target.pkl")
        pickle.dump(t2, open(tp, "wb"))
        json.dump(dict(fj, target_sha256=KC.sha256_file(tp), masked_by_safe_list=dict(
            source_target_sha256=fj["target_sha256"], list=os.path.basename(a.list),
            list_sha256=KC.sha256_file(a.list), masked_couplers=[list(e) for e in masked],
            paths=[list(x) for x in paths])), open(os.path.join(a.out_fetch, "fetch.json"), "w"), indent=1)
        print(f"{fj['backend']}: masked {len(masked)} coupler(s) {masked} from {len(paths)} listed path(s)")
        return 0

    # judge
    for f in (a.out, a.next):
        if os.path.exists(f):
            raise SystemExit(f"STOP: {f} exists")
    lst = json.load(open(a.list))
    pr = lst["params"]
    sc = scan_job(a.device, a.job, a.runs, a.label or os.path.basename(os.path.dirname(os.path.abspath(a.job))),
                  pr["thr"], pr["rel"], pr["min_len"])
    es = json.load(open(os.path.join(a.job, "echo_score.json")))
    dv = depth_verdicts(es)
    res = dict(list=os.path.basename(a.list), list_sha256=KC.sha256_file(a.list), sizes={})
    for s in sc:
        n = s["n"]
        r = dict(ring=s["ring"], median=s["median"], line=s["line"], weak=s["weak"])
        if n in dv:
            r.update(dv[n])
            r["verdict"] = "SAFE" if not s["weak"] and dv[n]["depth"] == "REACHED" else "NOT SAFE"
        res["sizes"][str(n)] = r
        line = f"n {n}: median {s['median']:.2f}, weak runs " + (
            "; ".join(f"{w['qubits']} (mean {w['mean']:.2f})" for w in s["weak"]) or "none")
        if n in dv:
            line += (f"; L* {dv[n]['L_star']:.2f} +- {dv[n]['se']:.2f} against n = 20 {dv[n]['L_star_control']:.2f} "
                     f"+- {dv[n]['se_control']:.2f} {dv[n]['depth']} -> {r['verdict']}")
        print(line)
    judged = [r["verdict"] for r in res["sizes"].values() if "verdict" in r]
    res["overall"] = "SUCCESS" if judged and all(v == "SAFE" for v in judged) else "NOT YET"
    print("overall:", res["overall"])
    json.dump(res, open(a.out, "w"), indent=1)
    new = add_paths(lst, [s for s in sc if s["n"] != 20])
    json.dump(new, open(a.next, "w"), indent=1)
    print(f"next list: {len(paths_of(new, a.device))} path(s) for {a.device}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
