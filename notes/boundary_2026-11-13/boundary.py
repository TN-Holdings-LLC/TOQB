"""Boundary table, 2026-11-13 version: the 11-12 table (notes/boundary_2026-11-12, kept as it was) plus the four
11-12 results registered in reproduce.py (Hubbard with two time steps, Ohm 6 cycles on fez and on kingston, XX chain
of 91 qubits). Built only from committed records (all results in reproduce.py RESULTS). No numbers are typed by hand. Circuit files
(.qpy, .qpy.gz) are not opened.

One row = one judged unit (one observable, size and step count; dual-unitary chains per h; IBM 2023 per observable).

usage (from the TOQB root):  python notes/boundary_2026-11-13/boundary.py
writes notes/boundary_2026-11-13/boundary.md, boundary.json (and, with matplotlib, boundary_a_whole.png,
boundary_b_cone.png and boundary_c_layers.png; needs rustworkx for the light-cone count)
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


def utility_cone(names=("z106_t4", "w10_t5", "w17_t5", "w17b_t5x")):
    """{observable: (qubits of Eagle's graph, light-cone qubits, CZ inside the light cone)} from the circuit
    definition (gpu/utility_tn_diag.network_diag on utility_exact.eagle_edges; no circuit file, no answers opened).
    Each R_ZZ of the circuit is one CZ on the device (Clifford angle); network_diag writes it once on the ket and once
    on the bra side ("zzd"), so the CZ inside the cone is half the "zzd" slots."""
    import sys
    sys.path.insert(0, os.path.join(ROOT, "gpu"))
    import utility_exact as UE
    import utility_tn as T
    import utility_tn_diag as D
    edges = UE.eagle_edges()
    n = len({q for e in edges for q in e})
    out = {}
    for ob in names:
        obs, t, ex = T.OBS[ob]
        slots, nq = D.network_diag(obs, t, ex, edges)[3:5]
        z = sum(1 for sl in slots if sl[0] == "zzd")
        assert z % 2 == 0
        out[ob] = (n, nq, z // 2)
    return out


def r_util(name, res, s, sp):
    rep = load(os.path.join(os.path.dirname(sp), "report.json"))
    cone = utility_cone(tuple(s["observables"]))
    out = []
    for ob, o in s["observables"].items():
        r = rep["observables"][ob]
        n, nq, ccz = cone[ob]
        x = row(name, ob, n, o["cz"], f"{o['reads']}, AGREES {o['agrees']} of {len(o['points'])}",
                [["observables", ob, "reads"], ["observables", ob, "agrees"]],
                common=ratio(o["mse"], o["mean_square_exact"]), mirror=o.get("mirror"), floor=o.get("floor"),
                cone_q=r.get("cone_qubits"), cone_cz=ccz, src=sp,
                note="qubits = the nodes of Eagle's graph (utility_exact.eagle_edges), the whole circuit; CZ = cz in "
                     "scores (= report cz_per_circuit), whole circuit, with the gates on failed elements left out (they "
                     "are outside the light cone); cone CZ = R_ZZ inside the light cone from gpu/utility_tn_diag."
                     "network_diag (half its 'zzd' slots), cone qubits from report.json (network_diag gives the same)")
        x["cone_qubits_by_network"] = nq
        out.append(x)
    return out


def r_hub(name, res, s, sp):
    """Scores of gpu/hub_score.py, one row per circuit: 1D Hubbard (L, steps, arm U 4 or the U 0 free-fermion
    ruler), Hubbard with two time steps (hub-dt), the XX chain (xx91). CZ layers from check_trybuild.json (cz_depth)
    beside scores.json where it exists (xx91 has none: empty)."""
    tp = os.path.join(ROOT, os.path.dirname(sp), "check_trybuild.json")
    tb = load(os.path.join(os.path.dirname(sp), "check_trybuild.json")) if os.path.exists(tp) else {}
    out = []
    for tag, c in s["circuits"].items():
        mt = re.match(r"L(\d+)_s(\d+)_U(\d+)$", tag)
        if mt:
            L, st, arm = mt.groups()
            unit, group = f"{tag} (L {L}, {st} steps, U {arm})", f"U{arm}"
        elif name.startswith("hub-dt"):
            L, T, st = re.match(r"L(\d+)_T([\d.]+)_s(\d+)$", tag).groups()
            unit, group = f"{tag} (L {L}, time {T}, {st} steps, U 4)", "dt"
        else:
            n, th, st = re.match(r"N(\d+)_th(\d+)_s(\d+)$", tag).groups()
            unit, group = f"{tag} (N {n}, theta {int(th) / 1000:g}, {int(st)} steps)", "xx"
        out.append(row(name, unit, c["qubits"], c["cz"],
                       f"{c['reads']}, AGREES {c['agrees']} of {c['qubits']}",
                       [["circuits", tag, "reads"], ["circuits", tag, "agrees"]],
                       common=ratio(c["mse"], c["mean_square"]), layers=tb.get(tag, {}).get("cz_depth"),
                       mirror=c.get("mirror"), floor=c.get("floor"), src=sp,
                       note="CZ layers = cz_depth in check_trybuild.json where it exists (xx91: no record, "
                            "empty); U 0 is the free-fermion ruler"))
        out[-1]["arm"] = group
    return out


def r_ohm(name, res, s, sp):
    """Ohm 6 cycles (gpu/ohm_score.py): one row per arm and cycle count; the unit is M per circuit (the right half's
    transferred magnetisation, a sum over 20 qubits), judged over the arm's 2K circuits. CZ and CZ layers from
    build.json (the same for every circuit of an arm); mirror and floor = the mean over the arm's circuits."""
    b = load(os.path.join(os.path.dirname(sp), "build.json"))
    out = []
    for arm, a in s["arms"].items():
        tags = [t for t in s["circuits"] if t.startswith(arm + "_")]
        cz = {s["circuits"][t]["cz"] for t in tags}
        lay = {b["cz_depth"][t] for t in tags}
        assert len(cz) == 1 and len(lay) == 1, (arm, cz, lay)
        mir = sum(s["circuits"][t]["mirror"] for t in tags) / len(tags)
        flo = sum(s["circuits"][t]["floor"] for t in tags) / len(tags)
        out.append(row(name, f"{arm}: M per circuit (sum over 20 qubits), {a['circuits']} circuits", b["N"], cz.pop(),
                       f"{a['reads']}, AGREES {a['agrees']} of {a['circuits']}",
                       [["arms", arm, "reads"], ["arms", arm, "agrees"]],
                       common=ratio(a["mse"], a["mean_square"]), layers=lay.pop(), mirror=mir, floor=flo, src=sp,
                       note="unit: M per circuit (sum over the right half's 20 qubits); CZ and CZ layers from build.json; "
                            "mirror and floor are means over the arm's circuits"))
        out[-1]["arm"] = "ohm"
    return out


READER = [("hubbard", r_hub), ("hub-dt", r_hub), ("xx91-", r_hub), ("ohm-", r_ohm), ("p6-", r_p6), ("corr-", r_corr), ("os2d-", r_os2d), ("practice-", r_run2d), ("daily-", r_run2d),
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
    notread = [r for r in rows if "DOES NOT READ" in r["verdict"]]
    plotted = [r for r in notread if r["cz_per_qubit"] and r["common"] is not None]
    cone_rows = [r for r in rows if r.get("cone_qubits_by_network") is not None]
    cone_bad = [(r["result"], r["unit"], r["cone_qubits"], r["cone_qubits_by_network"]) for r in cone_rows
                if r["cone_qubits"] != r["cone_qubits_by_network"]]
    layer_rows = [r for r in rows if r["cz_layers"] is not None and r["common"] is not None]

    # 11-13 check 1: every one of the four new results has rows
    NEW = ("hub-dt-fez-2026-11-12", "ohm-fez-2026-11-12", "ohm-kingston-2026-11-12", "xx91-fez-2026-11-12")
    new_rows = {n: sum(r["result"] == n for r in rows) for n in NEW}
    # 11-13 check 3: rows of the 11-12 version unchanged (same fields, compared in its number format)
    old = load("notes/boundary_2026-11-12/boundary.json")
    FIELDS = ("qubits", "cz", "cz_per_qubit", "cz_layers", "verdict", "common", "mirror", "floor", "cone_qubits",
              "cone_cz")

    def same(x):  # the 11-12 json writes floats as "%.3e" strings
        return f"{x:.3e}" if isinstance(x, float) else x
    mine = {(r["result"], r["unit"]): r for r in rows}
    old_bad, old_missing = [], []
    for o in old["rows"]:
        r = mine.get((o["result"], o["unit"]))
        if r is None:
            old_missing.append((o["result"], o["unit"]))
            continue
        for f in FIELDS:
            if same(r[f]) != o[f]:
                old_bad.append((o["result"], o["unit"], f, o[f], same(r[f])))
    n_old_results = len({o["result"] for o in old["rows"]})

    out = {"results_in_reproduce": len(R), "results_with_rows": len(covered), "rows": rows, "skipped": skipped,
           "check1_new_results_rows": new_rows,
           "check2_verdict_mismatches": bad,
           "check3_rows_of_11_12": len(old["rows"]), "check3_missing": old_missing, "check3_changed": old_bad,
           "paper8_cz": [list(p) for p in pairs], "paper8_cz_mismatches": [list(p) for p in mism],
           "not_read_rows": len(notread), "not_read_in_figure_a": len(plotted),
           "cone_qubits_network_vs_report": [list(c) for c in cone_bad], "cone_rows": len(cone_rows),
           "figure_c_points": len(layer_rows)}

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

    L = ["# Boundary table, 2026-11-13: raw device records, no mitigation (generated by boundary.py from committed "
         "records)", "",
         "The 11-12 table (notes/boundary_2026-11-12) is kept as it was; this version adds the four 11-12 results. "
         "Verdicts are the ones declared before each run, copied from each scores.json. 'common' = MSE / mean square "
         "of the exact values (0.5 is the READS line), only where scores.json has both; it is computed after the fact "
         "for tests whose declared measure was different. One device, one day per row; no line is fitted.", "",
         "## Checks (fixed before building)", "",
         "1. Every one of the four new results has rows: "
         + ", ".join(f"{n} {k}" for n, k in new_rows.items()) + f" (all results: {len(covered)} of {len(R)}, "
         f"{len(rows)} judged units" + ("" if not skipped else f"; not covered: {skipped}") + ").",
         f"2. Verdict words read again from each scores.json at their key paths: "
         f"{sum(len(r['verdict_path']) for r in rows)} looked up, {len(bad)} mismatches.",
         f"3. Rows of the 11-12 version ({len(old['rows'])} rows of {n_old_results} results), fields "
         f"{', '.join(FIELDS)}: {len(old_missing)} missing, {len(old_bad)} changed."
         + ("" if not (old_bad or old_missing) else f" {old_missing} {old_bad}"),
         "",
         "Kept from 11-11 and 11-12: CZ against notes/paper8/out/tables.json "
         f"{len(pairs)} pairs, {len(mism)} mismatches; rows that DO NOT READ {len(notread)}, in figure (a) "
         f"{len(plotted)}; light-cone qubits from network_diag against report.json {len(cone_rows)} rows, "
         f"{len(cone_bad)} mismatches; figure (c) {len(layer_rows)} points.", "",
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
    with open(os.path.join(HERE, "boundary.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        def finish(ax, xlabel, title, path):
            ax.set_xlabel(xlabel)
            ax.set_ylabel("MSE / mean square of exact")
            ax.set_yscale("log")
            ax.axhline(0.5, color="grey", lw=0.6, ls=":")
            ax.legend(fontsize=8)
            ax.set_title(title, fontsize=10)
            fig.tight_layout()
            fig.savefig(os.path.join(HERE, path), dpi=150)

        def reads(r):
            return "DOES NOT READ" not in r["verdict"]

        fig, ax = plt.subplots(figsize=(7, 4.5))
        for ok, mk, lab in ((True, "o", "READS"), (False, "x", "DOES NOT READ")):
            pts = [(r["cz_per_qubit"], r["common"]) for r in rows if r["cz_per_qubit"] and r["common"] is not None
                   and reads(r) == ok]
            ax.scatter(*zip(*pts), marker=mk, s=40, label=f"{lab} ({len(pts)})", alpha=0.75)
        finish(ax, "CZ / qubits (whole circuit)",
               "(a) Raw device records, no mitigation (one device, one day per point)\ndotted: the READS line 0.5",
               "boundary_a_whole.png")

        fig, ax = plt.subplots(figsize=(7.5, 5))
        for ok, mk, lab in ((True, "o", "READS"), (False, "x", "DOES NOT READ")):
            for day, col in (("2026-11-10", "C0"), ("2026-11-11", "C2")):
                pts = [(r["cone_cz"], r["common"]) for r in cone_rows if reads(r) == ok and r["result"].endswith(day)]
                if pts:
                    ax.scatter(*zip(*pts), marker=mk, s=45, color=col if ok else "C3",
                               label=f"{lab}, {day} ({len(pts)})", alpha=0.8)
        ax.set_xlim(0, 1.3 * max(r["cone_cz"] for r in cone_rows))
        for r in cone_rows:
            first = r["result"].endswith("2026-11-10")
            ax.annotate(f"{r['unit']} ({r['cone_qubits']} q)", (r["cone_cz"], r["common"]), fontsize=7,
                        xytext=(5, -10 if first else 4), textcoords="offset points", color="C0" if first else "k")
        finish(ax, "CZ inside the light cone",
               "(b) IBM 2023 observables on ibm_fez (raw); label: cone qubits (blue text: the 11-10 run)",
               "boundary_b_cone.png")

        fig, ax = plt.subplots(figsize=(7.5, 5))
        groups = [("Hubbard U 4 (11-11)", lambda r: r.get("arm") == "U4", "s", "C1"),
                  ("Hubbard U 0 ruler (11-11)", lambda r: r.get("arm") == "U0", "D", "C2"),
                  ("Hubbard two time steps (11-12)", lambda r: r.get("arm") == "dt", "^", "C4"),
                  ("Ohm, M per circuit by arm (11-12)", lambda r: r.get("arm") == "ohm", "v", "C3"),
                  ("other records with CZ layers", lambda r: r.get("arm") is None, "o", "C0")]
        for lab, sel, mk, col in groups:
            for ok in (True, False):
                pts = [(r["cz_layers"], r["common"]) for r in layer_rows if sel(r) and reads(r) == ok]
                if pts:
                    ax.scatter(*zip(*pts), marker=mk, s=40, edgecolors=col, facecolors=col if ok else "none",
                               label=f"{lab}, {'READS' if ok else 'DOES NOT READ'} ({len(pts)})", alpha=0.75)
        finish(ax, "CZ layers (whole circuit)",
               "(c) Raw device records with recorded CZ layers (one device, one day per point; XX91 has none)\n"
               "filled: READS, open: DOES NOT READ; dotted: the READS line 0.5", "boundary_c_layers.png")
    except ImportError:
        pass
    print(f"rows {len(rows)}; results {len(covered)}/{len(R)}; new {new_rows}; verdict mismatches {len(bad)}; "
          f"11-12 rows {len(old['rows'])}: missing {len(old_missing)}, changed {len(old_bad)}; "
          f"paper8 {len(pairs)} pairs {len(mism)} mismatches; not-read {len(notread)} in (a) {len(plotted)}; "
          f"cone {len(cone_rows)} rows {len(cone_bad)} mismatches; figure (c) {len(layer_rows)} points; skipped {skipped}")
    for x in old_bad[:10]:
        print("  changed:", x)


if __name__ == "__main__":
    main()
