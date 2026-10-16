"""Writes the 200 plans of the loop reach run (n = 6, L = 8): the pilot's plan (run 1's settings) unchanged except
1,000 iterations, test evaluations every 50 iterations, the loss curve every 10th iteration, the fast engine, and loop
seeds 8001-8200. No budget stop. From the TOQB root:
    python prereg/loop-n6-reach-2026-10-16/make_plans.py
"""
import hashlib
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SEEDS = list(range(8001, 8201))


def main():
    base = json.load(open(os.path.join(HERE, "..", "..", "plan_loop_pilot_n6_s11.json"), encoding="utf-8"))
    lines = []
    for s in SEEDS:
        plan = json.loads(json.dumps(base))
        plan["name"] = f"TOQB loop reach run n6 L8, 1,000 iterations (seed {s})"
        plan["note"] = ("Reach run, scored against prereg/2026-10-16-loop-n6-reach.md. The pilot's plan with 1,000 "
                        "iterations, test evaluations every 50, the loss curve every 10th iteration, the fast engine, "
                        "and loop_seed.")
        plan["engine"] = "fast"
        plan["optimizer"].update(iterations=1000, loop_seed=s)
        plan["evaluation"].update(every=50, curve_every=10)
        plan["evaluation"].pop("stop_budget_usd", None)
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
