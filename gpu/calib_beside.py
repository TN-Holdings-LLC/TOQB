"""Report only (owner 2026-11-06 06:28 CET: "報告する"): beside each arm of a built job, the day's worst CZ error and
worst readout error on the elements that arm uses, so that a verdict decided by one bad element can be seen as such.

Kept out of psf-os on purpose: psf-os reads and stores no quality number, and the placement does not change. This
script reads the backend's current Target (saved IBM account; VPN OFF, at the IBM step, right after the submit) and
writes CALIB_BESIDE.json next to the run. It never feeds anything back into a build or a score.

usage: python gpu/calib_beside.py RUNS_DIR OUT.json --backend ibm_fez        (at home, VPN OFF, right after the submit)
       python gpu/calib_beside.py RUNS_DIR OUT.json --backend ibm_fez --job JOB_ID
                                       (at the result step: the properties at the time the job started running)
       python gpu/calib_beside.py RUNS_DIR OUT.json --fake FakeFez [--properties]   (offline check)

Workplace review 2026-11-06 (06m item 1), added:
  * missing_at: the elements an arm uses that the source does not report. The live Target of qiskit-ibm-runtime
    leaves out non-operational qubits and gates (convert_to_target, filter_faulty=True), so the worst element of the
    day can show up only as "missing"; it is now listed and printed, never silently dropped.
  * --job (and --properties for the offline check): read BackendProperties instead of the Target; they keep the
    non-operational elements, flagged in non_operational. With --job they are those at the time the job started
    running (RuntimeJobV2.properties), not at the submit; a queue can cross a calibration.
  * other_2q: two-qubit operations other than cz in the records (e.g. ecr, fractional rzz), listed so that a basis
    change cannot hide elements from the report.
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
        a = out.setdefault(arm, dict(records=[], pairs=set(), measured=set(), other_2q=set()))
        a["records"].append(name)
        with open(f, "rb") as fh:
            for c in qpy.load(fh):
                for ins in c.data:
                    qs = tuple(sorted(c.find_bit(q).index for q in ins.qubits))
                    if ins.operation.name == "cz":
                        a["pairs"].add(qs)
                    elif len(qs) == 2 and ins.operation.name not in ("barrier",):
                        a["other_2q"].add((ins.operation.name,) + qs)
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
    return _summary(vals)


def _summary(vals, non_operational=()):
    known = [(e, v) for e, v in vals if v is not None]
    miss = [list(e) for e, v in vals if v is None]
    if not known:
        return dict(worst=None, at=None, median=None, count=0, missing=len(miss), missing_at=miss,
                    non_operational=[list(e) for e in non_operational])
    e, v = max(known, key=lambda kv: kv[1])
    return dict(worst=v, at=list(e), median=statistics.median(v for _, v in known), count=len(known),
                missing=len(miss), missing_at=miss, non_operational=[list(e) for e in non_operational])


def worst_props(props, gate, elems):
    """The same summary from BackendProperties (kept non-operational elements are reported with their error and
    listed in non_operational)."""
    vals, nonop = [], []
    for e in sorted(elems):
        v = None
        if gate == "measure":
            try:
                v = props.readout_error(e[0])
                if not props.is_qubit_operational(e[0]):
                    nonop.append(e)
            except Exception:
                v = None
        else:
            for ee in (e, tuple(reversed(e))):
                try:
                    v = props.gate_error(gate, list(ee))
                    if not props.is_gate_operational(gate, list(ee)):
                        nonop.append(e)
                    break
                except Exception:
                    v = None
        vals.append((e, v))
    return _summary(vals, nonop)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("runs")
    ap.add_argument("out")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--backend")
    g.add_argument("--fake")
    ap.add_argument("--job", help="with --backend: read the properties at the time this job started running")
    ap.add_argument("--properties", action="store_true", help="with --fake: read BackendProperties, not the Target")
    a = ap.parse_args()
    if a.job and not a.backend:
        raise SystemExit("STOP: --job needs --backend")
    if os.path.exists(a.out):
        raise SystemExit(f"STOP: {a.out} exists")
    props = None
    if a.backend:
        from qiskit_ibm_runtime import QiskitRuntimeService
        svc = QiskitRuntimeService()
        b = svc.backend(a.backend)
        if a.job:
            props = svc.job(a.job).properties()
            if props is None:
                raise SystemExit("STOP: the job has no properties (not run yet?)")
    else:
        from qiskit_ibm_runtime import fake_provider
        b = getattr(fake_provider, a.fake)()
        if a.properties:
            props = b.properties()
    source = "properties" + (f" of job {a.job} (at its start)" if a.job else "") if props is not None else "target"
    rep = dict(note="report only; not used by any placement, build or verdict", backend=b.name,
               read=dt.datetime.now(dt.timezone.utc).isoformat(), fake=bool(a.fake), source=source,
               calibrated=str(props.last_update_date) if props is not None else None, arms={})
    for arm, d in arms(a.runs).items():
        meas = {(q,) for q in d["measured"]}
        if props is not None:
            cz, ro = worst_props(props, "cz", d["pairs"]), worst_props(props, "measure", meas)
        else:
            cz, ro = worst(b.target, "cz", d["pairs"]), worst(b.target, "measure", meas)
        rep["arms"][arm] = dict(records=d["records"], cz=cz, readout=ro,
                                other_2q=[list(x) for x in sorted(d["other_2q"])])
        print(f"{arm:24} worst CZ {cz['worst']} at {cz['at']} (median {cz['median']})   "
              f"worst readout {ro['worst']} at {ro['at']} (median {ro['median']})")
        for k, v in (("CZ", cz), ("readout", ro)):
            if v["missing"]:
                print(f"{'':24} WARNING {k}: {v['missing']} element(s) not reported by the {source} "
                      f"(non-operational on a live Target?): {v['missing_at']}")
            if v["non_operational"]:
                print(f"{'':24} WARNING {k}: non-operational: {v['non_operational']}")
        if d["other_2q"]:
            print(f"{'':24} WARNING two-qubit operations other than cz: {sorted(d['other_2q'])[:5]}")
    json.dump(rep, open(a.out, "w"), indent=1)


if __name__ == "__main__":
    main()
