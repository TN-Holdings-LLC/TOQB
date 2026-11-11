"""Boundary table: how far the raw (unmitigated) device records read, across problems, built only from committed
records (the 24 results in reproduce.py RESULTS; papers 7, 8, 9). No numbers are typed by hand. Circuit files
(.qpy, .qpy.gz) are not opened.

One row = one judged unit (one observable, size and step count; dual-unitary chains per h; IBM 2023 per observable).

usage (from the TOQB root):  python notes/boundary_2026-11-11/boundary.py
writes notes/boundary_2026-11-11/boundary.md, boundary.json (and boundary.png if matplotlib is present)
"""
import importlib.util
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))


def load(p):
    with open(os.path.join(ROOT, p)) as f:
        return json.load(f)


def results():
    spec = importlib.util.spec_from_file_location("reproduce", os.path.join(ROOT, "reproduce.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m.RESULTS


def ratio(mse, msq):
    return None if mse is None or not msq else mse / msq


def row(result, unit, qubits, cz, verdict, vpath, common=None, layers=None, mirror=None, floor=None,
        cone_q=None, cone_cz=None, src="", note=""):
    """vpath: the key path inside the scores file where the verdict is read (for the check)."""
    return {"result": result, "unit": unit, "qubits": qubits, "cz": cz,
            "cz_per_qubit": None if not (cz and qubits) else cz / qubits, "cz_layers": layers,
            "verdict": verdict, "verdict_path": vpath, "common": common, "mirror": mirror, "floor": floor,
            "cone_qubits": cone_q, "cone_cz": cone_cz, "source": src, "note": note}


def get(obj, path):
    for k in path:
        obj = obj[k]
    return obj


# ---- one reader per scores shape -------------------------------------------------------------------------------

def r_p6(name, res, s, sp):
    out = []
    for ang in ("0.3", "0.53", "0.8"):
        f = s[ang]["full"]
        q = max(r["n"] for r in f["rows"].values())
        steps = max(int(k) for k in f["rows"])
        v = f"{f['reads']}, {f['agrees']}"
        out.append(row(name, f"angle {ang}, steps 1-{steps}", q, None, v, [[ang, "full", "reads"], [ang, "full", "agrees"]],
                       common=ratio(f["mse"], f["mean_square_answer"]), src=sp,
                       note="CZ per circuit not in scores/report (build.json counts per cell, not per unit)"))
    return out


def r_corr(name, res, s, sp):
    out = []
    for ang in ("0.3", "0.53", "0.8"):
        a = s[ang]
        steps = max(int(k) for k in a["raw"]["diffs"])
        v = f"raw {a['raw']['reads']}; corrected {a['corrected']['agrees']}"
        out.append(row(name, f"angle {ang}, steps 1-{steps}", len(a["gate_rate_per_qubit"]), None, v,
                       [[ang, "raw", "reads"], [ang, "corrected", "agrees"]], src=sp,
                       note="common measure: no mean square of the exact values in scores; CZ per circuit not in scores/report"))
    return out


def r_os2d(name, res, s, sp):
    p = s["P6"]
    steps = max(int(k) for k in p["rows"])
    return [row(name, f"P6, steps 1-{steps}", len(s["floor"]), None, f"{p['reads']}, {p['agrees']}",
                [["P6", "reads"], ["P6", "agrees"]], common=ratio(p["mse"], p["mean_square_answer"]), src=sp,
                note="CZ per circuit not in scores/report")]


def r_run2d(name, res, s, sp):
    rep_p = os.path.join(os.path.dirname(sp), "report.json")
    rep = load(rep_p)
    out = []
    for tag, p in s["problems"].items():
        it = rep["items"].get(tag, {}) if "items" in rep else {"cz": rep.get("cz")}  # single-problem runs
        out.append(row(name, tag, p["n"], it.get("cz"), f"{p['reads']}, {p['agrees']}, {p['beats']}",
                       [["problems", tag, "reads"], ["problems", tag, "agrees"], ["problems", tag, "beats"]],
                       common=ratio(p["mse"], p["mean_square_answer"]), mirror=p.get("mirror_mean"),
                       floor=p.get("floor_mean"), src=sp))
    return out


def r_du(name, res, s, sp):
    n = int(re.search(r"du(\d+)", name).group(1))
    groups = {}
    for k, p in s["points"].items():
        h, t = k.rsplit("_t", 1)
        groups.setdefault(h[1:] if h.startswith("h") else h, []).append((int(t), p))
    out = []
    for h, pts in groups.items():
        pts.sort(key=lambda x: x[0])
        tmax, last = pts[-1]
        mse = sum((p["on"] - p["exact"]) ** 2 for _, p in pts) / len(pts)
        msq = sum(p["exact"] ** 2 for _, p in pts) / len(pts)
        rk = next((k for k in s["rate"] if float(k) == float(h)), None) if re.match(r"^[\d.]+$", h) else None
        depth = s["readable_depth"].get(h, next((v for k, v in s["readable_depth"].items()
                                                  if re.match(r"^[\d.]+$", k) and re.match(r"^[\d.]+$", h)
                                                  and float(k) == float(h)), None))
        dk = next((k for k in s["readable_depth"] if k == h or (re.match(r"^[\d.]+$", k) and re.match(r"^[\d.]+$", h)
                                                               and float(k) == float(h))), None)
        if rk is not None:
            v, vp = f"rate {s['rate'][rk]['verdict']}; readable depth {depth}", [["rate", rk, "verdict"], ["readable_depth", dk]]
        else:
            v, vp = f"{s['reads']} (all h); readable depth {depth}", [["reads"], ["readable_depth", dk]]
        out.append(row(name, f"N {n}, h {h}, t 4-{tmax}", n, last["cz"], v, vp, common=mse / msq if msq else None,
                       mirror=last["mirror_mean"], floor=last["floor_mean"], src=sp,
                       note="common measure over this h's points (after the fact; the declared READS is over all h); "
                            "CZ, mirror, floor at the deepest t"))
    return out


def r_phys(name, res, s, sp):
    out = []
    ch = s["chosen"]
    for key, j in s["judged"].items():
        for kind, arm in (("3D", f"g3d{ch}_{key}"), ("2D", f"hex_{key}")):
            a = s["arms"].get(arm)
            if a is None:
                continue
            jj = j[kind]
            out.append(row(name, f"{arm} ({kind}, place {ch if kind == '3D' else '-'})", a["n"], a["cz"],
                           f"{jj['reads']}, {jj['agrees']}, {jj['beats']}",
                           [["judged", key, kind, "reads"], ["judged", key, kind, "agrees"], ["judged", key, kind, "beats"]],
                           common=ratio(a["mse"], a["mean_square_answer"]), layers=a.get("cz_layers"),
                           mirror=a.get("mirror_mean"), floor=a.get("floor_mean"), src=sp))
    return out


def r_arms(name, res, s, sp, chosen_of):
    rep = load(os.path.join(os.path.dirname(sp), "report.json"))
    out = []
    for arm, a in s["arms"].items():
        if a["candidate"] != chosen_of(a):
            continue
        ra = rep["arms"].get(arm, {})
        q = a.get("used") or len(ra.get("mapping", {})) or None
        lay = a.get("cz_layers", ra.get("cz_layers"))
        lab = f"{arm} (place {a['candidate']}" + (f", {a['variant']}" if a.get("variant") else "") + \
              (f", {a['layout']}" if a.get("layout") else "") + ")"
        out.append(row(name, lab, q, a["cz"], f"{a['reads']}, {a['agrees']}",
                       [["arms", arm, "reads"], ["arms", arm, "agrees"]],
                       common=ratio(a["mse"], a["mean_square_exact"]), layers=lay, mirror=a.get("mirror_mean"),
                       floor=a.get("floor_mean"), src=sp))
    return out


def r_heis(name, res, s, sp):
    return r_arms(name, res, s, sp, lambda a: s["chosen"])


def r_ising(name, res, s, sp):
    return r_arms(name, res, s, sp, lambda a: s["lattices"]["x".join(map(str, a["lattice"]))]["chosen"])


def r_schw(name, res, s, sp):
    out = []
    for tag, it in s["items"].items():
        out.append(row(name, tag, it["n"], it["cz"], f"{it['reads']}, {it['beats']}, nu {it['nu_agrees']}",
                       [["items", tag, "reads"], ["items", tag, "beats"], ["items", tag, "nu_agrees"]],
                       common=ratio(it["mse"], it["mean_square_exact"]), mirror=it.get("mirror_mean"),
                       floor=it.get("floor_mean"), src=sp))
    return out


def r_lc(name, res, s, sp):
    rep = load(os.path.join(os.path.dirname(sp), "report.json"))
    ch = str(s["chosen"])
    c = s["candidates"][ch]
    out = []
    for t, r in c["rows"].items():
        arm = rep["arms"].get(f"lc{ch}_t{t}", {})
        words = [d["agrees"] for d in r["d"].values()]
        out.append(row(name, f"place {ch}, t {t}", len(arm.get("mapping", {})) or None, r["cz"],
                       f"{words.count('AGREES')} of {len(words)} distances AGREE (d 0-{len(words) - 1}: {'/'.join(words)})",
                       [["candidates", ch, "rows", t, "d", d, "agrees"] for d in r["d"]],
                       layers=arm.get("cz_layers"), mirror=r.get("mirror_flip"), src=sp,
                       note="common measure: no mean square of the exact values in scores; mirror = mirror_flip"))
    return out


def r_util(name, res, s, sp):
    rep = load(os.path.join(os.path.dirname(sp), "report.json"))
    out = []
    for ob, o in s["observables"].items():
        r = rep["observables"][ob]
        out.append(row(name, ob, None, o["cz"], f"{o['reads']}, AGREES {o['agrees']} of {len(o['points'])}",
                       [["observables", ob, "reads"], ["observables", ob, "agrees"]],
                       common=ratio(o["mse"], o["mean_square_exact"]), mirror=o.get("mirror"), floor=o.get("floor"),
                       cone_q=r.get("cone_qubits"), src=sp,
                       note="CZ = cz in scores (= report cz_per_circuit, the whole circuit: Eagle's graph embedded, gates on "
                            "failed elements outside the cone left out); the circuit's qubit count and the CZ inside the "
                            "light cone are not in scores/report, so qubits, CZ/qubit and cone CZ are empty"))
    return out


READER = [("p6-", r_p6), ("corr-", r_corr), ("os2d-", r_os2d), ("practice-", r_run2d), ("daily-", r_run2d),
          ("du", r_du), ("physA-", r_phys), ("heis", r_heis), ("schw-", r_schw), ("lc3d-", r_lc),
          ("isingL-", r_ising), ("utility-", r_util)]


# ---- checks --------------------------------------------------------------------------------------------------------

def check_verdicts(rows):
    """Check 2: every verdict word in the row is read again from its scores.json at the stored path."""
    bad = []
    for r in rows:
        s = load(r["source"])
        vals = [str(get(s, p)) for p in r["verdict_path"]]
        # in order: each value must appear after the previous one; repeated words (distances) as one joined string
        pos, ok = 0, True
        if "/".join(vals) in r["verdict"]:
            continue
        for v in vals:
            i = r["verdict"].find(v, pos)
            ok, pos = ok and i >= 0, (i + len(v) if i >= 0 else pos)
        if not ok:
            bad.append((r["result"], r["unit"], r["verdict_path"], vals))
    return bad


def check_paper8(rows):
    """Check 3: CZ of the same row in notes/paper8/out/tables.json."""
    t = load("notes/paper8/out/tables.json")
    by = {(r["result"], r["unit"].split(" ")[0]): r for r in rows}
    pairs = []  # (table, description, table cz, our cz)
    dev = {"ibm_kingston": "kingston", "ibm_marrakesh": "marrakesh", "ibm_fez": "fez"}
    for x in t["Table 1"]:
        src = x["source"]
        ours = [r for r in rows if src.startswith(os.path.dirname(r["source"])) or os.path.dirname(r["source"]).startswith(src)]
        cz = max((r["cz"] for r in ours if r["cz"]), default=None)
        pairs.append(("Table 1", f"N {x['n']} {x['device']}", x["cz_t24"], cz))
    for x in t["Table 2"]:
        name = f"physA-{x['lattice']}-fez-2026-11-07"
        th = f"th{round(x['theta'] * 10):02d}" if x["theta"] < 1 else None
        cand = [r for r in rows if r["result"] == name and r["unit"].startswith(f"g3d{x['place']}_")
                and r["unit"].split(" ")[0].endswith(f"_t{x['t']}")]
        cz = {r["cz"] for r in cand}
        pairs.append(("Table 2", f"{x['lattice']} place {x['place']} t {x['t']}", x["cz"], cz.pop() if len(cz) == 1 else sorted(cz)))
    for x in t["Table 3"]:
        r = by.get(("heisB-fez-2026-11-08", f"h3d0_t{x['t']}"))
        pairs.append(("Table 3", f"heisB t {x['t']}", x["cz"], r and r["cz"]))
    for x in t["Table 6"]:
        r = by.get(("schw-marrakesh-2026-11-09", x["tag"]))
        pairs.append(("Table 6", x["tag"], x["cz"], r and r["cz"]))
    for x in t["Table 8"]["rows"]:
        r = [y for y in rows if y["result"] == "lc3d-marrakesh-2026-11-09" and y["unit"].endswith(f"t {x['t']}")]
        pairs.append(("Table 8", f"lc3d t {x['t']}", x["cz"], r[0]["cz"] if r else None))
    for x in t["Table 9"]:
        if not x["judged"]:
            continue
        lat = "22" if x["lattice"] == "4x2x2" else "32"
        for lay, key in (("f", "cz_fold"), ("l", "cz_line")):
            r = by.get(("isingL-fez-2026-11-10", f"q{lat}{lay}{x['place']}_t{x['t']}"))
            pairs.append(("Table 9", f"{x['lattice']} {key} place {x['place']} t {x['t']}", x[key], r and r["cz"]))
    return pairs


# ---- output --------------------------------------------------------------------------------------------------------

def fmt(x, nd=3):
    if x is None:
        return ""
    if isinstance(x, float):
        # below 0.1 in exponent form, so that no number with 4 decimals appears (seal.py leakcheck)
        return f"{x:.2e}" if (x != 0 and abs(x) < 0.1) else f"{x:.{nd}g}"
    return str(x)


def main():
    R = results()
    rows, skipped = [], []
    for name, v in R.items():
        sp = os.path.join(v[0], v[3]).replace("\\", "/")
        rd = next((f for p, f in READER if name.startswith(p)), None)
        if rd is None:
            skipped.append((name, "no reader"))
            continue
        try:
            got = rd(name, v, load(sp), sp)
        except (KeyError, TypeError, ValueError) as e:
            skipped.append((name, f"{type(e).__name__}: {e}"))
            continue
        rows.extend(got)
    covered = sorted({r["result"] for r in rows})
    bad = check_verdicts(rows)
    pairs = check_paper8(rows)
    mism = [p for p in pairs if p[2] != p[3]]

    hub = os.path.join(ROOT, "notes/hubbard_2026-11-11/README.md")
    out = {"results_in_reproduce": len(R), "results_with_rows": len(covered), "rows": rows, "skipped": skipped,
           "check1_all_results_have_rows": len(covered) == len(R),
           "check2_verdict_mismatches": bad, "check3_paper8_cz": [list(p) for p in pairs],
           "check3_mismatches": [list(p) for p in mism],
           "planned_not_in_table": "notes/hubbard_2026-11-11/README.md (1D Hubbard; no device result yet)"
           if os.path.exists(hub) else None}
    def ex(o):  # floats as exponent strings (4 significant digits), so that no number with 4 decimals appears
        if isinstance(o, float):
            return f"{o:.3e}"
        if isinstance(o, dict):
            return {k: ex(v) for k, v in o.items()}
        if isinstance(o, (list, tuple)):
            return [ex(v) for v in o]
        return o
    with open(os.path.join(HERE, "boundary.json"), "w") as f:
        json.dump(ex(out), f, indent=1)

    L = ["# Boundary table: raw device records, no mitigation (generated by boundary.py from committed records)", "",
         "Verdicts are the ones declared before each run, copied from each scores.json. 'common' = MSE / mean square "
         "of the exact values (0.5 is the READS line), only where scores.json has both; it is computed after the fact "
         "for tests whose declared measure was different. One device, one day per row; no line is fitted.", "",
         "## Checks (fixed before building)", "",
         f"1. Results with rows: {len(covered)} of {len(R)} in reproduce.py RESULTS ({len(rows)} judged units)."
         + ("" if not skipped else f" Not covered: {skipped}"),
         f"2. Verdict words read again from each scores.json at their key paths: "
         f"{sum(len(r['verdict_path']) for r in rows)} looked up, {len(bad)} mismatches.",
         f"3. CZ against notes/paper8/out/tables.json (Tables 1, 2, 3, 6, 8, 9): {len(pairs)} pairs, {len(mism)} mismatches."
         + ("" if not mism else f" {mism}"), "",
         "## Table", "",
         "| result | unit | qubits | CZ | CZ/qubit | CZ layers | verdict (declared) | common | mirror | floor | cone qubits / CZ |",
         "|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        cone = "" if r["cone_qubits"] is None else f"{r['cone_qubits']} / {fmt(r['cone_cz'])}"
        L.append(f"| {r['result']} | {r['unit']} | {fmt(r['qubits'])} | {fmt(r['cz'])} | {fmt(r['cz_per_qubit'])} | "
                 f"{fmt(r['cz_layers'])} | {r['verdict']} | {fmt(r['common'])} | {fmt(r['mirror'])} | {fmt(r['floor'])} | {cone} |")
    L += ["", "## Notes per result", ""]
    for name in covered:
        notes = sorted({r["note"] for r in rows if r["result"] == name and r["note"]})
        src = sorted({r["source"] for r in rows if r["result"] == name})
        L.append(f"- {name}: {', '.join(src)}" + (f". {' '.join(notes)}" if notes else ""))
    L += ["", "## Planned (not in the table)", "",
          "- 1D Hubbard (paper 9): no device result yet; estimates in notes/hubbard_2026-11-11/README.md."]
    with open(os.path.join(HERE, "boundary.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(7, 4.5))
        for reads, mk, lab in ((True, "o", "READS"), (False, "x", "DOES NOT READ")):
            pts = [(r["cz_per_qubit"], r["common"]) for r in rows if r["cz_per_qubit"] and r["common"] is not None
                   and (("DOES NOT READ" not in r["verdict"]) == reads)]
            if pts:
                ax.scatter(*zip(*pts), marker=mk, label=f"{lab} ({len(pts)})", alpha=0.7)
        ax.set_xlabel("CZ per qubit (whole circuit)")
        ax.set_ylabel("MSE / mean square of exact")
        ax.set_yscale("log")
        ax.legend()
        ax.set_title("Raw device records, no mitigation (one device, one day per point)")
        fig.tight_layout()
        fig.savefig(os.path.join(HERE, "boundary.png"), dpi=150)
    except ImportError:
        pass
    print(f"rows {len(rows)}; results {len(covered)}/{len(R)}; check2 mismatches {len(bad)}; "
          f"check3 {len(pairs)} pairs, {len(mism)} mismatches; skipped {skipped}")
    for m in mism:
        print("  check3:", m)


if __name__ == "__main__":
    main()
