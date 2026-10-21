"""Score table and verdicts of the E4 against C test match (rules fixed before the results; W8, 2026-10-21).

    python -m toqb.match_score RUNS_DIR OUT.md [--json OUT.json] [--dev TEACHER:ANGLE ...] [--alpha 0.01]

Reads every run record (`*.json`) in RUNS_DIR: kind "s2re4" with sweeps = 0 is Z (theta = 0, no training), kind
"s2re4" with sweeps > 0 is E4, kind "s2rc" with init 0 is C0. A task is (teacher_seed, teacher_angle, layers, arm).
Pure Python with numpy and scipy; nothing is simulated here. Outputs are never overwritten (exit 2).

The rules (W8):

- Unit: the test point. For each arm, the per-point CE on the stand-in is computed from the stand-in's exact P(1)
  (`rehearsal.standin_p1`, the trajectory mean over predict.traj; per-point shots are not stored), with the formula of
  toqb.s2r2._ce (p = 1 - P(1) clipped to [1e-4, 1 - 1e-4]; -log p for y = +1, -log(1 - p) for y = -1).
- Comparison X against Y in a task: d_i = CE_i(Y) - CE_i(X) (positive favours X). Two-sided Wilcoxon signed-rank
  test (normal approximation with the tie correction; zero differences dropped), p_t. Holm over the tasks of that
  comparison. Verdict per task: WIN if the Holm-adjusted p < alpha and the mean of d > 0; LOSS if adjusted p < alpha
  and mean of d < 0; otherwise TIE.
- Overall for a comparison: Stouffer's combination of the tasks' signed-rank z, Z = sum(z_t) / sqrt(T), two-sided p.
  WIN if p < alpha, Z > 0 and no task is a LOSS; LOSS if p < alpha, Z < 0 and no task is a WIN; MIXED if tasks have
  both WIN and LOSS; otherwise TIE.
- Accuracy (secondary): per-point correctness from the exact P(1) (strict: P(1) = 0.5 is wrong); exact McNemar test
  on the discordant points, Holm over the tasks; reported with the same verdict words, not part of the headline.
- Headline ("won from lane 1", owner's criterion of 2026-10-21): on the fresh tasks only (tasks whose
  (teacher_seed, teacher_angle) was not used while E4 was developed, `--dev`), the overall verdict of E4 against C0 is
  WIN and the overall verdict of E4 against Z is WIN. Anything else is written as it is (tie, loss, mixed).
- Reported beside it, never folded in: C0 against Z; the job-level stand-in CE and accuracy with shots
  (`rehearsal.ce`, `rehearsal.acc`); the prediction layer (stand-in CE inside the twin's 99 % interval, twin-standin
  P(1) rms); the training cost (trajectory-circuits) and whether E4 stayed within C0's budget; the start (both from 0).
"""
from __future__ import annotations

import glob
import json
import math
import os
import sys

import numpy as np
from scipy.stats import binomtest, norm, rankdata

CLIP = 1e-4
DEFAULT_DEV = ("4:1.0",)  # teacher 4 at angle 1.0 was used in the noiseless rounds of 2026-10-20 (E4's development)


class Stop(Exception):
    pass


# ------------------------------------------------------------------------------------------------ per-point scores

def ce_points(p1, y):
    """Per-point CE from P(1) values, as toqb.s2r2._ce (labels +1 <-> P(1) < 0.5)."""
    p = np.clip(1.0 - np.asarray(p1, float), CLIP, 1.0 - CLIP)
    y = np.asarray(y)
    return -np.where(y > 0, np.log(p), np.log(1.0 - p))


def correct_points(p1, y):
    """Strict correctness: P(1) on the label's side; P(1) = 0.5 counts as wrong."""
    p1, y = np.asarray(p1, float), np.asarray(y)
    return np.where(y > 0, p1 < 0.5, p1 > 0.5)


# ------------------------------------------------------------------------------------------------ tests

def signed_rank_z(d):
    """Wilcoxon signed-rank z (normal approximation, tie-corrected, zeros dropped) and its two-sided p."""
    d = np.asarray(d, float)
    d = d[d != 0]
    n = len(d)
    if n == 0:
        return 0.0, 1.0
    r = rankdata(np.abs(d))
    w_plus = float(r[d > 0].sum())
    mean = n * (n + 1) / 4.0
    _, counts = np.unique(np.abs(d), return_counts=True)
    var = n * (n + 1) * (2 * n + 1) / 24.0 - float(np.sum(counts ** 3 - counts)) / 48.0
    if var <= 0:
        return 0.0, 1.0
    z = (w_plus - mean) / math.sqrt(var)
    return z, float(2 * norm.sf(abs(z)))


def mcnemar(cx, cy):
    """Exact McNemar on paired correctness: X right / Y wrong (b) against X wrong / Y right (c); two-sided p."""
    cx, cy = np.asarray(cx, bool), np.asarray(cy, bool)
    b, c = int(np.sum(cx & ~cy)), int(np.sum(~cx & cy))
    p = 1.0 if b + c == 0 else float(binomtest(b, b + c, 0.5).pvalue)
    return b, c, p


def holm(pvals):
    m = len(pvals)
    order = sorted(range(m), key=lambda i: pvals[i])
    adj, run = [0.0] * m, 0.0
    for k, i in enumerate(order):
        run = max(run, min(1.0, (m - k) * pvals[i]))
        adj[i] = run
    return adj


def verdict(p_adj, effect, alpha):
    if p_adj < alpha and effect > 0:
        return "WIN"
    if p_adj < alpha and effect < 0:
        return "LOSS"
    return "TIE"


def overall(zs, verdicts, alpha):
    if not zs:
        return dict(Z=None, p=None, verdict="NONE")
    Z = float(sum(zs) / math.sqrt(len(zs)))
    p = float(2 * norm.sf(abs(Z)))
    wins, losses = verdicts.count("WIN"), verdicts.count("LOSS")
    if wins and losses:
        v = "MIXED"
    elif p < alpha and Z > 0 and not losses:
        v = "WIN"
    elif p < alpha and Z < 0 and not wins:
        v = "LOSS"
    else:
        v = "TIE"
    return dict(Z=Z, p=p, verdict=v, task_wins=wins, task_losses=losses, tasks=len(zs))


# ------------------------------------------------------------------------------------------------ reading runs

def role_of(rec):
    if rec.get("kind") == "s2re4":
        return "Z" if int(rec.get("sweeps", rec.get("train", {}).get("sweeps", 0)) or 0) == 0 else "E4"
    if rec.get("kind") == "s2rc":
        return "C0" if float(rec.get("train", {}).get("init", 1.0)) == 0.0 else "C"
    raise Stop(f"unknown kind {rec.get('kind')!r}")


def train_cost(rec, role):
    if role in ("Z",):
        return 0
    if role == "E4":
        return int(rec.get("train_traj_circuits", 0))
    t = rec["train"]
    return int(t["loops"]) * 2 * int(t["pairs"]) * int(t["sim_batch"]) * int(t["sim_traj"])


def load_runs(runs_dir):
    files = sorted(glob.glob(os.path.join(runs_dir, "*.json")))
    if not files:
        raise Stop(f"no run records in {runs_dir}")
    tasks = {}
    for f in files:
        with open(f, encoding="utf-8") as fh:
            rec = json.load(fh)
        role = role_of(rec)
        t = rec["task"]
        key = (int(t["teacher_seed"]), float(t["teacher_angle"]), int(t["layers"]), rec.get("arm"))
        if not rec.get("valid") or "rehearsal" not in rec:
            raise Stop(f"{os.path.basename(f)} is not a valid run with a stand-in verification ({rec.get('error')})")
        y = list(rec["test_labels"])
        if set(y) != {1, -1}:
            raise Stop(f"{os.path.basename(f)}: a one-class test set is refused")
        if len(rec["rehearsal"]["standin_p1"]) != len(y):
            raise Stop(f"{os.path.basename(f)}: {len(y)} labels, {len(rec['rehearsal']['standin_p1'])} P(1) values")
        slot = tasks.setdefault(key, {})
        if role in slot:
            raise Stop(f"two {role} runs for task {key}")
        slot[role] = dict(file=os.path.basename(f), rec=rec, y=np.array(y))
    for key, slot in tasks.items():
        ys = [v["y"] for v in slot.values()]
        if any(not np.array_equal(ys[0], yy) for yy in ys[1:]):
            raise Stop(f"task {key}: the arms were scored on different test labels")
    return tasks


# ------------------------------------------------------------------------------------------------ the match

COMPARISONS = (("E4", "C0"), ("E4", "Z"), ("C0", "Z"))


def score_match(tasks, dev=DEFAULT_DEV, alpha=0.01):
    dev_set = {(int(s.split(":")[0]), float(s.split(":")[1])) for s in dev}
    keys = sorted(tasks)
    out = dict(alpha=alpha, dev_tasks=sorted(dev), tasks=[], comparisons={})
    per_arm = {}
    for key in keys:
        slot = tasks[key]
        row = dict(teacher_seed=key[0], teacher_angle=key[1], layers=key[2], arm=key[3],
                   fresh=(key[0], key[1]) not in dev_set, arms={})
        for role, v in slot.items():
            rec, rh, pr = v["rec"], v["rec"]["rehearsal"], v["rec"]["prediction"]
            p1 = np.asarray(rh["standin_p1"], float)
            ce_i = ce_points(p1, v["y"])
            per_arm[(key, role)] = (ce_i, correct_points(p1, v["y"]))
            row["arms"][role] = dict(
                file=v["file"], ce_exact_mean=float(ce_i.mean()), acc_exact=float(correct_points(p1, v["y"]).mean()),
                ce_shots=rh.get("ce"), acc_shots=rh.get("acc"), ce_inside=rh.get("ce_inside"),
                acc_inside=rh.get("acc_inside"), p1_rmse=rh.get("twin_vs_standin_p1_rmse"),
                pred_ce=pr.get("ce_mean"), train_cost=train_cost(rec, role),
                start_zero=role in ("Z", "E4", "C0"),
                sweeps=rec.get("sweeps"), loops=rec.get("loops"), train_wall_s=rec.get("train_wall_s"))
        c0, e4 = row["arms"].get("C0"), row["arms"].get("E4")
        row["e4_within_c0_budget"] = None if not (c0 and e4) else bool(e4["train_cost"] <= c0["train_cost"])
        out["tasks"].append(row)
    for x, ycmp in COMPARISONS:
        name = f"{x} vs {ycmp}"
        items = [k for k in keys if x in tasks[k] and ycmp in tasks[k]]
        res = []
        for k in items:
            cex, accx = per_arm[(k, x)]
            cey, accy = per_arm[(k, ycmp)]
            d = cey - cex
            z, p = signed_rank_z(d)
            b, c, pm = mcnemar(accx, accy)
            n = len(d)
            se = float(np.std(d, ddof=1) / math.sqrt(n)) if n > 1 else float("nan")
            res.append(dict(task=list(k), fresh=(k[0], k[1]) not in dev_set, n=n, mean_d=float(d.mean()),
                            ci99=[float(d.mean() - 2.576 * se), float(d.mean() + 2.576 * se)], z=z, p=p,
                            acc_diff=float(accx.mean() - accy.mean()), mcnemar_b=b, mcnemar_c=c, p_acc=pm))
        for sub, sel in (("all", lambda r: True), ("fresh", lambda r: r["fresh"])):
            rs = [r for r in res if sel(r)]
            adj = holm([r["p"] for r in rs])
            adj_acc = holm([r["p_acc"] for r in rs])
            vs, vs_acc = [], []
            for r, a, aa in zip(rs, adj, adj_acc):
                r.setdefault("p_holm", {})[sub] = a
                r.setdefault("verdict", {})[sub] = verdict(a, r["mean_d"], alpha)
                r.setdefault("p_acc_holm", {})[sub] = aa
                r.setdefault("verdict_acc", {})[sub] = verdict(aa, r["acc_diff"], alpha)
                vs.append(r["verdict"][sub])
                vs_acc.append(r["verdict_acc"][sub])
            out["comparisons"].setdefault(name, {})[sub] = dict(
                overall=overall([r["z"] for r in rs], vs, alpha),
                accuracy_task_verdicts=vs_acc)
        out["comparisons"][name]["tasks"] = res
    fe = out["comparisons"].get("E4 vs C0", {}).get("fresh", {}).get("overall", {}).get("verdict")
    fz = out["comparisons"].get("E4 vs Z", {}).get("fresh", {}).get("overall", {}).get("verdict")
    out["headline"] = dict(won_from_lane_1=bool(fe == "WIN" and fz == "WIN"), e4_vs_c0_fresh=fe, e4_vs_z_fresh=fz)
    budget_ok = [t["e4_within_c0_budget"] for t in out["tasks"] if t["e4_within_c0_budget"] is not None]
    out["checks"] = dict(e4_within_budget_all=all(budget_ok) if budget_ok else None,
                         fresh_tasks=sum(1 for t in out["tasks"] if t["fresh"]), tasks=len(out["tasks"]))
    return out


# ------------------------------------------------------------------------------------------------ report

def _f(v, nd=4):
    return "-" if v is None else (f"{v:.{nd}f}" if isinstance(v, float) else str(v))


def markdown(res):
    L = ["# E4 against C0 (and the theta = 0 control): match score", "",
         f"Rules: W8 (2026-10-21), alpha = {res['alpha']}, Holm over tasks per comparison; development tasks excluded "
         f"from the headline: {', '.join(res['dev_tasks']) or 'none'}. Truth tier: stand-in (simulation), not a device.", ""]
    h = res["headline"]
    L += ["## Headline (owner's criterion)", "",
          f"- Won from lane 1: **{'YES' if h['won_from_lane_1'] else 'NO'}** (fresh tasks: E4 vs C0 "
          f"{h['e4_vs_c0_fresh']}, E4 vs Z {h['e4_vs_z_fresh']}).",
          f"- E4 within C0's training budget in every task: {_f(res['checks']['e4_within_budget_all'])}; "
          f"fresh tasks {res['checks']['fresh_tasks']} of {res['checks']['tasks']}.", ""]
    L += ["## Per task and arm (stand-in)", "",
          "| teacher | angle | L | fresh | arm | CE (exact P(1)) | acc (exact, strict) | CE / acc (shots) | CE in 99 % (prediction layer) | P(1) rms | training cost (traj x circuits) |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    for t in res["tasks"]:
        for role in ("Z", "E4", "C0", "C"):
            a = t["arms"].get(role)
            if not a:
                continue
            L.append(f"| {t['teacher_seed']} | {t['teacher_angle']} | {t['layers']} | {'yes' if t['fresh'] else 'no'} | "
                     f"{role} | {_f(a['ce_exact_mean'])} | {_f(a['acc_exact'], 3)} | {_f(a['ce_shots'])} / "
                     f"{_f(a['acc_shots'], 3)} | {_f(a['ce_inside'])} | {_f(a['p1_rmse'])} | {a['train_cost']:,} |")
    for name, comp in res["comparisons"].items():
        L += ["", f"## {name}", "",
              f"- Overall, all tasks: {comp['all']['overall']['verdict']} (Stouffer Z {_f(comp['all']['overall']['Z'], 2)}, "
              f"p {_f(comp['all']['overall']['p'], 4)}); fresh tasks: {comp['fresh']['overall']['verdict']} "
              f"(Z {_f(comp['fresh']['overall']['Z'], 2)}, p {_f(comp['fresh']['overall']['p'], 4)}).", "",
              "| teacher | angle | L | fresh | mean CE gain (99 % CI) | Wilcoxon p | Holm p (all) | verdict (all / fresh) | acc diff | McNemar b / c | acc verdict (all) |",
              "|---|---|---|---|---|---|---|---|---|---|---|"]
        for r in comp["tasks"]:
            ts, ta, Ly, _ = r["task"]
            L.append(f"| {ts} | {ta} | {Ly} | {'yes' if r['fresh'] else 'no'} | {r['mean_d']:+.4f} "
                     f"({r['ci99'][0]:+.4f}, {r['ci99'][1]:+.4f}) | {r['p']:.2e} | {r['p_holm']['all']:.2e} | "
                     f"{r['verdict']['all']} / {r['verdict'].get('fresh', '-')} | {r['acc_diff']:+.3f} | "
                     f"{r['mcnemar_b']} / {r['mcnemar_c']} | {r['verdict_acc']['all']} |")
    L += ["", "## Vanity and essential figures", "",
          "| | figure |", "|---|---|",
          "| Vanity | the best single task's accuracy gain of E4 over C0 (fill from the table above) |",
          "| Essential | the fresh-task overall verdicts above (E4 vs C0, E4 vs Z), with the mean CE gains and 99 % CIs; "
          "one stand-in, PSF arm only, simulation, 3 teachers x 2 depths; equal training budget and the same start |", ""]
    return "\n".join(L) + "\n"


def main(argv):
    try:
        args, dev, js, alpha = [], list(DEFAULT_DEV), None, 0.01
        i, dev_given = 0, False
        while i < len(argv):
            a = argv[i]
            if a == "--json":
                js, i = argv[i + 1], i + 2
            elif a == "--alpha":
                alpha, i = float(argv[i + 1]), i + 2
            elif a == "--dev":
                if not dev_given:
                    dev, dev_given = [], True
                i += 1
                while i < len(argv) and not argv[i].startswith("--"):
                    dev.append(argv[i])
                    i += 1
            else:
                args.append(a)
                i += 1
        if len(args) != 2:
            print(__doc__)
            return 1
        runs, out_md = args
        for f in (out_md, js):
            if f and os.path.exists(f):
                raise Stop(f"{f} exists: an output is never overwritten")
        res = score_match(load_runs(runs), dev=dev, alpha=alpha)
        with open(out_md, "w", encoding="utf-8") as f:
            f.write(markdown(res))
        if js:
            with open(js, "w", encoding="utf-8") as f:
                json.dump(res, f, indent=1)
        print(f"written {out_md}" + (f" and {js}" if js else "") + f"; won from lane 1: {res['headline']['won_from_lane_1']}")
        return 0
    except Stop as exc:
        print(f"STOP: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
