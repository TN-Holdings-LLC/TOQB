"""Tables of out/correlations_posthoc.json (or the run log while it runs): per job, theta, t, distance."""
import ast
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def rows():
    p = os.path.join(HERE, "out", "correlations_posthoc.json")
    if os.path.exists(p):
        return list(json.load(open(p)).values())
    out = []
    for line in open(os.path.join(HERE, "out", "run.txt")):
        if " | " in line and "{" in line:
            head, body = line.split(" {", 1)
            job, th, t, d = [x.strip() for x in head.split("|")]
            r = ast.literal_eval("{" + body)
            r.update(job=job, theta=float(th.split()[1]), t=int(t.split()[1]), d=int(d.split()[1]))
            out.append(r)
    return out


def main():
    rs = rows()
    print("| job | theta | t | d | pairs (answered) | raw <ZZ> | C measured | C exact | ratio | mean abs diff |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for r in rs:
        ans = r.get("answered")
        cm = r.get("meas_conn_mean_answered", r["conn_mean"])
        ce = r.get("exact_conn_mean")
        ratio = r.get("ratio_measured_to_exact")
        print(f"| {r['job']} | {r['theta']:g} | {r['t']} | {r['d']} | {r['pairs']} ({ans if ans is not None else '-'}) | "
              f"{r['raw_zz_mean']:.3f} | {cm:+.4f} | {'' if ce is None else f'{ce:+.4f}'} | "
              f"{'' if ratio is None else f'{ratio:.2f}'} | {'' if 'mean_abs_diff' not in r else f'{r[chr(109)+chr(101)+chr(97)+chr(110)+chr(95)+chr(97)+chr(98)+chr(115)+chr(95)+chr(100)+chr(105)+chr(102)+chr(102)]:.4f}'} |")


if __name__ == "__main__":
    main()
