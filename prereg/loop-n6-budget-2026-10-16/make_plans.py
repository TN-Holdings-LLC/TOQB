"""Writes the 1,000 plans of the loop budget run (n = 6, L = 8): the pilot's plan (run 1's settings) unchanged except
the hard 2-minute QPU budget, the fast engine, evaluations at the start and at the stop only, and loop seeds
6001-7000. From the TOQB root:
    python prereg/loop-n6-budget-2026-10-16/make_plans.py
"""
import hashlib
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SEEDS = list(range(6001, 7001))


def main():
    base = json.load(open(os.path.join(HERE, "..", "..", "plan_loop_pilot_n6_s11.json"), encoding="utf-8"))
    lines = []
    for s in SEEDS:
        plan = json.loads(json.dumps(base))
        plan["name"] = f"TOQB loop budget run n6 L8, 2 minutes of QPU (seed {s})"
        plan["note"] = ("Budget run, scored against prereg/2026-10-16-loop-n6-budget.md. The pilot's plan with a hard "
                        "QPU budget of $192 (2 min at $96/min, batch mode), the fast engine, and loop_seed.")
        plan["engine"] = "fast"
        plan["optimizer"].update(iterations=60, loop_seed=s)
        plan["evaluation"].update(every=1000, stop_budget_usd=192.0)
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
