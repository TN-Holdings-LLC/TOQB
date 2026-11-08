"""Two mirrors: mirror 1 (plain round trip) and mirror 2 (Pauli-twirled round trip, 16 frames), D = m2 - m1, per
circuit and stated coherent CZ error EPS (and sx over-rotation DELTA); forward retention under the same EPS; and the
device cost of resolving D at EPS = 0.02. Nothing is fitted."""
import itertools, json, os, sys
import numpy as np
D = sys.argv[1]
EPS = ["0", "0.01", "0.02", "0.04"]

def load(p):
    return json.load(open(os.path.join(D, "out", p)))

def m1_stats(r):
    v = np.asarray(r["z"]).mean(axis=1)
    return v.mean(), v.std(ddof=1) / np.sqrt(len(v)), v.var(ddof=1)

def m2_stats(r):
    v = np.asarray(r["z"]).mean(axis=1)
    idx = np.cumsum([0] + r["chunks"])
    fm = np.array([v[a:b].mean() for a, b in zip(idx[:-1], idx[1:])])
    within = np.mean([v[a:b].var(ddof=1) for a, b in zip(idx[:-1], idx[1:])])
    per = np.mean(r["chunks"])
    sf2 = max(0.0, fm.var(ddof=1) - within / per)          # spread between frames, trajectory noise removed
    return fm.mean(), fm.std(ddof=1) / np.sqrt(len(fm)), sf2, len(fm)

rows = {}
print("== 1. mirror 1, mirror 2, D = m2 - m1 (mean <Z> over the measured qubits; SE in brackets)")
for tag in EPS + ["dx"]:
    for key in ("heisB_mf", "isingA_m9"):
        a, b = load(f"{key}_m1_{tag}.json"), load(f"{key}_m2_{tag}.json")
        for name in a["circuits"]:
            if name.endswith("_floor"):
                continue
            ra, rb = a["circuits"][name], b["circuits"][name]
            m1, s1, v1 = m1_stats(ra); m2, s2, sf2, F = m2_stats(rb)
            d, sd = m2 - m1, np.hypot(s1, s2)
            rows[(tag, name)] = dict(m1=m1, s1=s1, m2=m2, s2=s2, d=d, sd=sd, sf2=sf2, F=F, cz=ra["cz"])
            lab = "eps " + tag if tag != "dx" else "sx dx 0.01"
            print(f"{lab:11} {name:24} CZ {ra['cz']:4}  m1 {m1:.3f} ({s1:.3f})  m2 {m2:.3f} ({s2:.3f})  D {d:+.3f} ({sd:.3f})"
                  f"  {'> 2SE' if abs(d) > 2 * sd else 'within 2SE'}   [traj {len(ra['z'])}, frames {F} x {rb['chunks'][0]}]")
print("\n== 2. eps = 0: is D within 2 SE of 0?")
names = [n for (t, n) in rows if t == "0"]
for n in names:
    r = rows[("0", n)]
    print(f"{n:24} D {r['d']:+.4f} +- {r['sd']:.4f}  ({r['d'] / r['sd']:+.1f} SE)")
print("\n== 3. growth of D with eps and depth; compare with (n eps)^2 and n eps^2 (n = CZ of the mirror circuit)")
for n in names:
    base = rows[("0", n)]["d"]; cz = rows[("0", n)]["cz"]
    parts = []
    for e in EPS[1:]:
        r = rows[(e, n)]; ex = r["d"] - base; ef = float(e)
        parts.append(f"eps {e}: D {r['d']:+.3f}, D-D0 {ex:+.3f}, /(n eps)^2 {ex / (cz * ef) ** 2:.3f}, /(n eps^2) {ex / (cz * ef ** 2):.2f};"
                     f" 1-m1 {1 - r['m1']:.3f}, 1-m2 {1 - r['m2']:.3f}")
    print(f"{n} (CZ {cz}):\n    " + "\n    ".join(parts))
print("\n== 5. forward retention (relative to eps = 0) against D")
sign = np.array([(-1) ** (x + y + w) for x, y, w in itertools.product(range(4), range(2), range(2))])
for key, kind, mkey in (("heisB", "heis", "heisB_mf"), ("isingA_f9", "ising", "isingA_m9")):
    f0 = load(f"{key}_fwd_0.json")["circuits"]
    for name in f0:
        val = lambda r: ((np.asarray(r["z"])[:, :16] * sign).mean() if kind == "heis" else np.asarray(r["z"])[:, :16].mean())
        v0 = val(f0[name])
        mname = name + "_mirror"
        parts = []
        for e in EPS[1:]:
            fe = load(f"{key}_fwd_{e}.json")["circuits"][name]
            dd = rows.get((e, mname), {}).get("d", float("nan")) - rows.get(("0", mname), {}).get("d", float("nan"))
            parts.append(f"eps {e}: forward {val(fe) / v0:.3f}, D-D0 {dd:+.3f}")
        print(f"{name:20} " + " | ".join(parts))
print("\n== 6. device cost to resolve D at eps = 0.02 (2 SE), shot noise per circuit v = (1 - m^2)/16 (sites independent,")
print("   an assumption), frame spread from the simulation; mirror 2 added for every arm with S shots split over F frames")
for n in names:
    r = rows[("0.02", n)]; d = abs(r["d"] - rows[("0", n)]["d"]) if False else abs(r["d"])
    v1, v2 = (1 - r["m1"] ** 2) / 16, (1 - r["m2"] ** 2) / 16
    out = []
    for F in (16, 32, 64):
        need = (d / 2) ** 2 - r["sf2"] / F
        S = (v1 + v2) / need if need > 0 else float("inf")
        out.append(f"F {F}: S {S:,.0f}" if np.isfinite(S) else f"F {F}: not reachable")
    print(f"{n:24} |D| {d:.3f}  frame spread sd {np.sqrt(r['sf2']):.3f}  " + "  ".join(out))
print("   heisE today: 148 circuits, 168 s (48 arms x user/floor/mirror + 4 sentinel, 4000 shots each)."
      " Adding one mirror 2 per arm at 4000 shots: about 1 + 48/148 = 1.32 x the device time (time taken as proportional to shots).")
