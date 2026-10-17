"""Writes the 20 plans of S2R stage 0 (prereg/2026-10-17-s2r-stage0.md), seeds 9001-9020, and SHA256SUMS. From the
TOQB root:
    python prereg/s2r-stage0-2026-10-17/make_plans.py
"""
import hashlib
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SEEDS = list(range(9001, 9021))
SIGMA0, DECAY = 1.0, 0.7  # chosen by the exploratory pilot (seed 901) before the pre-registration (see it)


def plan(seed):
    return dict(
        name=f"TOQB S2R stage 0, n6 L8 (seed {seed})",
        note="S2R stage 0, scored against prereg/2026-10-17-s2r-stage0.md.",
        device="fake:FakeFez",
        task=dict(n=6, layers=8, enc=math.pi / 2, teacher_seed=4, teacher_gap=0.2, n_train=64, n_test=48),
        s2r=dict(seed=seed, init=0.5, sigma0=SIGMA0, decay=DECAY, candidates=10000, batch=8, top_k=16, mu=8,
                 budget_usd=192.0, max_loops=50),
        spsa=dict(name="SPSA", iterations=1000, batch=8, a=3.0, c=0.2, A=2, init=0.5, loop_seed=seed),
        evaluation=dict(shots=400, shot_seed=20261017, spsa_every=10),
        standin=dict(t12=0.3, over=0.01, zz_hz=1.0e4, seed=20261017),
        qpu_cost=dict(per_shot_s=0.00027, per_circuit_s=0.036, usd_per_s=96 / 60))


def main():
    lines = []
    for s in SEEDS:
        name = f"plan_s{s}.json"
        text = json.dumps(plan(s), indent=1) + "\n"
        with open(os.path.join(HERE, name), "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        lines.append(f"{hashlib.sha256(text.encode()).hexdigest()}  {name}")
    with open(os.path.join(HERE, "SHA256SUMS"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    print("written", len(SEEDS), "plans")


if __name__ == "__main__":
    main()
