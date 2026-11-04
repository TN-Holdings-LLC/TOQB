"""Tables of the SPD runs (out/*.jsonl): per (phase, theta, t, delta) the qubits, the magnetisation (SPD and exact on
the same qubits), the largest and the mean per-qubit error, the peak term count and the wall time."""
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEVICE_T20 = {0.4: 0.819, 0.8: 0.253, 1.0: 0.050}  # results/kim-cd-2026-11-03 README (all 151 qubits, raw)
THETA0_T20 = 0.979                                  # theta = 0 control at t = 20 (same job)


def rows():
    out = []
    for f in sorted(glob.glob(os.path.join(HERE, "out", "*.jsonl"))):
        for line in open(f):
            out.append(json.loads(line))
    return out


def main():
    rs = rows()
    print("| phase | theta | t | delta | qubits | M SPD | M exact | max err | mean err | peak terms | wall s |")
    print("|---|---|---|---|---|---|---|---|---|---|---|")
    for r in sorted(rs, key=lambda r: (r["phase"] != "t5", r["phase"], r["theta"], r["t"], -r["delta"])):
        ok = [i for i, c in enumerate(r["capped"]) if not c]
        ms = sum(r["z"][i] for i in ok) / len(ok)
        if r["exact"][0] is not None or any(e is not None for e in r["exact"]):
            okx = [i for i in ok if r["exact"][i] is not None]
            me = sum(r["exact"][i] for i in okx) / len(okx)
            err = [abs(r["z"][i] - r["exact"][i]) for i in okx]
            ex = f"{me:.4f} | {max(err):.4f} | {sum(err) / len(err):.4f}"
        else:
            ex = "- | - | -"
        cap = f" ({sum(r['capped'])} capped)" if sum(r["capped"]) else ""
        print(f"| {r['phase']} | {r['theta']} | {r['t']} | {r['delta']:g} | {len(ok)}{cap} | {ms:.4f} | {ex} | {max(r['peak'])} | {r['wall']:.0f} |")
    print()
    print("t = 20, all qubits: SPD magnetisation by delta against the device (raw; and raw / theta-0 control 0.979)")
    for th in (0.4, 0.8, 1.0):
        seq = [(r["delta"], sum(r["z"]) / len(r["z"])) for r in rs if r["phase"] == "t20" and r["theta"] == th
               and len(r["z"]) == 151 and not any(r["capped"])]
        seq.sort(key=lambda x: -x[0])
        s = ", ".join(f"{d:g}: {m:.4f}" for d, m in seq)
        print(f"theta {th}: {s} | device {DEVICE_T20[th]:.3f} (normalised {DEVICE_T20[th] / THETA0_T20:.3f})")


if __name__ == "__main__":
    main()
