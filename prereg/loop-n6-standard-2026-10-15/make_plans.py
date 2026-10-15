"""Writes the 20 plans of the loop standard run (n = 6, L = 8) from the pilot's plan.

Each plan is the pilot's seed-11 plan with only the name, the note and `loop_seed` changed. The loop seeds are 101-120;
the pilot's seeds (11, 12) are not reused. Run from the TOQB root:
    python prereg/loop-n6-standard-2026-10-15/make_plans.py
"""
import hashlib
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SEEDS = list(range(101, 121))


def main():
    base = json.load(open(os.path.join(HERE, "..", "..", "plan_loop_pilot_n6_s11.json"), encoding="utf-8"))
    lines = []
    for s in SEEDS:
        plan = json.loads(json.dumps(base))
        plan["name"] = f"TOQB loop standard run n6 L8 (seed {s})"
        plan["note"] = ("Standard run, scored against prereg/2026-10-15-loop-n6-standard.md. The pilot's plan "
                        "(plan_loop_pilot_n6_s11.json) with only the name, this note and loop_seed changed.")
        plan["optimizer"]["loop_seed"] = s
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
