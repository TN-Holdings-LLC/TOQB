"""Scores TOQB standard run 2 (prereg/2026-10-10-standard-run-2.md): P0 and the table as toqb.score computes them,
with run 2's expected PSF-Zero release, and predictions S1-S5, one of them against run 1c's records. Writes
score.md and score.json into the run's directory.

    python -m toqb.score_run2 --out DIR
"""
from __future__ import annotations

import argparse
import json
import math
import os

from toqb import score as SC
from toqb.runner import BUDGET_FLOOR_S

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUN1C = os.path.join(ROOT, "results", "standard-run-1", "run-1c")
# run 2's PSF-Zero: fixed when the pre-registration is committed
EXPECTED2 = dict(psf_release="2026-10-10.2", psf_zero_head="0b7f790")
CORE57 = "0.1.0"  # the version of the package psf-zero-core57 the run must record
S3_CONFIRM, S3_REFUTE = 2.2, 2.53  # run 1c: 2.53 on 17 FakeTorino tests


def _key(r):
    return r["adapter"], r["case"], r["device"]


def score2(out, run1c=RUN1C):
    saved = dict(SC.EXPECTED)
    SC.EXPECTED.update(EXPECTED2)
    try:
        S = SC.score(out)
    finally:
        SC.EXPECTED.clear()
        SC.EXPECTED.update(saved)
    meta, recs, _ = SC.load(out)
    _, old, _ = SC.load(run1c)
    prov = meta.get("provenance") or {}
    if CORE57:
        S["P0"]["checks"]["psf-zero-core57 installed, at the version of the release"] = \
            (prov.get("versions") or {}).get("psf-zero-core57") == CORE57
        S["P0"]["verdict"] = "PASS" if all(S["P0"]["checks"].values()) else "FAIL"
    now, was = {_key(r): r for r in recs}, {_key(r): r for r in old}
    ref = {(r["case"], r["device"]): r for r in recs if r["adapter"] == SC.REFERENCE}
    rows = S["adapters"]
    bad = {a: (rows[a]["invalid"], rows[a]["not_equivalent"]) for a in rows}

    # S2: psf:default's two-qubit counts are run 1c's wherever both outputs are usable
    both = [k for k, r in now.items() if k[0] == "psf:default" and k in was and SC.usable(r) and SC.usable(was[k])]
    differ = [(k[1], was[k]["q2"], now[k]["q2"]) for k in both if was[k]["q2"] != now[k]["q2"]]

    # S3: psf:recommended's time against the reference on FakeTorino tests (geometric mean of t / max(floor, ref))
    tor = []
    for k, r in now.items():
        q = ref.get(k[1:])
        if (k[0] == "psf:recommended" and SC.family(k[1]).endswith("FakeTorino") and "error" not in r
                and q is not None and "t_s" in q):
            tor.append(r["t_s"] / max(BUDGET_FLOOR_S, q["t_s"]))
    g = math.exp(sum(math.log(x) for x in tor) / len(tor)) if tor else float("nan")

    rec, psf = rows["psf:recommended"], rows["psf:default"]
    n_ref = psf["reference_finished"]
    fail_share = psf["failed_where_reference_finished"] / n_ref if n_ref else float("nan")
    t6_low = (psf["failed_where_reference_finished"] - psf["time_failures_where_ref_finished"]) / n_ref \
        if n_ref else float("nan")
    a6, b6 = (SC.verdict(x, lambda v: v <= 0.02, lambda v: v > 0.05) for x in (t6_low, fail_share))
    S["predictions"] = {
        "S1": dict(text="every output of every compiler is valid (v13's structural check), and every checked one is "
                        "equivalent", value=bad,
                   verdict="CONFIRMED" if all(v == (0, 0) for v in bad.values()) else "REFUTED"),
        "S2": dict(text="psf:default's two-qubit count equals run 1c's on every test where both outputs are usable",
                   value=dict(tests=len(both), differ=differ[:20]),
                   verdict="CONFIRMED" if both and not differ else "REFUTED" if differ else "NOT DECIDED"),
        "S3": dict(text=f"psf:recommended on FakeTorino: geometric mean of its time / the reference's <= {S3_CONFIRM} "
                        f"(REFUTED >= {S3_REFUTE}, run 1c's value)", value=g, n=len(tor),
                   verdict=SC.verdict(g, lambda v: v <= S3_CONFIRM, lambda v: v >= S3_REFUTE)),
        "S4": dict(text="psf:recommended places no two-qubit gate on FakeTorino's failed elements",
                   value=(rec["torino_tests_on_failed"], rec["torino_tests"]),
                   verdict="CONFIRMED" if rec["torino_tests_on_failed"] == 0 and rec["torino_tests"] > 0
                   else "REFUTED" if rec["torino_tests_on_failed"] > 0 else "NOT DECIDED"),
        "S5": dict(text="psf:default fails on <= 2% of the tests the reference finishes (REFUTED > 5%)",
                   value=fail_share, bounds=(t6_low, fail_share),
                   verdict=a6 if a6 == b6 else "NOT DECIDED (the cap of amendment 1)"),
    }
    # reported: run 1c's rows beside run 2's
    S1c = json.load(open(os.path.join(run1c, "score.json"), encoding="utf-8"))
    S["run1c"] = {a: dict(within=r["within"], q_all=r["q_all"], time_ratio_median=r["time_ratio_median"],
                          failed=r["failed"]) for a, r in S1c["adapters"].items()}
    S["exit_codes"] = sorted({str(r.get("exit_code")) for r in recs if "error" in r})
    return S


def markdown2(S):
    f = lambda x: "n/a" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:.3f}"  # noqa: E731
    md = SC.markdown(S).replace("# TOQB standard run 1: score", "# TOQB standard run 2: score", 1)
    L = ["", "Beside run 1c (`results/standard-run-1/run-1c`):", "",
         "| adapter | within 1x (1c / 2) | within 3x (1c / 2) | within 10x (1c / 2) | Q_all (1c / 2) | "
         "time / ref, median (1c / 2) | failed (1c / 2) |", "|---|---|---|---|---|---|---|"]
    for a, r in S["adapters"].items():
        o = S["run1c"].get(a)
        if not o:
            continue
        w = " | ".join(f"{f(o['within'][t])} / {f(r['within'][t])}" for t in ("1.0", "3.0", "10.0"))
        L.append(f"| {a} | {w} | {f(o['q_all'])} / {f(r['q_all'])} | {f(o['time_ratio_median'])} / "
                 f"{f(r['time_ratio_median'])} | {o['failed']} / {r['failed']} |")
    L += ["", f"Exit codes of the failed measurements: {', '.join(S['exit_codes']) or 'none'}"]
    return md + "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    S = score2(a.out)
    with open(os.path.join(a.out, "score.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(S, fh, indent=1, default=str)
        fh.write("\n")
    md = markdown2(S)
    with open(os.path.join(a.out, "score.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(md)
    print(md)
    print("SUMMARY " + json.dumps({k: p["verdict"] for k, p in S["predictions"].items()} | {"P0": S["P0"]["verdict"]}))


if __name__ == "__main__":
    main()
