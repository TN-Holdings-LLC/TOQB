"""Paper 7 tables, built from the committed records only (DRAFT; no number is typed by hand).

Inputs (all committed): results/practice-2026-11-04/run/scores.json and results/practice-fez-2026-11-04/run/scores.json
(practice), results/daily/<date>/<device>/run/scores.json (the daily record; job IDs from run/job/submission.json),
results/corr-2026-11-04 and results/corr-marrakesh-2026-11-04 (the declared floor-and-mirror correction),
results/twirl-explore-2026-11-05/<device>/run*/scores.json (the twirl exploration: not declared, marked so).

Outputs (notes/paper7/out/): tables.md and tables.tex with
  (a) the practice verdicts, (b) the daily record with retention and normalised error, (c) FX-A day to day,
  (d) the corrections compared.
Rules (notes/reporting/verdict_and_retention.md): the declared verdict first; retention R = M / M_exact and the
normalised error beside it on every row; R is not given when |M_exact| < 0.1 ("small answer"); no row is dropped.

usage: python notes/paper7/tables.py [OUT_DIR]
"""
from __future__ import annotations

import glob
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
FOOTNOTE = ("The declared criterion is an absolute difference; the same relative loss gives a larger difference when "
            "the exact answer is larger. R and the normalised error show the loss relative to the answer.")


def load(rel):
    with open(os.path.join(ROOT, rel)) as f:
        return json.load(f)


def job_of(run_dir):
    p = os.path.join(ROOT, run_dir, "job", "submission.json")
    if not os.path.exists(p):
        return None, None
    s = load(os.path.relpath(p, ROOT))
    return s.get("job_id"), s.get("backend")


def retention(M, Mx):
    if abs(Mx) < 0.1:
        return None, None
    return M / Mx, abs(M - Mx) / abs(Mx)


def fmt(x, nd=3, signed=False):
    if x is None:
        return "small answer"
    return f"{x:+.{nd}f}" if signed else f"{x:.{nd}f}"


def practice_rows():
    rows = []
    for rel, dev in (("results/practice-2026-11-04/run", None), ("results/practice-fez-2026-11-04/run", None)):
        sc = load(f"{rel}/scores.json")
        job, backend = job_of(rel)
        for name, p in sc["problems"].items():
            R, ne = retention(p["M"], p["M_exact"])
            rows.append(dict(source=rel, device=backend, job=job, problem=name, n=p["n"], reads=p["reads"],
                             agrees=p["agrees"], beats=p["beats"], M=p["M"], M_exact=p["M_exact"], diff=p["diff"],
                             two_se=p["two_se"], R=R, norm_error=ne, sentinel=sc.get("sentinel")))
    return rows


def daily_rows():
    rows = []
    for sc_path in sorted(glob.glob(os.path.join(ROOT, "results", "daily", "*", "*", "run", "scores.json"))):
        rel = os.path.relpath(os.path.dirname(sc_path), ROOT)
        date = rel.split(os.sep)[2]
        sc = load(os.path.relpath(sc_path, ROOT))
        job, backend = job_of(rel)
        for name, p in sc["problems"].items():
            R, ne = retention(p["M"], p["M_exact"])
            if name == "user" and len(sc["problems"]) == 1:
                # psf-os run2d's single-circuit form tags its one circuit "user"; on 2026-11-06 it was FX-A run
                # alone (results/daily/2026-11-06/README.md, answers_by_tag.json = {"user": answers["FX-A"]})
                name = "FX-A"
            rows.append(dict(date=date, device=backend, job=job, problem=name, n=p["n"], reads=p["reads"],
                             agrees=p["agrees"], beats=p["beats"], M=p["M"], M_exact=p["M_exact"], diff=p["diff"],
                             R=R, norm_error=ne, guessable=p.get("guessable"), cz_layers=p.get("cz_layers"),
                             decay_per_layer=p.get("decay_per_layer"), floor=p.get("floor_mean"),
                             sentinel=sc.get("sentinel")))
    # refusals are rows too ("no row is dropped"): <date>/<device>/<problem>_REFUSED_*.txt
    for txt in sorted(glob.glob(os.path.join(ROOT, "results", "daily", "*", "*", "*_REFUSED_*.txt"))):
        rel = os.path.relpath(txt, ROOT).split(os.sep)
        rows.append(dict(date=rel[2], device=rel[3], job=None, problem=rel[4].split("_REFUSED")[0], n=None,
                         reads="REFUSED", agrees="REFUSED", beats="-", M=None, M_exact=None, diff=None, R=None,
                         norm_error=None, guessable=None, cz_layers=None, decay_per_layer=None, floor=None,
                         sentinel=None))
    rows.sort(key=lambda r: (r["date"], r["device"], r["problem"]))
    return rows


def fxa_rows(prac, daily):
    out = [dict(date="2026-11-04 (practice)", **{k: r[k] for k in ("device", "job", "diff", "R", "agrees")})
           for r in prac if r["problem"] == "p4_b0.485_t12"]
    out += [dict(date=r["date"], **{k: r[k] for k in ("device", "job", "diff", "R", "agrees")})
            for r in daily if r["problem"] == "FX-A"]
    return out


def correction_rows():
    rows = []
    for rel, dev in (("results/corr-2026-11-04", "ibm_fez"), ("results/corr-marrakesh-2026-11-04", "ibm_marrakesh")):
        sc = load(f"{rel}/scores.json")
        job, backend = job_of(f"{rel}/V")
        for th in ("0.53", "0.3", "0.8"):
            c = sc[th]
            rows.append(dict(kind="declared (11-04)", device=backend or dev, job=job, problem=f"P6 theta_x {th}",
                             raw_mse=c["raw"]["mse"], corr_mse=c["corrected"]["mse"], ratio=c["corrected"]["ratio"],
                             verdict=c["corrected"]["verdict"], agrees=c["corrected"]["agrees"]))
    for sc_path in sorted(glob.glob(os.path.join(ROOT, "results", "twirl-explore-2026-11-05", "*", "run*", "scores.json"))):
        rel = os.path.relpath(os.path.dirname(sc_path), ROOT)
        sc = load(os.path.relpath(sc_path, ROOT))
        job, backend = job_of(rel)
        for prob, p in sc.items():
            if not isinstance(p, dict) or "raw" not in p:
                continue
            for arm in ("corr_raw", "corr_tw", "corr_btw"):
                if arm in p:
                    rows.append(dict(kind=f"exploratory, not declared (11-05, {os.path.basename(rel)})", device=backend,
                                     job=job, problem=f"{prob} {arm}", raw_mse=p["raw"]["mse"], corr_mse=p[arm]["mse"],
                                     ratio=p[arm]["mse"] / p["raw"]["mse"], verdict=None,
                                     agrees="AGREES" if abs(p[arm]["diff"]) <= 0.05 else "DIFFERS"))
    return rows


def md_table(head, rows):
    out = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


def tex_table(head, rows, caption):
    esc = lambda s: str(s).replace("_", r"\_").replace("%", r"\%")
    cols = "l" * len(head)
    body = "\n".join(" & ".join(esc(c) for c in r) + r" \\" for r in rows)
    # scaled down to the text width when wider (needs graphicx); never scaled up
    return (f"\\begin{{table}}[htbp]\\centering\\small\n\\caption{{{esc(caption)}}}\n"
            f"\\resizebox{{\\ifdim\\width>\\textwidth\\textwidth\\else\\width\\fi}}{{!}}{{\\begin{{tabular}}{{{cols}}}\\toprule\n"
            + " & ".join(esc(h) for h in head) + r" \\ \midrule" + "\n" + body
            + "\n\\bottomrule\\end{tabular}}\n\\end{table}")


def build(out_dir):
    prac, daily = practice_rows(), daily_rows()
    fxa, corr = fxa_rows(prac, daily), correction_rows()
    T = []
    head_a = ["device", "problem", "READS", "AGREES", "BEATS", "M - M_exact", "R", "norm. error", "job"]
    T.append(("(a) Practice problems, 2026-11-04 (declared; raw, no correction)", head_a,
              [[r["device"], r["problem"], r["reads"], r["agrees"], r["beats"], fmt(r["diff"], signed=True),
                fmt(r["R"]), fmt(r["norm_error"]), r["job"]] for r in prac]))
    head_b = ["date", "device", "problem", "AGREES", "BEATS", "M - M_exact", "R", "norm. error", "decay / CZ layer",
              "job"]
    T.append(("(b) Daily record (declared; raw, no correction)", head_b,
              [[r["date"], r["device"], r["problem"], r["agrees"], r["beats"], fmt(r["diff"], signed=True), fmt(r["R"]),
                fmt(r["norm_error"]), fmt(r["decay_per_layer"], 4) if r["decay_per_layer"] is not None else "-",
                r["job"]] if r["agrees"] != "REFUSED" else
               [r["date"], r["device"], r["problem"], "REFUSED", "-", "-", "-", "-", "-", "not run (no copy qualifies)"]
               for r in daily]))
    T.append(("(c) FX-A day to day (the same circuit as practice p4_b0.485_t12)", ["date", "device", "M - M_exact", "R",
              "AGREES", "job"],
              [[r["date"], r["device"], fmt(r["diff"], signed=True), fmt(r["R"]), r["agrees"], r["job"]] for r in fxa]))
    T.append(("(d) Corrections compared (declared 11-04; exploratory 11-05 marked so: corrected MSE over the qubits kept by rule R, raw over all; AGREES after computed here with the same 0.05)", ["kind", "device", "problem",
              "raw MSE", "corrected MSE", "ratio", "verdict", "AGREES after", "job"],
              [[r["kind"], r["device"], r["problem"], fmt(r["raw_mse"], 4), fmt(r["corr_mse"], 4), fmt(r["ratio"]),
                r["verdict"] or "not judged", r["agrees"], r["job"]] for r in corr]))
    os.makedirs(out_dir, exist_ok=True)
    md = ["# Paper 7 tables (generated by notes/paper7/tables.py from committed records; DRAFT)", ""]
    tex = ["% generated by notes/paper7/tables.py from committed records (DRAFT); do not edit by hand"]
    for cap, head, rows in T:
        md += [f"## {cap}", "", md_table(head, rows), "", f"*{FOOTNOTE}*", ""]
        tex += [tex_table(head, rows, cap + ". " + FOOTNOTE), ""]
    open(os.path.join(out_dir, "tables.md"), "w").write("\n".join(md))
    open(os.path.join(out_dir, "tables.tex"), "w").write("\n".join(tex))
    json.dump(dict(practice=prac, daily=daily, fxa=fxa, corrections=corr), open(os.path.join(out_dir, "tables.json"), "w"),
              indent=1)
    return {cap: len(rows) for cap, _, rows in T}


if __name__ == "__main__":
    print(build(sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "notes", "paper7", "out")))
