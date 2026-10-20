"""TOQB v0.2, prediction layer (prototype): score a twin's pre-registered prediction against a measurement.

    python -m toqb.predscore PRED.json MEAS.json OUT.json [--ref REF_PRED.json]
    python -m toqb.predscore from-s2rc RECORD.json OUT_PRED.json [--price USD_PER_GPU_HOUR]
    python -m toqb.predscore from-device JOB_DIR CELL OUT_MEAS.json --pred PRED.json
    python -m toqb.predscore from-rehearsal RECORD.json OUT_MEAS.json --pred PRED.json

Three artifacts (JSON), each written once and never overwritten (an existing output stops the command, exit 2):

- prediction (`toqb-pred/0`): per test point, the twin's P(1) (readout included) and label, the twin's trajectory
  count (its Monte Carlo error), the job-level intervals and the prediction's cost;
- measurement (`toqb-meas/0`): per test point, the shot count of 1s out of n shots ("shots"), or an exact P(1)
  ("exact-no-shots", the rehearsal's stand-in, where shot counts were not stored). It names the truth tier
  ("device", "stand-in", "twin", "noiseless") and the SHA-256 of the prediction file it answers;
- score (`toqb-score/0`): the metrics below, with the SHA-256 of both inputs.

Separation of truth and scored code (checked by tests/test_predscore.py): this module imports numpy and scipy only. It
cannot simulate a circuit, so it cannot produce truth; it only compares two files, and it stops when the measurement
does not name the exact prediction file (by SHA-256) it is scored against.

Metrics (W4 section 2):

- per point, shots: the log predictive probability of the observed count, log P(k_i), where P is the binomial mixed
  over the twin's Monte Carlo error, p ~ Normal(p1, p1 (1 - p1) / T) clipped (Gauss-Hermite, no sampling); summed, and
  as the difference against a reference prediction ("information over the reference", nats);
- calibration: the observed total log score against its expectation under the prediction, in standard deviations;
- coverage: the share of points whose mid-distribution PIT lies inside the central 50 / 90 / 99 % of the predictive;
- job level (design C's R1 and R2): CE and accuracy of the measured fractions, inside the predicted intervals or not,
  and the gaps;
- the same metrics per class. A measurement or prediction with only one class is refused (a one-class evaluation was
  the learning curve's flaw found on 2026-10-20).

Labels: y = +1 means <Z> > 0, that is P(1) < 0.5 (as toqb.s2r2). CE as toqb.s2r2._ce: p = 1 - P(1) clipped to
[1e-4, 1 - 1e-4]; -log p for y = +1, -log(1 - p) for y = -1.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import os
import sys

import numpy as np
from scipy.special import roots_hermite
from scipy.stats import binom

VERSION = "toqb.predscore prototype 0.1 (2026-10-20)"
FORMAT_PRED, FORMAT_MEAS, FORMAT_SCORE = "toqb-pred/0", "toqb-meas/0", "toqb-score/0"
TIERS = ("noiseless", "twin", "stand-in", "device")
CLIP_CE = 1e-4
P_EPS = 1e-9
GH_NODES = 24
LEVELS = (0.5, 0.9, 0.99)


class Stop(Exception):
    """A refusal: the inputs are inconsistent, a hash differs, or an output exists. Exit code 2."""


# ------------------------------------------------------------------------------------------------ files and hashes

def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha256_file(path):
    with open(path, "rb") as f:
        return sha256_bytes(f.read())


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def write_new(path, obj):
    """Write obj as JSON to a path that must not exist; return the file's SHA-256."""
    if os.path.exists(path):
        raise Stop(f"{path} exists: an artifact is never overwritten")
    data = json.dumps(obj, indent=1, sort_keys=True).encode("utf-8")
    with open(path + ".tmp", "wb") as f:
        f.write(data)
    os.replace(path + ".tmp", path)
    return sha256_bytes(data)


def now_stamp():
    t = dt.datetime.now(dt.timezone.utc)
    return t.isoformat(timespec="seconds")


def parse_time(s):
    """UTC datetime from an ISO stamp ('2026-10-20T04:07:09+00:00 (…)' or plain ISO); None when not parseable."""
    if not s or not isinstance(s, str):
        return None
    try:
        t = dt.datetime.fromisoformat(s.split(" (")[0].strip())
    except ValueError:
        return None
    if t.tzinfo is None:
        return None
    return t.astimezone(dt.timezone.utc)


# ------------------------------------------------------------------------------------------------ scoring rules

def ce_of_p1(p1, y):
    """Cross-entropy of P(1) values against labels y in {+1, -1}, as toqb.s2r2._ce."""
    p = np.clip(1.0 - np.asarray(p1, float), CLIP_CE, 1.0 - CLIP_CE)
    y = np.asarray(y)
    return float(np.mean(-np.where(y > 0, np.log(p), np.log(1.0 - p))))


def acc_strict(p1, y):
    """Correct when P(1) is strictly on the label's side; P(1) = 0.5 counts as wrong (design C's H1 count)."""
    p1, y = np.asarray(p1, float), np.asarray(y)
    return float(np.mean(np.where(y > 0, p1 < 0.5, p1 > 0.5)))


def acc_half(p1, y):
    """Accuracy with a tie (P(1) = 0.5) counted 0.5, as the predictions count it."""
    p1, y = np.asarray(p1, float), np.asarray(y)
    right = np.where(y > 0, p1 < 0.5, p1 > 0.5).astype(float)
    return float(np.mean(np.where(p1 == 0.5, 0.5, right)))


_GH = roots_hermite(GH_NODES)


def predictive_pmf(p1, traj, n):
    """P(k) for k = 0..n: Binomial(n, p) mixed over p ~ Normal(p1, p1 (1 - p1) / traj), clipped to (0, 1).
    traj = None or 0 means no Monte Carlo error (a point prediction)."""
    k = np.arange(n + 1)
    if not traj:
        return binom.pmf(k, n, min(max(p1, P_EPS), 1 - P_EPS))
    x, w = _GH
    sd = math.sqrt(max(p1 * (1 - p1), 0.0) / traj)
    ps = np.clip(p1 + math.sqrt(2.0) * sd * x, P_EPS, 1 - P_EPS)
    pmf = (w / math.sqrt(math.pi)) @ binom.pmf(k[None, :], n, ps[:, None])
    return pmf / pmf.sum()


def _point_shots(p1, traj, k, n):
    """Log score, its expectation and variance under the prediction, and the mid-distribution PIT of k."""
    pmf = predictive_pmf(p1, traj, n)
    logp = np.log(np.maximum(pmf, 1e-300))
    ls = float(logp[k])
    e = float(np.sum(pmf * logp))
    v = float(np.sum(pmf * logp ** 2) - e ** 2)
    cdf_below = float(pmf[:k].sum())
    pit = cdf_below + 0.5 * float(pmf[k])
    return ls, e, max(v, 0.0), pit


def _coverage(pit):
    pit = np.asarray(pit)
    return {f"{lev:.2f}": float(np.mean((pit > (1 - lev) / 2) & (pit < (1 + lev) / 2))) for lev in LEVELS}


def _coverage_z(r):
    """Coverage of standardised residuals r against Normal(0, 1) central intervals."""
    from scipy.stats import norm
    r = np.abs(np.asarray(r))
    return {f"{lev:.2f}": float(np.mean(r <= norm.ppf((1 + lev) / 2))) for lev in LEVELS}


# ------------------------------------------------------------------------------------------------ validation

def _check_pred(pred):
    if pred.get("format") != FORMAT_PRED:
        raise Stop(f"prediction format {pred.get('format')!r}, expected {FORMAT_PRED}")
    pts = pred["points"]
    if [p["i"] for p in pts] != list(range(len(pts))):
        raise Stop("prediction points must be numbered 0..P-1 in order")
    ys = {p["label"] for p in pts}
    if not ys <= {1, -1}:
        raise Stop(f"labels must be +1 or -1, found {sorted(ys)}")
    if ys != {1, -1}:
        raise Stop("one-class evaluation refused: the prediction must cover both classes")
    if any(not (0.0 <= p["p1"] <= 1.0) for p in pts):
        raise Stop("a predicted P(1) lies outside [0, 1]")


def _check_meas(meas, pred_sha):
    if meas.get("format") != FORMAT_MEAS:
        raise Stop(f"measurement format {meas.get('format')!r}, expected {FORMAT_MEAS}")
    if meas.get("kind") not in ("shots", "exact-no-shots"):
        raise Stop(f"measurement kind {meas.get('kind')!r}")
    if meas.get("tier") not in TIERS:
        raise Stop(f"truth tier {meas.get('tier')!r}, expected one of {TIERS}")
    named = meas.get("inputs", {}).get("prediction_sha256")
    if named != pred_sha:
        raise Stop(f"the measurement answers prediction {str(named)[:16]}..., not this file ({pred_sha[:16]}...)")


def _aligned(pred, meas):
    mp = {m["i"]: m for m in meas["points"]}
    if sorted(mp) != [p["i"] for p in pred["points"]]:
        raise Stop("the measurement does not cover exactly the prediction's points")
    return [mp[p["i"]] for p in pred["points"]]


# ------------------------------------------------------------------------------------------------ the score

def score(pred, meas, pred_sha, meas_sha, ref=None, ref_sha=None):
    """The Score artifact (a dict) for a prediction and a measurement already loaded; pure: reads nothing else."""
    _check_pred(pred)
    _check_meas(meas, pred_sha)
    m_pts = _aligned(pred, meas)
    if ref is not None:
        _check_pred(ref)
        if [(p["i"], p["label"]) for p in ref["points"]] != [(p["i"], p["label"]) for p in pred["points"]]:
            raise Stop("the reference prediction has other points or labels")
    y = np.array([p["label"] for p in pred["points"]])
    p1 = np.array([p["p1"] for p in pred["points"]], float)
    traj = pred["twin"].get("traj")
    refs = {"chance": (np.full_like(p1, 0.5), None)}
    if ref is not None:
        refs["reference"] = (np.array([p["p1"] for p in ref["points"]], float), ref["twin"].get("traj"))
    out = dict(format=FORMAT_SCORE, written=now_stamp(), producer=dict(name="toqb.predscore", version=VERSION,
               script_sha256=sha256_file(os.path.abspath(__file__))),
               inputs=dict(prediction_sha256=pred_sha, measurement_sha256=meas_sha, reference_sha256=ref_sha),
               kind=meas["kind"], tier=meas["tier"], points=int(len(y)),
               classes={"+1": int(np.sum(y > 0)), "-1": int(np.sum(y < 0))})
    # when was the prediction fixed: its own field, or the device job's manifest (written and hashed before submission)
    t_pred = parse_time(pred.get("fixed_at")) or parse_time(meas.get("prediction_fixed_at"))
    # the truth cannot exist before the job was submitted: compare with the submission time when the measurement has
    # it (home review, 2026-10-20), else with the time the truth was observed
    t_obs = parse_time(meas.get("truth_not_before")) or parse_time(meas.get("observed_at"))
    order = None if (t_pred is None or t_obs is None) else bool(t_pred < t_obs)
    by_hash = bool(pred.get("fixed_by_hash", False) or meas.get("inputs", {}).get("manifest_sha256"))
    out["prediction_fixed_before_truth"] = order
    out["prediction_fixed_by_hash"] = by_hash
    out["claimable"] = bool(meas["tier"] == "device" and meas["kind"] == "shots" and order is True and by_hash)
    if meas["kind"] == "shots":
        out.update(_score_shots(pred, m_pts, y, p1, traj, refs))
    else:
        out.update(_score_exact(pred, m_pts, y, p1, traj, refs))
    warn = []
    if order is None:
        warn.append("the order of prediction and truth could not be read from the artifacts' times")
    elif order is False:
        warn.append("the truth was observed before the prediction was fixed")
    if meas["tier"] != "device":
        warn.append(f"truth tier '{meas['tier']}': not evidence about a device")
    if pred["twin"].get("traj"):
        warn.append("the twin's Monte Carlo error is modelled as Normal(p1, p1 (1 - p1) / traj), an upper bound for "
                    "trajectories that each give an exact P(1): coverage errs on the wide side")
    if meas["kind"] == "exact-no-shots":
        warn.append("exact truth without shots: log scores are per shot (Bernoulli), not comparable with shot scores")
    out["warnings"] = warn
    return out


def _score_shots(pred, m_pts, y, p1, traj, refs):
    k = np.array([m["k"] for m in m_pts], int)
    n = np.array([m["n"] for m in m_pts], int)
    if np.any(k < 0) or np.any(k > n) or np.any(n <= 0):
        raise Stop("shot counts must satisfy 0 <= k <= n, n > 0")
    ls, ex, va, pit = (np.empty(len(y)) for _ in range(4))
    for i in range(len(y)):
        ls[i], ex[i], va[i], pit[i] = _point_shots(p1[i], traj, int(k[i]), int(n[i]))
    info = {}
    for name, (rp1, rtraj) in refs.items():
        rls = np.array([_point_shots(rp1[i], rtraj, int(k[i]), int(n[i]))[0] for i in range(len(y))])
        info[name] = dict(total_nats=float(np.sum(ls - rls)), per_point_nats=float(np.mean(ls - rls)))
    z = float((ls.sum() - ex.sum()) / math.sqrt(va.sum())) if va.sum() > 0 else None
    phat = k / n
    per_class = {}
    for c, lab in (("+1", 1), ("-1", -1)):
        s = y == lab
        per_class[c] = dict(points=int(s.sum()), log_score_mean=float(ls[s].mean()), coverage=_coverage(pit[s]),
                            mean_abs_dev=float(np.mean(np.abs(phat[s] - p1[s]))),
                            info_over_chance_per_point=float(np.mean(ls[s] - np.array(
                                [_point_shots(0.5, None, int(k[i]), int(n[i]))[0] for i in np.where(s)[0]]))))
    job = pred.get("job", {})
    ce, a_s, a_h = ce_of_p1(phat, y), acc_strict(phat, y), acc_half(phat, y)

    def inside(v, iv):
        return None if not iv else bool(iv[0] <= v <= iv[1])
    r1 = dict(ce=ce, acc_strict=a_s, acc_half=a_h, ce_pred=job.get("ce_mean"), acc_pred=job.get("acc_mean"),
              ce_inside=inside(ce, job.get("ce_interval")), acc_inside=inside(a_h, job.get("acc_interval")),
              ce_inside_shots_only=inside(ce, job.get("ce_interval_shots_only")),
              acc_inside_shots_only=inside(a_h, job.get("acc_interval_shots_only")),
              ce_gap=None if job.get("ce_mean") is None else ce - job["ce_mean"],
              acc_gap=None if job.get("acc_mean") is None else a_h - job["acc_mean"])
    shot_floor = float(np.mean(np.sqrt(p1 * (1 - p1) / n)))
    return dict(log_score=dict(total=float(ls.sum()), per_point=float(ls.mean()), expected_total=float(ex.sum()),
                               calibration_z=z),
                information=info, coverage=_coverage(pit), per_class=per_class, job=r1,
                deviation=dict(mean_abs=float(np.mean(np.abs(phat - p1))), shot_floor_mean=shot_floor))


def _score_exact(pred, m_pts, y, p1, traj, refs):
    pt = np.array([m["p_exact"] for m in m_pts], float)
    if np.any((pt < 0) | (pt > 1)):
        raise Stop("an exact P(1) lies outside [0, 1]")

    def bern(q):
        q = np.clip(q, P_EPS, 1 - P_EPS)
        return pt * np.log(q) + (1 - pt) * np.log(1 - q)
    s = bern(p1)
    info = {name: dict(per_shot_per_point_nats=float(np.mean(s - bern(rp1)))) for name, (rp1, _) in refs.items()}
    var = p1 * (1 - p1) / traj if traj else np.zeros_like(p1)
    r = (pt - p1) / np.sqrt(np.maximum(var, 1e-12))
    per_class = {}
    for c, lab in (("+1", 1), ("-1", -1)):
        m = y == lab
        per_class[c] = dict(points=int(m.sum()), bernoulli_score_mean=float(s[m].mean()),
                            coverage_twin_error=_coverage_z(r[m]), mean_abs_dev=float(np.mean(np.abs(pt[m] - p1[m]))))
    job = pred.get("job", {})
    return dict(bernoulli_score=dict(per_point_per_shot=float(s.mean())), information=info,
                coverage_twin_error=_coverage_z(r), per_class=per_class,
                job=dict(ce_exact=ce_of_p1(pt, y), ce_exact_pred=job.get("ce_exact"),
                         acc_strict_exact=acc_strict(pt, y), acc_strict_pred=acc_strict(p1, y)),
                deviation=dict(rms=float(np.sqrt(np.mean((pt - p1) ** 2))), mean_abs=float(np.mean(np.abs(pt - p1)))))


# ------------------------------------------------------------------------------------------------ converters

def pred_from_s2rc(rec, rec_sha, price_per_gpu_hour=None):
    """A prediction artifact from a toqb.s2rc record (rehearsal or device run)."""
    P = rec["prediction"]
    so = rec.get("prediction_shots_only", {})
    labels, p1 = rec["test_labels"], P["twin_p1"]
    if len(labels) != len(p1):
        raise Stop(f"{len(labels)} labels, {len(p1)} predictions")
    times = rec.get("times", {})
    gpu_s = rec.get("wall_s")
    return dict(
        format=FORMAT_PRED, written=now_stamp(), fixed_at=None, fixed_by_hash=False,
        producer=dict(name="toqb.s2rc", version=rec.get("version"), engine=rec.get("engine"), dtype=rec.get("dtype")),
        inputs=dict(run_record_sha256=rec_sha, target_sha256=rec.get("target_sha256"),
                    qpy_sha256=(rec.get("export") or {}).get("sha256"), device=rec.get("device")),
        twin=dict(name="traj2", traj=rec["predict"]["traj"], mc_error="P(1) ~ Normal(p1, p1 (1 - p1) / traj), clipped"),
        compiler=dict(arm=rec.get("arm")),
        cell=dict(layers=rec.get("task", {}).get("layers"), n=rec.get("task", {}).get("n"), seed=rec.get("seed")),
        shots=rec["predict"]["shots"],
        points=[dict(i=i, label=int(labels[i]), p1=float(p1[i])) for i in range(len(p1))],
        job=dict(level=P.get("level"), ce_mean=P.get("ce_mean"), ce_interval=P.get("ce_interval"),
                 acc_mean=P.get("acc_mean"), acc_interval=P.get("acc_interval"), ce_exact=P.get("ce_exact"),
                 ce_interval_shots_only=so.get("ce_interval"), acc_interval_shots_only=so.get("acc_interval")),
        cost=dict(wall_s=gpu_s, train_wall_s=rec.get("train_wall_s"), times_s=times,
                  note="s2rc records the whole run; the prediction alone is inside times_s['eval'] with the curve's "
                       "evaluations (and, in a rehearsal, the stand-in's verification)",
                  price_per_gpu_hour=price_per_gpu_hour,
                  usd=None if (price_per_gpu_hour is None or gpu_s is None) else gpu_s / 3600 * price_per_gpu_hour),
        notes=["fixed_at and fixed_by_hash are set when the prediction is fixed (for example by the device job's "
               "manifest); a rehearsal record holds prediction and truth in one file"])


def meas_from_rehearsal(rec, rec_sha, pred_sha):
    """An exact-no-shots measurement from a rehearsal record: the stand-in's exact P(1) (shots were not stored)."""
    rh = rec["rehearsal"]
    return dict(format=FORMAT_MEAS, written=now_stamp(), kind="exact-no-shots", tier="stand-in",
                observed_at=None, truth_producer="toqb.s2rc stand-in (stage 0), trajectory mean over predict.traj",
                declared_deviation=rec.get("standin"),
                inputs=dict(prediction_sha256=pred_sha, run_record_sha256=rec_sha),
                points=[dict(i=i, p_exact=float(v)) for i, v in enumerate(rh["standin_p1"])],
                notes=["the rehearsal stored no per-point shot counts; only the stand-in's exact P(1)",
                       "prediction and truth come from the same run and the same engine family (traj2): stand-in "
                       "tier only, never a claim"])


def _p1_from_counts(counts, clbit=0):
    total = sum(counts.values())
    one = sum(v for key, v in counts.items() if key.replace(" ", "")[-1 - clbit] == "1")
    return one, total


def meas_from_device(job_dir, cell, pred, pred_sha):
    """A shots measurement for one cell of a toqb.s2rc_device job folder (manifest.json, raw_counts.json)."""
    man_f, raw_f = os.path.join(job_dir, "manifest.json"), os.path.join(job_dir, "raw_counts.json")
    man, raw = load_json(man_f), load_json(raw_f)
    sub_f = os.path.join(job_dir, "submission.json")
    submitted = load_json(sub_f).get("submitted") if os.path.exists(sub_f) else None
    cells = {c["cell"]: c for c in man["cells"]}
    if cell not in cells:
        raise Stop(f"cell {cell} is not in the manifest")
    c = cells[cell]
    if pred["inputs"].get("run_record_sha256") != c.get("run_sha256"):
        raise Stop("the prediction was made from another run record than the manifest's cell")
    if [p["p1"] for p in pred["points"]] != list(c["twin_p1"]) or [p["label"] for p in pred["points"]] != list(c["labels"]):
        raise Stop("the prediction's P(1) or labels differ from the manifest's")
    rows = {r["pub"]: r["counts"] for r in raw["rows"]}
    pts = []
    for idx, pub in enumerate(man["pubs"]):
        if pub["cell"] == cell:
            k, n = _p1_from_counts(rows[idx])
            pts.append(dict(i=pub["point"], k=int(k), n=int(n)))
    pts.sort(key=lambda d: d["i"])
    return dict(format=FORMAT_MEAS, written=now_stamp(), kind="shots", tier="device",
                observed_at=raw.get("fetched"), truth_not_before=submitted, prediction_fixed_at=man.get("written"),
                truth_producer="IBM device via toqb.s2rc_device submit / result",
                backend=man["fetch"].get("backend"), calibration_fetched=man["fetch"].get("calibration_time"),
                calibration_at_result=raw.get("calibration_at_fetch"), job_id=raw.get("job_id"),
                inputs=dict(prediction_sha256=pred_sha, manifest_sha256=sha256_file(man_f),
                            raw_counts_sha256=sha256_file(raw_f), qpy_sha256=man.get("qpy_sha256")),
                points=pts)


# ------------------------------------------------------------------------------------------------ CLI

def _opt(argv, name):
    if name in argv:
        i = argv.index(name)
        if i + 1 >= len(argv):
            raise Stop(f"{name} needs a value")
        val = argv[i + 1]
        return argv[:i] + argv[i + 2:], val
    return argv, None


def main(argv):
    try:
        if argv and argv[0] == "from-s2rc":
            argv, price = _opt(argv[1:], "--price")
            if len(argv) != 2:
                print(__doc__)
                return 1
            rec_f, out = argv
            if os.path.exists(out):
                raise Stop(f"{out} exists: an artifact is never overwritten")
            pred = pred_from_s2rc(load_json(rec_f), sha256_file(rec_f), None if price is None else float(price))
            print(f"prediction written: {out}, sha256 {write_new(out, pred)}")
            return 0
        if argv and argv[0] in ("from-device", "from-rehearsal"):
            kind = argv[0]
            argv, pred_f = _opt(argv[1:], "--pred")
            if pred_f is None:
                raise Stop("--pred PRED.json is required: a measurement names the prediction it answers")
            pred, pred_sha = load_json(pred_f), sha256_file(pred_f)
            if kind == "from-device":
                if len(argv) != 3:
                    print(__doc__)
                    return 1
                job, cell, out = argv[0], int(argv[1]), argv[2]
                if os.path.exists(out):
                    raise Stop(f"{out} exists: an artifact is never overwritten")
                meas = meas_from_device(job, cell, pred, pred_sha)
            else:
                if len(argv) != 2:
                    print(__doc__)
                    return 1
                rec_f, out = argv
                if os.path.exists(out):
                    raise Stop(f"{out} exists: an artifact is never overwritten")
                rec = load_json(rec_f)
                if pred["inputs"].get("run_record_sha256") != sha256_file(rec_f):
                    raise Stop("the prediction was not made from this rehearsal record")
                meas = meas_from_rehearsal(rec, sha256_file(rec_f), pred_sha)
            print(f"measurement written: {out}, sha256 {write_new(out, meas)}")
            return 0
        argv, ref_f = _opt(argv, "--ref")
        if len(argv) != 3:
            print(__doc__)
            return 1
        pred_f, meas_f, out = argv
        if os.path.exists(out):
            raise Stop(f"{out} exists: an artifact is never overwritten")
        ref = load_json(ref_f) if ref_f else None
        sc = score(load_json(pred_f), load_json(meas_f), sha256_file(pred_f), sha256_file(meas_f),
                   ref=ref, ref_sha=sha256_file(ref_f) if ref_f else None)
        print(f"score written: {out}, sha256 {write_new(out, sc)}")
        return 0
    except Stop as exc:
        print(f"STOP: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
