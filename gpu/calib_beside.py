"""Report only (owner 2026-11-06 06:28 CET: "報告する"): beside each arm of a built job, the day's worst CZ error and
worst readout error on the elements that arm uses, so that a verdict decided by one bad element can be seen as such.

Kept out of psf-os on purpose: psf-os reads and stores no quality number, and the placement does not change. This
script reads the backend's current Target (saved IBM account; VPN OFF, at the IBM step, right after the submit) and
writes CALIB_BESIDE.json next to the run. It never feeds anything back into a build or a score.

usage: python gpu/calib_beside.py RUNS_DIR OUT.json --backend ibm_fez        (at home, VPN OFF)
       python gpu/calib_beside.py RUNS_DIR OUT.json --fake FakeFez           (offline check)
Arms: records grouped by name with the role suffix (_floor, _mirror) removed; the sentinel is listed apart.
"""
import argparse
import datetime as dt
import glob
import json
import os
import statistics


def arms(runs):
    from qiskit import qpy
    out = {}
    for f in sorted(glob.glob(os.path.join(runs, "*.qpy"))):
        name = os.path.basename(f)[:-4]
        arm = name
        for suf in ("_floor", "_mirror"):
            if arm.endswith(suf):
                arm = arm[: -len(suf)]
        a = out.setdefault(arm, dict(records=[], pairs=set(), measured=set()))
        a["records"].append(name)
        with open(f, "rb") as fh:
            for c in qpy.load(fh):
                for ins in c.data:
                    qs = tuple(sorted(c.find_bit(q).index for q in ins.qubits))
                    if ins.operation.name == "cz":
                        a["pairs"].add(qs)
                    elif ins.operation.name == "measure":
                        a["measured"].add(qs[0])
    return out


def worst(target, gate, elems):
    vals = []
    for e in sorted(elems):
        p = None
        if gate in target.operation_names:
            p = target[gate].get(e) or target[gate].get(tuple(reversed(e)))
        vals.append((e, None if p is None else p.error))
    known = [(e, v) for e, v in vals if v is not None]
    if not known:
        return dict(worst=None, at=None, median=None, missing=len(vals))
    e, v = max(known, key=lambda kv: kv[1])
    return dict(worst=v, at=list(e), median=statistics.median(v for _, v in known), count=len(known),
                missing=len(vals) - len(known))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("runs")
    ap.add_argument("out")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--backend")
    g.add_argument("--fake")
    a = ap.parse_args()
    if os.path.exists(a.out):
        raise SystemExit(f"STOP: {a.out} exists")
    if a.backend:
        from qiskit_ibm_runtime import QiskitRuntimeService
        b = QiskitRuntimeService().backend(a.backend)
    else:
        from qiskit_ibm_runtime import fake_provider
        b = getattr(fake_provider, a.fake)()
    t = b.target
    rep = dict(note="report only; not used by any placement, build or verdict", backend=b.name,
               read=dt.datetime.now(dt.timezone.utc).isoformat(), fake=bool(a.fake), arms={})
    for arm, d in arms(a.runs).items():
        rep["arms"][arm] = dict(records=d["records"], cz=worst(t, "cz", d["pairs"]),
                                readout=worst(t, "measure", {(q,) for q in d["measured"]}))
        cz, ro = rep["arms"][arm]["cz"], rep["arms"][arm]["readout"]
        print(f"{arm:24} worst CZ {cz['worst']} at {cz['at']} (median {cz['median']})   "
              f"worst readout {ro['worst']} at {ro['at']} (median {ro['median']})")
    json.dump(rep, open(a.out, "w"), indent=1)


if __name__ == "__main__":
    main()
