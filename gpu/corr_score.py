"""Score the correction test (prereg/drafts-2026-11-04/correction_note.md), written before the device run.

The correction, fixed by the note:
  1. rule R (as P6): z0_q = mean floor at t 1, 5, 9; keep q if z0_q >= median - max(5 x 1.4826 x MAD, 0.05).
  2. F_q(t): the floor at t, linear between the measured depths.
  3. a_theta = median over kept q of mean_{t=3,5} [ 0.5 ln( clip(mirror_q(t) / max(F_q(2t), 0.05), 1e-3, 1) ) / t ].
  4. z_corr = z / ( F_q(t) exp(a_theta t) ).
Judged per theta_x: MSE(z_corr, kept) / MSE(raw, all) at 0.8 / 1.25; AGREES if |M_corr - M_exact| <= 0.05 at t 1-9.

usage: PYTHONPATH=<psf-os 1250c90>:<TOQB> python gpu/corr_score.py OUT_DIR   (writes OUT_DIR/scores.json)
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p6_score as P  # noqa: E402  (answers(), judge(), TUTORIAL; unchanged)

TXS = ("0.53", "0.3", "0.8")
TS = range(1, 10)
SHOTS = 4000


def rule_r(floor):
    z0 = np.mean([floor[t] for t in (1, 5, 9)], axis=0)
    med = float(np.median(z0))
    mad = float(np.median(np.abs(z0 - med)))
    line = med - max(5 * 1.4826 * mad, 0.05)
    return z0 >= line, dict(median=med, mad=mad, line=line)


def floor_fn(floor):
    ts = sorted(floor)
    arr = np.array([floor[t] for t in ts])  # [depth, qubit]
    return lambda t: np.array([np.interp(t, ts, arr[:, q]) for q in range(arr.shape[1])])


def gate_rate(mirror, F, keep):
    """mirror: {t: [<Z>_q]} at t 3, 5 of one theta_x."""
    per_q = np.mean([0.5 * np.log(np.clip(np.array(mirror[t]) / np.maximum(F(2 * t), 0.05), 1e-3, 1.0)) / t
                     for t in (3, 5)], axis=0)
    return float(np.median(per_q[keep])), per_q


def verdict(r):
    return "HELPS" if r <= 0.8 else ("HURTS" if r >= 1.25 else "NO EFFECT")


def correct(raw, floor, mirror, ans):
    """raw: {t: [<Z>]} of one theta_x; floor: {t: [<Z>]}; mirror: {t: [<Z>]}; ans: {t: [answer or None]}."""
    keep, rr = rule_r(floor)
    F = floor_fn(floor)
    a, per_q = gate_rate(mirror, F, keep)
    fac = {t: F(t) * np.exp(a * t) for t in TS}
    corr = {t: list(np.array(raw[t]) / fac[t]) for t in TS}
    fonly = {t: list(np.array(raw[t]) / F(t)) for t in TS}
    gonly = {t: list(np.array(raw[t]) / np.exp(a * t)) for t in TS}
    base = P.judge(raw, ans)
    jc, jf, jg = P.judge(corr, ans, keep), P.judge(fonly, ans, keep), P.judge(gonly, ans, keep)
    rows = {}
    for t in TS:
        idx = [i for i, x in enumerate(ans[t]) if x is not None and keep[i]]
        z = np.array(raw[t])[idx]
        se_q = np.sqrt(np.clip(1 - z ** 2, 0, None) / SHOTS) / fac[t][idx]
        d = jc["rows"][t]["diff"]
        se = float(np.sqrt(np.sum(se_q ** 2)) / len(idx))
        rows[t] = dict(n=len(idx), M_corr=jc["rows"][t]["M"], M_exact=jc["rows"][t]["M_exact"], diff=d,
                       two_se=2 * se, diff_over_se=d / se, mean_factor=float(np.mean(fac[t][idx])))
    ratio = jc["mse"] / base["mse"]
    first = next((t for t in TS if abs(rows[t]["diff"]) > 0.05), None)
    return dict(rule_R=dict(rr, dropped=[int(i) for i in np.where(~keep)[0]]), gate_rate=a,
                gate_per_step=float(np.exp(a)), gate_rate_per_qubit=[float(x) for x in per_q],
                raw=dict(mse=base["mse"], diffs={t: base["rows"][t]["diff"] for t in TS}, reads=base["reads"]),
                corrected=dict(mse=jc["mse"], ratio=ratio, verdict=verdict(ratio), rows=rows,
                               agrees="AGREES" if first is None else "DIFFERS", first_miss=first),
                floor_only=dict(ratio=jf["mse"] / base["mse"], diffs={t: jf["rows"][t]["diff"] for t in TS}),
                gate_only=dict(ratio=jg["mse"] / base["mse"], diffs={t: jg["rows"][t]["diff"] for t in TS}))


def read_job(out):
    from psf_os import ising2d as I
    from psf_os import job as J
    from psf_os.kim import z_values
    jd, runs = f"{out}/V/job", f"{out}/V/runs"
    sc = I.score(jd, runs)
    mir = {}
    for name, (rec, cc) in J.read(jd, runs).items():
        if rec.get("psfos_job", {}).get("kind") == "mirror2d":
            tx = f"{float(rec['psfos_job']['theta_x']):g}"
            mir[tx] = {p["t"]: z_values(cc[(p["input"], "z")], len(I.QUBITS))[0].tolist() for p in rec["points"]}
    return sc, mir, jd, runs


def main(out):
    from psf_os import ising2d as I
    from psf_os import sentinel
    sc, mir, jd, runs = read_job(out)
    floor = sc["0"]
    res = dict(sentinel=sentinel.verdict(jd, runs)["status"], floor={t: float(np.mean(floor[t])) for t in sorted(floor)})
    for tx in TXS:
        ans = P.answers(float(tx))
        r = correct(sc[tx], floor, mir[tx], ans)
        r["rule_R"]["dropped"] = [I.QUBITS[i] for i in r["rule_R"]["dropped"]]
        if tx == "0.53":
            r["tutorial"] = {t: dict(ours_raw_abs=abs(r["raw"]["diffs"][t]), ours_corr_abs=abs(r["corrected"]["rows"][t]["diff"]),
                                     tutorial_unmitigated_gap=abs(u - p)) for t, (u, p) in P.TUTORIAL.items()}
        res[tx] = r
    json.dump(res, open(f"{out}/scores.json", "w"), indent=1, default=str)
    print(f"sentinel {res['sentinel']} | floor {({t: round(v, 3) for t, v in res['floor'].items()})}")
    for tx in TXS:
        r = res[tx]
        c = r["corrected"]
        print(f"theta_x {tx}: gate/step {r['gate_per_step']:.4f}; dropped {r['rule_R']['dropped']}; "
              f"ratio {c['ratio']:.3f} {c['verdict']}; {c['agrees']}"
              + (f" (first miss t {c['first_miss']})" if c["first_miss"] else "")
              + f" | floor only {r['floor_only']['ratio']:.3f}, gate only {r['gate_only']['ratio']:.3f}")
        print("   raw  diff", [round(r["raw"]["diffs"][t], 3) for t in TS])
        print("   corr diff", [round(c["rows"][t]["diff"], 3) for t in TS], "2SE",
              [round(c["rows"][t]["two_se"], 3) for t in TS], "factor", [round(c["rows"][t]["mean_factor"], 2) for t in TS])
    return res


if __name__ == "__main__":
    main(sys.argv[1])
