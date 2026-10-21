"""Score table and verdicts of the fruit match (E4 against C0 at equal early cost), rules fixed before the results
(W11, 2026-10-21).

    python -m toqb.match_score_fruit RUNS_DIR OUT.md [--json OUT.json] [--alpha 0.01] [--seen 4 5 6]

Reads every run record (`*.json`) in RUNS_DIR:

- Z: kind "s2re4" with sweeps = 0 (theta = 0, no training);
- E4: kind "s2re4" with sweeps > 0; its checkpoints carry `sweep` and the last sweep is at the record's top level;
- C0: kind "s2rc" with runner "toqb.s2rc_ckpt" and init 0; its checkpoints carry `loop` and the full budget
  (2,000 loops) is at the top level.

A task is (teacher_seed, teacher_angle, layers, arm). The headline uses, per task, the C0 run with training seed 201
and the E4 run whose twin seed equals the teacher seed; any other C0 or E4 runs of a task are used for F3 only.
Budget points are matched by `train_traj_circuits` exactly (a mismatch is a STOP). The W8 machinery is imported from
toqb.match_score (per-point CE from the stand-in's exact P(1), Wilcoxon signed-rank z, Holm, verdicts). Pure Python
with numpy and scipy; nothing is simulated. Outputs are never overwritten (exit 2).

The rules (W11; the text is in W11_fruit_rules_2026-10-21.md):

- F1 (headline), at f_min = E4's first sweep and C0 at exactly the same cost: E4 against C0 and E4 against Z, per
  task (Wilcoxon on per-point CE differences, Holm over all tasks of that comparison at f_min, alpha 0.01).
  Per group g = (angle, layers): Stouffer's Z over the group's tasks, two-sided p, Holm over the groups;
  group verdict WIN if the Holm-adjusted p < alpha, Z > 0 and no task of the group LOSS; LOSS symmetrically; MIXED if
  the group's tasks have both WIN and LOSS; else TIE. A group is "won in the fruit zone" iff its E4-vs-C0 verdict and
  its E4-vs-Z verdict are both WIN. The headline lists every group's result; no group is singled out. A pooled
  verdict over all tasks (W8's overall) is reported beside it, not as the headline.
- F2 (reported): the same statistics at every matched point, and E4's last sweep against C0's full budget
  (unequal cost, labelled: the peel).
- F3 (reported): on tasks with several seeds, the standard deviation over seeds of the stand-in CE (exact P(1) mean
  and shots) at every point.
- F4 (reported): for every run and every point, the stand-in CE inside the twin's 99 % interval; the count and an
  exact two-sided binomial test against 0.99 (points of one run are not independent; stated).
- F5 (reported): for every E4 run, whether its stand-in CE (exact P(1) mean) is non-increasing over its sweeps.
"""
from __future__ import annotations

import glob
import json
import math
import os
import sys

import numpy as np
from scipy.stats import binomtest, norm

from toqb.match_score import Stop, ce_points, correct_points, holm, mcnemar, overall, signed_rank_z, verdict

PRIMARY_C0_SEED = 201
DEFAULT_SEEN = (4, 5, 6)


# ------------------------------------------------------------------------------------------------ reading

def role_of(rec):
    if rec.get("kind") == "s2re4":
        return "Z" if int(rec.get("sweeps", 0) or 0) == 0 else "E4"
    if rec.get("kind") == "s2rc":
        if rec.get("runner") != "toqb.s2rc_ckpt":
            raise Stop("a C0 record without checkpoints (runner is not toqb.s2rc_ckpt)")
        if float(rec.get("train", {}).get("init", 1.0)) != 0.0:
            raise Stop("a C record that does not start from theta = 0")
        return "C0"
    raise Stop(f"unknown kind {rec.get('kind')!r}")


def points_of(rec, role):
    """The run's budget points, sorted by cost: dicts with cost, label, rehearsal, prediction, final."""
    if role == "Z":
        return [dict(cost=0, label="theta = 0", rh=rec["rehearsal"], pr=rec["prediction"], final=True)]
    pts = []
    for c in rec.get("checkpoints", []):
        lab = f"loop {c['loop']}" if role == "C0" else f"sweep {c['sweep']}"
        pts.append(dict(cost=int(c["train_traj_circuits"]), label=lab, rh=c["rehearsal"], pr=c["prediction"],
                        final=False))
    lab = f"loop {rec.get('loops')}" if role == "C0" else f"sweep {rec.get('sweeps')}"
    pts.append(dict(cost=int(rec["train_traj_circuits"]), label=lab, rh=rec["rehearsal"], pr=rec["prediction"],
                    final=True))
    pts.sort(key=lambda p: p["cost"])
    return pts


def load_runs(runs_dir):
    files = sorted(glob.glob(os.path.join(runs_dir, "*.json")))
    if not files:
        raise Stop(f"no run records in {runs_dir}")
    tasks = {}
    for f in files:
        with open(f, encoding="utf-8") as fh:
            rec = json.load(fh)
        name = os.path.basename(f)
        if not rec.get("valid") or "rehearsal" not in rec:
            raise Stop(f"{name} is not a valid run with a stand-in verification ({rec.get('error')})")
        role = role_of(rec)
        t = rec["task"]
        key = (int(t["teacher_seed"]), float(t["teacher_angle"]), int(t["layers"]), rec.get("arm"))
        y = np.array(rec["test_labels"])
        if set(y.tolist()) != {1, -1}:
            raise Stop(f"{name}: a one-class test set is refused")
        pts = points_of(rec, role)
        for p in pts:
            if len(p["rh"]["standin_p1"]) != len(y):
                raise Stop(f"{name}: {len(y)} labels, {len(p['rh']['standin_p1'])} P(1) values at {p['label']}")
        seed = int(rec.get("seed", rec.get("train", {}).get("seed", -1)))
        slot = tasks.setdefault(key, {"Z": None, "C0": {}, "E4": {}, "y": y})
        if not np.array_equal(slot["y"], y):
            raise Stop(f"task {key}: runs scored on different test labels")
        run = dict(file=name, seed=seed, points=pts, rec=rec)
        if role == "Z":
            if slot["Z"] is not None:
                raise Stop(f"two Z runs for task {key}")
            slot["Z"] = run
        else:
            if seed in slot[role]:
                raise Stop(f"two {role} runs with seed {seed} for task {key}")
            slot[role][seed] = run
    return tasks


def primary(tasks, key):
    slot = tasks[key]
    c0 = slot["C0"].get(PRIMARY_C0_SEED)
    e4 = slot["E4"].get(key[0])
    if slot["Z"] is None or c0 is None or e4 is None:
        raise Stop(f"task {key}: needs Z, C0 seed {PRIMARY_C0_SEED} and E4 twin seed {key[0]}")
    return slot["Z"], c0, e4


def matched(c0, e4):
    """Pairs (E4 point, C0 point) at equal cost, one per E4 sweep; a cost E4 reaches that C0 lacks is a STOP."""
    by_cost = {p["cost"]: p for p in c0["points"]}
    pairs = []
    for p in e4["points"]:
        if p["cost"] not in by_cost:
            raise Stop(f"no C0 point at E4's cost {p['cost']:,} ({e4['file']} {p['label']}; C0 has "
                       f"{sorted(by_cost)})")
        pairs.append((p, by_cost[p["cost"]]))
    return pairs


# ------------------------------------------------------------------------------------------------ statistics

def compare(x_pt, y_pt, ylab):
    """X against Y at one point of one task: per-point CE gain d = CE(Y) - CE(X), Wilcoxon z / p, accuracy."""
    cex, cey = ce_points(x_pt["rh"]["standin_p1"], ylab), ce_points(y_pt["rh"]["standin_p1"], ylab)
    accx, accy = correct_points(x_pt["rh"]["standin_p1"], ylab), correct_points(y_pt["rh"]["standin_p1"], ylab)
    d = cey - cex
    z, p = signed_rank_z(d)
    b, c, pm = mcnemar(accx, accy)
    se = float(np.std(d, ddof=1) / math.sqrt(len(d)))
    return dict(mean_d=float(d.mean()), ci99=[float(d.mean() - 2.576 * se), float(d.mean() + 2.576 * se)], z=z, p=p,
                acc_diff=float(accx.mean() - accy.mean()), mcnemar_b=b, mcnemar_c=c, p_acc=pm,
                ce_x=float(cex.mean()), ce_y=float(cey.mean()))


def group_verdicts(rows, alpha):
    """rows: dicts with group, z, verdict (task-level). Stouffer per group, Holm over groups."""
    groups = sorted({r["group"] for r in rows})
    res = []
    for g in groups:
        rs = [r for r in rows if r["group"] == g]
        Z = float(sum(r["z"] for r in rs) / math.sqrt(len(rs)))
        res.append(dict(group=list(g), tasks=len(rs), Z=Z, p=float(2 * norm.sf(abs(Z))),
                        task_wins=sum(r["verdict"] == "WIN" for r in rs),
                        task_losses=sum(r["verdict"] == "LOSS" for r in rs)))
    adj = holm([r["p"] for r in res])
    for r, a in zip(res, adj):
        r["p_holm"] = a
        if r["task_wins"] and r["task_losses"]:
            r["verdict"] = "MIXED"
        elif a < alpha and r["Z"] > 0 and not r["task_losses"]:
            r["verdict"] = "WIN"
        elif a < alpha and r["Z"] < 0 and not r["task_wins"]:
            r["verdict"] = "LOSS"
        else:
            r["verdict"] = "TIE"
    return res


def comparison_at(tasks, keys, which, k, alpha, seen):
    """One comparison ('E4 vs C0', 'E4 vs Z', 'C0 vs Z') at matched point index k (0 = f_min), all tasks."""
    rows = []
    for key in keys:
        Z, c0, e4 = primary(tasks, key)
        pairs = matched(c0, e4)
        if k >= len(pairs):
            continue
        e_pt, c_pt = pairs[k]
        z_pt = Z["points"][0]
        x, y = {"E4 vs C0": (e_pt, c_pt), "E4 vs Z": (e_pt, z_pt), "C0 vs Z": (c_pt, z_pt)}[which]
        r = compare(x, y, tasks[key]["y"])
        r.update(task=list(key), group=(key[1], key[2]), fresh=key[0] not in seen, cost=e_pt["cost"],
                 labels=[e_pt["label"], c_pt["label"]])
        rows.append(r)
    adj = holm([r["p"] for r in rows])
    adj_acc = holm([r["p_acc"] for r in rows])
    for r, a, aa in zip(rows, adj, adj_acc):
        r["p_holm"], r["verdict"] = a, verdict(a, r["mean_d"], alpha)
        r["p_acc_holm"], r["verdict_acc"] = aa, verdict(aa, r["acc_diff"], alpha)
    groups = group_verdicts(rows, alpha) if rows else []
    pooled = overall([r["z"] for r in rows], [r["verdict"] for r in rows], alpha)
    return dict(rows=rows, groups=groups, pooled=pooled)


# ------------------------------------------------------------------------------------------------ the match

def score_fruit(tasks, alpha=0.01, seen=DEFAULT_SEEN):
    seen = set(int(s) for s in seen)
    keys = sorted(tasks)
    n_pts = {key: len(matched(primary(tasks, key)[1], primary(tasks, key)[2])) for key in keys}
    out = dict(alpha=alpha, seen_teachers=sorted(seen), tasks=[list(k) for k in keys], f1={}, f2=[], peel={})
    stale = [k for k in keys if k[0] in seen]
    if stale:
        out["warning_seen_teachers_present"] = [list(k) for k in stale]
    # F1
    for which in ("E4 vs C0", "E4 vs Z", "C0 vs Z"):
        out["f1"][which] = comparison_at(tasks, keys, which, 0, alpha, seen)
    g_c0 = {tuple(g["group"]): g["verdict"] for g in out["f1"]["E4 vs C0"]["groups"]}
    g_z = {tuple(g["group"]): g["verdict"] for g in out["f1"]["E4 vs Z"]["groups"]}
    out["headline"] = [dict(angle=g[0], layers=g[1], e4_vs_c0=g_c0[g], e4_vs_z=g_z.get(g),
                            won_in_fruit_zone=bool(g_c0[g] == "WIN" and g_z.get(g) == "WIN"))
                       for g in sorted(g_c0)]
    out["headline_pooled"] = dict(e4_vs_c0=out["f1"]["E4 vs C0"]["pooled"]["verdict"],
                                  e4_vs_z=out["f1"]["E4 vs Z"]["pooled"]["verdict"])
    # F2: every matched point, and the peel (E4's last sweep against C0's full budget)
    for k in range(max(n_pts.values())):
        out["f2"].append(dict(point=k + 1, **{w: comparison_at(tasks, [kk for kk in keys if n_pts[kk] > k], w, k,
                                                               alpha, seen) for w in ("E4 vs C0", "E4 vs Z")}))
    peel_rows = []
    for key in keys:
        _, c0, e4 = primary(tasks, key)
        r = compare(e4["points"][-1], c0["points"][-1], tasks[key]["y"])
        r.update(task=list(key), group=(key[1], key[2]), costs=[e4["points"][-1]["cost"], c0["points"][-1]["cost"]],
                 labels=[e4["points"][-1]["label"], c0["points"][-1]["label"]])
        peel_rows.append(r)
    adj = holm([r["p"] for r in peel_rows])
    for r, a in zip(peel_rows, adj):
        r["p_holm"], r["verdict"] = a, verdict(a, r["mean_d"], alpha)
    out["peel"] = dict(rows=peel_rows, pooled=overall([r["z"] for r in peel_rows], [r["verdict"] for r in peel_rows],
                                                      alpha), note="unequal cost: E4's last sweep against C0's full budget")
    # F3: spread over seeds
    f3 = []
    for key in keys:
        slot = tasks[key]
        for role in ("C0", "E4"):
            runs = slot[role]
            if len(runs) < 2:
                continue
            costs = sorted({p["cost"] for r in runs.values() for p in r["points"]})
            for cst in costs:
                vals_exact, vals_shots = [], []
                for r in runs.values():
                    p = next((q for q in r["points"] if q["cost"] == cst), None)
                    if p is not None:
                        vals_exact.append(float(ce_points(p["rh"]["standin_p1"], slot["y"]).mean()))
                        vals_shots.append(float(p["rh"].get("ce", float("nan"))))
                if len(vals_exact) >= 2:
                    f3.append(dict(task=list(key), arm=role, cost=cst, seeds=sorted(runs), n=len(vals_exact),
                                   mean_ce_exact=float(np.mean(vals_exact)), sd_ce_exact=float(np.std(vals_exact, ddof=1)),
                                   sd_ce_shots=float(np.std(vals_shots, ddof=1))))
    out["f3"] = f3
    # F4: the prediction layer over every run and point
    k_in, n_all, per_role = 0, 0, {}
    for key in keys:
        slot = tasks[key]
        runs = ([("Z", slot["Z"])] if slot["Z"] else []) + [("C0", r) for r in slot["C0"].values()] + \
               [("E4", r) for r in slot["E4"].values()]
        for role, r in runs:
            for p in r["points"]:
                inside = bool(p["rh"].get("ce_inside"))
                k_in += inside
                n_all += 1
                pr = per_role.setdefault(role, [0, 0])
                pr[0] += inside
                pr[1] += 1
    out["f4"] = dict(inside=k_in, total=n_all, p_binom_vs_099=float(binomtest(k_in, n_all, 0.99).pvalue) if n_all else None,
                     per_role={k: dict(inside=v[0], total=v[1]) for k, v in per_role.items()},
                     note="checkpoints of one run are not independent; the binomial p is indicative only")
    # F5: E4's stand-in CE over sweeps
    f5 = []
    for key in keys:
        for seed, r in sorted(tasks[key]["E4"].items()):
            ces = [float(ce_points(p["rh"]["standin_p1"], tasks[key]["y"]).mean()) for p in r["points"]]
            rises = [round(ces[i + 1] - ces[i], 6) for i in range(len(ces) - 1) if ces[i + 1] > ces[i]]
            f5.append(dict(task=list(key), seed=seed, ce_by_sweep=ces, non_increasing=not rises, rises=rises))
    out["f5"] = dict(runs=f5, non_increasing=sum(x["non_increasing"] for x in f5), total=len(f5),
                     note="E4's guarantee is on the twin's training loss; this checks the stand-in's test CE")
    out["checks"] = dict(points_per_task={f"{k[0]}/{k[1]}/L{k[2]}": n_pts[k] for k in keys})
    return out


# ------------------------------------------------------------------------------------------------ report

def _f(v, nd=4):
    if v is None:
        return "-"
    return f"{v:.{nd}f}" if isinstance(v, float) else str(v)


def _comp_table(c, title):
    L = [f"### {title}", "",
         "| group (angle, L) | tasks | Stouffer Z | Holm p | verdict |", "|---|---|---|---|---|"]
    for g in c["groups"]:
        L.append(f"| {g['group'][0]}, L{g['group'][1]} | {g['tasks']} | {g['Z']:+.2f} | {g['p_holm']:.2e} | {g['verdict']} |")
    L += ["", f"Pooled over all tasks: {c['pooled']['verdict']} (Z {_f(c['pooled']['Z'], 2)}, p {_f(c['pooled']['p'], 4)}).", "",
          "| teacher | angle | L | points | CE X / CE Y | mean CE gain (99 % CI) | Wilcoxon p | Holm p | verdict | acc diff | McNemar b / c | acc verdict |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in c["rows"]:
        ts, ta, Ly, _ = r["task"]
        L.append(f"| {ts} | {ta} | {Ly} | {' / '.join(r['labels'])} | {r['ce_x']:.4f} / {r['ce_y']:.4f} | "
                 f"{r['mean_d']:+.4f} ({r['ci99'][0]:+.4f}, {r['ci99'][1]:+.4f}) | {r['p']:.2e} | {r['p_holm']:.2e} | "
                 f"{r['verdict']} | {r['acc_diff']:+.3f} | {r['mcnemar_b']} / {r['mcnemar_c']} | {r['verdict_acc']} |")
    return L + [""]


def markdown(res):
    L = ["# The fruit match: E4 against C0 at equal early cost (with the theta = 0 control)", "",
         f"Rules: W11 (2026-10-21), alpha = {res['alpha']}; W8's per-point statistics; groups = (angle, layers), Holm "
         f"over groups. Truth tier: stand-in (simulation), not a device.", ""]
    if res.get("warning_seen_teachers_present"):
        L += [f"**Warning:** tasks with teachers seen before (not fresh): {res['warning_seen_teachers_present']}.", ""]
    L += ["## Headline (F1, at f_min = E4's first sweep and C0 at the same cost)", "",
          "| group (angle, L) | E4 vs C0 | E4 vs Z | won in the fruit zone |", "|---|---|---|---|"]
    for h in res["headline"]:
        L.append(f"| {h['angle']}, L{h['layers']} | {h['e4_vs_c0']} | {h['e4_vs_z']} | {'YES' if h['won_in_fruit_zone'] else 'NO'} |")
    won = [f"{h['angle']}/L{h['layers']}" for h in res["headline"] if h["won_in_fruit_zone"]]
    L += ["", f"Won in the fruit zone in {len(won)} of {len(res['headline'])} groups"
          + (f": {', '.join(won)}." if won else "."),
          f"Pooled over all tasks (reported, not the headline): E4 vs C0 {res['headline_pooled']['e4_vs_c0']}, "
          f"E4 vs Z {res['headline_pooled']['e4_vs_z']}.", ""]
    for w in ("E4 vs C0", "E4 vs Z", "C0 vs Z"):
        L += _comp_table(res["f1"][w], f"F1: {w}")
    L += ["## F2: every matched point (reported)", ""]
    for pt in res["f2"]:
        for w in ("E4 vs C0", "E4 vs Z"):
            c = pt[w]
            gs = "; ".join(f"{g['group'][0]}/L{g['group'][1]} {g['verdict']} (Z {g['Z']:+.2f})" for g in c["groups"])
            L.append(f"- point {pt['point']}, {w}: pooled {c['pooled']['verdict']} (Z {_f(c['pooled']['Z'], 2)}); groups: {gs}")
    pe = res["peel"]
    L += ["", f"**The peel** ({pe['note']}): pooled {pe['pooled']['verdict']} (Z {_f(pe['pooled']['Z'], 2)}).", "",
          "| teacher | angle | L | points (E4 / C0) | mean CE gain of E4 (99 % CI) | Holm p | verdict |", "|---|---|---|---|---|---|---|"]
    for r in pe["rows"]:
        ts, ta, Ly, _ = r["task"]
        L.append(f"| {ts} | {ta} | {Ly} | {' / '.join(r['labels'])} | {r['mean_d']:+.4f} ({r['ci99'][0]:+.4f}, "
                 f"{r['ci99'][1]:+.4f}) | {r['p_holm']:.2e} | {r['verdict']} |")
    L += ["", "## F3: spread over seeds (reported)", "",
          "| task (teacher, angle, L) | arm | cost (traj x circuits) | seeds | mean CE (exact) | SD CE (exact) | SD CE (shots) |",
          "|---|---|---|---|---|---|---|"]
    for r in res["f3"]:
        L.append(f"| {r['task'][0]}, {r['task'][1]}, L{r['task'][2]} | {r['arm']} | {r['cost']:,} | {r['seeds']} | "
                 f"{r['mean_ce_exact']:.4f} | {r['sd_ce_exact']:.4f} | {r['sd_ce_shots']:.4f} |")
    f4 = res["f4"]
    L += ["", "## F4: the prediction layer (reported)", "",
          f"Stand-in CE inside the twin's 99 % interval: {f4['inside']} of {f4['total']} run-points "
          f"(exact binomial against 0.99: p = {_f(f4['p_binom_vs_099'], 4)}; {f4['note']}). By arm: "
          + ", ".join(f"{k} {v['inside']}/{v['total']}" for k, v in f4["per_role"].items()) + ".", ""]
    f5 = res["f5"]
    L += ["## F5: E4's stand-in CE over its sweeps (reported)", "",
          f"Non-increasing in {f5['non_increasing']} of {f5['total']} E4 runs ({f5['note']}).", ""]
    for r in f5["runs"]:
        if not r["non_increasing"]:
            L.append(f"- rises in task {r['task'][:3]}, seed {r['seed']}: CE by sweep {[round(x, 4) for x in r['ce_by_sweep']]}")
    L += ["", "## Vanity and essential figures", "", "| | figure |", "|---|---|",
          "| Vanity | the largest single-task CE gain of E4 over C0 at f_min (from the F1 table) |",
          "| Essential | the per-group headline above (every group, as it came), with mean CE gains and 99 % CIs; the peel "
          "at full budget as it came; one stand-in, PSF arm only, simulation, fresh teachers 7-9 |", ""]
    return "\n".join(L) + "\n"


def main(argv):
    try:
        args, js, alpha, seen = [], None, 0.01, list(DEFAULT_SEEN)
        i, seen_given = 0, False
        while i < len(argv):
            a = argv[i]
            if a == "--json":
                js, i = argv[i + 1], i + 2
            elif a == "--alpha":
                alpha, i = float(argv[i + 1]), i + 2
            elif a == "--seen":
                if not seen_given:
                    seen, seen_given = [], True
                i += 1
                while i < len(argv) and not argv[i].startswith("--"):
                    seen.append(int(argv[i]))
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
        res = score_fruit(load_runs(runs), alpha=alpha, seen=seen)
        with open(out_md, "w", encoding="utf-8") as f:
            f.write(markdown(res))
        if js:
            with open(js, "w", encoding="utf-8") as f:
                json.dump(res, f, indent=1)
        won = sum(h["won_in_fruit_zone"] for h in res["headline"])
        print(f"written {out_md}" + (f" and {js}" if js else "") + f"; won in the fruit zone in {won} of "
              f"{len(res['headline'])} groups")
        return 0
    except Stop as exc:
        print(f"STOP: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
