"""P3D (2026-10-29): the check of the Paper 3 diagnosis (psf-zero docs/findings/paper3-learning-failure-diagnosis-
2026-10-29.md), noiseless and classical. Declaration: prereg/drafts-2026-10-29/p3d_note.md.

    python -m toqb.p3d run  --part A|C --arm Z|C|G|E [--seed S] [--teacher T] [--ntrain N] OUT.json
    python -m toqb.p3d score RUNS_DIR [--out-name p3d_score]
    python -m toqb.p3d check                 # procedure checks (A0): fast simulator and adjoint gradient

The model is TOQB's ring classifier (`toqb.task_loop`: per layer RY(enc x_q), then RY and RZ per qubit, then the CZ
ring; a final RY per qubit; output <Z_0>). Three ways to train it from theta = 0, all noiseless:

- C: design C's update exactly as `toqb.s2rc` (random +-1 directions, antithetic differences, a batch of training
  points, a fixed learning rate; the same random-number sequence), with the exact output in place of the twin's.
- G: the expectation of C's update: the exact gradient of the same loss mean((1 - y f) / 2) over all training points,
  the same learning rate and number of steps. Only the estimator's randomness is removed.
- E: design E4 (`toqb.s2re.train_e4`): the exact per-parameter Brier minimum, fixed order, a fixed number of sweeps.

The fast simulator merges each layer's data RY and trainable RY on a qubit into one RY (RY(a) RY(b) = RY(a + b)) and
the layer's RZs and CZ ring into one diagonal; the gradient is the adjoint method. Both are checked against
`toqb.exact_batch.z0_batch` and the parameter-shift rule (`check`, tests).
"""
from __future__ import annotations

import json
import math
import os
import sys
import time

import numpy as np

from toqb import task_loop as TL

ENC = math.pi / 2
CLIP = 1e-4

# ------------------------------------------------------------------------------------------------ tasks (declared)

TASK_A = dict(n=10, layers=16, enc=ENC, teacher_seed=4, teacher_angle=0.3, teacher_gap=0.2, n_train=64, n_test=500)
TRAIN_C = dict(init=0.0, pairs=8, sim_batch=4, h=0.1, lr=0.4, loops=2000)
TRAIN_G = dict(lr=0.4, steps=2000)
TRAIN_E = dict(sweeps=2)
SEEDS_C = (301, 302, 303)
TEACHERS_C = (17, 18, 19)
NTRAIN_C = (64, 330)
TEST_AFTER_C = 165


SMOKE = bool(os.environ.get("P3D_SMOKE"))  # rehearsal of the procedure only: tiny model and loops, never scored
if SMOKE:
    TASK_A = dict(TASK_A, n=4, layers=2)
    TRAIN_C = dict(TRAIN_C, loops=20)
    TRAIN_G = dict(TRAIN_G, steps=20)


def task_c(teacher, ntrain):
    n, L = (4, 2) if SMOKE else (10, 16)
    return dict(n=n, layers=L, enc=ENC, teacher_seed=int(teacher), teacher_angle=1.0, teacher_gap=0.2,
                n_train=int(ntrain), n_test=500, test_after=TEST_AFTER_C)


def data(task):
    from toqb import s2r2 as S2
    return S2.teacher_data2(task)


def teacher_theta(task):
    rng = np.random.default_rng(task["teacher_seed"])
    return rng.uniform(-task["teacher_angle"], task["teacher_angle"], TL.n_params(task["n"], task["layers"]))


# ------------------------------------------------------------------------------------------------ fast simulator

class Model:
    """Batched noiseless simulator and adjoint gradient of <Z_0> for one (n, L, enc)."""

    def __init__(self, n, L, enc=ENC):
        self.n, self.L, self.enc = n, L, enc
        self.d = TL.n_params(n, L)
        b = np.arange(2 ** n)
        self.zq = np.stack([1.0 - 2.0 * ((b >> q) & 1) for q in range(n)], axis=1)  # (2^n, n): z_q(b)
        ring = np.ones(2 ** n)
        for q in range(n):
            ring *= np.where(((b >> q) & 1) & ((b >> ((q + 1) % n)) & 1), -1.0, 1.0)
        self.ring = ring
        self.z0 = self.zq[:, 0].copy()

    def split(self, theta):
        n, L = self.n, self.L
        th = np.asarray(theta, float)
        body = th[:2 * n * L].reshape(L, n, 2)
        return body[:, :, 0], body[:, :, 1], th[2 * n * L:]

    def _alpha(self, theta, X):
        ry, rz, fin = self.split(theta)
        return self.enc * np.asarray(X, float)[:, None, :] + ry[None, :, :], rz, fin  # (B, L, n)

    def _diag(self, rz_l):
        return self.ring * np.exp(-0.5j * (self.zq @ rz_l))

    def _ry(self, psi, q, a):
        B = psi.shape[0]
        v = psi.reshape(B, 2 ** (self.n - 1 - q), 2, 2 ** q)
        c, s = np.cos(a / 2)[:, None, None], np.sin(a / 2)[:, None, None]
        a0, a1 = v[:, :, 0, :].copy(), v[:, :, 1, :]
        v[:, :, 0, :] = c * a0 - s * a1
        v[:, :, 1, :] = s * a0 + c * v[:, :, 1, :]

    def forward(self, theta, X):
        X = np.atleast_2d(X)
        B = X.shape[0]
        al, rz, fin = self._alpha(theta, X)
        psi = np.zeros((B, 2 ** self.n), complex)
        psi[:, 0] = 1.0
        for l in range(self.L):
            for q in range(self.n):
                self._ry(psi, q, al[:, l, q])
            psi *= self._diag(rz[l])[None, :]
        for q in range(self.n):
            self._ry(psi, q, np.full(B, fin[q]))
        return psi

    def f(self, theta, X):
        psi = self.forward(theta, X)
        return (np.abs(psi) ** 2) @ self.z0

    def f_many(self, thetas, X):
        """Outputs for several parameter vectors on the same points: (len(thetas), len(X))."""
        return np.stack([self.f(t, X) for t in thetas])

    def grad(self, theta, X):
        """(f (B,), J (B, d)): outputs and their exact gradients by the adjoint method."""
        X = np.atleast_2d(X)
        B, n, L = X.shape[0], self.n, self.L
        al, rz, fin = self._alpha(theta, X)
        psi = self.forward(theta, X)
        f = (np.abs(psi) ** 2) @ self.z0
        lam = psi * self.z0[None, :]
        g_ry, g_rz, g_fin = np.zeros((B, L, n)), np.zeros((B, L, n)), np.zeros((B, n))

        def d_ry(q):  # 2 Re <lam| (-i Y / 2) |psi> = Re sum (conj(lam1) psi0 - conj(lam0) psi1)
            vp = psi.reshape(B, 2 ** (n - 1 - q), 2, 2 ** q)
            vl = lam.reshape(B, 2 ** (n - 1 - q), 2, 2 ** q)
            return np.real(np.sum(np.conj(vl[:, :, 1, :]) * vp[:, :, 0, :] - np.conj(vl[:, :, 0, :]) * vp[:, :, 1, :],
                                  axis=(1, 2)))
        for q in reversed(range(n)):
            g_fin[:, q] = d_ry(q)
            a = np.full(B, -fin[q])
            self._ry(psi, q, a)
            self._ry(lam, q, a)
        for l in reversed(range(L)):
            g_rz[:, l, :] = np.imag(np.conj(lam) * psi) @ self.zq
            dc = np.conj(self._diag(rz[l]))[None, :]
            psi *= dc
            lam *= dc
            for q in reversed(range(n)):
                g_ry[:, l, q] = d_ry(q)
                a = -al[:, l, q]
                self._ry(psi, q, a)
                self._ry(lam, q, a)
        J = np.concatenate([np.stack([g_ry, g_rz], axis=3).reshape(B, 2 * n * L), g_fin], axis=1)
        return f, J


# ------------------------------------------------------------------------------------------------ scores

def scores(z, y):
    z, y = np.asarray(z, float), np.asarray(y, float)
    p = np.clip((1 + y * z) / 2, CLIP, 1 - CLIP)
    return dict(acc=float(np.mean(np.sign(z) == y)), brier=float(np.mean(((z - y) / 2) ** 2)),
                ce=float(np.mean(-np.log(p))), correct=[int(v) for v in (np.sign(z) == y)])


def path(theta0, thetas_steps_norms, lr):
    """walk and straight references from the per-step update norms (lr * |g_k|)."""
    s = lr * np.asarray(thetas_steps_norms, float)
    return float(np.sqrt(np.sum(s ** 2))), float(np.sum(s))


# ------------------------------------------------------------------------------------------------ the three trainers

def train_c(M, Xtr, ytr, seed, p=TRAIN_C):
    """Design C's loop (toqb.s2rc.run_s2rc) with exact outputs; the same random-number sequence."""
    d = M.d
    rng = np.random.default_rng(seed)
    m = rng.uniform(-p["init"], p["init"], d)
    K, b, h, lr = p["pairs"], p["sim_batch"], p["h"], p["lr"]
    gnorm = []
    for _ in range(p["loops"]):
        idx = rng.choice(len(Xtr), b, replace=False)
        D = rng.choice([-1.0, 1.0], (K, d))
        cands = np.vstack([m[None, :] + h * D, m[None, :] - h * D])
        zs = M.f_many(cands, Xtr[idx])  # (2K, b), the order of s2rc's [th for th in cands for i in idx]
        ls = ((1 - zs * ytr[idx][None, :]) / 2).mean(axis=1)
        g = (((ls[:K] - ls[K:]) / (2 * h))[:, None] * D).mean(axis=0)
        m = m - lr * g
        gnorm.append(float(np.linalg.norm(g)))
    return m, gnorm


def train_g(M, Xtr, ytr, p=TRAIN_G):
    """The exact gradient of mean((1 - y f) / 2) over all training points, fixed lr, fixed steps, from 0."""
    th = np.zeros(M.d)
    gnorm = []
    for _ in range(p["steps"]):
        _, J = M.grad(th, Xtr)
        g = -(ytr[:, None] * J).mean(axis=0) / 2
        th = th - p["lr"] * g
        gnorm.append(float(np.linalg.norm(g)))
    return th, gnorm


def train_e(M, Xtr, ytr, p=TRAIN_E):
    from toqb import s2re as SE

    def fv(th):
        return M.f(th, Xtr)
    fv.y = ytr
    th, hist = SE.train_e4(fv, np.zeros(M.d), p["sweeps"])
    return th, hist


# ------------------------------------------------------------------------------------------------ run / score

def run(part, arm, seed=None, teacher=None, ntrain=None):
    task = TASK_A if part == "A" else task_c(teacher, ntrain)
    Xtr, ytr, Xte, yte = data(task)
    M = Model(task["n"], task["layers"], task["enc"])
    t0 = time.perf_counter()
    rec = dict(kind="p3d", part=part, arm=arm, task=task, seed=seed, started=_cet(), smoke=SMOKE)
    extra = {}
    if arm == "Z":
        th = np.zeros(M.d)
    elif arm == "C":
        th, gn = train_c(M, Xtr, ytr, seed)
        w, s = path(0, gn, TRAIN_C["lr"])
        extra = dict(train=TRAIN_C, gnorm=gn, walk=w, straight=s)
    elif arm == "G":
        th, gn = train_g(M, Xtr, ytr)
        w, s = path(0, gn, TRAIN_G["lr"])
        extra = dict(train=TRAIN_G, gnorm=gn, walk=w, straight=s)
    elif arm == "E":
        th, hist = train_e(M, Xtr, ytr)
        extra = dict(train=TRAIN_E, train_brier_per_sweep=hist)
    else:
        raise ValueError(arm)
    te = teacher_theta(task)
    rec.update(extra)
    rec.update(theta=[float(v) for v in th], disp=float(np.linalg.norm(th)), dist_teacher=float(np.linalg.norm(th - te)),
               teacher_norm=float(np.linalg.norm(te)),
               test=scores(M.f(th, Xte), yte), train_scores=scores(M.f(th, Xtr), ytr),
               test_labels=[int(v) for v in yte], n_train=len(ytr), wall_s=time.perf_counter() - t0, ended=_cet())
    rec["train_scores"].pop("correct")
    return rec


def _cet():
    os.environ["TZ"] = "Europe/Zurich"
    time.tzset()
    return time.strftime("%Y-%m-%d %H:%M:%S %Z")


def mcnemar_worse(a_correct, b_correct):
    """One-sided exact McNemar: is a less accurate than b? Returns (b_only, a_only, p)."""
    from scipy.stats import binomtest
    a, b = np.asarray(a_correct), np.asarray(b_correct)
    bo, ao = int(np.sum((b == 1) & (a == 0))), int(np.sum((a == 1) & (b == 0)))
    p = 1.0 if bo + ao == 0 else float(binomtest(bo, bo + ao, 0.5, alternative="greater").pvalue)
    return bo, ao, p


def holm(ps, alpha=0.01):
    order = np.argsort(ps)
    rej = [False] * len(ps)
    for i, k in enumerate(order):
        if ps[k] <= alpha / (len(ps) - i):
            rej[k] = True
        else:
            break
    return rej


def score(runs_dir):
    """Verdicts of the declaration (p3d_note.md section 4). Returns (dict, markdown)."""
    import glob
    R = [json.load(open(f)) for f in sorted(glob.glob(os.path.join(runs_dir, "*.json")))]
    R = [r for r in R if isinstance(r, dict) and r.get("kind") == "p3d"]
    A = {(r["arm"], r.get("seed")): r for r in R if r["part"] == "A"}
    out, md = {}, ["# P3D score (noiseless simulation; not a device result)", ""]
    if any(r.get("smoke") for r in R):
        md += ["**SMOKE (procedure rehearsal, tiny model): not a result, not scored against the declaration.**", ""]
    if A:
        Z = A[("Z", None)]
        accZ = Z["test"]["acc"]
        Cs = [A[("C", s)] for s in SEEDS_C]
        G, E = A[("G", None)], A[("E", None)]
        a0 = dict(theta0_acc=accZ, recorded=0.934, match=round(accZ, 3) == 0.934)
        p1 = [mcnemar_worse(c["test"]["correct"], Z["test"]["correct"]) for c in Cs]
        r1 = holm([p for _, _, p in p1])
        p2 = [mcnemar_worse(c["test"]["correct"], G["test"]["correct"]) for c in Cs]
        r2 = holm([p for _, _, p in p2])
        v = dict(
            A0=a0,
            A1=dict(verdict="HOLDS" if all(r1) else ("FAILS" if not any(r1) else "PARTLY"), tests=p1, holm=r1),
            A2=dict(verdict="HOLDS" if G["test"]["acc"] >= accZ - 0.02 and all(r2) else "FAILS",
                    acc_G=G["test"]["acc"], bound=accZ - 0.02, tests=p2, holm=r2),
            A3=dict(verdict="HOLDS" if E["test"]["acc"] >= accZ - 0.02 else "FAILS", acc_E=E["test"]["acc"]),
            A4=dict(verdict="HOLDS" if all(0.6 <= c["disp"] / c["walk"] <= 1.2 and c["straight"] / c["disp"] >= 20
                                           for c in Cs) and G["straight"] / max(G["disp"], 1e-12) <= 3 else "FAILS",
                    C=[(c["disp"] / c["walk"], c["straight"] / c["disp"]) for c in Cs],
                    G=G["straight"] / max(G["disp"], 1e-12)))
        out["A"] = v
        md += ["## Part A: device-day task (teacher 4, angle 0.3, n 10, L 16), noiseless", "",
               f"A0 (gate): theta = 0 accuracy {accZ:.3f}, recorded 0.934: {'MATCH' if a0['match'] else 'NO MATCH'}", "",
               "| arm | test acc / Brier / CE | train acc | \\|dtheta\\| | walk | straight | dist to teacher |",
               "|---|---|---|---|---|---|---|"]
        for nm, r in [("Z", Z)] + [(f"C s{s}", c) for s, c in zip(SEEDS_C, Cs)] + [("G", G), ("E", E)]:
            md.append(f"| {nm} | {r['test']['acc']:.3f} / {r['test']['brier']:.4f} / {r['test']['ce']:.4f} | "
                      f"{r['train_scores']['acc']:.3f} | {r['disp']:.2f} | {r.get('walk', float('nan')):.2f} | "
                      f"{r.get('straight', float('nan')):.1f} | {r['dist_teacher']:.2f} |")
        md += ["", *(f"- {k}: **{v[k]['verdict']}**" for k in ("A1", "A2", "A3", "A4")), ""]
    Cp = [r for r in R if r["part"] == "C"]
    if Cp:
        idx = {(r["arm"], r["task"]["teacher_seed"], r["n_train"]): r for r in Cp}
        vc = {}
        md += ["## Part C: far teachers 17-19 (angle 1.0, L 16), N = 64 vs 330, shared test set", "",
               "| arm | teacher | N | train acc | test acc / Brier | gap |", "|---|---|---|---|---|---|"]
        for t in TEACHERS_C:
            z = idx.get(("Z", t, 64))
            if z is not None:
                md.append(f"| Z (theta = 0) | {t} | - | {z['train_scores']['acc']:.3f} | {z['test']['acc']:.3f} / "
                          f"{z['test']['brier']:.4f} | - |")
        for arm in ("E", "G"):
            ps, gaps = [], []
            for t in TEACHERS_C:
                lo, hi = idx.get((arm, t, 64)), idx.get((arm, t, 330))
                if lo is None or hi is None:
                    continue
                if lo["test_labels"] != hi["test_labels"]:
                    raise SystemExit("C0 FAIL: test sets differ")
                ps.append(mcnemar_worse(lo["test"]["correct"], hi["test"]["correct"]))
                gl = lo["train_scores"]["acc"] - lo["test"]["acc"]
                gh = hi["train_scores"]["acc"] - hi["test"]["acc"]
                gaps.append(gh < gl)
                for r, g in ((lo, gl), (hi, gh)):
                    md.append(f"| {arm} | {t} | {r['n_train']} | {r['train_scores']['acc']:.3f} | "
                              f"{r['test']['acc']:.3f} / {r['test']['brier']:.4f} | {g:+.3f} |")
            if ps:
                rej = holm([p for _, _, p in ps])
                vc[arm] = dict(C1="HOLDS" if sum(rej) >= 2 else "FAILS", tests=ps, holm=rej,
                               C2=f"{sum(gaps)} of {len(gaps)} smaller gap at N = 330")
        out["C"] = vc
        md += ["", *(f"- {a}: C1 **{vc[a]['C1']}**; C2 {vc[a]['C2']}" for a in vc), ""]
    return out, "\n".join(md) + "\n"


def check(n=10, L=16, seed=7):
    """A0's procedure checks: the fast simulator against z0_batch, and the adjoint gradient against parameter shift."""
    from toqb import exact_batch as EB
    rng = np.random.default_rng(seed)
    M = Model(n, L)
    worst_f, worst_g = 0.0, 0.0
    for scale in (0.0, 0.3, math.pi):
        th = rng.uniform(-scale, scale, M.d)
        X = rng.uniform(-1, 1, (4, n))
        ref = EB.z0_batch(np.array([TL.angle_list(th, x, n, L, ENC) for x in X]), n, L)
        f, J = M.grad(th, X)
        worst_f = max(worst_f, float(np.max(np.abs(f - ref))), float(np.max(np.abs(M.f(th, X) - ref))))
        for k in rng.choice(M.d, 12, replace=False):
            e = np.zeros(M.d)
            e[k] = math.pi / 2
            ps = (M.f(th + e, X) - M.f(th - e, X)) / 2
            worst_g = max(worst_g, float(np.max(np.abs(ps - J[:, k]))))
    ok = worst_f < 1e-10 and worst_g < 1e-10
    return dict(n=n, L=L, max_f_diff=worst_f, max_grad_diff=worst_g, ok=ok)


def main(argv):
    if not argv or argv[0] not in ("run", "score", "check"):
        print(__doc__)
        return 2
    if argv[0] == "check":
        r = check()
        print(json.dumps(r))
        return 0 if r["ok"] else 1
    if argv[0] == "score":
        d = argv[1]
        name = argv[argv.index("--out-name") + 1] if "--out-name" in argv else "p3d_score"
        v, md = score(d)
        json.dump(v, open(os.path.join(d, name + ".json"), "w"), indent=1)
        open(os.path.join(d, name + ".md"), "w").write(md)
        print(md)
        return 0
    a = argv[1:]
    get = lambda k, t=str: t(a[a.index(k) + 1]) if k in a else None
    rec = run(get("--part"), get("--arm"), get("--seed", int), get("--teacher", int), get("--ntrain", int))
    json.dump(rec, open(a[-1], "w"))
    print(rec["part"], rec["arm"], rec.get("seed"), rec["task"]["teacher_seed"], rec["n_train"],
          "test acc %.3f" % rec["test"]["acc"], "train acc %.3f" % rec["train_scores"]["acc"],
          "disp %.2f" % rec["disp"], "wall %.0f s" % rec["wall_s"])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
