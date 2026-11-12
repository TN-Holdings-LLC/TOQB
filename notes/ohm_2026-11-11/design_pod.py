"""Design scan for the Ohm device job, for a POD (workplace, 2026-11-12; not declared). The workplace check
(samples6w.py, N 40, K 30) found the gap between A1 (isotropic) and A2 (isotropic + period-3 field) in the exponent
3 -> 6 of the mean transfer much smaller at finite bias than in linear response (m 0.5: 0.66 against 0.61; linear
response 0.71 against 0.50), and below the shot error a 160 s job can reach. This scan asks which setting separates
them: arms, bias m, string count K, time window.

Per configuration (an arm: phi, field H and its pattern; a bias m): K random strings (seed 11, as samples6.py) and
their complements, N qubits, the exact per-qubit <Z> after every cycle 1..CYC (quimb CircuitMPS, cutoff 1e-10, cap
4096; one string per process), then per window (a, b): the exponent of the mean transfer W(t) = mean of (M_s - M_c)/2
and of the plain mean M over the K strings, the string-resample spread (bootstrap) and the shot error at S shots per
circuit (per-shot variance of the right-half count bounded by the sum of p (1 - p), which overestimates: sampling at
N 40 gave about 0.2 of the bound). Writes one JSON line per configuration with the per-string transfers (design
strings, not the declared ones: the declaration uses another seed).
usage: python design_pod.py OUT.jsonl --N 40 --K 100 --cycles 6 --m 0.2 0.3 0.5 --procs 30
       [--arms A0 A1 A2 A2h2 B1 B2]   (B: phi pi, easy-axis; h2: field H 2)
"""
import argparse
import json
import multiprocessing as mp
import time

import numpy as np

ARMS = {"A0": (0.0, 0.0), "A1": (np.pi / 2, 0.0), "A2": (np.pi / 2, 1.0), "A2h2": (np.pi / 2, 2.0),
        "B1": (np.pi, 0.0), "B2": (np.pi, 1.0)}
PATTERN = (1, -1, 0)


def fsim(theta, phi):
    c, s = np.cos(theta), np.sin(theta)
    return np.array([[1, 0, 0, 0], [0, c, -1j * s, 0], [0, -1j * s, c, 0], [0, 0, 0, np.exp(-1j * phi)]])


def one(args):
    import quimb.tensor as qtn
    N, cycles, phi, H, bits = args
    c = qtn.CircuitMPS(N, max_bond=4096, cutoff=1e-10)
    X = np.array([[0, 1], [1, 0]])
    for k, b in enumerate(bits):
        if b:
            c.apply_gate_raw(X, (k,))
    G = fsim(np.pi / 4, phi)
    Z = np.diag([1.0, -1.0])
    m0 = sum(bits[N // 2:])
    M, V = [], []
    for _ in range(cycles):
        for par in (0, 1):
            for q in range(par, N - 1, 2):
                c.apply_gate_raw(G, (q, q + 1))
        if H:
            for k in range(N):
                h = H * PATTERN[k % 3]
                if h:
                    c.apply_gate_raw(np.diag([np.exp(-0.5j * h), np.exp(0.5j * h)]), (k,))
        z = np.array([float(np.real(c.psi.local_expectation(Z, k))) for k in range(N // 2, N)])
        M.append(float(((1 - z) / 2).sum() - m0))
        V.append(float(((1 - z ** 2) / 4).sum()))
    return M, V, c.psi.max_bond()


def strings(N, K, m, seed=11):
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(K):
        b = [int(rng.random() < ((1 + m) / 2 if k < N // 2 else (1 - m) / 2)) for k in range(N)]
        out.append(b)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--N", type=int, default=40)
    ap.add_argument("--K", type=int, default=100)
    ap.add_argument("--cycles", type=int, default=6)
    ap.add_argument("--m", type=float, nargs="+", default=[0.2, 0.3, 0.5])
    ap.add_argument("--arms", nargs="+", default=["A0", "A1", "A2", "A2h2", "B1", "B2"])
    ap.add_argument("--procs", type=int, default=mp.cpu_count())
    ap.add_argument("--shots", type=int, nargs="+", default=[500, 1000, 2000])
    a = ap.parse_args()
    boot = np.random.default_rng(5)
    with mp.Pool(a.procs) as pool:
        for m in a.m:
            S = strings(a.N, a.K, m)
            C = [[1 - x for x in b] for b in S]
            for arm in a.arms:
                phi, H = ARMS[arm]
                t0 = time.time()
                rs = pool.map(one, [(a.N, a.cycles, phi, H, b) for b in S + C])
                Ms = np.array([r[0] for r in rs[:a.K]])
                Mc = np.array([r[0] for r in rs[a.K:]])
                V = np.array([r[1] for r in rs])
                W = (Ms - Mc) / 2
                idx = boot.integers(0, a.K, size=(2000, a.K))
                win = {}
                for (x, y) in ((2, 4), (3, 6), (2, 6), (1, 4)):
                    if y > a.cycles:
                        continue
                    f = np.log(y / x)
                    e = float(np.log(W[:, y - 1].mean() / W[:, x - 1].mean()) / f)
                    eM = float(np.log(Ms[:, y - 1].mean() / Ms[:, x - 1].mean()) / f)
                    with np.errstate(invalid="ignore", divide="ignore"):
                        bs = np.log(W[idx, y - 1].mean(1) / W[idx, x - 1].mean(1)) / f
                    sh = {}
                    for s in a.shots:   # W from 2K circuits: var(W mean) = mean(V) / (2 K S) / ... per circuit halves
                        d = [np.sqrt(V[:, t - 1].mean() / (2 * a.K * s)) for t in (x, y)]
                        sh[str(s)] = float(np.hypot(d[1] / W[:, y - 1].mean(), d[0] / W[:, x - 1].mean()) / f)
                    win[f"{x}-{y}"] = dict(exponent_W=e, exponent_M=eM, string_spread=float(np.nanstd(bs)),
                                           resamples_invalid=int(np.sum(~np.isfinite(bs))),
                                           shot_error_bound=sh)
                row = dict(arm=arm, phi=phi, H=H, m=m, N=a.N, K=a.K, W=W.mean(0).tolist(), M=Ms.mean(0).tolist(),
                           bond=max(r[2] for r in rs), seconds=round(time.time() - t0, 1), windows=win,
                           W_per_string=W.tolist())
                with open(a.out, "a") as f:
                    f.write(json.dumps(row) + "\n")
                print(f"m {m} {arm}: bond {row['bond']}, {row['seconds']} s; " + "; ".join(
                    f"{k}: W {v['exponent_W']:.3f} (M {v['exponent_M']:.3f}) +- {v['string_spread']:.3f} strings, "
                    f"shots 1000 {v['shot_error_bound'].get('1000', float('nan')):.3f}" for k, v in win.items()),
                    flush=True)


if __name__ == "__main__":
    main()
