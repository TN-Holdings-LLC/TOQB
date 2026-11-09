"""N = 91 dual-unitary run on marrakesh (raw jobs of 2026-11-09, read only): decay rates with their standard errors
and the bias against cos 2h, and the off-light-cone check. The chain order is rebuilt from the compiled circuits
(the CZ graph of a user circuit is the chain path); site 0 is the end at which the h = 0 on-cone values are large.
Decay rate as in gpu/du51_score.py: R(t) = <X_t>(h) / <X_t>(0), weighted least squares on ln R through the origin
over the t where both values exceed 3 SE; SE of k from the fit. Shot SE of <Z>: sqrt((1 - z^2) / shots)."""
import json, sys
from collections import defaultdict
import numpy as np
from qiskit import qpy

D = sys.argv[1]
H = (0.0, 0.05, 0.1, 0.15)
data = {}           # (h, t) -> dict(z: {qubit: z}, shots, chain)
paths = {}
for job in ("du91_A", "du91_B"):
    man = json.load(open(f"{D}/{job}/job/manifest.json"))
    names = [man["cells"][p["cell"]]["name"] for p in man["pubs"]]
    circs = qpy.load(open(f"{D}/{job}/job/circuits.qpy", "rb"))
    rows = json.load(open(f"{D}/{job}/job/raw_counts.json"))["rows"]
    for k, n in enumerate(names):
        if not n.startswith("p2d_du91_") or n.endswith(("_floor", "_mirror")):
            continue
        _, _, hs, ts = n.split("_")
        h, t = int(hs[1:]) / 100, int(ts[1:])
        c = circs[k]
        meas = {c.find_bit(i.clbits[0]).index: c.find_bit(i.qubits[0]).index for i in c.data if i.operation.name == "measure"}
        adj = defaultdict(set)
        for i in c.data:
            if i.operation.name == "cz":
                a, b = (c.find_bit(q).index for q in i.qubits)
                adj[a].add(b); adj[b].add(a)
        counts = rows[k]["counts"]
        S = sum(counts.values())
        nb = len(meas)
        acc = np.zeros(nb)
        for bits, v in counts.items():
            b = bits.replace(" ", "")
            acc += v * np.array([1 - 2 * int(b[len(b) - 1 - j]) for j in range(nb)])
        z = {meas[j]: acc[j] / S for j in range(nb)}
        data[(h, t)] = dict(z=z, shots=S, adj={q: set(v) for q, v in adj.items()}, job=job)
# chain path from the CZ graph (degree <= 2 on the measured qubits)
any_pt = data[(0.0, 24)]
adj = any_pt["adj"]
qs = set(any_pt["z"])
deg = {q: len(adj.get(q, set()) & qs) for q in qs}
ends = [q for q, d in deg.items() if d == 1]
assert len(ends) == 2 and max(deg.values()) <= 2, (ends, max(deg.values()))

def walk(start):
    order, prev, cur = [start], None, start
    while True:
        nxt = [q for q in adj[cur] & qs if q != prev]
        if not nxt:
            return order
        prev, cur = cur, nxt[0]; order.append(cur)
cands = [walk(e) for e in ends]
score = [sum(data[(0.0, t)]["z"][ch[t]] for t in (4, 8, 12, 16, 20, 24)) for ch in cands]
chain = cands[int(np.argmax(score))]
print(f"chain rebuilt: {len(chain)} qubits, site 0 = qubit {chain[0]}, site 24 = qubit {chain[24]}; h=0 on-cone sums {score}")
T = (4, 8, 12, 16, 20, 24)
se = lambda z, S: float(np.sqrt(max(1 - z * z, 1e-12) / S))
print("\n== on-cone values <X_t> (site t) with shot SE")
for h in H:
    parts = []
    for t in T:
        zz = data[(h, t)]["z"][chain[t]]
        parts.append("t%d %+.3f+-%.3f" % (t, zz, se(zz, data[(h, t)]["shots"])))
    print("h %.2f: " % h + "  ".join(parts))
print("\n== decay rate k (WLS on ln R through the origin) against cos 2h")
res = {}
for h in H[1:]:
    xs, ys, ws = [], [], []
    for t in T:
        a, b = data[(h, t)], data[(0.0, t)]
        za, zb = a["z"][chain[t]], b["z"][chain[t]]
        sa, sb = se(za, a["shots"]), se(zb, b["shots"])
        if za > 3 * sa and zb > 3 * sb:
            r = za / zb
            var = (sa / za) ** 2 + (sb / zb) ** 2         # variance of ln R
            xs.append(t); ys.append(np.log(r)); ws.append(1 / var)
    xs, ys, ws = map(np.array, (xs, ys, ws))
    slope = np.sum(ws * xs * ys) / np.sum(ws * xs * xs)
    s_slope = np.sqrt(1 / np.sum(ws * xs * xs))
    resid = ys - slope * xs
    chi2 = float(np.sum(ws * resid ** 2)); dof = len(xs) - 1
    k, sk = np.exp(slope), np.exp(slope) * s_slope
    ex = np.cos(2 * h)
    res[h] = dict(k=k, se=sk, exact=ex, z=(k - ex) / sk, chi2=chi2, dof=dof, ts=list(map(int, xs)))
    print(f"h {h:.2f}: k {k:.4f} ± {sk:.4f}  cos2h {ex:.4f}  k - cos2h {k - ex:+.4f} ({(k - ex) / sk:+.1f} SE)  "
          f"fit chi2 {chi2:.1f} / dof {dof}  t used {list(map(int, xs))}")
zs = np.array([r["z"] for r in res.values()])
print(f"bias: all three above cos 2h: {all(z > 0 for z in zs)}; combined (k - cos2h)/SE: mean {zs.mean():+.2f}, "
      f"sum/sqrt(3) {zs.sum() / np.sqrt(3):+.2f}  (the three share the h = 0 ruler, so they are not independent)")
print("\n== off-light-cone check: |<X>| of every measured qubit other than site t (ideal 0 outside the cone)")
allo = []
by_q = defaultdict(list)
for (h, t), d in sorted(data.items()):
    off = {q: abs(v) for q, v in d["z"].items() if q != chain[t]}
    vals = np.array(list(off.values()))
    worst = sorted(off, key=lambda q: -off[q])[:3]
    for q, v in off.items():
        by_q[q].append(v)
    allo.append(vals)
    print(f"h {h:.2f} t {t:2}: mean {vals.mean():.4f}  median {np.median(vals):.4f}  max {vals.max():.3f} at q{worst[0]} "
          f"(next q{worst[1]} {off[worst[1]]:.3f}, q{worst[2]} {off[worst[2]]:.3f})  shot SE ~{1 / np.sqrt(d['shots']):.4f}")
allv = np.concatenate(allo)
print(f"all points: mean {allv.mean():.4f}, median {np.median(allv):.4f}; fraction above 3 shot-SE (0.047): {np.mean(allv > 3 / np.sqrt(4000)):.3f}")
qm = sorted(by_q, key=lambda q: -np.mean(by_q[q]))[:6]
print("qubits with the largest mean off-cone |<X>| over the 24 points: " +
      ", ".join(f"q{q} (chain site {chain.index(q)}) {np.mean(by_q[q]):.3f}" for q in qm))
excl = np.concatenate([[v for q, v in zip(d["z"].keys(), [abs(x) for x in d["z"].values()]) if q != chain[t] and q not in qm[:2]] for (h, t), d in data.items()])
print(f"without the two largest: mean {excl.mean():.4f}, max {excl.max():.3f}")
json.dump(dict(chain=chain, rates={str(h): r for h, r in res.items()}), open("du91_check.json", "w"), indent=1)

print("\n== which job holds which h; decay-rate SE scaled by sqrt(chi2/dof) (fit scatter above shot noise)")
for h in H:
    print(f"h {h:.2f}: job " + ", ".join(sorted({data[(h, t)]['job'] for t in T})))
for h, r in res.items():
    f = np.sqrt(max(r["chi2"] / r["dof"], 1.0))
    print(f"h {h:.2f}: k {r['k']:.4f}, SE {r['se']:.4f} x {f:.2f} = {r['se'] * f:.4f}; k - cos2h {r['k'] - r['exact']:+.4f} = {(r['k'] - r['exact']) / (r['se'] * f):+.1f} scaled SE")
