"""Noiseless calibration of SPSA settings for TOQB's loop task (n6 L8, teacher 4): exact <Z0> by a batched state
vector, 400 shots drawn per point, test accuracy without noise. Seeds 901+ (never the scored runs' seeds)."""
import json, math, sys, itertools, time
import numpy as np
import os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from toqb.task_loop import teacher_data, spsa_schedule, gains, exact_z0, angle_list, n_params

def z0_batch(theta, X, n, L, enc):
    """theta (B, d), X (B, n) -> exact <Z0> (B,), same conventions as exact_z0."""
    B = theta.shape[0]; D = 2 ** n
    psi = np.zeros((B, D), complex); psi[:, 0] = 1
    b = np.arange(D)
    ring = np.ones(D)
    for q in range(n):
        ring *= np.where(((b >> q) & 1) & ((b >> ((q + 1) % n)) & 1), -1, 1)
    def apply(psi, U, q):  # U (B,2,2)
        t = psi.reshape((B,) + (2,) * n)
        ax = 1 + (n - 1 - q)
        t = np.moveaxis(t, ax, 1)
        s = t.shape
        t = np.einsum("bij,bj...->bi...", U, t)
        return np.moveaxis(t, 1, ax).reshape(B, D)
    def ry(a):
        c, s = np.cos(a / 2), np.sin(a / 2)
        return np.stack([np.stack([c, -s], -1), np.stack([s, c], -1)], -2).astype(complex)
    def rz(a):
        z = np.zeros((len(a), 2, 2), complex); z[:, 0, 0] = np.exp(-0.5j * a); z[:, 1, 1] = np.exp(0.5j * a); return z
    k = 0
    for _ in range(L):
        for q in range(n):
            psi = apply(psi, ry(enc * X[:, q]), q)
        for q in range(n):
            psi = apply(psi, ry(theta[:, k]), q); psi = apply(psi, rz(theta[:, k + 1]), q); k += 2
        psi = ring * psi
    for q in range(n):
        psi = apply(psi, ry(theta[:, k + q]), q)
    pr = np.abs(psi) ** 2
    return (pr * (1 - 2 * (b & 1))).sum(1)

def run(cfg, seeds, task, checkpoints):
    n, L, enc = task["n"], task["layers"], task["enc"]
    Xtr, ytr, Xte, yte = teacher_data(task)
    S = len(seeds); d = n_params(n, L); bt = cfg["batch"]
    opt = dict(cfg, init=0.5)
    th, steps = [], []
    for s in seeds:
        o = dict(opt, loop_seed=s); t0, st = spsa_schedule(dict(task), o); th.append(t0); steps.append(st)
    th = np.array(th)
    rng = np.random.default_rng(12345)
    def test_acc(th):
        T = np.repeat(th, len(Xte), 0); X = np.tile(Xte, (S, 1))
        z = z0_batch(T, X, n, L, enc).reshape(S, len(Xte))
        return (np.sign(z) == yte[None]).mean(1)
    out = {0: test_acc(th)}
    for k in range(cfg["iterations"]):
        ak, ck = gains(k, opt)
        idx = np.array([steps[i][k][0] for i in range(S)]); dl = np.array([steps[i][k][1] for i in range(S)])
        P = np.concatenate([th + ck * dl, th - ck * dl])  # (2S, d)
        T = np.repeat(P, bt, 0); X = np.concatenate([Xtr[idx].reshape(-1, n)] * 2)
        z = z0_batch(T, X, n, L, enc)
        p1 = (1 - z) / 2; z = 1 - 2 * rng.binomial(400, np.clip(p1, 0, 1)) / 400
        z = z.reshape(2, S, bt); y = np.concatenate([ytr[idx]]).reshape(S, bt)
        lp = ((1 - y * z[0]) / 2).mean(1); lm = ((1 - y * z[1]) / 2).mean(1)
        th = th - (ak * (lp - lm) / (2 * ck))[:, None] * dl
        if k + 1 in checkpoints: out[k + 1] = test_acc(th)
    return out

if __name__ == "__main__":
    plan = json.load(open(os.path.join(ROOT, "plan_loop_pilot_n6_s11.json"))); task = plan["task"]
    if sys.argv[1] == "selftest":
        n, L, enc = 6, 8, task["enc"]; rng = np.random.default_rng(0)
        th = rng.uniform(-3, 3, (5, n_params(n, L))); X = rng.uniform(-1, 1, (5, n))
        a = z0_batch(th, X, n, L, enc); b = [exact_z0(angle_list(th[i], X[i], n, L, enc), n, L) for i in range(5)]
        print("selftest max diff", np.max(np.abs(a - np.array(b)))); sys.exit()
    cfg = json.loads(sys.argv[1]); seeds = list(range(901, 901 + int(sys.argv[2])))
    cps = [int(c) for c in sys.argv[3].split(",")]
    t = time.perf_counter(); o = run(cfg, seeds, task, set(cps))
    print(json.dumps(dict(cfg=cfg, seeds=len(seeds), secs=round(time.perf_counter() - t, 1),
        **{str(k): dict(mean=round(float(v.mean()), 3), p25=round(float(np.percentile(v, 25)), 3), ge70=round(float((v >= 0.7).mean()), 2)) for k, v in o.items()})))
