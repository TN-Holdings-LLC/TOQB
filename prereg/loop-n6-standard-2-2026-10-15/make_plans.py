"""Writes the 200 plans of the loop standard run 2 (n = 6, L = 8) from the pilot's plan, with the calibrated SPSA
settings and the fast engine. Loop seeds 1001-1200. Run from the TOQB root:
    python prereg/loop-n6-standard-2-2026-10-15/make_plans.py
"""
import hashlib
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SEEDS = list(range(1001, 1201))


def main():
    base = json.load(open(os.path.join(HERE, "..", "..", "plan_loop_pilot_n6_s11.json"), encoding="utf-8"))
    lines = []
    for s in SEEDS:
        plan = json.loads(json.dumps(base))
        plan["name"] = f"TOQB loop standard run 2 n6 L8 (seed {s})"
        plan["note"] = ("Standard run 2, scored against prereg/2026-10-15-loop-n6-standard-2.md. The pilot's plan with "
                        "the calibrated SPSA settings (calibration/), 200 iterations, an evaluation every 20, the fast "
                        "engine, and loop_seed.")
        plan["engine"] = "fast"
        plan["optimizer"].update(iterations=200, batch=16, a=10.0, c=0.4, A=2, loop_seed=s)
        plan["evaluation"]["every"] = 20
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
