"""Paper 8 tables, built from the committed records only (DRAFT; no number is typed by hand). Form of
notes/paper7/tables.py; the table list of notes/paper8/outline.md, plus table 8 (the light cone, home 2026-11-10).

  1  the dual-unitary chain at N = 51 / 71 / 91: device, placement rule, CZ at t = 24, READS, k - cos 2h per h,
     readable depth
  2  physics A (kicked Ising, fez 11-07, 4x4x3 and 4x2x2): the judged place, per theta and t (3D sites)
  3  physics B (Heisenberg XXX 4x2x2, fez 11-08): the judged place, per t
  4  CZ per layout and t: Heisenberg old / carry / line (heisE builds), Ising fold / line (isingL noiseless check)
  5  heisE (marrakesh, kingston 11-08): line against old per place and t; the declared retention difference and,
     after the fact, nMSE (= MSE / mean square of the exact values, from the same arms)
  6  Schwinger pair creation (marrakesh 11-09)
  7  the simulator against the device (fez 11-07 / 11-08 records; noise from that day's calibration, never fitted)
  8  the light cone (marrakesh 11-09, judged place): front per distance; K, background and shape TVD per t
  9  Ising line against fold at the same places (fez 11-10), nMSE as declared
 10  IBM's 2023 utility observables raw on the embedded Eagle graph (fez 11-10)

usage: python notes/paper8/tables.py [OUT_DIR]   (writes tables.md, tables.tex, tables.json)
"""
from __future__ import annotations

import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
FOOTNOTE = ("From the committed records named in each caption; raw device values, no mitigation; verdicts as declared "
            "before each run; after-the-fact numbers are marked so.")


def load(rel):
    with open(os.path.join(ROOT, rel)) as f:
        return json.load(f)


def job_of(run_dir):
    p = os.path.join(ROOT, run_dir, "job", "submission.json")
    if not os.path.exists(p):
        return None
    return load(os.path.relpath(p, ROOT)).get("job_id")


def f(x, nd=3, signed=False):
    if x is None:
        return "-"
    return f"{x:+.{nd}f}" if signed else f"{x:.{nd}f}"


def t1_dual_unitary():
    rows = []
    for n, rel in ((51, "results/du51-2026-11-07/ibm_kingston/run"), (71, "results/du71-2026-11-07/ibm_kingston/run"),
                   (91, "results/du91-2026-11-09/ibm_marrakesh/run")):
        sc, b = load(f"{rel}/scores.json"), load(f"{rel}/build.json")
        r = dict(n=n, device=b["device"], rule="C" if b["shape"] == "C" else f"shape {b['shape']}",
                 cz_t24=sc["points"]["h0.0_t24"]["cz"], reads=sc["reads"], mse=sc["mse"], msq=sc["mean_square_exact"],
                 jobs=[job_of(f"{rel}/{j}") for j in ("A", "B")], source=rel)
        for h in ("0.05", "0.1", "0.15"):
            x = sc["rate"][h]
            r[f"k_{h}"], r[f"d_{h}"], r[f"v_{h}"] = x.get("k"), x.get("diff"), x["verdict"]
        r["depth"] = sc["readable_depth"]
        rows.append(r)
    rel = "results/night-2026-11-10/du91r/ibm_fez"
    sc, b = load(f"{rel}/scores.json"), load(f"{rel}/build.json")
    r = dict(n=91, device=b["device"] + " (2nd run, ruler in both jobs)", rule="C" if b["shape"] == "C" else b["shape"],
             cz_t24=sc["points"]["A0_t24"]["cz"], reads=sc["reads"], mse=sc["mse"], msq=sc["mean_square_exact"],
             jobs=[job_of(f"{rel}/{j}") for j in ("A", "B")], source=rel)
    for h, key in (("0.05", "0.05"), ("0.1", "0.10"), ("0.15", "0.15")):
        x = sc["rate"][key]
        r[f"k_{h}"], r[f"d_{h}"], r[f"v_{h}"] = x.get("k"), x.get("diff"), x["verdict"]
    d = sc["readable_depth"]
    r["depth"] = {"0.0": d["A0"], "0.05": d["0.05"], "0.1": d["0.10"], "0.15": d["0.15"]}
    rows.append(r)
    head = ["N", "device", "placement", "CZ (t 24)", "READS (MSE / mean sq.)", "k - cos2h, h 0.05", "h 0.10", "h 0.15",
            "readable depth (h 0 / .05 / .10 / .15)"]
    body = [[r["n"], r["device"], r["rule"], r["cz_t24"], f"{r['reads']} ({f(r['mse'], 4)} / {f(r['msq'])})",
             f"{f(r['d_0.05'], 4, True)} {r['v_0.05']}", f"{f(r['d_0.1'], 4, True)} {r['v_0.1']}",
             f"{f(r['d_0.15'], 4, True)} {r['v_0.15']}",
             " / ".join(str(r["depth"][h]) for h in ("0.0", "0.05", "0.1", "0.15"))] for r in rows]
    return ("Table 1. The dual-unitary chain (arXiv 2411.00765) raw: N = 51, 71 (paper 7) and 91 twice "
            "(results/du51-2026-11-07, du71-2026-11-07, du91-2026-11-09, night-2026-11-10/du91r; in the second run each "
            "rate is against the ruler of its own job)", head, body, rows)


def t2_physA():
    rows = []
    for lat, rel in (("4x4x3", "results/os3d-physA-2026-11-07/j1_4x4x3"), ("4x2x2", "results/os3d-physA-2026-11-07/j2_4x2x2")):
        sc = load(f"{rel}/scores.json")
        for tag, a in sorted(sc["arms"].items(), key=lambda kv: (kv[1]["theta"], kv[1]["t"])):
            if a["candidate"] != sc["chosen"] or a["kind"] != "3D":
                continue
            rows.append(dict(lattice=lat, device=sc["device"], place=sc["chosen"], theta=a["theta"], t=a["t"], cz=a["cz"],
                             M=a["M"], M_exact=a["M_exact"], retention=a["retention"], norm_error=a["norm_error"],
                             reads=a["reads"], agrees=a["agrees"], beats=a["beats"], sentinel=sc["sentinel"]))
    head = ["lattice", "theta", "t", "CZ", "M", "M exact", "retention", "READS", "AGREES", "BEATS"]
    body = [[r["lattice"], r["theta"], r["t"], r["cz"], f(r["M"]), f(r["M_exact"]), f(r["retention"]), r["reads"],
             r["agrees"], r["beats"]] for r in rows]
    return ("Table 2. Physics A: kicked Ising on 3D lattices, ibm_fez 2026-11-07, the judged place (rule top), 3D "
            "sites (results/os3d-physA-2026-11-07)", head, body, rows)


def t3_heisB():
    rel = "results/os3d-heisB-2026-11-08/fez"
    sc = load(f"{rel}/scores.json")
    rows = [dict(t=a["t"], cz=a["cz"], m_s=a["m_s"], m_s_exact=a["m_s_exact"], retention=a["retention"],
                 nmse=a["mse"] / a["mean_square_exact"], reads=a["reads"], agrees=a["agrees"])
            for a in sorted(sc["arms"].values(), key=lambda a: a["t"]) if a["candidate"] == sc["chosen"]]
    head = ["t", "CZ", "m_s", "m_s exact", "retention", "nMSE (after the fact)", "READS", "AGREES"]
    body = [[r["t"], r["cz"], f(r["m_s"]), f(r["m_s_exact"]), f(r["retention"]), f(r["nmse"]), r["reads"], r["agrees"]]
            for r in rows]
    return (f"Table 3. Physics B: Heisenberg XXX 4x2x2, {sc['device']} 2026-11-08, the judged place {sc['chosen']} "
            f"({rel})", head, body, rows)


def t4_cz():
    rows = []
    sc = load("results/os3d-heisE-2026-11-08/marrakesh/scores.json")
    cz = {}
    for a in sc["arms"].values():
        if a["candidate"] == sc["chosen"]:
            cz[(a["variant"], a["t"])] = a["cz"]
    for v in ("old", "carry", "line"):
        rows.append(dict(model="Heisenberg 4x2x2", layout=v, cz=[cz.get((v, t)) for t in (1, 2, 3, 4)]))
    r = load("notes/isingL_noiseless_2026-11-10/report.json")
    for lat in ((4, 2, 2), (4, 3, 2)):
        for lay in ("fold", "line"):
            c = {a["t"]: a["cz"] for a in r["arms"].values()
                 if tuple(a["lattice"]) == lat and a["layout"] == lay and a["candidate"] == 0}
            rows.append(dict(model=f"Ising {'x'.join(map(str, lat))}", layout=lay, cz=[c.get(t) for t in (1, 2, 3, 4)]))
    head = ["model", "layout", "CZ t 1", "t 2", "t 3", "t 4"]
    body = [[r["model"], r["layout"]] + [x if x is not None else "-" for x in r["cz"]] for r in rows]
    return ("Table 4. CZ per layout and t (Heisenberg: heisE marrakesh build, judged place; Ising: the isingL build "
            "of the noiseless check, place 0; notes/isingL_noiseless_2026-11-10)", head, body, rows)


def t5_heisE():
    rows = []
    for dev, rel in (("ibm_marrakesh", "results/os3d-heisE-2026-11-08/marrakesh"),
                     ("ibm_kingston", "results/os3d-heisE-kingston-2026-11-08/kingston")):
        sc = load(f"{rel}/scores.json")
        arm = {(a["variant"], a["candidate"], a["t"]): a for a in sc["arms"].values()}
        for k, c in sorted(sc["comparison"].items(), key=lambda kv: (kv[1]["candidate"], kv[1]["t"])):
            if c["variant"] != "line":
                continue
            o, l = arm[("old", c["candidate"], c["t"])], arm[("line", c["candidate"], c["t"])]
            rows.append(dict(device=dev, place=c["candidate"], judged=c["judged"], t=c["t"], cz_old=c["cz_old"],
                             cz_line=c["cz_new"], diff=c["new_minus_old"], bound=c["bound"], resolved=c["resolved"],
                             nmse_old=o["mse"] / o["mean_square_exact"], nmse_line=l["mse"] / l["mean_square_exact"]))
    head = ["device", "place", "t", "CZ old / line", "retention line - old (declared)", "resolved", "nMSE old",
            "nMSE line (after the fact)"]
    body = [[r["device"], f"{r['place']}{' (judged)' if r['judged'] else ''}", r["t"], f"{r['cz_old']} / {r['cz_line']}",
             f(r["diff"], 3, True), "yes" if r["resolved"] else "no", f(r["nmse_old"]), f(r["nmse_line"])] for r in rows]
    return ("Table 5. Heisenberg layouts on the same places: line against old (results/os3d-heisE-2026-11-08, "
            "os3d-heisE-kingston-2026-11-08); the declared measure was the retention difference, nMSE is after the "
            "fact (notes/reporting/layout_comparison_metric.md)", head, body, rows)


def t6_schwinger():
    sc = load("results/schw-2026-11-09/ibm_marrakesh/scores.json")
    rows = [dict(tag=t, **{k: v for k, v in r.items() if k != "sentinel"}) for t, r in sc["items"].items()]
    head = ["N", "set", "steps", "CZ", "nMSE", "READS", "BEATS", "nu / exact", "nu", "Sum Z (exact 0)"]
    body = [[r["n"], r["params"], r["steps"], r["cz"], f(r["nmse"]), r["reads"], r["beats"],
             f"{f(r['nu'])} / {f(r['nu_exact'])}", r["nu_agrees"], f(r["charge"], 3, True)] for r in rows]
    return (f"Table 6. Schwinger pair creation from the bare vacuum, {sc['device']} 2026-11-09, sentinel "
            f"{sc['sentinel']} (results/schw-2026-11-09)", head, body, rows)


def t7_simulator():
    rows = []
    for model, rel in (("Heisenberg B", "notes/simproto_2026-11-08/pod_out/out/heisB_props_compare.json"),
                       ("Ising A 4x2x2", "notes/simproto_2026-11-08/pod_out/out/isingA_props_compare.json")):
        d = load(rel)
        for r in d["rows"]:
            rows.append(dict(model=model, arm=r["arm"], cz=r["cz"], exact=r["exact"], device=r["device"], sim=r["sim"],
                             sim_se=r["sim_se"], ratio=r["ratio"]))
    head = ["model", "arm", "CZ", "exact", "device", "simulator (+- SE)", "simulator / device retention"]
    body = [[r["model"], r["arm"], r["cz"], f(r["exact"]), f(r["device"]), f"{f(r['sim'])} +- {f(r['sim_se'])}",
             f(r["ratio"])] for r in rows]
    return ("Table 7. The simulator (notes/os3d_sim_2026-11-07/realsim.py --expect; noise from the device's "
            "calibration of that day, never fitted) against the device (notes/simproto_2026-11-08)", head, body, rows)


def t8_light_cone():
    sc = load("results/lc3d-2026-11-09/ibm_marrakesh/scores.json")
    c = sc["candidates"][str(sc["chosen"])]
    fr = [dict(d=int(d), **v) for d, v in sorted(c["front"].items(), key=lambda kv: int(kv[0]))]
    rows = [dict(t=int(t), cz=v["cz"], K=v["K"], background=v["background_total"], tvd=v["tvd"])
            for t, v in sorted(c["rows"].items(), key=lambda kv: int(kv[0]))]
    head = ["t", "CZ", "excitation kept K", "background flips", "shape TVD"]
    body = [[r["t"], r["cz"], f(r["K"]), f(r["background"]), f(r["tvd"])] for r in rows]
    fronts = "; ".join(f"d {x['d']}: exact t {x['exact_arrival']}, measured {x["measured_arrival"] if x["measured_arrival"] is not None else "none"} ({x['verdict']})"
                       for x in fr)
    return (f"Table 8. The light cone of one flipped spin, 4x2x2 XXX, {sc['device']} 2026-11-09, judged place "
            f"{sc['chosen']}; fronts: {fronts} (results/lc3d-2026-11-09)", head, body, dict(rows=rows, fronts=fr))


def t9_isingL():
    rel = "results/night-2026-11-10/isingL/ibm_fez"
    sc = load(f"{rel}/scores.json")
    rows = []
    for lat, r in sc["lattices"].items():
        for k, c in sorted(r["comparison"].items(), key=lambda kv: (kv[1]["candidate"], kv[1]["t"])):
            rows.append(dict(lattice=lat, place=c["candidate"], judged=c["judged"], t=c["t"], cz_fold=c["cz_fold"],
                             cz_line=c["cz_line"], nmse_fold=c["nmse_fold"], nmse_line=c["nmse_line"],
                             d=c["line_minus_fold"], bound=c["bound"], resolved=c["resolved"]))
    head = ["lattice", "place", "t", "CZ fold / line", "nMSE fold", "nMSE line", "line - fold", "resolved"]
    body = [[r["lattice"], f"{r['place']}{' (judged)' if r['judged'] else ''}", r["t"], f"{r['cz_fold']} / {r['cz_line']}",
             f(r["nmse_fold"], 4), f(r["nmse_line"], 4), f(r["d"], 4, True), "yes" if r["resolved"] else "no"] for r in rows]
    return (f"Table 9. Ising (theta 0.6): the line layout against the fold at the same places, {sc['device']} 2026-11-10; "
            "main measure nMSE as declared (results/night-2026-11-10/isingL)", head, body, rows)


def t10_utility():
    sc = load("results/utility-2026-11-10/ibm_fez/scores.json")
    names = {"z106_t4": "Z_106, 4 steps (Fig. 2)", "w10_t5": "weight-10, 5 steps (Fig. 3)",
             "w17_t5": "weight-17, 5 steps (Fig. 3)", "w17b_t5x": "Fig. 4a product, 5 steps + R_X"}
    rows = []
    for key, r in sc["observables"].items():
        end = r["points"][-1]
        rows.append(dict(observable=names[key], embedding=r["embedding"], cz=r["cz"], reads=r["reads"], mse=r["mse"],
                         msq=r["mean_square_exact"], agrees=r["agrees"], z_pi2=end["z"], e_pi2=end["exact"],
                         floor=r["floor"], mirror=r["mirror"]))
    head = ["observable", "embedding", "CZ", "verdict (MSE / mean sq.)", "AGREES of 17", "theta_h = pi/2: raw / exact",
            "floor / mirror parity"]
    body = [[r["observable"], r["embedding"], r["cz"], f"{r['reads']} ({f(r['mse'], 4)} / {f(r['msq'], 4)})", r["agrees"],
             f"{f(r['z_pi2'], 2, True)} / {f(r['e_pi2'], 2, True)}", f"{f(r['floor'])} / {f(r['mirror'])}"] for r in rows]
    return (f"Table 10. IBM's 2023 utility observables (Kim et al. 2023) on the Eagle graph embedded in {sc['device']}, "
            "2026-11-10, raw, 4000 shots, 17 values of theta_h; sentinel " + sc["sentinel"] + " (results/utility-2026-11-10)",
            head, body, rows)


def md_table(head, rows):
    out = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


def tex_table(head, rows, caption):
    esc = lambda s: str(s).replace("_", r"\_").replace("%", r"\%")
    cols = "l" * len(head)
    body = "\n".join(" & ".join(esc(c) for c in r) + r" \\" for r in rows)
    return (f"\\begin{{table}}[htbp]\\centering\\small\n\\caption{{{esc(caption)}}}\n"
            f"\\resizebox{{\\ifdim\\width>\\textwidth\\textwidth\\else\\width\\fi}}{{!}}{{\\begin{{tabular}}{{{cols}}}\\toprule\n"
            + " & ".join(esc(h) for h in head) + r" \\ \midrule" + "\n" + body
            + "\n\\bottomrule\\end{tabular}}\n\\end{table}")


def build(out_dir):
    T = [t1_dual_unitary(), t2_physA(), t3_heisB(), t4_cz(), t5_heisE(), t6_schwinger(), t7_simulator(), t8_light_cone(),
         t9_isingL(), t10_utility()]
    os.makedirs(out_dir, exist_ok=True)
    md = ["# Paper 8 tables (generated by notes/paper8/tables.py from committed records; DRAFT)", ""]
    tex = ["% generated by notes/paper8/tables.py from committed records (DRAFT); do not edit by hand"]
    js = {}
    for cap, head, rows, data in T:
        md += [f"## {cap}", "", md_table(head, rows), "", f"*{FOOTNOTE}*", ""]
        tex += [tex_table(head, rows, cap + ". " + FOOTNOTE), ""]
        js[cap.split(".")[0]] = data
    open(os.path.join(out_dir, "tables.md"), "w").write("\n".join(md))
    open(os.path.join(out_dir, "tables.tex"), "w").write("\n".join(tex))
    json.dump(js, open(os.path.join(out_dir, "tables.json"), "w"), indent=1)
    return {cap.split(".")[0]: len(rows) for cap, _, rows, _ in T}


if __name__ == "__main__":
    print(build(sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "notes", "paper8", "out")))
