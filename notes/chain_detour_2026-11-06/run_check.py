"""Apply detour.place to the same device records as notes/du91_2026-11-06/placement.py, N = 51, 71, 91, beside the
shape rule (du91.place); check that without holes it is du91's S1 / S2. usage (from the TOQB root):
PYTHONPATH=<psf-os>:. python notes/chain_detour_2026-11-06/run_check.py OUT.json"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "du91_2026-11-06"))
import detour as T  # noqa: E402
from daily import du91 as X  # noqa: E402
from placement import RECORDS, load  # noqa: E402
from psf_os import device as D  # noqa: E402

out = dict(identity={}, records=[])
# 1. without holes: start (+1, 0, 0) = S1, (+1, 1, 0) = S2
clean = load(RECORDS[1][1])
clean = D.Device(**{**clean.__dict__, "failed_qubits": [], "failed_couplers": []})
for n in X.WIDTHS:
    for st, sh in (((1, 0, 0), X.SHAPES[0]), ((1, 1, 0), X.SHAPES[1])):
        ch, why = T.chain_from(clean, n, *st)
        try:
            ref = X.snake(n, sh)
        except ValueError:
            ref = None
        out["identity"][f"{n} {sh[0]}"] = (ref is None and why is not None) or ch == ref
print("no holes, detour start = du91 shape:", out["identity"])
# 2. the records
for label, path in RECORDS:
    dev = load(path)
    row = dict(record=label, device=dev.name, failed_qubits=dev.failed_qubits, failed_couplers=dev.failed_couplers,
               widths={})
    for n in X.WIDTHS:
        shape = X.place(dev, n)
        w = dict(shape_rule=shape["shape"])
        for rule, fn in (("A", lambda: T.place(dev, n)), ("B", lambda: T.place(dev, n, bypass=True)),
                         ("C", lambda: T.place_dfs(dev, n))):
            try:
                ch, st, passed = fn()
                w[rule] = dict(start=list(st), starts_passed=len(passed), check=T.check(dev, ch), chain=ch)
            except T.Refused as e:
                w[rule] = dict(start=None, why=str(e))
        row["widths"][n] = w
        print(f"{label:20} {dev.name:14} N {n}: shape {w['shape_rule'] or '-':3} " + "  ".join(
            f"{r} {w[r]['start'] if w[r]['start'] else 'no (best ' + w[r]['why'].split()[-1] + ')'}"
            + ("" if not w[r]["start"] or not w[r]["check"]["bad_links"] else " BAD") for r in "ABC"))
    out["records"].append(row)
json.dump(out, open(sys.argv[1], "w"), indent=1)
