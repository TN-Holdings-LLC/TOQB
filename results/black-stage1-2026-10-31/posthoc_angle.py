"""Post hoc (not declared): block B's Z signal divided by the rest's at each depth, and arccos of that ratio, as the
angle a pure turn would need. Read only; nothing here is judged."""
import json, math, os
d = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "stage1_score.json")))
b, r = d["depth"]["block"], d["depth"]["rest"]
for D, x, y in zip(b["depths"], b["a"], r["a"]):
    q = max(-1.0, min(1.0, x / y))
    print(f"D {D:2d}: block {x:+.3f}, rest {y:+.3f}, ratio {q:+.3f}, arccos {math.acos(q):.3f} rad")
