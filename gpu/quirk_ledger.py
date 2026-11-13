"""Write the quirk ledger in the form psf_os.quirk.rank reads (OS item 4, workplace VS Claude, 2026-11-13).

device -> day label -> physical qubit -> {"floor", "mirror", "n"}, from the user's own finished user2d job records
under results/, read as notes/quirk_ledger_2026-11-13/ledger.py reads them (the same as psf_os.user2d.card). The day
is the record folder's date (the project's day label). No IBM calibration number is read.

With --before DAY only records dated strictly before DAY are written (psf_os.quirk.rank also ignores later days on
its own; this keeps the written file free of them too).
Floats are written as exponent strings ("%.3e"), which quirk.rank reads with float().

usage: python gpu/quirk_ledger.py --psf-os PATH OUT.json [--before YYYY-MM-DD] [--device ibm_fez ...]
"""
import argparse
import importlib.util
import json
import os
import sys
from collections import defaultdict

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FORMAT = "psf-os quirk ledger 1"


def _ledger_module():
    p = os.path.join(ROOT, "notes", "quirk_ledger_2026-11-13", "ledger.py")
    spec = importlib.util.spec_from_file_location("quirk_ledger_notes", p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def build(before=None, devices=None):
    """(ledger dict in FORMAT, list of job folders read, list of (folder, reason) skipped)."""
    M = _ledger_module()
    acc = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: {"floor": [], "mirror": []})))
    read, skipped = [], []
    for d in M.job_dirs():
        try:
            circ = M.read_job(d)
        except Exception as e:  # noqa: BLE001
            skipped.append((M.rel(d), type(e).__name__))
            continue
        if not circ:
            skipped.append((M.rel(d), "no user2d circuit with its floor and mirror"))
            continue
        used = False
        for tag, dev, day, q in circ:
            if (before and day >= before) or (devices and dev not in devices):
                continue
            zm = np.array([v[1] for v in q.values()])
            sd = zm.std() or 1.0
            for ph, (fl, m) in q.items():
                acc[dev][day][ph]["floor"].append(fl)
                acc[dev][day][ph]["mirror"].append((m - zm.mean()) / sd)
            used = True
        if used:
            read.append(M.rel(d))
    out = {"format": FORMAT, "before": before, "source": "user2d job records under results/ (own records only)",
           "devices": {dev: {day: {str(ph): {"floor": f"{np.mean(v['floor']):.3e}",
                                             "mirror": f"{np.mean(v['mirror']):.3e}", "n": len(v["floor"])}
                                   for ph, v in sorted(acc[dev][day].items())}
                             for day in sorted(acc[dev])}
                       for dev in sorted(acc)}}
    return out, sorted(read), skipped


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--psf-os", required=True)
    ap.add_argument("out")
    ap.add_argument("--before", default=None)
    ap.add_argument("--device", nargs="*", default=None)
    a = ap.parse_args()
    sys.path.insert(0, a.psf_os)
    L, read, skipped = build(a.before, a.device)
    L["jobs_read"] = read
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(L, f, indent=1)
    n = sum(len(v) for v in L["devices"].values())
    print(f"devices {len(L['devices'])}, device-days {n}, jobs read {len(read)}, skipped {len(skipped)}")


if __name__ == "__main__":
    main()
