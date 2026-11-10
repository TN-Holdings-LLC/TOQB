"""2. Error map on the 4 x 3 x 2 judged place (candidate 0), t 2-4: per site |z - exact| for fold and line, the
physical qubit each layout puts the site on, and that qubit's floor and mirror values in the same arm (cards).
Also: how the excess of the line's squared error is spread over the 24 sites."""
import json, sys
import numpy as np
from psf_os import user2d as U
R = sys.argv[1]
ans = json.load(open(f"{R}/answers/isingL_fez.json"))
cards = U.cards(f"{R}/ibm_fez/job", f"{R}/ibm_fez/runs", ans)
read = None
from psf_os import job as J
read = J.read(f"{R}/ibm_fez/job", f"{R}/ibm_fez/runs")
res = {}
for c in (0, 1):
    for t in (1, 2, 3, 4):
        rows = {}
        for lay in ("f", "l"):
            tag = f"q32{lay}{c}_t{t}"
            cd = cards[tag]
            mp = read["p2d_" + tag][0]["mapping"]
            rows[lay] = {x["q"]: dict(z=x["z"], ex=x["exact"], err=abs(x["z"] - x["exact"]), floor=x["floor"], mirror=x["mirror"],
                                      phys=mp[str(x["q"])]) for x in cd["qubits"]}
        sites = sorted(rows["f"])
        ef = np.array([rows["f"][s]["err"] ** 2 for s in sites]); el = np.array([rows["l"][s]["err"] ** 2 for s in sites])
        d = el - ef
        order = np.argsort(-d)
        tot = d.sum()
        top3 = d[order[:3]].sum() / tot if tot > 0 else float("nan")
        pos = int((d > 0).sum())
        print(f"place {c} t {t}: mean sq err fold {ef.mean():.4f} line {el.mean():.4f}; line worse at {pos}/24 sites; "
              f"top 3 sites carry {top3:.0%} of the excess")
        if c == 0 and t >= 2:
            print("   site: |err| fold (phys, floor, mirror) | |err| line (phys, floor, mirror)   [sorted by line excess]")
            for s in [sites[i] for i in order[:8]]:
                f, l = rows["f"][s], rows["l"][s]
                print(f"   {s:2}: {f['err']:.3f} (q{f['phys']}, {f['floor']:.2f}, {f['mirror']:+.2f}) | {l['err']:.3f} (q{l['phys']}, {l['floor']:.2f}, {l['mirror']:+.2f})")
        res[f"c{c}_t{t}"] = dict(sites=sites, sq_err_fold=ef.tolist(), sq_err_line=el.tolist(), rows=rows)
json.dump(res, open("a2_map.json", "w"), indent=1)
