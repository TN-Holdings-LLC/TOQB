"""Score E1 / E2 against the twin's lam (prereg/drafts-2026-10-26/esp_check_note.md):
    python -m toqb.esp_score ESP.jsonl LAM.jsonl ...
A: Spearman per L >= 0.8; B: pairs at the same (n, L) with |lam difference| > 0.1 ordered alike >= 90 %."""
import itertools
import json
import sys

from scipy.stats import spearmanr


def main(argv):
    est = {}
    for l in open(argv[0]):
        r = json.loads(l)
        if "error" not in r:
            est[(r["n"], r["L"], r["arm"])] = r
    lam = {}
    for f in argv[1:]:
        for l in open(f):
            r = json.loads(l)
            if r.get("model") == "sim" and "lam" in r and r.get("mseed", 0) == 0:
                lam[(r["n"], r["L"], r["arm"])] = r["lam"]
    keys = sorted(k for k in lam if k in est)
    ok = {}
    for E in ("E1", "E2"):
        res = []
        for L in sorted({k[1] for k in keys}):
            ks = [k for k in keys if k[1] == L]
            rho = spearmanr([est[k][E] for k in ks], [lam[k] for k in ks]).correlation
            pairs = [(a, b) for a, b in itertools.combinations(ks, 2) if a[0] == b[0] and abs(lam[a] - lam[b]) > 0.1]
            agree = sum((est[a][E] - est[b][E]) * (lam[a] - lam[b]) > 0 for a, b in pairs)
            frac = agree / len(pairs) if pairs else float("nan")
            passed = rho >= 0.8 and frac >= 0.9
            res.append(passed)
            print(f"{E} L={L}: cells {len(ks)}, Spearman {rho:.3f}, pairs {len(pairs)}, ordered alike {agree} ({frac:.0%}): {'pass' if passed else 'FAIL'}")
            for a, b in pairs:
                if (est[a][E] - est[b][E]) * (lam[a] - lam[b]) <= 0:
                    print(f"   misordered n={a[0]}: {a[2]} lam {lam[a]:.2f} {E} {est[a][E]:.3f} | {b[2]} lam {lam[b]:.2f} {E} {est[b][E]:.3f}")
        ok[E] = all(res)
    print("used:", "E2" if ok["E2"] else ("E1" if ok["E1"] else "none"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
