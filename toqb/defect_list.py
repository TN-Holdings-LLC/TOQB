"""Defect list (2026-10-31, design draft, not declared): a quantum analogue of memtest plus a bad-block list.

An operating system keeps a list of bad memory pages or disk sectors found by its own tests and allocates around
them. Here the test is the rule's own mirror echo (toqb.kising_echo), read per ring site; a dead run is a contiguous
stretch of sites whose echo signal is near zero or inverted. The 30-31 October data showed that the defect is not a
property of single qubits: every qubit of kingston's 18-site run at n = 40 was healthy on another ring. So the list
does not ban qubits. It records the *path* at the centre of each dead run (by Lemma 2 of Paper 5 a single fault
spreads at most L sites each way, so the centre is where the source most likely sits), and placement skips a
candidate outline that contains a listed centre path, taking the next outline in the rule's fixed order. Nothing here
reads a calibration number; the list comes only from the user's own runs.

    python -m toqb.defect_list ingest OUT.json --obs DEVICE:JOB:RUNS[:LABEL] ... [--thr 0.12] [--min-len 3] [--centre 4]
    python -m toqb.defect_list status LIST.json [--min-repeats 2] [--expiry-days 7] [--now ISO]
    python -m toqb.defect_list place FETCH N LIST.json [--min-repeats 2] [--expiry-days 7] [--now ISO]
    python -m toqb.defect_list mask FETCH LIST.json OUT_FETCH [--min-repeats 2] [--expiry-days 7] [--now ISO]
    python -m toqb.defect_list coverage JOB_A RUNS_A [--b JOB_B RUNS_B] [--paths 28-29-38-49,...] --out F
    (ingest takes --base OLD.json to keep the earlier observations in front: the list grows day by day)

`mask` writes a copy of the day's fetch in which the middle coupler of every listed path is marked failed (error 1),
so that the unchanged build tools (toqb.kising_echo build with the fold:rule arm) place around the list; its
fetch.json records the source fetch, the list's SHA-256 and the masked couplers. It is stricter than `place` (it also
skips outlines that use the middle coupler without the whole path); `compare_mask` reports where the two differ.

The parameters (threshold 0.12, minimum run 3, centre path 4 qubits, 2 repeats, expiry) are drafts for the owner.
"""
from __future__ import annotations

import datetime as dt
import gzip
import json
import os
import re
import sys
from collections import defaultdict

import numpy as np

from toqb import kising_charge as KC

ECHO_NAME = re.compile(r"kecho_n(\d+)_D(\d+)_hz([0-9.]+)_h([0-9.]+)-(.+)$")


# ------------------------------------------------------------------------------------------------ reading a job

def _load_counts(job):
    for name in ("raw_counts.json", "raw_counts.json.gz"):
        p = os.path.join(job, name)
        if os.path.exists(p):
            return json.load(gzip.open(p) if name.endswith(".gz") else open(p))["rows"]
    raise FileNotFoundError(f"no raw counts in {job}")


def site_signal(counts_by_input, n):
    """Raw per-site echo signal a_j = mean over the 4 inputs of <-z_in,j Z_j> (1 perfect, 0 random, < 0 inverted)."""
    a = np.zeros(n)
    for i in KC.INPUTS:
        zin = 1 - 2 * np.array(KC.input_bits(i, n))
        c = counts_by_input[i]
        N = float(sum(c.values()))
        m = np.zeros(n)
        for key, k in c.items():
            b = key.replace(" ", "")
            m += k * np.array([1 - 2 * int(b[n - 1 - j]) for j in range(n)])
        a += -zin * m / N / 4
    return a


def job_profiles(job, runs, D=24, arm="fold_rule"):
    """{n: (physical qubits in ring order, a_j averaged over the hz present)} for the job's cells at depth D."""
    man = json.load(open(os.path.join(job, "manifest.json")))
    rows = _load_counts(job)
    sub = json.load(open(os.path.join(job, "submission.json")))
    per = defaultdict(list)
    phys_of = {}
    for cid, c in enumerate(man["cells"]):
        m = ECHO_NAME.match(c["name"])
        if not m or int(m.group(2)) != D or m.group(5) != arm:
            continue
        rec = json.load(open(os.path.join(runs, c["name"] + ".json")))
        if not rec.get("valid"):
            continue
        n = rec["task"]["n"]
        cc = {}
        for k, p in enumerate(man["pubs"]):
            if p["cell"] == cid:
                pt = rec["points"][p["point"]]
                if pt["setting"] == "echo":
                    cc[pt["input"]] = rows[k]["counts"]
        mq = rec["echo"]["measured_qubits"]
        phys = tuple(int(mq[str(j)]) for j in range(n))
        if n in phys_of and phys_of[n] != phys:
            raise ValueError(f"{job}: two rings for n = {n}")
        phys_of[n] = phys
        per[n].append(site_signal(cc, n))
    when = sub.get("submitted", "")
    return {n: (phys_of[n], np.mean(per[n], axis=0)) for n in per}, sub.get("job_id"), sub.get("backend"), when


# ------------------------------------------------------------------------------------------------ dead runs

def dead_runs(a, thr=0.12, min_len=3):
    """Contiguous runs (on the ring, cyclic) of sites with a < thr, at least min_len long: [(start, length)]."""
    n = len(a)
    dead = [x < thr for x in a]
    if all(dead):
        return [(0, n)]
    s0 = next(i for i in range(n) if not dead[i])  # start scanning after a live site so no run is cut at index 0
    out, i = [], 0
    while i < n:
        j = (s0 + i) % n
        if dead[j]:
            k = 0
            while k < n and dead[(j + k) % n]:
                k += 1
            if k >= min_len:
                out.append((j, k))
            i += k
        else:
            i += 1
    return out


def centre_path(phys, start, length, width=4):
    """The `width` qubits at the centre of a dead run, in ring order (fewer if the run is shorter)."""
    w = min(width, length)
    first = start + (length - w) // 2
    return tuple(phys[(first + t) % len(phys)] for t in range(w))


def contains_path(cycle, path):
    """True if `path` appears as consecutive qubits of the cycle, in either direction."""
    m, w = len(cycle), len(path)
    if w > m:
        return False
    for seq in (path, tuple(reversed(path))):
        for s in range(m):
            if all(cycle[(s + t) % m] == seq[t] for t in range(w)):
                return True
    return False


# ------------------------------------------------------------------------------------------------ the list

def observe(device_job_runs, thr=0.12, min_len=3, width=4):
    """One observation per (job, n): the ring, its dead runs and their centre paths."""
    obs = []
    for device, job, runs, label in device_job_runs:
        prof, job_id, backend, when = job_profiles(job, runs)
        if backend and backend != device:
            raise ValueError(f"{job}: submitted to {backend}, not {device}")
        for n, (phys, a) in sorted(prof.items()):
            runs_ = dead_runs(a, thr, min_len)
            obs.append(dict(device=device, job=job_id, label=label, submitted=when, n=n, ring=list(phys),
                            median=float(np.median(a)),
                            dead=[dict(start=s, length=L, qubits=[phys[(s + t) % n] for t in range(L)],
                                       centre=list(centre_path(phys, s, L, width)),
                                       mean=float(np.mean([a[(s + t) % n] for t in range(L)]))) for s, L in runs_]))
    return obs


def _time(s):
    m = re.search(r"\((\d{4}-\d\d-\d\d \d\d:\d\d:\d\d) CET\)", s or "")
    if m:
        return dt.datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S")
    return dt.datetime.fromisoformat(s[:19]) if s else None


def entries(obs, min_repeats=2, expiry_days=7.0, now=None, overlap=2):
    """Group dead runs per device: two sightings belong to one entry when their centre paths share at least `overlap`
    qubits (a run's ends move by a site or two between runs). The entry's path is the part of the centre common to all
    its sightings, in ring order (the first sighting's centre if that is shorter than `overlap`). LISTED: seen in
    >= min_repeats jobs and last seen within expiry_days of `now`; CANDIDATE: fewer jobs; EXPIRED: older. A ring
    observed healthy that contains the entry's path is reported as a contradiction (the entry stays)."""
    groups = []
    for o in obs:
        for d in o["dead"]:
            c = list(d["centre"])
            sight = dict(job=o["job"], label=o["label"], n=o["n"], submitted=o["submitted"], mean=d["mean"],
                         length=d["length"], centre=c, ring=o["ring"])
            for g in groups:
                if g["device"] == o["device"] and any(len(set(c) & set(s["centre"])) >= overlap for s in g["seen"]):
                    g["seen"].append(sight)
                    g["qubits"].update(d["qubits"])
                    break
            else:
                groups.append(dict(device=o["device"], seen=[sight], qubits=set(d["qubits"])))
    t_now = now or max((_time(o["submitted"]) for o in obs if o["submitted"]), default=None)
    out = []
    for g in groups:
        first = g["seen"][0]["centre"]
        common = [q for q in first if all(q in s["centre"] for s in g["seen"])]
        path = common if len(common) >= overlap else first
        device = g["device"]
        jobs = {s["job"] for s in g["seen"]}
        last = max(_time(s["submitted"]) for s in g["seen"])
        contra = [dict(job=o["job"], n=o["n"]) for o in obs if o["device"] == device and not o["dead"]
                  and contains_path(o["ring"], path)]
        if t_now is not None and (t_now - last).total_seconds() > expiry_days * 86400:
            status = "EXPIRED"
        elif len(jobs) >= min_repeats:
            status = "LISTED"
        else:
            status = "CANDIDATE"
        out.append(dict(device=device, centre=list(path), status=status, jobs=sorted(j for j in jobs if j),
                        sightings=len(g["seen"]), last_seen=last.isoformat(sep=" "), qubits=sorted(g["qubits"]),
                        contradictions=contra,
                        seen=[{k: v for k, v in s.items() if k != "ring"} for s in g["seen"]]))
    out.sort(key=lambda e: (e["device"], e["status"], e["centre"]))
    return out


# ------------------------------------------------------------------------------------------------ placement

def place_avoiding(target, n, listed_paths):
    """The rule's placement (toqb.fold.fold_place: shortest outline of m >= n, first in the fixed order, working
    elements only) with one more condition: the outline contains no listed centre path. Returns (m, name, cycle,
    skipped) or None; `skipped` lists the outlines passed over because of the list, in order."""
    from toqb import fold as F

    def bad(name, qa):
        p = target[name].get(qa) if name in target.operation_names else None
        return p is None or (p.error is not None and p.error >= 1)
    edges = {tuple(sorted(qa)) for qa in target["cz"] if qa is not None and not bad("cz", qa)}
    cands = F.shapes_for(F.lattice(edges, target.num_qubits), n, F._all_pairs(target))
    skipped = []
    for m in sorted({c[0] for c in cands}):
        if m < n:
            continue
        for length, name, cyc in cands:
            if length != m:
                continue
            if any(bad("sx", (q,)) or bad("measure", (q,)) for q in cyc):
                continue
            if not all(tuple(sorted((cyc[i], cyc[(i + 1) % m]))) in edges for i in range(m)):
                continue
            hit = [p for p in listed_paths if contains_path(cyc, p)]
            if hit:
                skipped.append(dict(m=m, name=str(name), hits=[list(p) for p in hit]))
                continue
            return m, name, cyc, skipped
    return None


def middle_edge(path):
    k = (len(path) - 1) // 2
    return tuple(sorted((path[k], path[k + 1])))


def mask_target(target, listed_paths):
    """A copy of the Target with the middle coupler of each listed path marked failed (error 1, both directions)."""
    import copy
    from qiskit.transpiler import InstructionProperties
    t2 = copy.deepcopy(target)
    masked = sorted({middle_edge(p) for p in listed_paths if len(p) >= 2})
    for a, b in masked:
        for qa in ((a, b), (b, a)):
            if qa in t2["cz"]:
                old = t2["cz"][qa]
                t2.update_instruction_properties("cz", qa, InstructionProperties(
                    duration=old.duration if old is not None else None, error=1.0))
    return t2, masked


# ------------------------------------------------------------------------------------------------ coverage

def usable(a, thr=0.12, min_len=3):
    """Ring sites outside every dead run: the part of the ring that still carries information."""
    n = len(a)
    dead = set()
    for st, ln in dead_runs(np.asarray(a), thr, min_len):
        dead.update((st + t) % n for t in range(ln))
    return [j for j in range(n) if j not in dead]


def coverage_verdict(u_a, u_b, margin=3):
    """WIDER: the avoiding ring keeps at least `margin` more usable sites than the standard ring at the same n;
    NARROWER: at least `margin` fewer; SAME otherwise (margin = the shortest dead run)."""
    d = u_b - u_a
    return "WIDER" if d >= margin else "NARROWER" if d <= -margin else "SAME"


def path_present(phys, a, path, thr=0.12, min_len=3, need=2):
    """True if a dead run of this ring holds at least `need` qubits of the path."""
    n = len(phys)
    for st, ln in dead_runs(np.asarray(a), thr, min_len):
        if len({phys[(st + t) % n] for t in range(ln)} & set(path)) >= need:
            return True
    return False


def coverage(job_a, runs_a, job_b=None, runs_b=None, paths=(), thr=0.12, min_len=3):
    """Per ring size: usable sites on the standard ring (job A) and on the avoiding ring (job B, if run), the mean
    signal over the usable sites, the dead runs, the verdict, and whether each listed path is dead on job A's ring."""
    pa = job_profiles(job_a, runs_a)[0]
    pb = job_profiles(job_b, runs_b)[0] if job_b else {}
    out = {}
    for n in sorted(pa):
        row = {}
        for tag, prof in (("A", pa), ("B", pb)):
            if n not in prof:
                continue
            phys, a = prof[n]
            u = usable(a, thr, min_len)
            row[tag] = dict(ring=list(phys), usable=len(u), mean_usable=float(np.mean(a[u])) if u else None,
                            mean_all=float(np.mean(a)),
                            dead=[dict(start=st, length=ln, qubits=[phys[(st + t) % n] for t in range(ln)])
                                  for st, ln in dead_runs(a, thr, min_len)])
        if "B" in row:
            row["verdict"] = coverage_verdict(row["A"]["usable"], row["B"]["usable"])
        phys, a = pa[n]
        row["paths"] = {"-".join(map(str, p)): (path_present(phys, a, p, thr, min_len) if contains_path(phys, p)
                                                 else None) for p in paths}
        out[n] = row
    return out


# ------------------------------------------------------------------------------------------------ CLI

def _parse_obs(items):
    out = []
    for it in items:
        parts = it.split(":")
        device, job, runs = parts[0], parts[1], parts[2]
        out.append((device, job, runs, parts[3] if len(parts) > 3 else os.path.basename(os.path.dirname(job))))
    return out


def main(argv):
    import argparse
    p = argparse.ArgumentParser(prog="defect_list")
    sp = p.add_subparsers(dest="cmd", required=True)
    a1 = sp.add_parser("ingest")
    a1.add_argument("out")
    a1.add_argument("--obs", nargs="+", required=True)
    a1.add_argument("--thr", type=float, default=0.12)
    a1.add_argument("--min-len", type=int, default=3)
    a1.add_argument("--centre", type=int, default=4)
    a1.add_argument("--base", default=None, help="an earlier list file whose observations are kept in front")
    c1 = sp.add_parser("coverage")
    c1.add_argument("job_a")
    c1.add_argument("runs_a")
    c1.add_argument("--b", nargs=2, metavar=("JOB_B", "RUNS_B"), default=None)
    c1.add_argument("--paths", default="", help="listed paths to check on job A's ring, e.g. 28-29-38-49,9-10-11")
    c1.add_argument("--thr", type=float, default=0.12)
    c1.add_argument("--min-len", type=int, default=3)
    c1.add_argument("--out", required=True)
    for name in ("status", "place", "mask"):
        a = sp.add_parser(name)
        if name in ("place", "mask"):
            a.add_argument("fetch")
        if name == "place":
            a.add_argument("n", type=int)
        a.add_argument("list")
        if name == "mask":
            a.add_argument("out_fetch")
        a.add_argument("--min-repeats", type=int, default=2)
        a.add_argument("--expiry-days", type=float, default=7.0)
        a.add_argument("--now", default=None)
    a = p.parse_args(argv)
    if a.cmd == "ingest":
        if os.path.exists(a.out):
            raise SystemExit(f"STOP: {a.out} exists")
        obs = observe(_parse_obs(a.obs), a.thr, a.min_len, a.centre)
        prev = []
        if a.base:
            b = json.load(open(a.base))
            if b["params"] != dict(thr=a.thr, min_len=a.min_len, centre=a.centre):
                raise SystemExit(f"STOP: {a.base} was made with other parameters {b['params']}")
            prev = b["observations"]
            seen = {(o["device"], o["job"], o["n"]) for o in prev}
            dup = [o for o in obs if (o["device"], o["job"], o["n"]) in seen]
            if dup:
                raise SystemExit(f"STOP: job {dup[0]['job']} n {dup[0]['n']} is already in {a.base}")
        json.dump(dict(params=dict(thr=a.thr, min_len=a.min_len, centre=a.centre), observations=prev + obs,
                       base=(dict(file=os.path.basename(a.base), sha256=KC.sha256_file(a.base)) if a.base else None)),
                  open(a.out, "w"), indent=1)
        for o in obs:
            print(f"{o['device']} {o['label']} n {o['n']}: median {o['median']:.2f}; dead runs "
                  + ("; ".join(f"{d['length']} sites, centre {d['centre']}" for d in o["dead"]) or "none"))
        return 0
    if a.cmd == "coverage":
        if os.path.exists(a.out):
            raise SystemExit(f"STOP: {a.out} exists")
        paths = [tuple(int(x) for x in t.split("-")) for t in a.paths.split(",") if t]
        cov = coverage(a.job_a, a.runs_a, *(a.b or (None, None)), paths=paths, thr=a.thr, min_len=a.min_len)
        json.dump(dict(params=dict(thr=a.thr, min_len=a.min_len), job_a=a.job_a, job_b=a.b[0] if a.b else None,
                       sizes={str(n): r for n, r in cov.items()}), open(a.out, "w"), indent=1)
        for n, r in cov.items():
            line = f"n {n}: usable A {r['A']['usable']}/{n} (signal {r['A']['mean_usable'] or 0:+.3f})"
            if "B" in r:
                line += (f", B {r['B']['usable']}/{n} (signal {r['B']['mean_usable'] or 0:+.3f})"
                         f" -> {r['verdict']}")
            pres = {k: v for k, v in r["paths"].items() if v is not None}
            if pres:
                line += "; on A's ring: " + ", ".join(f"[{k}] {'PRESENT' if v else 'ABSENT'}" for k, v in pres.items())
            print(line)
        return 0
    data = json.load(open(a.list))
    now = dt.datetime.fromisoformat(a.now) if a.now else None
    ent = entries(data["observations"], a.min_repeats, a.expiry_days, now)
    if a.cmd == "status":
        for e in ent:
            print(f"{e['device']} centre {e['centre']}: {e['status']} ({e['sightings']} sightings in {len(e['jobs'])} "
                  f"jobs, last {e['last_seen']}; contradictions {len(e['contradictions'])})")
        return 0
    import pickle
    fj = json.load(open(os.path.join(a.fetch, "fetch.json")))
    target = pickle.load(open(os.path.join(a.fetch, "target.pkl"), "rb"))
    listed = [tuple(e["centre"]) for e in ent if e["status"] == "LISTED" and e["device"] == fj["backend"]]
    if a.cmd == "mask":
        if os.path.exists(a.out_fetch):
            raise SystemExit(f"STOP: {a.out_fetch} exists")
        t2, masked = mask_target(target, listed)
        os.makedirs(a.out_fetch)
        tp = os.path.join(a.out_fetch, "target.pkl")
        pickle.dump(t2, open(tp, "wb"))
        fj2 = dict(fj, target_sha256=KC.sha256_file(tp), masked_by_defect_list=dict(
            source_target_sha256=fj["target_sha256"], list=os.path.basename(a.list),
            list_sha256=KC.sha256_file(a.list), masked_couplers=[list(e) for e in masked],
            listed_paths=[list(p) for p in listed], min_repeats=a.min_repeats, expiry_days=a.expiry_days,
            now=a.now))
        json.dump(fj2, open(os.path.join(a.out_fetch, "fetch.json"), "w"), indent=1)
        print(f"{fj['backend']}: masked {len(masked)} coupler(s) {masked} from {len(listed)} listed path(s)")
        return 0
    res = place_avoiding(target, a.n, listed)
    if res is None:
        print(f"n {a.n}: no outline avoids the list")
        return 2
    m, name, cyc, skipped = res
    print(f"{fj['backend']} n {a.n}: outline {name} (m = {m}); passed over {len(skipped)} listed outline(s)")
    for s in skipped:
        print(f"  skipped {s['name']} (m {s['m']}): contains {s['hits']}")
    print("  ring: " + " ".join(map(str, cyc)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
