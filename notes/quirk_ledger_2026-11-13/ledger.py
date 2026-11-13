"""Quirk ledger: what our own job records say about each physical qubit, per device and day (workplace VS Claude,
2026-11-13; desk only, from committed records; nothing corrected, nothing used for placement or judging).

Sources: every finished user2d job under results/ (folders holding job/manifest.json and runs/ with user2d,
user2d_floor and user2d_mirror records). For each user circuit, the per-label <Z> of its floor circuit (all qubits
measured right after reset) and of its mirror circuit (the circuit, a barrier, its inverse) are read exactly as
psf_os.user2d.card reads them (psf_os.job.read, psf_os.kim.z_values), and put on the physical qubit through the
record's mapping. The day is the record folder's date (the project's day label, Japan time; e.g. the 11-07 daily ran
at 23:56 CET on 11-06). Per circuit:
  floor   1 - z_floor                                     (readout loss; 0 is perfect)
  mirror  standardised within the circuit: (z_mirror - mean) / std over its qubits (negative = returns worse than
          the circuit's other qubits; the circuit's depth sets the mean, so only the within-circuit rank is kept)
  rest    for the hub_score records (per-qubit z and exact in scores.json, chain order from build.json): z = r e +
          rest, rest orthogonal to e (as notes/noise_structure_2026-11-13); kept as rest^2 / mean(rest^2) over the
          circuit (how much of the circuit's wrong-shape error sits on this qubit)
Ledger: the mean of each quantity over the circuits of one device and day that used the qubit.
Then (2) day-to-day correlation per device on the shared qubits, (3) prediction of the next recorded day from the
earlier day only: Spearman correlation, and the share of the earlier day's weakest fifth that is again in the
weakest fifth (chance 0.2).
usage: python ledger.py --psf-os PATH   (from the notebook root or anywhere; writes ledger.json, ledger.md)
"""
import argparse
import glob
import json
import os
import re
import sys
from collections import defaultdict

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))


def rel(p):
    return os.path.relpath(p, ROOT).replace("\\", "/")


def job_dirs():
    out = []
    for m in glob.glob(os.path.join(ROOT, "results", "**", "job", "manifest.json"), recursive=True):
        d = os.path.dirname(os.path.dirname(m))
        if os.path.isdir(os.path.join(d, "runs")):
            out.append(d)
    return sorted(out)


def read_job(d):
    """[(tag, device, day, {phys: (floor_loss, z_mirror)})] for the user circuits of one job, as psf_os reads them."""
    from psf_os import job as J
    from psf_os.kim import z_values
    day = re.search(r"\d{4}-\d{2}-\d{2}", rel(d)).group(0)   # the record folder's date (the project's day label)
    read = J.read(os.path.join(d, "job"), os.path.join(d, "runs"))
    per = defaultdict(dict)
    for name, (rec, cc) in read.items():
        kind = rec.get("psfos_job", {}).get("kind")
        if kind not in ("user2d", "user2d_floor", "user2d_mirror"):
            continue
        tag = rec.get("tag") or re.sub(r"_(floor|mirror)$", "", name[len("p2d_"):])
        p = rec["points"][0]
        z, _ = z_values(cc[(p["input"], "z")], len(rec["labels"]))
        per[tag][kind] = (rec, z)
    out = []
    for tag, got in per.items():
        if not all(k in got for k in ("user2d", "user2d_floor", "user2d_mirror")):
            continue
        rec = got["user2d"][0]
        labels, mp = rec["labels"], rec["mapping"]
        z0, zm = got["user2d_floor"][1], got["user2d_mirror"][1]
        assert got["user2d_floor"][0]["labels"] == labels and got["user2d_mirror"][0]["labels"] == labels
        q = {int(mp[str(l)]): (1 - float(z0[k]), float(zm[k])) for k, l in enumerate(labels)}
        out.append((tag, rec["device"], day, q))
    return out


def rest_of(d):
    """{tag: {phys: rest^2 / mean rest^2}} from a hub_score scores.json (per-qubit z, exact in chain order)."""
    sp = os.path.join(d, "scores.json")
    if not os.path.exists(sp):
        return {}
    s = json.load(open(sp))
    if "circuits" not in s or not s["circuits"] or "z" not in next(iter(s["circuits"].values())):
        return {}
    b = json.load(open(os.path.join(d, "build.json")))
    out = {}
    for tag, c in s["circuits"].items():
        n = re.match(r"[LN](\d+)_", tag).group(1)
        chain = b["chains"][n]["labels"]
        mp = json.load(open(os.path.join(d, "runs", f"p2d_{tag}.json")))["mapping"]
        z, e = np.asarray(c["z"], float), np.asarray(c["exact"], float)
        r = float(z @ e / (e @ e))
        rest = z - r * e
        w = rest ** 2 / np.mean(rest ** 2)
        out[tag] = {int(mp[str(l)]): float(w[k]) for k, l in enumerate(chain)}
    return out


def spearman(a, b):
    ra, rb = np.argsort(np.argsort(a)), np.argsort(np.argsort(b))
    return float(np.corrcoef(ra, rb)[0, 1])


def weak_hits(prev, nxt, worse_is_high):
    """share of the earlier day's weakest fifth that is again in the weakest fifth (chance 0.2)."""
    n = len(prev)
    k = max(1, n // 5)
    sgn = -1 if worse_is_high else 1
    wp = set(np.argsort(sgn * np.asarray(prev))[:k])
    wn = set(np.argsort(sgn * np.asarray(nxt))[:k])
    return len(wp & wn) / k, k


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--psf-os", required=True)
    a = ap.parse_args()
    sys.path.insert(0, a.psf_os)
    led = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))   # (device, day) -> phys -> quantity -> values
    sources, skipped = [], []
    for d in job_dirs():
        try:
            circ = read_job(d)
        except Exception as e:  # noqa: BLE001
            skipped.append((rel(d), f"{type(e).__name__}: " + str(e).replace(ROOT, "").replace(ROOT.replace("/", "\\"), "")))
            continue
        if not circ:
            skipped.append((rel(d), "no user2d circuit with its floor and mirror (other record format)"))
            continue
        rest = rest_of(d)
        for tag, dev, day, q in circ:
            zm = np.array([v[1] for v in q.values()])
            sd = zm.std() or 1.0
            for ph, (fl, m) in q.items():
                led[(dev, day)][ph]["floor"].append(fl)
                led[(dev, day)][ph]["mirror"].append((m - zm.mean()) / sd)
            for ph, w in rest.get(tag, {}).items():
                led[(dev, day)][ph]["rest"].append(w)
        sources.append(dict(job=rel(d), device=circ[0][1], day=circ[0][2], circuits=len(circ),
                            rest_circuits=len(rest)))
    ledger = {f"{dev} {day}": {str(ph): {k: float(np.mean(v)) for k, v in qs.items()} | {"n": len(qs["floor"])}
                               for ph, qs in sorted(led[(dev, day)].items())}
              for dev, day in sorted(led)}

    QUANT = (("floor", True), ("mirror", False), ("rest", True))   # worse is high for floor loss and rest share
    pairs, preds = [], []
    devs = sorted({dev for dev, _ in led})
    for dev in devs:
        days = sorted(day for d_, day in led if d_ == dev)
        for i, d1 in enumerate(days):
            for d2 in days[i + 1:]:
                A, B = led[(dev, d1)], led[(dev, d2)]
                for qn, hi in QUANT:
                    common = sorted(ph for ph in A if ph in B and A[ph].get(qn) and B[ph].get(qn))
                    if len(common) < 10:
                        continue
                    x = [np.mean(A[ph][qn]) for ph in common]
                    y = [np.mean(B[ph][qn]) for ph in common]
                    row = dict(device=dev, day1=d1, day2=d2, quantity=qn, qubits=len(common),
                               pearson=float(np.corrcoef(x, y)[0, 1]), spearman=spearman(x, y))
                    pairs.append(row)
                    if d2 == days[i + 1]:           # prediction: the next recorded day, from the earlier day only
                        h, k = weak_hits(x, y, hi)
                        preds.append(dict(row, weak_fifth=k, weak_hit=h))
    out = dict(sources=sources, skipped=skipped, ledger=ledger, day_pairs=pairs, next_day=preds)

    def ex(o):  # floats as exponent strings, so that no number with 4 decimals appears (seal.py leakcheck)
        if isinstance(o, float):
            return f"{o:.3e}"
        if isinstance(o, dict):
            return {k: ex(v) for k, v in o.items()}
        if isinstance(o, (list, tuple)):
            return [ex(v) for v in o]
        return o
    json.dump(ex(out), open(os.path.join(HERE, "ledger.json"), "w"), indent=1)

    from datetime import date
    L = ["# Quirk ledger (generated by ledger.py from committed job records; nothing corrected, not used for placement)",
         "", f"Jobs read: {len(sources)}; device-days: {len(ledger)}; skipped records: {len(skipped)} (list at the end).",
         "", "## Device-days", "", "| device day | qubits | circuits |", "|---|---|---|"]
    for k in ledger:
        dev, day = k.split()
        nc = sum(s["circuits"] for s in sources if s["device"] == dev and s["day"] == day)
        L.append(f"| {k} | {len(ledger[k])} | {nc} |")
    L += ["", "## Next recorded day, from the earlier day only", "",
          "Spearman over the shared qubits; 'weak hit' = share of the earlier day's weakest fifth that is again in the "
          "weakest fifth (chance 0.2).", "",
          "| device | day -> next | quantity | qubits | Spearman | Pearson | weak fifth | weak hit |",
          "|---|---|---|---|---|---|---|---|"]
    for p in preds:
        L.append(f"| {p['device']} | {p['day1']} -> {p['day2']} | {p['quantity']} | {p['qubits']} | {p['spearman']:+.2f} | "
                 f"{p['pearson']:+.2f} | {p['weak_fifth']} | {p['weak_hit']:.2f} |")
    L += ["", "## Summary over all day pairs", "", "| device | quantity | pairs | median Spearman | min | max |",
          "|---|---|---|---|---|---|"]
    g = defaultdict(list)
    for p in pairs:
        g[(p["device"], p["quantity"])].append(p["spearman"])
    for (dev, qn), v in sorted(g.items()):
        L.append(f"| {dev} | {qn} | {len(v)} | {np.median(v):+.2f} | {min(v):+.2f} | {max(v):+.2f} |")
    L += ["", "## ibm_fez floor: Spearman against the gap in days", "", "| gap (days) | pairs | median | min | max |",
          "|---|---|---|---|---|"]
    gg = defaultdict(list)
    for p in pairs:
        if p["device"] == "ibm_fez" and p["quantity"] == "floor":
            gap = (date.fromisoformat(p["day2"]) - date.fromisoformat(p["day1"])).days
            gg[gap].append(p["spearman"])
    for gap, v in sorted(gg.items()):
        L.append(f"| {gap} | {len(v)} | {np.median(v):+.2f} | {min(v):+.2f} | {max(v):+.2f} |")
    L += ["", "## Records read", "", "| job | device | day | circuits | with rest |", "|---|---|---|---|---|"]
    for s_ in sources:
        L.append(f"| {s_['job']} | {s_['device']} | {s_['day']} | {s_['circuits']} | {s_['rest_circuits']} |")
    L += ["", "## Records not read (reason)", ""]
    for j, r in skipped:
        L.append(f"- {j}: {r}")
    open(os.path.join(HERE, "ledger.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
    print(f"jobs {len(sources)}, skipped {len(skipped)}, device-days {len(ledger)}, pairs {len(pairs)}, "
          f"next-day predictions {len(preds)}")


if __name__ == "__main__":
    main()
