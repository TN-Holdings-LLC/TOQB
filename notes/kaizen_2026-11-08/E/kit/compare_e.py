"""E: (1) mirror and floor means, simulation (fez calibration) against the device; (2) forward retention ratio
sim/device under the probe switches. Not a fit: each probe has one stated value."""
import itertools, json, sys
import numpy as np
D = sys.argv[1]
dev_h = json.load(open(f"{D}/inputs/heisB_device_scores.json"))["arms"]
dev_i = json.load(open(f"{D}/inputs/isingA_device_scores.json"))["arms"]
print("== (1) mirror / floor: mean <Z> over the measured qubits (ideal 1)")
for key, dev in (("heisB_mf", dev_h), ("isingA_mf", dev_i)):
    s = json.load(open(f"{D}/out/{key}.json"))
    for name, r in s["circuits"].items():
        z = np.asarray(r["z"]).mean(axis=1)          # per trajectory: mean over qubits
        tag = name[4:].replace("_mirror", "").replace("_floor", "")
        kind = "mirror_mean" if name.endswith("_mirror") else "floor_mean"
        d = dev[tag][kind]
        print(f"{name:26} sim {z.mean():.3f} +- {z.std(ddof=1) / np.sqrt(len(z)):.3f}  device {d:.3f}  sim/device {z.mean() / d:.3f}")
print("== (2) forward: retention ratio sim / device per probe")
sign = np.array([(-1) ** (x + y + w) for x, y, w in itertools.product(range(4), range(2), range(2))])
ans_h = json.load(open(f"{D}/inputs/heisB_answers.json")); ans_i = json.load(open(f"{D}/inputs/isingA_answers.json"))
for probe in ("base", "t2half", "czzz"):
    for key, dev, ans, kind in (("heisB", dev_h, ans_h, "heis"), ("isingA", dev_i, ans_i, "ising")):
        s = json.load(open(f"{D}/out/{key}_{probe}.json"))
        ratios = []
        for name, r in s["circuits"].items():
            tag = name[4:]
            z = np.asarray(r["z"])[:, :16]; ex = np.array([ans[tag][str(q)] for q in range(16)])
            if kind == "heis":
                sim, exv, d = (z * sign).mean(), (ex * sign).mean(), dev[tag]["m_s"]
            else:
                sim, exv, d = z.mean(), ex.mean(), dev[tag]["M"]
            ratios.append((tag, sim / d))
        print(f"{probe:7} {key:7} " + "  ".join(f"{t}:{v:.3f}" for t, v in ratios) + f"   mean {np.mean([v for _, v in ratios]):.3f}")
