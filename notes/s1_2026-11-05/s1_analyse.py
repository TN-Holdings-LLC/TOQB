"""S1 (post hoc, not a test): where does the loss the mirror does not see sit? Reads the table of s1_extract.py.
Per run: rule R (as P6), own floor F_q(t) (linear between measured depths), floor-corrected value y = z / F,
answer a. Reports (i) forward decay per step against the mirror's, per theta; (ii) the alternating part in t;
(iii) residual by patch degree, by number of spectators (heavy-hex neighbours outside the patch), by layer;
(iv) per-qubit stability between runs and per-qubit correlation with the mirror.
usage: python notes/s1_2026-11-05/s1_analyse.py DATA.json [OUT.json]"""
import json, sys
import numpy as np

TXS = ("0.53", "0.3", "0.8")
TS = list(range(1, 10))
LAYERS = [
    [(6, 7), (10, 11), (16, 23), (24, 25), (17, 27), (28, 29), (18, 31), (36, 41), (42, 43), (37, 45), (46, 47), (38, 49)],
    [(3, 4), (5, 6), (7, 8), (9, 10), (21, 22), (23, 24), (25, 26), (27, 28), (29, 30), (43, 44), (45, 46), (47, 48)],
    [(3, 16), (7, 17), (11, 18), (22, 23), (26, 27), (30, 31), (21, 36), (25, 37), (29, 38), (41, 42), (44, 45),
     (48, 49), (4, 5), (8, 9)],
]


def heron_r2_edges():
    """Coupling graph of a Heron r2 lattice from its construction (8 rows of 16, bridges 20r+16+k at column 3+4k for
    even r, 1+4k for odd r). Geometry only; no calibration data."""
    E = set()
    for r in range(8):
        for c in range(15):
            E.add((20 * r + c, 20 * r + c + 1))
    for r in range(7):
        for k in range(4):
            b = 20 * r + 16 + k
            col = 3 + 4 * k if r % 2 == 0 else 1 + 4 * k
            E.add(tuple(sorted((20 * r + col, b))))
            E.add(tuple(sorted((b, 20 * (r + 1) + col))))
    return E


def rule_r(floor):
    z0 = np.mean([floor["1"], floor["5"], floor["9"]], axis=0)
    med = np.median(z0)
    mad = np.median(np.abs(z0 - med))
    return z0 >= med - max(5 * 1.4826 * mad, 0.05)


def F_of(floor):
    ts = sorted(int(t) for t in floor)
    arr = np.array([floor[str(t)] for t in ts])
    return lambda t: np.array([np.interp(t, ts, arr[:, q]) for q in range(arr.shape[1])])


def main(path, out=None):
    D = json.load(open(path))
    Q = D["qubits"]
    n = len(Q)
    patch = {tuple(sorted(e)) for L in LAYERS for e in L}
    adj = {q: set() for q in Q}
    for a, b in patch:
        adj[a].add(b); adj[b].add(a)
    deg = np.array([len(adj[q]) for q in Q])
    phys = heron_r2_edges()
    for a, b in patch:
        assert (a, b) in phys, (a, b)
    nb = {q: {b for a, b in phys if a == q} | {a for a, b in phys if b == q} for q in Q}
    spect = np.array([len(nb[q] - set(Q)) for q in Q])
    nlay = {q: [sum(1 for e in L if q in e) for L in LAYERS] for q in Q}
    A = {tx: {int(t): np.array([np.nan if x is None else x for x in v], float) for t, v in D["answers"][tx].items()}
         for tx in TXS}
    res = {"degree": dict(zip(map(str, Q), map(int, deg))), "spectators": dict(zip(map(str, Q), map(int, spect))),
           "runs": {}}
    print("patch degree counts", {int(k): int(v) for k, v in zip(*np.unique(deg, return_counts=True))},
          "| spectators", {int(k): int(v) for k, v in zip(*np.unique(spect, return_counts=True))})
    Y = {}
    for name, R in D["runs"].items():
        floor = R["z"]["0"]
        keep = rule_r(floor)
        F = F_of(floor)
        rr = {"dropped": [Q[i] for i in np.where(~keep)[0]]}
        Y[name] = {}
        print(f"\n== {name}: dropped {rr['dropped']}")
        for tx in TXS:
            z = {t: np.array(R["z"][tx][str(t)]) for t in TS}
            y = {t: z[t] / F(t) for t in TS}
            Y[name][tx] = y
            ok = {t: keep & ~np.isnan(A[tx][t]) for t in TS}
            ratio = np.array([np.mean(y[t][ok[t]]) / np.mean(A[tx][t][ok[t]]) for t in TS])
            resid = np.array([np.mean(y[t][ok[t]] - A[tx][t][ok[t]]) for t in TS])
            # forward decay per step: least squares of log(ratio) = c + a t, t 1..9
            fa = np.polyfit(TS, np.log(ratio), 1)
            row = dict(ratio=ratio.tolist(), resid=resid.tolist(), fwd_rate=float(fa[0]), fwd_per_step=float(np.exp(fa[0])),
                       fwd_intercept=float(np.exp(fa[1])))
            if R["mirror"]:
                m = R["mirror"][tx]
                mr = [np.median((0.5 * np.log(np.clip(np.array(m[str(t)]) / np.maximum(F(2 * t), .05), 1e-3, 1)) / t)[keep])
                      for t in (3, 5)]
                row["mirror_rate"] = float(np.mean(mr)); row["mirror_per_step"] = float(np.exp(np.mean(mr)))
                row["mirror_rate_t3_t5"] = [float(x) for x in mr]
            # alternating part: residual minus a quadratic in t; then project on (-1)^t
            fit = np.polyval(np.polyfit(TS, resid, 2), TS)
            alt = resid - fit
            row["alternating_amp"] = float(np.dot(alt, (-1.0) ** np.array(TS)) / len(TS))
            row["alternating_rms"] = float(np.sqrt(np.mean(alt ** 2)))
            # by degree and spectators, t 5-9, per qubit mean residual
            per_q = np.array([np.nanmean([y[t][i] - A[tx][t][i] for t in range(5, 10)]) for i in range(n)])
            row["per_qubit_resid_t5_9"] = dict(zip(map(str, Q), map(float, per_q)))
            for key, arr in (("by_degree", deg), ("by_spectators", spect)):
                row[key] = {int(v): float(np.nanmean(per_q[keep & (arr == v)])) for v in np.unique(arr)}
            rr[tx] = row
            print(f"th {tx}: fwd/step {row['fwd_per_step']:.4f} (intercept {row['fwd_intercept']:.3f})"
                  + (f" mirror/step {row['mirror_per_step']:.4f} [t3 {np.exp(mr[0]):.4f} t5 {np.exp(mr[1]):.4f}]"
                     if R['mirror'] else "")
                  + f" | resid t1..9 {np.round(resid, 3).tolist()} | alt amp {row['alternating_amp']:+.4f} rms {row['alternating_rms']:.4f}"
                  + f" | by degree {({k: round(v, 3) for k, v in row['by_degree'].items()})}"
                  + f" by spect {({k: round(v, 3) for k, v in row['by_spectators'].items()})}")
        res["runs"][name] = rr
    # per-qubit stability and correlation
    print("\n== per-qubit, t 5-9 mean residual (kept in both)")
    pairs = [("corr_marrakesh", "p6_marrakesh"), ("corr_fez", "p6_fez"), ("corr_marrakesh", "corr_fez")]
    res["pairs"] = {}
    for a, b in pairs:
        for tx in TXS:
            pa = np.array([res["runs"][a][tx]["per_qubit_resid_t5_9"][str(q)] for q in Q])
            pb = np.array([res["runs"][b][tx]["per_qubit_resid_t5_9"][str(q)] for q in Q])
            m = ~np.isnan(pa) & ~np.isnan(pb) & np.array([q not in res["runs"][a]["dropped"] + res["runs"][b]["dropped"] for q in Q])
            c = float(np.corrcoef(pa[m], pb[m])[0, 1])
            res["pairs"][f"{a}|{b}|{tx}"] = c
            print(f"   {a} vs {b} th {tx}: corr {c:+.2f} (n {m.sum()}), mean {pa[m].mean():+.3f} vs {pb[m].mean():+.3f}")
    # does the per-qubit mirror predict the per-qubit forward loss?
    print("\n== per-qubit mirror decay vs per-qubit forward residual (t 5-9)")
    for name in ("corr_fez", "corr_marrakesh"):
        R = D["runs"][name]; F = F_of(R["z"]["0"]); keep = rule_r(R["z"]["0"])
        for tx in TXS:
            m = R["mirror"][tx]
            mq = np.mean([0.5 * np.log(np.clip(np.array(m[str(t)]) / np.maximum(F(2 * t), .05), 1e-3, 1)) / t for t in (3, 5)], axis=0)
            pf = np.array([res["runs"][name][tx]["per_qubit_resid_t5_9"][str(q)] for q in Q])
            k = keep & ~np.isnan(pf)
            c = float(np.corrcoef(mq[k], pf[k])[0, 1])
            res["pairs"][f"mirror|{name}|{tx}"] = c
            print(f"   {name} th {tx}: corr(mirror rate, fwd resid) {c:+.2f}; mirror rate spread {np.std(mq[k]):.4f}")
    if out:
        json.dump(res, open(out, "w"), indent=1)


if __name__ == "__main__":
    main(*sys.argv[1:])
