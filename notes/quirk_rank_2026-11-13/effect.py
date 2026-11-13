"""Desk check of psf_os.quirk.rank on ibm_fez (OS item 4, workplace VS Claude, 2026-11-13; not a verdict, not
declared, nothing placed or run).

For every ibm_fez ledger day D that has an earlier ledger day:
  - the device record of day D (a committed fez device.json in a results folder dated D) gives the candidates for
    chains of n = 20 (Hubbard L 20), 40 and 91 (XX91): first the default chain (as gpu/hub_build.chain_of: du91 shape,
    else psf-os rule C), then the rule C chain from every start of chain.START_ORDER that reaches n, in that order
    (a chain whose qubit set equals an earlier candidate's is left out);
  - quirk.rank orders them with the ledger before D (it reads only the latest day before D);
  - the chosen chain and the default chain are compared on day D's own floor (the ledger's day D values), which the
    ranking never saw: mean floor loss over the chain qubits measured on D, how many of them were measured, and how
    many are in day D's weakest fifth.
usage: python notes/quirk_rank_2026-11-13/effect.py --psf-os PATH   (writes effect.json, effect.md)
"""
import argparse
import glob
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
DEV = "ibm_fez"
NS = (20, 40, 91)


def device_record(day):
    hits = sorted(glob.glob(os.path.join(ROOT, "results", f"*{day}*", "**", DEV, "dev", "device.json"), recursive=True)
                  + glob.glob(os.path.join(ROOT, "results", "*", day, DEV, "dev", "device.json")))
    return hits[0] if hits else None


def chain_of(dev, n):
    """The default chain, as gpu/hub_build.chain_of (copied here: hub_build imports the Unix-only module resource
    through hub_cost): the first du91 shape with a qualifying copy, else psf-os rule C."""
    from daily import du91 as X
    from psf_os import chain as CH
    pl = X.place(dev, n)
    if pl["shape"] is not None:
        shape = next(s for s in X.SHAPES if s[0] == pl["shape"])
        return list(X.snake(n, shape)), dict(rule="shape", shape=pl["shape"])
    return list(CH.place(dev, n)["chain"]), dict(rule="C")


def candidates(dev, n):
    sys.path.insert(0, ROOT)
    from psf_os import chain as CH
    out, seen = [], set()
    lab, how = chain_of(dev, n)
    out.append(dict(name=f"default ({how['rule']})", qubits=[int(x) for x in lab]))
    seen.add(frozenset(lab))
    for st in CH.START_ORDER:
        ch, _, why = CH.walk(dev, n, *st)
        if why is None and frozenset(ch) not in seen:
            seen.add(frozenset(ch))
            out.append(dict(name=f"rule C start {tuple(st)}", qubits=[int(x) for x in ch]))
    return out


def judge(day_rows, qubits):
    fl = {int(q): float(v["floor"]) for q, v in day_rows.items()}
    k = max(1, len(fl) // 5)
    weak = set(sorted(fl, key=lambda q: (-fl[q], q))[:k])
    got = [fl[q] for q in qubits if q in fl]
    return dict(measured=len(got), mean_floor=float(np.mean(got)) if got else None,
                weak_fifth=sum(1 for q in qubits if q in weak))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--psf-os", required=True)
    ap.add_argument("--ledger", default=os.path.join(HERE, "quirk_ledger.json"))
    a = ap.parse_args()
    sys.path.insert(0, a.psf_os)
    from psf_os import device as Dv
    from psf_os import quirk
    L = quirk.load(a.ledger)
    days = sorted(L["devices"][DEV])
    rows = []
    for D in days[1:]:
        p = device_record(D)
        if p is None:
            rows.append(dict(day=D, note="no committed fez device record dated this day"))
            continue
        dev = Dv.Device.load(os.path.dirname(p))
        for n in NS:
            try:
                cands = candidates(dev, n)
            except Exception as e:  # noqa: BLE001
                rows.append(dict(day=D, n=n, note=f"no candidates: {type(e).__name__}"))
                continue
            ordered, rep = quirk.rank(DEV, cands, L, before=D)
            ch, df = ordered[0], cands[0]
            allj = [judge(L["devices"][DEV][D], c["qubits"]) for c in cands]
            means = [j["mean_floor"] for j in allj if j["mean_floor"] is not None]
            rows.append(dict(day=D, n=n, ledger_day=rep["ledger_day"], candidates=len(cands),
                             device_record=os.path.relpath(p, ROOT).replace("\\", "/"),
                             marked=len(rep["marked"]), chosen=ch["name"], default=df["name"],
                             marks_chosen=rep["counts"][ch["name"]], marks_default=rep["counts"][df["name"]],
                             chosen_on_D=judge(L["devices"][DEV][D], ch["qubits"]),
                             default_on_D=judge(L["devices"][DEV][D], df["qubits"]),
                             median_candidate_mean_floor=float(np.median(means)) if means else None))

    def ex(o):  # exponent strings (seal.py leakcheck)
        if isinstance(o, float):
            return f"{o:.3e}"
        if isinstance(o, dict):
            return {k: ex(v) for k, v in o.items()}
        if isinstance(o, list):
            return [ex(v) for v in o]
        return o
    json.dump(ex(dict(device=DEV, rule=f"{quirk.RULE} v{quirk.VERSION}", rows=rows)),
              open(os.path.join(HERE, "effect.json"), "w"), indent=1)

    def f(x):
        return "-" if x is None else f"{x:.3f}"
    M = ["# quirk.rank on ibm_fez: desk check against the next day's floor (generated by effect.py)", "",
         f"Rule {quirk.RULE} v{quirk.VERSION}. Floor = 1 - <Z> after reset, on day D (never seen by the ranking). "
         "'meas' = chain qubits measured on D; 'weak' = of them in D's weakest fifth.", "",
         "| day D | n | ledger day | cands | marked | default: marks / meas / mean floor / weak | "
         "chosen: marks / meas / mean floor / weak | median cand. mean floor | moved |",
         "|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        if "note" in r:
            M.append(f"| {r['day']} | {r.get('n', '-')} | {r['note']} |||||||")
            continue
        c, d = r["chosen_on_D"], r["default_on_D"]
        M.append(f"| {r['day']} | {r['n']} | {r['ledger_day']} | {r['candidates']} | {r['marked']} | "
                 f"{r['marks_default']} / {d['measured']} / {f(d['mean_floor'])} / {d['weak_fifth']} | "
                 f"{r['marks_chosen']} / {c['measured']} / {f(c['mean_floor'])} / {c['weak_fifth']} | "
                 f"{f(r['median_candidate_mean_floor'])} | {'yes' if r['chosen'] != r['default'] else 'no'} |")
    mv = [r for r in rows if "note" not in r and r["chosen"] != r["default"]]
    cmp = [r for r in mv if r["chosen_on_D"]["mean_floor"] is not None and r["default_on_D"]["mean_floor"] is not None]
    better = sum(1 for r in cmp if r["chosen_on_D"]["mean_floor"] < r["default_on_D"]["mean_floor"])
    fewer = sum(1 for r in mv if r["chosen_on_D"]["weak_fifth"] < r["default_on_D"]["weak_fifth"])
    more = sum(1 for r in mv if r["chosen_on_D"]["weak_fifth"] > r["default_on_D"]["weak_fifth"])
    M += ["", f"Moved: {len(mv)} of {sum(1 for r in rows if 'note' not in r)} (day, n) cases. Of the moved: chosen "
          f"chain's mean floor on D lower than the default's in {better} of {len(cmp)}; fewer of D's weakest fifth in "
          f"{fewer}, more in {more}, equal in {len(mv) - fewer - more}."]
    open(os.path.join(HERE, "effect.md"), "w", encoding="utf-8").write("\n".join(M) + "\n")
    print("\n".join(M))


if __name__ == "__main__":
    main()
