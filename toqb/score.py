"""Scores a run of the standard compilation set (records.jsonl) against the predictions of its pre-registration
(prereg/2026-10-08-standard-run-1.md). Writes score.md and score.json into the run's directory.

    python -m toqb.score --out DIR

Definitions (the pre-registration states them in words):
    usable(r)       no error, structurally valid, and not "not equivalent" (an unchecked output is usable)
    within(r, t)    usable and its time <= t x max(BUDGET_FLOOR_S, the reference's time)  (toqb.runner.within)
    Q_all(A)        geometric mean of (q2_A + 1) / (q2_ref + 1) over the pairs where A's and the reference's outputs
                    are both usable, whatever the time
    Q_t(A)          the same over the pairs where A returned within tier t
    family(case)    QASMBench | HamLib (abstract maps) | HamLib, FakeTorino | Feynman, FakeTorino
"""
from __future__ import annotations

import argparse
import json
import math
import os
import random

from toqb.runner import NOT_RUN, REFERENCE, TIERS, gmean, not_equivalent, within

EXPECTED = dict(n_pairs=126, adapters=["qiskit:2:target", "qiskit:1:target", "qiskit:3:target", "tket:2",
                                       "psf:default", "psf:recommended"],
                versions={"qiskit": "2.5.2", "pytket": "2.18.5", "pytket-qiskit": "0.78.0"},
                psf_release="2026-10-07.1", psf_zero_head="79b70ad", benchpress_head="b695f30",
                # the circuit breakers of amendment 1 (prereg/2026-10-09-standard-run-1-amendment.md)
                rules=dict(mem_cap_gb=3.0, b10_cap_s=600.0, warmup_grace_s=30.0, ref_limit_s=600.0, check_limit_s=60.0,
                           run_budget_h=10.0))
# errors that come from TOQB's TKET adapter (its conversion of the input or of the output), not from TKET
ADAPTER_ERRORS = ("unsupported by qiskit_to_tk", "TKET returned", "Invoked with types")
BOOT = 2000


def family(case):
    tid = case.split(":", 1)[1]
    if tid.startswith("test_QASMBench"):
        return "QASMBench"
    if tid.startswith("test_hamiltonians"):
        return "HamLib"
    if tid.startswith("test_hamlib_hamiltonians_transpile"):
        return "HamLib, FakeTorino"
    if tid.startswith("test_feynman_transpile"):
        return "Feynman, FakeTorino"
    return "other"


def usable(r):
    return "error" not in r and r.get("valid") is True and not not_equivalent(r)


def load(out):
    meta, recs, end = None, [], None
    with open(os.path.join(out, "records.jsonl"), encoding="utf-8") as fh:
        for ln in fh:
            x = json.loads(ln)
            if "meta" in x:
                meta = x["meta"]
            elif "end" in x:
                end = x["end"]
            else:
                recs.append(x)
    return meta, recs, end


def ratio_logs(recs, ref, adapter, tier=None):
    """{pair: log((q2_A + 1) / (q2_ref + 1))} over the pairs counted by Q_all (tier None) or Q_t."""
    out = {}
    for r in recs:
        if r["adapter"] != adapter:
            continue
        k = (r["case"], r["device"])
        q = ref.get(k)
        if q is None or not usable(q) or not usable(r):
            continue
        if tier is not None and not within(r, q["t_s"])[tier]:
            continue
        out[k] = math.log((r["q2"] + 1) / (q["q2"] + 1))
    return out


def boot_ci(logs, seed=0):
    xs = list(logs.values())
    if len(xs) < 2:
        return (float("nan"), float("nan"))
    rng = random.Random(seed)
    means = sorted(sum(rng.choice(xs) for _ in xs) / len(xs) for _ in range(BOOT))
    return (math.exp(means[int(0.025 * BOOT)]), math.exp(means[int(0.975 * BOOT) - 1]))


def verdict(value, confirm, refute):
    """confirm/refute: functions of the value. Neither = NOT DECIDED."""
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "NOT DECIDED"
    return "CONFIRMED" if confirm(value) else "REFUTED" if refute(value) else "NOT DECIDED"


def score(out):
    meta, recs, end = load(out)
    plan = meta["plan"]
    adapters = list(dict.fromkeys([REFERENCE] + plan["adapters"]))
    if "drawn" in plan:
        pairs = [(f"bp:{t}", f"bp:{t}") for t in plan["drawn"]]
    else:  # a plan without the standard sample (a smoke run): its own pairs; P0 then fails, as it should
        pairs = [(c, d) for c in plan.get("cases", []) for d in plan.get("devices", [])]
        pairs += [tuple(p) for p in plan.get("pairs", [])]
    ref = {(r["case"], r["device"]): r for r in recs if r["adapter"] == REFERENCE}
    by = {(r["adapter"], r["case"], r["device"]): r for r in recs}
    S = dict(meta=dict(start_utc=meta["start_utc"], end=end, cpus=meta["cpus"], par=meta["par"],
                       platform=meta["platform"], python=meta["python"], provenance=meta.get("provenance")))

    # P0: integrity
    prov = meta.get("provenance") or {}
    psf_versions = {r.get("adapter_version") for r in recs if r["adapter"].startswith("psf:") and "adapter_version" in r}
    checks = {
        "126 tests drawn from the committed seed": len(pairs) == EXPECTED["n_pairs"],
        "the six adapters": adapters == EXPECTED["adapters"],
        "one record per adapter and test": len(recs) == len(by) == len(adapters) * len(pairs)
        and all((a, c, d) in by for a in adapters for c, d in pairs),
        "run with --lock; no uncommitted change in TOQB, PSF-Zero or Benchpress": meta.get("lock") is True and all(
            (prov.get(n) or {}).get("dirty") == "" for n in ("toqb", "psf_zero", "benchpress")),
        "PSF-Zero release and head": psf_versions == {EXPECTED["psf_release"]}
        and str((prov.get("psf_zero") or {}).get("head", "")).startswith(EXPECTED["psf_zero_head"]),
        "Benchpress head": str((prov.get("benchpress") or {}).get("head", "")).startswith(EXPECTED["benchpress_head"]),
        "package versions": all((prov.get("versions") or {}).get(k) == v for k, v in EXPECTED["versions"].items()),
        "the circuit breakers of amendment 1": all(meta.get(k) == v for k, v in EXPECTED["rules"].items()),
        "the run is complete (not stopped by a STOP file or the run budget)": bool(end) and end.get("complete") is True,
    }
    S["P0"] = dict(checks=checks, verdict="PASS" if all(checks.values()) else "FAIL",
                   toqb_head=(prov.get("toqb") or {}).get("head"))

    # per adapter
    rows = {}
    for a in adapters:
        rs = [by[(a, c, d)] for c, d in pairs if (a, c, d) in by]
        rs_ref_ok = [r for r in rs if (r["case"], r["device"]) in ref and "t_s" in ref[(r["case"], r["device"])]]
        w = [within(r, ref[(r["case"], r["device"])]["t_s"]) for r in rs_ref_ok]
        logs_all = ratio_logs(recs, ref, a)
        torino = [r for r in rs if family(r["case"]).endswith("FakeTorino") and "error" not in r]
        d2 = [math.log((r["d2"] + 1) / (ref[(r["case"], r["device"])]["d2"] + 1)) for r in rs
              if (r["case"], r["device"]) in ref and usable(r) and usable(ref[(r["case"], r["device"])])]
        rows[a] = dict(
            pairs=len(rs),
            within={str(t): sum(x[t] for x in w) / len(w) if w else float("nan") for t in TIERS},
            q_all=math.exp(sum(logs_all.values()) / len(logs_all)) if logs_all else float("nan"),
            q_all_n=len(logs_all),
            q_all_ci=boot_ci(logs_all),
            q_tier={str(t): (lambda L: (math.exp(sum(L.values()) / len(L)) if L else float("nan"), len(L)))(
                ratio_logs(recs, ref, a, t)) for t in TIERS},
            d2_all=math.exp(sum(d2) / len(d2)) if d2 else float("nan"),
            invalid=sum(1 for r in rs if r.get("valid") is False),
            not_equivalent=sum(1 for r in rs if not_equivalent(r)),
            checked=sum(1 for r in rs if (r.get("equivalence") or {}).get("checked") is True),
            failed=sum(1 for r in rs if "error" in r and r["error"] != NOT_RUN),
            failed_time=sum(1 for r in rs if str(r.get("error", "")).startswith("time")),
            failed_memory=sum(1 for r in rs if str(r.get("error", "")).startswith("memory limit")),
            failed_adapter=sum(1 for r in rs if any(e in str(r.get("error", "")) for e in ADAPTER_ERRORS)),
            failed_harness=sum(1 for r in rs if str(r.get("error", "")).startswith("interrupted")),
            not_run=sum(1 for r in rs if r.get("error") == NOT_RUN),
            run_again=sum(1 for r in rs if r.get("run_again_after_interruption")),
            # amendment 1: outputs the cap at 10x (and 600 s) stopped; and, of those, on tests whose reference took
            # over 60 s, where the cap is below 10x the reference
            time_failures_where_ref_finished=sum(1 for r in rs_ref_ok if str(r.get("error", "")).startswith("time")),
            time_failures_ref_over_60s=sum(1 for r in rs_ref_ok if str(r.get("error", "")).startswith("time")
                                           and ref[(r["case"], r["device"])]["t_s"] > 60.0),
            peak_rss_mb_max=max([r["peak_rss_mb"] for r in rs if "peak_rss_mb" in r], default=None),
            failed_where_reference_finished=sum(1 for r in rs_ref_ok if "error" in r),
            reference_finished=len(rs_ref_ok),
            torino_tests=len(torino),
            torino_tests_on_failed=sum(1 for r in torino if (r.get("on_failed") or 0) > 0),
            trailing=sum((r.get("equivalence") or {}).get("trailing", 0) or 0 for r in rs),
            families={f: (lambda L: (math.exp(sum(L.values()) / len(L)) if L else float("nan"), len(L)))(
                {k: v for k, v in logs_all.items() if family(k[0]) == f})
                for f in ("QASMBench", "HamLib", "HamLib, FakeTorino", "Feynman, FakeTorino")},
            time_ratio_median=_median([r["t_s"] / ref[(r["case"], r["device"])]["t_s"] for r in rs_ref_ok
                                       if "t_s" in r and "error" not in r]),
        )
    S["adapters"] = rows

    # the common set: pairs every adapter returned within 10x
    common = [k for k in pairs if k in ref and "t_s" in ref[k]
              and all((a, *k) in by and within(by[(a, *k)], ref[k]["t_s"])[10.0] for a in adapters)]
    S["common_10x"] = dict(n=len(common), q={a: gmean((by[(a, *k)]["q2"] + 1) / (ref[k]["q2"] + 1) for k in common)
                                              if common else float("nan") for a in adapters})

    psf, rec, tk = rows["psf:default"], rows["psf:recommended"], rows["tket:2"]
    bad = {a: (rows[a]["invalid"], rows[a]["not_equivalent"]) for a in adapters}
    n_ref = psf["reference_finished"]
    fail_share = psf["failed_where_reference_finished"] / n_ref if n_ref else float("nan")
    # amendment 1: bounds on T3 and T6 under the pre-registration's own definitions, which measured further
    w10 = psf["within"]["10.0"]
    t3_high = w10 + psf["time_failures_ref_over_60s"] / n_ref if n_ref else float("nan")
    t6_low = (psf["failed_where_reference_finished"] - psf["time_failures_where_ref_finished"]) / n_ref \
        if n_ref else float("nan")

    def bounded(lo, hi, confirm, refute):
        a, b = verdict(lo, confirm, refute), verdict(hi, confirm, refute)
        return a if a == b else "NOT DECIDED (the cap of amendment 1)"
    S["predictions"] = {
        "T1": dict(text="every output of every compiler is valid, and every checked one is equivalent",
                   value=bad, verdict="CONFIRMED" if all(v == (0, 0) for v in bad.values()) else "REFUTED"),
        "T2": dict(text="psf:default Q_all <= 1.07 (REFUTED > 1.10)", value=psf["q_all"],
                   verdict=verdict(psf["q_all"], lambda v: v <= 1.07, lambda v: v > 1.10)),
        "T3": dict(text="psf:default within 10x >= 0.90 (REFUTED < 0.80); 10x at most 600 s (amendment 1)", value=w10,
                   bounds=(w10, t3_high),
                   verdict=bounded(w10, t3_high, lambda v: v >= 0.90, lambda v: v < 0.80)),
        "T4": dict(text="psf:recommended places no two-qubit gate on FakeTorino's failed elements",
                   value=(rec["torino_tests_on_failed"], rec["torino_tests"]),
                   verdict="CONFIRMED" if rec["torino_tests_on_failed"] == 0 and rec["torino_tests"] > 0
                   else "REFUTED" if rec["torino_tests_on_failed"] > 0 else "NOT DECIDED"),
        "T5": dict(text="tket:2 Q_all >= 1.05 (REFUTED < 1.00)", value=tk["q_all"],
                   verdict=verdict(tk["q_all"], lambda v: v >= 1.05, lambda v: v < 1.00)),
        "T6": dict(text="psf:default fails on <= 2% of the tests the reference finishes (REFUTED > 5%); stopped at "
                   "its largest budget (amendment 1)", value=fail_share, bounds=(t6_low, fail_share),
                   verdict=bounded(t6_low, fail_share, lambda v: v <= 0.02, lambda v: v > 0.05)),
    }
    return S


def _median(xs):
    xs = sorted(xs)
    if not xs:
        return float("nan")
    m = len(xs) // 2
    return xs[m] if len(xs) % 2 else (xs[m - 1] + xs[m]) / 2


def markdown(S):
    f = lambda x: "n/a" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:.3f}"  # noqa: E731
    L = ["# TOQB standard run 1: score", ""]
    m = S["meta"]
    L += [f"start {m['start_utc']} UTC; end {(m['end'] or {}).get('end_utc')} UTC; wall "
          f"{(m['end'] or {}).get('wall_s')} s; {m['cpus']} CPUs, {m['par']} at a time; {m['platform']}; "
          f"Python {m['python']}; TOQB head {S['P0']['toqb_head']}", ""]
    L += [f"**P0: {S['P0']['verdict']}**", ""] + [f"- {k}: {v}" for k, v in S["P0"]["checks"].items()] + [""]
    L += ["| ID | prediction | value | verdict |", "|---|---|---|---|"]
    for k, p in S["predictions"].items():
        v = p["value"]
        v = f(v) if isinstance(v, float) else json.dumps(v)
        if "bounds" in p:
            v += f" (under the pre-registration's own stopping: {f(p['bounds'][0])}-{f(p['bounds'][1])})"
        L.append(f"| {k} | {p['text']} | {v} | **{p['verdict']}** |")
    L += ["", "Reported without prediction:", "",
          "| adapter | within 1x | within 3x | within 10x | Q_all (95%) | n | Q_1x (n) | Q_3x (n) | Q_10x (n) | "
          "depth Q_all | time / ref (median) | invalid | not equiv. | checked | "
          "failed (time, memory, adapter, harness) | "
          "not run (no reference) | run again after an interruption | "
          "FakeTorino tests with gates on failed elements | trailing gates | peak memory (MB) |", "|" + "---|" * 20]
    for a, r in S["adapters"].items():
        lo, hi = r["q_all_ci"]
        qt = " | ".join(f"{f(r['q_tier'][str(t)][0])} ({r['q_tier'][str(t)][1]})" for t in TIERS)
        L.append(f"| {a} | " + " | ".join(f(r["within"][str(t)]) for t in TIERS)
                 + f" | {f(r['q_all'])} ({f(lo)}-{f(hi)}) | {r['q_all_n']} | {qt} | {f(r['d2_all'])} | "
                 f"{f(r['time_ratio_median'])} | {r['invalid']} | {r['not_equivalent']} | {r['checked']} | "
                 f"{r['failed']} ({r['failed_time']}, {r['failed_memory']}, {r['failed_adapter']}, "
                 f"{r['failed_harness']}) | {r['not_run']} | {r['run_again']} | "
                 f"{r['torino_tests_on_failed']} of {r['torino_tests']} | {r['trailing']} | {r['peak_rss_mb_max']} |")
    L += ["", "Q_all by family:", "", "| adapter | " + " | ".join(next(iter(S["adapters"].values()))["families"])
          + " |", "|---|---|---|---|---|"]
    for a, r in S["adapters"].items():
        L.append(f"| {a} | " + " | ".join(f"{f(q)} ({n})" for q, n in r["families"].values()) + " |")
    c = S["common_10x"]
    L += ["", f"On the {c['n']} tests every compiler returned within 10x: "
          + ", ".join(f"{a} {f(q)}" for a, q in c["q"].items())]
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    S = score(a.out)
    with open(os.path.join(a.out, "score.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(S, fh, indent=1, default=str)
        fh.write("\n")
    md = markdown(S)
    with open(os.path.join(a.out, "score.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(md)
    print(md)
    print("SUMMARY " + json.dumps({k: p["verdict"] for k, p in S["predictions"].items()} | {"P0": S["P0"]["verdict"]}))


if __name__ == "__main__":
    main()
