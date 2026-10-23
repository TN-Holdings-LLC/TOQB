"""S2R, second design (the owner's decisions of 2026-10-18): thousands of light loops, the simulator on a GPU.

Stage 0 (`toqb.s2r`, Addendum 523 of PSF-Zero) sent 128 circuits per loop to the stand-in device, so $192 bought six
loops and the compilers could not differ in how much they learned for the money. Here a loop sends **two** circuits:

**One loop** (`run_s2r2`): the simulator (the user's model of the device: TOQB's noise model on FakeFez, run as
trajectories by `toqb.traj2`) evaluates N candidates theta_i = m + sigma eps_i on a batch of b training points
(T trajectories per circuit, not billed) and picks the best; the stand-in runs the current mean m and that candidate
on one training point with `shots` shots (2 circuits, billed at IBM's price); the candidate replaces m if its stand-in
loss is lower; sigma follows the one-fifth rule (x exp(1/3) on success, x exp(-1/12) otherwise, kept in
[sigma_min, sigma_max]). The run stops before the loop that would pass the budget.

**The device-only baseline** (`run_spsa2`): SPSA on the stand-in alone, two circuits per iteration (theta +- c_k Delta
on one training point, `shots` shots), the same budget.

**Evaluation** (not billed), every `every` loops or iterations and at the stop: the stand-in's <Z> on the n_test test
points as the mean of T_eval trajectories (no shots); cross-entropy of p(y = +1) = (1 + z) / 2 (clipped to
[1e-4, 1 - 1e-4]) and accuracy; the dollars spent so far.

**The task:** TOQB's ring classifier (`task_loop`'s model) with n qubits and L layers; a teacher of the same model
with angles uniform in [-teacher_angle, teacher_angle] (a teacher with angles in [-pi, pi] gives |<Z>| < 0.2 on
almost every point at n = 10 from L = 16 on: its labels would be noise), points kept when |<Z>| >= teacher_gap, and
the classes balanced (n_train / 2 and n_test / 2 of each). The stand-in and the price are stage 0's (`s2r.StandIn`).

Every random draw (initial mean, candidates, batches, points, trajectories, shots) comes from the run's seed and is the
same for both compilers; only the circuits differ. `TOQB_XP=cupy` runs the trajectories on a GPU.
"""
from __future__ import annotations

import json
import math
import os
import time

import numpy as np

from toqb import s2r as S
from toqb import task_loop as TL
from toqb import traj2 as T2


def teacher_data2(task):
    """(X_train, y_train, X_test, y_test): the narrow teacher, the gap, balanced classes (see the module).

    Optional `test_after` (2026-10-23): the test points start after that many points per class, so that tasks with
    different n_train share one test set (n_train 64 with test_after 128 tests on the points of n_train 256; its
    training points are the first 32 per class, a subset of those of 256). Without it, the behaviour is unchanged."""
    n, L, enc = task["n"], task["layers"], task["enc"]
    rng = np.random.default_rng(task["teacher_seed"])
    a = task["teacher_angle"]
    teacher = rng.uniform(-a, a, TL.n_params(n, L))
    skip = task.get("test_after")
    if skip is None:
        want = {1.0: (task["n_train"] + task["n_test"]) // 2, -1.0: (task["n_train"] + task["n_test"]) // 2}
    else:
        if int(skip) < task["n_train"] // 2:
            raise ValueError("teacher_data2: test_after must be at least n_train / 2")
        want = {1.0: int(skip) + task["n_test"] // 2, -1.0: int(skip) + task["n_test"] // 2}
    got = {1.0: [], -1.0: []}
    tries = 0
    while len(got[1.0]) < want[1.0] or len(got[-1.0]) < want[-1.0]:
        tries += 1
        if tries > 200 * (want[1.0] + want[-1.0]):
            raise RuntimeError("teacher_data2: the teacher does not give enough points of both classes")
        x = rng.uniform(-1, 1, n)
        z = TL.exact_z0(TL.angle_list(teacher, x, n, L, enc), n, L)
        if abs(z) < task["teacher_gap"]:
            continue
        y = 1.0 if z > 0 else -1.0
        if len(got[y]) < want[y]:
            got[y].append(x)
    htr = task["n_train"] // 2
    st = htr if skip is None else int(skip)
    Xtr = np.array(got[1.0][:htr] + got[-1.0][:htr])
    ytr = np.array([1.0] * htr + [-1.0] * htr)
    Xte = np.array(got[1.0][st:] + got[-1.0][st:])
    yte = np.array([1.0] * (len(got[1.0]) - st) + [-1.0] * (len(got[-1.0]) - st))
    p = rng.permutation(len(Xtr))
    return Xtr[p], ytr[p], Xte, yte


class _Point:
    """A point of the fast path (TOQB_FAST_PSF): the model's parameters and input, compiled on demand in Rust."""

    __slots__ = ("theta", "x")

    def __init__(self, theta, x):
        self.theta, self.x = theta, x


def _make_fast(R):
    import sys
    try:
        from toqb import rustbind
        F = rustbind.FastPSF(R)
        rng = np.random.default_rng(20261021)
        d = TL.n_params(R.task["n"], R.task["layers"])
        ths = [rng.uniform(-np.pi, np.pi, d) for _ in range(4)]
        xs = [rng.uniform(-1, 1, R.task["n"]) for _ in range(4)]
        err = max(F.check("sim", ths, xs), F.check("dev", ths, xs))
        if err > 1e-12:
            print(f"note: TOQB_FAST_PSF off: the fast path differs from the slow one by {err:.2e}", file=sys.stderr)
            return None
        return F
    except Exception as exc:  # noqa: BLE001 - the slow path stays
        print(f"note: TOQB_FAST_PSF off: {type(exc).__name__}: {exc}", file=sys.stderr)
        return None


class Runner:
    """Compiles with one arm and evaluates circuits in the simulator's model and on the stand-in, by trajectories."""

    def __init__(self, plan, spec):
        from toqb.devices import get_device
        from toqb.fast_noise import FastNoisyDevice
        self.plan = plan
        self.task = plan["task"]
        self.cost = dict(TL.DEFAULT_COST, **plan.get("qpu_cost", {}))
        self.device = get_device(plan["device"])
        self.arm = S.Arm(spec, self.device)
        self.sim = FastNoisyDevice(self.device.target)
        self.standin = S.StandIn(**plan["standin"])
        self.eng = T2.Engine()
        self.sk = {"sim": {}, "dev": {}}
        self.n_struct = 0
        self.t = dict(compile=0.0, sim=0.0, dev=0.0, eval=0.0)
        # opt-in (2026-10-21): TOQB_FAST_PSF=1 binds the PSF template arm in Rust (toqb.rustbind) and skips the
        # Qiskit circuits; never for a device run (verify false: its circuits are exported); checked against the
        # slow path on random points before use, and off (with a note) if it is unavailable or differs.
        self._fast = None
        if (os.environ.get("TOQB_FAST_PSF") == "1" and spec.startswith("psfai:template")
                and plan.get("verify", True)):
            self._fast = _make_fast(self)

    def compile(self, theta, x):
        n, L, enc = self.task["n"], self.task["layers"], self.task["enc"]
        s = time.perf_counter()
        if self._fast is not None:
            c = _Point(np.array(theta, dtype=float), np.array(x, dtype=float))
        else:
            c = self.arm.compile(TL.model_circuit(TL.angle_list(theta, x, n, L, enc), n, L))
        self.t["compile"] += time.perf_counter() - s
        return c

    def _skel(self, model, c):
        key = self.sim._structure_of(c) if hasattr(self.sim, "_structure_of") else _structure(c)
        hit = self.sk[model].get(key)
        if hit is None:
            if model == "sim":
                r, _act, _nm, _rp = self.sim.noisy_circuit(c)
                hit = T2.plan(c, r, self.device.target)
            else:
                r, _nm = self.standin.prepared(c)
                hit = T2.plan(c, r, self.standin.target, over=self.standin.params["over"])
            self.sk[model][key] = hit
            self.arm.duration(c, self.sim._scan(c)[0])
            self.n_struct += 1
        return key, hit

    def z(self, model, circuits, T, seed, shots=False, crn=False):
        """<Z> on clbit 0 of each circuit: the trajectory mean (T trajectories; with `crn` every circuit of a structure
        sees the same draws), or from T shots if `shots`."""
        if self._fast is not None and circuits and isinstance(circuits[0], _Point):
            if not all(isinstance(c, _Point) for c in circuits):
                raise ValueError("Runner.z: fast points and circuits mixed in one call")
            return self._fast.z(model, [c.theta for c in circuits], [c.x for c in circuits], T, seed, shots=shots,
                                crn=crn)
        groups = {}
        for i, c in enumerate(circuits):
            key, sk = self._skel(model, c)
            groups.setdefault(key, (sk, []))[1].append(i)
        out = np.empty(len(circuits))
        for g, (key, (sk, idx)) in enumerate(sorted(groups.items(), key=lambda kv: kv[1][1][0])):
            A = np.stack([sk.angles(circuits[i]) for i in idx])
            if shots:
                out[idx] = self.eng.z_shots(sk, A, T, seed + 7919 * g)
            else:
                out[idx] = self.eng.z_mean(sk, A, T, seed + 7919 * g, crn=crn)
        return out

    def job_seconds(self, circuits, shots):
        durs = [self.arm.duration(c, self.sim._scan(c)[0])[0] for c in circuits]
        return TL.qpu_seconds(durs, shots, self.cost)


def _structure(c):
    return tuple((i.operation.name, tuple(c.find_bit(q).index for q in i.qubits)) for i in c.data)


def _ce(z, y):
    p = np.clip((1 + z) / 2, 1e-4, 1 - 1e-4)
    return float(np.mean(-np.where(y > 0, np.log(p), np.log(1 - p))))


def _evaluate(R, theta, Xte, yte, T, seed, spent_s, k, t0, evals):
    s = time.perf_counter()
    cs = [R.compile(theta, x) for x in Xte]
    z = R.z("dev", cs, T, seed)
    R.t["eval"] += time.perf_counter() - s
    evals.append(dict(step=k, usd=spent_s * R.cost["usd_per_s"], ce=_ce(z, yte),
                      accuracy=float(np.mean(np.where(z == 0, 0.5, np.sign(z) == yte))),
                      wall_s=time.perf_counter() - t0))


def _auc(evals, budget):
    """Mean cross-entropy over the budget: the trapezoid of (usd, ce) from 0 to the last evaluation, the last value held
    to `budget`, divided by `budget`."""
    xs = [e["usd"] for e in evals]
    ys = [e["ce"] for e in evals]
    area = sum((xs[i + 1] - xs[i]) * (ys[i + 1] + ys[i]) / 2 for i in range(len(xs) - 1))
    area += max(budget - xs[-1], 0.0) * ys[-1]
    return area / budget


def run_s2r2(plan, spec):
    task, p, ev = plan["task"], plan["s2r2"], plan["evaluation"]
    R = Runner(plan, spec)
    rec = dict(kind="s2r2", arm=spec, seed=p["seed"], plan=plan["name"], started=S._cest(), s2r2=p,
               qpu_cost=R.cost, version=R.arm.version(), standin=R.standin.params, engine=R.eng.xp.__name__,
               dtype=str(R.eng.dtype))
    Xtr, ytr, Xte, yte = teacher_data2(task)
    n, L = task["n"], task["layers"]
    d = TL.n_params(n, L)
    rng = np.random.default_rng(p["seed"])
    m = rng.uniform(-p["init"], p["init"], d)
    sigma = p["sigma0"]
    N, b, Ts, shots, budget = p["candidates"], p["sim_batch"], p["sim_traj"], p["shots"], p["budget_usd"]
    spent = 0.0
    evals, log = [], dict(success=[], sigma=[], sim_m=[], sim_best=[], dev_m=[], dev_best=[], usd=[])
    t0 = time.perf_counter()
    k = 0
    try:
        _evaluate(R, m, Xte, yte, ev["test_traj"], ev["seed"], spent, 0, t0, evals)
        while k < p["max_loops"]:
            idx = rng.choice(len(Xtr), b, replace=False)
            eps = rng.standard_normal((N, d))
            cands = np.vstack([m[None, :], m[None, :] + sigma * eps])
            s = time.perf_counter()
            cs = [R.compile(th, Xtr[i]) for th in cands for i in idx]
            zs = R.z("sim", cs, Ts, p["seed"] * 1000003 + 2 * k).reshape(N + 1, b)
            R.t["sim"] += time.perf_counter() - s
            ls = ((1 - zs * ytr[idx][None, :]) / 2).mean(axis=1)
            best = 1 + int(np.argmin(ls[1:]))
            j = int(rng.integers(len(Xtr)))
            dev_cs = [R.compile(m, Xtr[j]), R.compile(cands[best], Xtr[j])]
            job = R.job_seconds(dev_cs, shots)
            if (spent + job) * R.cost["usd_per_s"] > budget + 1e-9:
                break
            s = time.perf_counter()
            zd = R.z("dev", dev_cs, shots, p["seed"] * 1000003 + 2 * k + 1, shots=True)
            R.t["dev"] += time.perf_counter() - s
            spent += job
            k += 1
            ld = (1 - zd * ytr[j]) / 2
            ok = bool(ld[1] < ld[0])
            if ok:
                m = cands[best]
            sigma = min(max(sigma * (math.exp(1 / 3) if ok else math.exp(-1 / 12)), p["sigma_min"]), p["sigma_max"])
            for key, v in (("success", ok), ("sigma", sigma), ("sim_m", float(ls[0])), ("sim_best", float(ls[best])),
                           ("dev_m", float(ld[0])), ("dev_best", float(ld[1])), ("usd", spent * R.cost["usd_per_s"])):
                log[key].append(v)
            if k % ev["every"] == 0:
                _evaluate(R, m, Xte, yte, ev["test_traj"], ev["seed"] + k, spent, k, t0, evals)
        if evals[-1]["step"] != k:
            _evaluate(R, m, Xte, yte, ev["test_traj"], ev["seed"] + k, spent, k, t0, evals)
    except Exception as exc:  # noqa: BLE001 - recorded
        rec["error"] = f"loop: {type(exc).__name__}: {exc}"
    agree = [(sb - sm) * (db - dm) > 0 for sm, sb, dm, db in zip(log["sim_m"], log["sim_best"], log["dev_m"],
                                                                 log["dev_best"]) if db != dm]
    rec.update(loops=k, evals=evals, log=log, spent_usd=spent * R.cost["usd_per_s"], auc_ce=_auc(evals, budget)
               if evals else None, agreement=float(np.mean(agree)) if agree else None,
               wall_s=time.perf_counter() - t0, times=R.t, structures=R.n_struct, compiled=R.arm.compiled,
               structural_fail=R.arm.structural_fail, on_failed_ops=R.arm.on_failed_ops,
               durations_us=sorted({round(v[0] * 1e6, 4) for v in R.arm._dur.values()}),
               q2=sorted({v[1] for v in R.arm._dur.values()}), final_mean=[float(x) for x in m], ended=S._cest())
    rec["valid"] = "error" not in rec and not R.arm.structural_fail and not R.arm.on_failed_ops
    return rec


def run_s2rg(plan, spec):
    """S2R2-B (the owner's decision B of 2026-10-19): the simulator learns, the stand-in is only measured.

    One loop: the simulator's antithetic gradient of the training loss, `pairs` random +-1 directions D_i at
    m +- h D_i on a batch of b training points (T trajectories, common random numbers across the batch), averaged;
    m <- m - lr * g. The stand-in then runs the new m on two training points with `shots` shots (2 circuits, billed),
    and the simulator predicts the same two (recorded: the device's answers do not change the learning; that is the
    finding of 2026-10-18, the simulator already knows the stand-in's gradient direction to cos ~ 0.99, PSF, L = 8).
    Evaluation as in `run_s2r2`; the run stops before the loop that would pass the budget."""
    task, p, ev = plan["task"], plan["s2rg"], plan["evaluation"]
    budget, shots = plan["s2rg"]["budget_usd"], plan["s2rg"]["shots"]
    R = Runner(plan, spec)
    rec = dict(kind="s2rg", arm=spec, seed=p["seed"], plan=plan["name"], started=S._cest(), s2rg=p,
               qpu_cost=R.cost, version=R.arm.version(), standin=R.standin.params, engine=R.eng.xp.__name__,
               dtype=str(R.eng.dtype))
    Xtr, ytr, Xte, yte = teacher_data2(task)
    n, L = task["n"], task["layers"]
    d = TL.n_params(n, L)
    rng = np.random.default_rng(p["seed"])
    m = rng.uniform(-p["init"], p["init"], d)
    K, b, Ts, h, lr = p["pairs"], p["sim_batch"], p["sim_traj"], p["h"], p["lr"]
    spent, evals, k = 0.0, [], 0
    log = dict(gnorm=[], sim_loss=[], dev_loss=[], sim_pred=[], usd=[])
    t0 = time.perf_counter()
    try:
        _evaluate(R, m, Xte, yte, ev["test_traj"], ev["seed"], spent, 0, t0, evals)
        while k < p["max_loops"]:
            idx = rng.choice(len(Xtr), b, replace=False)
            D = rng.choice([-1.0, 1.0], (K, d))
            cands = np.vstack([m[None, :] + h * D, m[None, :] - h * D])
            s = time.perf_counter()
            cs = [R.compile(th, Xtr[i]) for th in cands for i in idx]
            zs = R.z("sim", cs, Ts, p["seed"] * 1000003 + 3 * k, crn=True).reshape(2 * K, b)
            R.t["sim"] += time.perf_counter() - s
            ls = ((1 - zs * ytr[idx][None, :]) / 2).mean(axis=1)
            g = (((ls[:K] - ls[K:]) / (2 * h))[:, None] * D).mean(axis=0)
            jj = rng.choice(len(Xtr), 2, replace=False)
            m_new = m - lr * g
            dev_cs = [R.compile(m_new, Xtr[j]) for j in jj]
            job = R.job_seconds(dev_cs, shots)
            if (spent + job) * R.cost["usd_per_s"] > budget + 1e-9:
                break
            m = m_new
            s = time.perf_counter()
            zd = R.z("dev", dev_cs, shots, p["seed"] * 1000003 + 3 * k + 1, shots=True)
            R.t["dev"] += time.perf_counter() - s
            zp = R.z("sim", dev_cs, Ts, p["seed"] * 1000003 + 3 * k + 2)
            spent += job
            k += 1
            for key, v in (("gnorm", float(np.linalg.norm(g))), ("sim_loss", float(ls.mean())),
                           ("dev_loss", float(((1 - zd * ytr[jj]) / 2).mean())),
                           ("sim_pred", float(((1 - zp * ytr[jj]) / 2).mean())), ("usd", spent * R.cost["usd_per_s"])):
                log[key].append(v)
            if k % ev["every"] == 0:
                _evaluate(R, m, Xte, yte, ev["test_traj"], ev["seed"] + k, spent, k, t0, evals)
        if evals[-1]["step"] != k:
            _evaluate(R, m, Xte, yte, ev["test_traj"], ev["seed"] + k, spent, k, t0, evals)
    except Exception as exc:  # noqa: BLE001 - recorded
        rec["error"] = f"loop: {type(exc).__name__}: {exc}"
    rec.update(loops=k, evals=evals, log=log, spent_usd=spent * R.cost["usd_per_s"],
               auc_ce=_auc(evals, budget) if evals else None, wall_s=time.perf_counter() - t0, times=R.t,
               structures=R.n_struct, compiled=R.arm.compiled, structural_fail=R.arm.structural_fail,
               on_failed_ops=R.arm.on_failed_ops,
               durations_us=sorted({round(v[0] * 1e6, 4) for v in R.arm._dur.values()}),
               q2=sorted({v[1] for v in R.arm._dur.values()}), final_mean=[float(x) for x in m], ended=S._cest())
    rec["valid"] = "error" not in rec and not R.arm.structural_fail and not R.arm.on_failed_ops
    return rec


def run_spsa2(plan, spec):
    task, o, ev = plan["task"], plan["spsa2"], plan["evaluation"]
    base = plan["s2rg"] if "s2rg" in plan else plan["s2r2"]
    budget, shots = base["budget_usd"], base["shots"]
    R = Runner(plan, spec)
    rec = dict(kind="spsa2", arm=spec, seed=o["seed"], plan=plan["name"], started=S._cest(), spsa2=o,
               qpu_cost=R.cost, version=R.arm.version(), standin=R.standin.params, engine=R.eng.xp.__name__,
               dtype=str(R.eng.dtype))
    Xtr, ytr, Xte, yte = teacher_data2(task)
    n, L = task["n"], task["layers"]
    d = TL.n_params(n, L)
    rng = np.random.default_rng(o["seed"])
    theta = rng.uniform(-o["init"], o["init"], d)
    spent, evals, k = 0.0, [], 0
    t0 = time.perf_counter()
    try:
        _evaluate(R, theta, Xte, yte, ev["test_traj"], ev["seed"], spent, 0, t0, evals)
        while k < o["max_iterations"]:
            ak, ck = TL.gains(k, o)
            delta = rng.choice([-1.0, 1.0], d)
            j = int(rng.integers(len(Xtr)))
            cs = [R.compile(theta + ck * delta, Xtr[j]), R.compile(theta - ck * delta, Xtr[j])]
            job = R.job_seconds(cs, shots)
            if (spent + job) * R.cost["usd_per_s"] > budget + 1e-9:
                break
            s = time.perf_counter()
            z = R.z("dev", cs, shots, o["seed"] * 1000003 + k, shots=True)
            R.t["dev"] += time.perf_counter() - s
            spent += job
            k += 1
            lp, lm = (1 - z[0] * ytr[j]) / 2, (1 - z[1] * ytr[j]) / 2
            theta = theta - ak * (lp - lm) / (2 * ck) * delta
            if k % ev["every"] == 0:
                _evaluate(R, theta, Xte, yte, ev["test_traj"], ev["seed"] + k, spent, k, t0, evals)
        if evals[-1]["step"] != k:
            _evaluate(R, theta, Xte, yte, ev["test_traj"], ev["seed"] + k, spent, k, t0, evals)
    except Exception as exc:  # noqa: BLE001
        rec["error"] = f"loop: {type(exc).__name__}: {exc}"
    rec.update(iterations=k, evals=evals, spent_usd=spent * R.cost["usd_per_s"],
               auc_ce=_auc(evals, budget) if evals else None, wall_s=time.perf_counter() - t0, times=R.t,
               structures=R.n_struct, compiled=R.arm.compiled, structural_fail=R.arm.structural_fail,
               on_failed_ops=R.arm.on_failed_ops, final_theta=[float(x) for x in theta], ended=S._cest())
    rec["valid"] = "error" not in rec and not R.arm.structural_fail and not R.arm.on_failed_ops
    return rec


def main(argv):
    """python -m toqb.s2r2 <s2r2|s2rg|spsa2> PLAN.json OUT.json SPEC"""
    import sys
    if len(argv) != 4 or argv[0] not in ("s2r2", "s2rg", "spsa2"):
        print(main.__doc__)
        return 1
    kind, plan_file, out, spec = argv
    if os.path.exists(out):
        print(f"{out} exists: a run never overwrites another", file=sys.stderr)
        return 2
    plan = json.load(open(plan_file, encoding="utf-8"))
    rec = dict(s2r2=run_s2r2, s2rg=run_s2rg, spsa2=run_spsa2)[kind](plan, spec)
    with open(out + ".tmp", "w", encoding="utf-8") as f:
        json.dump(rec, f)
    os.replace(out + ".tmp", out)
    print(json.dumps({k: rec.get(k) for k in ("kind", "arm", "seed", "valid", "spent_usd", "auc_ce", "loops",
                                             "iterations", "wall_s", "error")}), flush=True)
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main(sys.argv[1:]))
