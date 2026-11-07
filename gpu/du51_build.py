"""IBM's dual-unitary chain experiment (arXiv 2411.00765) at N = 51, raw, through psf-os's user entrance
(prereg/drafts-2026-11-06/du51_DRAFT.md; owner 2026-11-07 13:56 JST: "続きをやるなら、双対ユニタリの51量子ビット").

From one device record: the chain is the first qualifying copy of the first qualifying shape (daily/du91.SHAPES, fixed
order); the user circuits are gpu/practice_circuits.p4 on that shape's labels, J = b = pi/4, h in {0, 0.05, 0.1, 0.15},
t in {4, 8, 12, 16, 20, 24}; psf_os.user2d.build_batch places each one by translation (the same copy), with its
floor and mirror and one ring sentinel per job. Two jobs back to back: A = h {0, 0.05}, B = h {0.1, 0.15}.
Answers (closed form, psf_os.dual.exact): {tag: {label: <X>}} written to ANSWERS_OUT, to be sealed by hash.

usage: PYTHONPATH=<psf-os>:<TOQB> python gpu/du51_build.py DEV_DIR OUT_DIR ANSWERS_OUT [--dry-clifford-sentinel]
"""
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from daily import du91 as X  # noqa: E402
from psf_os import device as Dv  # noqa: E402
from psf_os import user2d as U  # noqa: E402

N = 51
JOBS = {"A": (0.0, 0.05), "B": (0.1, 0.15)}


def tag(h, t):
    return f"du51_h{int(round(h * 100)):02d}_t{t:02d}"


def main():
    dev_dir, out, ans_out = sys.argv[1:4]
    spec = dict(kind="echo_clifford", D=24) if "--dry-clifford-sentinel" in sys.argv else None
    for p in (out, ans_out):
        if os.path.exists(p):
            raise SystemExit(f"STOP: {p} exists")
    dev = Dv.Device.load(dev_dir)
    pl = X.place(dev, N)
    if pl["shape"] is None:
        raise SystemExit(f"NOT RUN: no shape qualifies on {dev.name}: {pl['passed_over']}")
    shape = next(s for s in X.SHAPES if s[0] == pl["shape"])
    labels = X.snake(N, shape)
    answers, reps = {}, {}
    for name, hs in JOBS.items():
        items = []
        for h in hs:
            for t in X.T_STEPS:
                items.append((tag(h, t), X.circuit(N, h, t, shape)))
                answers[tag(h, t)] = {str(q): v for q, v in zip(labels, X.exact(N, t, h))}
        reps[name] = U.build_batch(dev, items, os.path.join(out, name), shots=4000, sentinel_spec=spec,
                                   max_seconds=60)
    with open(ans_out, "w") as f:
        json.dump(answers, f, indent=1, sort_keys=True)
    log = dict(device=dev.name, shape=pl["shape"], copy=dict(drow=pl["drow"], dcol=pl["dcol"]), chain=pl["chain"],
               passed_over=pl["passed_over"],
               jobs={k: dict(circuits=r["circuits"], qpu_seconds_model=r["qpu_seconds_model"],
                             cz={t: v["cz"] for t, v in r["items"].items()},
                             copies={t: v["copy"] for t, v in r["items"].items()}) for k, r in reps.items()})
    json.dump(log, open(os.path.join(out, "build.json"), "w"), indent=1)
    print(f"{dev.name}: shape {pl['shape']} copy ({pl['drow']}, {pl['dcol']}), chain {pl['chain'][:3]}..{pl['chain'][-2:]}")
    for k, j in log["jobs"].items():
        print(f"job {k}: {j['circuits']} circuits, {j['qpu_seconds_model']} s by the model, CZ up to {max(j['cz'].values())},"
              f" copies {sorted({(c['drow'], c['dcol']) for c in j['copies'].values()})}")
    print("answers sha256", hashlib.sha256(open(ans_out, "rb").read()).hexdigest())


if __name__ == "__main__":
    main()
