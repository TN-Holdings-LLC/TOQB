"""The classifier task for the paper 3 follow-up (owner 2026-11-10: rule against SABRE, bands beside, 10-30's shots and
points kept, new seeds so that the labels can be sealed). The 10-30 teacher task (toqb.qelm.teacher_task) unchanged
in form: n = 20 ring, depth L (given: from the day's L* by toqb.qelm.depth_formula), inputs x uniform in [-1, 1]^20
from the public seed, a teacher w from a secret seed, centred labels, margin cut, 128 train / 200 test.

Writes OUT/task.json (public: the kept inputs and the settings; no label, no feature, no w) and ANSWERS_OUT (sealed:
the teacher's seed and w, mu, gamma, the noiseless features, every label, the noiseless ceiling). Prints the sha256
of ANSWERS_OUT, which the declaration records.

usage: PYTHONPATH=<TOQB> python gpu/qclf_task.py OUT ANSWERS_OUT --L 19 [--seed-x 20261110] [--procs N]
"""
import argparse
import hashlib
import json
import math
import os
import secrets
import sys
import time

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from toqb import qelm as Q  # noqa: E402

N = 20
ENC = math.pi / 2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("answers_out")
    ap.add_argument("--L", type=int, required=True)
    ap.add_argument("--seed-x", type=int, default=20261110)
    ap.add_argument("--procs", type=int, default=None)
    a = ap.parse_args()
    tf = os.path.join(a.out, "task.json")
    for p in (tf, a.answers_out):
        if os.path.exists(p):
            raise SystemExit(f"STOP: {p} exists")
    if a.procs:
        os.environ["QELM_PROCS"] = str(a.procs)
    seed_w = secrets.randbits(62)  # secret until the answers are released
    t0 = time.perf_counter()
    T = Q.teacher_task(n=N, L=a.L, enc=ENC, pool=Q.A_POOL, gamma_frac=Q.A_GAMMA_FRAC, seed_x=a.seed_x, seed_w=seed_w)
    ntr = Q.N_TRAIN
    F, y = T["F"], T["y"]
    ceiling = Q.accuracy(Q.ols_predict(Q.ols_fit(F[:ntr], y[:ntr]), F[ntr:]), y[ntr:])
    ans = dict(kind="qclf_answers", n=N, L=a.L, enc=ENC, seed_x=a.seed_x, seed_w=seed_w, w=T["w"].tolist(),
               mu=T["mu"].tolist(), gamma=T["gamma"], gamma_frac=Q.A_GAMMA_FRAC, pool=T["pool"], kept=T["kept"],
               features=F.tolist(), y_train=y[:ntr].tolist(), y_test=y[ntr:].tolist(), ceiling=ceiling,
               feature_sd=T["feature_sd"], feature_sd_by_basis=T["feature_sd_by_basis"],
               class_share_plus=[float(np.mean(y[:ntr] == 1)), float(np.mean(y[ntr:] == 1))])
    os.makedirs(os.path.dirname(os.path.abspath(a.answers_out)), exist_ok=True)
    with open(a.answers_out, "w") as f:
        json.dump(ans, f)
    sha = hashlib.sha256(open(a.answers_out, "rb").read()).hexdigest()
    os.makedirs(a.out, exist_ok=True)
    task = dict(kind="qclf_task", n=N, L=a.L, enc=ENC, seed_x=a.seed_x, pool=Q.A_POOL, gamma_frac=Q.A_GAMMA_FRAC,
                n_train=ntr, n_test=Q.N_TEST, X=T["X"].tolist(), answers_sha256=sha,
                wall_s=round(time.perf_counter() - t0, 1))
    json.dump(task, open(tf, "w"))
    print(f"task: n {N}, L {a.L}, kept {T['kept']} of {T['pool']}, feature sd {T['feature_sd']:.4f}, "
          f"class share (+1) {ans['class_share_plus'][0]:.3f} / {ans['class_share_plus'][1]:.3f}, "
          f"ceiling {ceiling:.3f}, {task['wall_s']:.0f} s")
    print(f"answers sha256 {sha}")


if __name__ == "__main__":
    main()
