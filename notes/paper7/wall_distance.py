"""Task Z (owner 2026-11-06): the distance to the wall, an ESTIMATE from our records (not a measurement).

Inputs, read from committed records only:
  - the daily record's decay per CZ layer (gpu/daily_score.py decay_per_layer) from results/daily/*/*/run/scores.json;
  - the same quantity for the practice problems of 2026-11-04, computed by psf_os.report2d (the same definition:
    gamma = -ln(slope) / CZ layers of the compiled circuit, slope = sum(z a) / sum(a^2)), only rows with |M_exact| >= 0.1.
Row rule for the fitted gamma (owner 2026-11-06, written here before it was computed): keep a row only if
|M_exact| >= 0.3 and the compiled circuit has >= 10 CZ layers; group the kept rows by family: chain (P4: practice
p4_*, FX-A and the daily F3 problems), P5 (practice p5_* and the daily F2 problems), P6's form (the daily F1 / F4
problems, H03, P6). Tables and orders of magnitude use the kept rows; the unfiltered values (|M_exact| >= 0.1, any depth)
stay beside them for comparison.
Model (an assumption fitted to records, not a law): without correction the signal falls as R(L) = exp(-gamma L);
for an allowed relative error eps, L_max = -ln(1 - eps) / gamma.
Literature numbers are constants below, each with its source (checked 2026-11-06 at the workplace).

usage: PYTHONPATH=<psf-os>:. python notes/paper7/wall_distance.py [OUT_DIR]
"""
from __future__ import annotations

import glob
import json
import math
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

HARTREE_KCAL = 627.5095          # kcal/mol per hartree (CODATA conversion)
CHEM_ACC_HA = 1.0 / HARTREE_KCAL  # 1 kcal/mol = 1.594 mHa
LIT = dict(
    water_correlation_ha=(0.3706, "total correlation energy of H2O, CBS extrapolation: 'Complete basis set correlation "
                                  "energies. IV. The total correlation energy of the water molecule', J. Chem. Phys. "
                                  "83, 5129 (1985)"),
    femoco_reiher_thc_toffoli=(5.3e9, "Lee et al., PRX Quantum 2, 030305 (2021), THC, Reiher et al. FeMoco Hamiltonian; "
                                      "2,142 logical qubits; chemical accuracy taken there as 1.6 mHa"),
    femoco_li_thc_toffoli=(3.2e10, "Lee et al., PRX Quantum 2, 030305 (2021), THC, Li et al. FeMoco Hamiltonian "
                                   "(CAS(113e,76o), J. Chem. Phys. 150, 024302 (2019)); 2,196 logical qubits"),
    femoco_reiher2017_T_1mHa_serial=(1.0e14, "Reiher et al., PNAS 114, 7555 (2017), Table 1, structure 1, 1 mHa, serial: "
                                             "1.0e14 T gates, 111 logical qubits"),
)
LOGICAL_QUBITS = dict(femoco_reiher_thc_toffoli=2142, femoco_li_thc_toffoli=2196, femoco_reiher2017_T_1mHa_serial=111)


def gammas():
    rows = []
    for p in sorted(glob.glob(os.path.join(ROOT, "results", "daily", "*", "*", "run", "scores.json"))):
        sc = json.load(open(p))
        dev = p.split(os.sep)[-3]
        date = p.split(os.sep)[-4]
        for tag, r in sc["problems"].items():
            if r.get("decay_per_layer") is not None:
                rows.append(dict(source=f"daily {date}", device=dev, problem=tag, gamma=r["decay_per_layer"],
                                 retention=r.get("retention"), layers=r.get("cz_layers"), M_exact=r["M_exact"]))
    from psf_os import report2d as X
    for rel, af, dev in (("results/practice-2026-11-04/run", "results/practice-2026-11-04/circuits/answers.json",
                          "ibm_marrakesh"),
                         ("results/practice-fez-2026-11-04/run", "results/practice-fez-2026-11-04/circuits/answers.json",
                          "ibm_fez")):
        run = os.path.join(ROOT, rel)
        cs = X.extended_cards(f"{run}/job", f"{run}/runs", json.load(open(os.path.join(ROOT, af))))
        for tag, c in cs.items():
            r = c.get("retention", {})
            if r.get("decay_per_layer") is not None and abs(r["M_exact"]) >= 0.1:
                rows.append(dict(source="practice 2026-11-04", device=dev, problem=tag, gamma=r["decay_per_layer"],
                                 retention=r.get("retention"), layers=r.get("cz_layers"), M_exact=r["M_exact"]))
    return rows


MIN_ABS_ANSWER, MIN_LAYERS = 0.3, 10


def family(problem):
    """chain / P5 / P6 form, from the problem's tag."""
    if problem.startswith("p4_") or problem.startswith("FX-A"):
        return "chain"
    if problem.startswith("p5_"):
        return "P5"
    try:
        from daily import pool as P
        fam = P.entry(problem)[1]
    except KeyError:
        return "other"
    return {"F3": "chain", "F2": "P5", "F1": "P6 form", "F4": "P6 form"}.get(fam, "other")


def kept(row):
    return abs(row["M_exact"]) >= MIN_ABS_ANSWER and (row["layers"] or 0) >= MIN_LAYERS


def spread(gs):
    gs = sorted(g for g in gs if g > 0)
    if not gs:
        return None
    med = gs[len(gs) // 2] if len(gs) % 2 else 0.5 * (gs[len(gs) // 2 - 1] + gs[len(gs) // 2])
    return dict(n=len(gs), smallest=gs[0], median=med, largest=gs[-1])


def lmax(gamma, eps):
    return -math.log(1 - eps) / gamma


def build(out_dir):
    rows = gammas()
    for r in rows:
        r["family"] = family(r["problem"])
        r["kept"] = kept(r)
    allg = spread(r["gamma"] for r in rows)                     # unfiltered (|M_exact| >= 0.1), for comparison
    keep = [r for r in rows if r["kept"]]
    kg = spread(r["gamma"] for r in keep)
    fams = {f: spread(r["gamma"] for r in keep if r["family"] == f) for f in ("chain", "P5", "P6 form")}
    eps_list = (0.1, 0.01, 0.001)
    lines1 = [("all kept, smallest", kg["smallest"]), ("all kept, median", kg["median"]), ("all kept, largest", kg["largest"])]
    lines1 += [(f"{f}, median", v["median"]) for f, v in fams.items() if v]
    lines1 += [("unfiltered, median (comparison)", allg["median"])]
    t1 = [dict(gamma_kind=k, gamma=g, **{f"Lmax_eps_{e}": lmax(g, e) for e in eps_list}) for k, g in lines1]
    eps_chem_water = CHEM_ACC_HA / LIT["water_correlation_ha"][0]
    t3 = []
    for key in ("femoco_reiher_thc_toffoli", "femoco_li_thc_toffoli", "femoco_reiher2017_T_1mHa_serial"):
        count = LIT[key][0]
        for depth_kind, L in (("serial (every non-Clifford gate one layer)", count),
                              ("fully parallel over the logical qubits (count / qubits)", count / LOGICAL_QUBITS[key])):
            need = -math.log(1 - eps_chem_water) / L
            t3.append(dict(estimate=key, depth=depth_kind, layers=L, gamma_needed=need,
                           orders_from_kept_median=math.log10(kg["median"] / need),
                           orders_from_kept_smallest=math.log10(kg["smallest"] / need),
                           orders_from_unfiltered_median=math.log10(allg["median"] / need)))
    res = dict(rule=dict(min_abs_answer=MIN_ABS_ANSWER, min_cz_layers=MIN_LAYERS), rows=rows,
               gamma_kept=kg, gamma_by_family=fams, gamma_unfiltered=allg, table1=t1,
               chem=dict(chem_acc_ha=CHEM_ACC_HA, water_correlation_ha=LIT["water_correlation_ha"][0],
                         eps_water=eps_chem_water), table3=t3, literature={k: v[1] for k, v in LIT.items()})
    os.makedirs(out_dir, exist_ok=True)
    json.dump(res, open(os.path.join(out_dir, "wall_distance.json"), "w"), indent=1)
    md = ["# Distance to the wall: generated tables (ESTIMATE, not a measurement; notes/paper7/wall_distance.py)", "",
          f"Row rule (written before computing): |M_exact| >= {MIN_ABS_ANSWER} and >= {MIN_LAYERS} CZ layers. "
          f"Kept {len(keep)} of {len(rows)} rows.", "",
          "## gamma per CZ layer by family (kept rows)", "",
          "| family | rows | smallest | median | largest |", "|---|---|---|---|---|"]
    for f, v in fams.items():
        md.append(f"| {f} | {v['n']} | {v['smallest']:.4f} | {v['median']:.4f} | {v['largest']:.4f} |" if v else
                  f"| {f} | 0 | - | - | - |")
    md.append(f"| all kept | {kg['n']} | {kg['smallest']:.4f} | {kg['median']:.4f} | {kg['largest']:.4f} |")
    md.append(f"| unfiltered (abs(M_exact) >= 0.1, any depth; comparison) | {allg['n']} | {allg['smallest']:.4f} | "
              f"{allg['median']:.4f} | {allg['largest']:.4f} |")
    md += ["", "## Table 1: L_max = -ln(1 - eps) / gamma (CZ layers without correction)", "",
           "| gamma | value | eps 0.1 | eps 0.01 | eps 0.001 |", "|---|---|---|---|---|"]
    for r in t1:
        md.append(f"| {r['gamma_kind']} | {r['gamma']:.4f} | {r['Lmax_eps_0.1']:.1f} | {r['Lmax_eps_0.01']:.2f} | "
                  f"{r['Lmax_eps_0.001']:.3f} |")
    md += ["", "## Table 2: chemical accuracy as a relative error (one example)", "",
           f"1 kcal/mol = {CHEM_ACC_HA * 1000:.3f} mHa; water's total correlation energy {LIT['water_correlation_ha'][0]} Ha "
           f"({LIT['water_correlation_ha'][1]}): eps = {eps_chem_water:.2e}. Larger molecules have larger correlation "
           "energies, so eps is smaller for them; FeMoco's correlation energy is not stated in the sources read.", "",
           "## Table 3: FeMoco estimates and the gamma they would need without correction (eps as in table 2)", "",
           "| estimate | depth taken as | layers | gamma needed | orders below the kept median | below the kept smallest | "
           "below the unfiltered median |", "|---|---|---|---|---|---|---|"]
    for r in t3:
        md.append(f"| {r['estimate']} | {r['depth']} | {r['layers']:.2e} | {r['gamma_needed']:.1e} | "
                  f"{r['orders_from_kept_median']:.1f} | {r['orders_from_kept_smallest']:.1f} | "
                  f"{r['orders_from_unfiltered_median']:.1f} |")
    md += ["", "## Kept rows", "", "| source | device | problem | family | M_exact | CZ layers | gamma |",
           "|---|---|---|---|---|---|---|"]
    for r in keep:
        md.append(f"| {r['source']} | {r['device']} | {r['problem']} | {r['family']} | {r['M_exact']:.3f} | {r['layers']} | "
                  f"{r['gamma']:.5f} |")
    md += ["", "Sources: " + "; ".join(f"{k}: {v[1]}" for k, v in LIT.items())]
    open(os.path.join(out_dir, "wall_distance_tables.md"), "w").write("\n".join(md) + "\n")
    return res


if __name__ == "__main__":
    r = build(sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "notes", "paper7", "out"))
    print(json.dumps(dict(kept=r["gamma_kept"], by_family=r["gamma_by_family"], unfiltered=r["gamma_unfiltered"],
                          eps_water=r["chem"]["eps_water"]), indent=1))
