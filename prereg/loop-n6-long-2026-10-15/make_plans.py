"""Writes the 5 plans of the loop long run (n = 6, L = 8): the pilot's plan unchanged except 100,000 iterations,
evaluations at fixed points, a thinned loss curve, the fast engine and loop seeds 3001-3005. From the TOQB root:
    python prereg/loop-n6-long-2026-10-15/make_plans.py
"""
import hashlib
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SEEDS = list(range(3001, 3006))
AT = [20, 40, 60, 100, 200, 300, 600, 1000, 2000, 3000, 6000]


def main():
    base = json.load(open(os.path.join(HERE, "..", "..", "plan_loop_pilot_n6_s11.json"), encoding="utf-8"))
    lines = []
    for s in SEEDS:
        plan = json.loads(json.dumps(base))
        plan["name"] = f"TOQB loop long run n6 L8 (seed {s})"
        plan["note"] = ("Long run, scored against prereg/2026-10-15-loop-n6-long.md. The pilot's plan with 100,000 "
                        "iterations, the fast engine, evaluations at fixed points and every 10,000, and loop_seed.")
        plan["engine"] = "fast"
        plan["optimizer"].update(iterations=100000, loop_seed=s)
        plan["evaluation"].update(every=10000, at=AT, curve_every=100)
        name = f"plan_s{s}.json"
        text = json.dumps(plan, indent=1) + "\n"
        with open(os.path.join(HERE, name), "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        lines.append(f"{hashlib.sha256(text.encode('utf-8')).hexdigest()}  {name}")
    with open(os.path.join(HERE, "SHA256SUMS"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    print(f"{len(SEEDS)} plans written")


if __name__ == "__main__":
    main()
