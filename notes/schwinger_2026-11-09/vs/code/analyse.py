"""Noiseless agreement and the candidate table, from run2d's compiled circuits. Writes NO answer value: per candidate only
the largest difference (compiled vs exact Trotter output), the RMS of the exact <Z_n> (2 decimals), a coarse band for
nu (width 0.05), and the largest Trotter error against continuous time (2 significant digits).

usage: python analyse.py WORK_DIR RUN2D.json OUT_AGREE.json OUT_TABLE.md
"""
import json, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import schwinger as S
from qiskit import qpy

work, run2d, out_agree, out_md = sys.argv[1:5]
R = json.load(open(run2d))
P = {p[0]: p for p in S.PARAMS}
exact, agree = {}, {}


def band(x, w=0.05):
    lo = math.floor(x / w) * w
    return f"{lo:.2f}–{lo + w:.2f}"


for key, r in sorted(R.items()):
    dn, cid = key.split("/")
    n, pn, st = int(cid.split("_")[0][1:]), cid.split("_")[1], int(cid.split("_")[2][1:])
    if (n, pn, st) not in exact:
        z = S.z_sites(S.trotter(n, st, P[pn]), n, st)
        zc = S.z_continuous(n, st * S.DT, P[pn])
        exact[(n, pn, st)] = dict(rms=math.sqrt(sum(v * v for v in z) / n), nu=S.nu(z),
                                  trotter_err=max(abs(a - b) for a, b in zip(z, zc)), z=z)
    if r["returncode"] != 0:
        agree[key] = dict(refused=r["refused"])
        continue
    with open(os.path.join(work, r.get("dir", os.path.join("run2d", dn, f"{cid}_{dn}")), "runs", "p2d_user.qpy"), "rb") as f:
        cq = qpy.load(f)[0]
    zq = S.z_sites(cq, n, st, r['chain'])
    agree[key] = dict(max_diff=max(abs(a - b) for a, b in zip(zq, exact[(n, pn, st)]["z"])),
                      qubits_touched=len({cq.find_bit(q).index for i in cq.data for q in i.qubits}))
    print(key, f"{agree[key]['max_diff']:.1e}", flush=True)

json.dump(dict(agree=agree, max_over_all=max(a["max_diff"] for a in agree.values() if "max_diff" in a)),
          open(out_agree, "w"), indent=1)

# table: one row per (N, params, steps); CZ / layers from run2d (fez first), placement per device
lines = ["| N | 組 | ステップ | 時間 wt | CZ | CZ の層 | 深さ | 二乗平均 <Z> | ν の帯 | トロッター誤差（最大） | fez | kingston | marrakesh | 雑音なしの最大のずれ |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
for (n, pn, st), e in sorted(exact.items(), key=lambda x: (x[0][0], x[0][1], x[0][2])):
    cells, cz, lay, dep, md = [], None, None, None, 0.0
    for dn in ("ibm_fez", "ibm_kingston", "ibm_marrakesh"):
        r = R.get(f"{dn}/N{n}_{pn}_s{st}")
        if r is None:
            cells.append("—"); continue
        if r["returncode"] != 0:
            cells.append("refuse"); continue
        c = r["copy"]
        cells.append(f"{r['rule']} ({c['drow']},{c['dcol']})" if isinstance(c, dict) else f"{r['rule']} {c}")
        if cz is None:
            cz, lay, dep = r["cz"], r["cz_layers"], r["depth"]
        md = max(md, agree[f"{dn}/N{n}_{pn}_s{st}"]["max_diff"])
    lines.append(f"| {n} | {pn} | {st} | {st * S.DT:.2f} | {cz} | {lay} | {dep} | {e['rms']:.2f} | {band(e['nu'])} | "
                 f"{e['trotter_err']:.2g} | " + " | ".join(cells) + f" | {md:.1e} |")
open(out_md, "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")
print(len(exact), "candidates;", len(agree), "compiled circuits; max diff",
      f"{max(a['max_diff'] for a in agree.values() if 'max_diff' in a):.1e}")
