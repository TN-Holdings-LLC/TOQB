"""C: the self-check rule, applied after the fact (not tuned): 'at each place, use line unless its t = 1 mirror mean
is below old's t = 1 mirror mean'. Count, per device, place and t, which layout the rule picks and whether the pick
had the higher measured retention (resolved = |z| >= 2 from a_boot_<dev>.json), and the same for the mirror itself."""
import json, sys
R = sys.argv[1]
for dev, sub in (("kingston", "os3d-heisE-kingston-2026-11-08/kingston"), ("marrakesh", "os3d-heisE-2026-11-08/marrakesh")):
    s = json.load(open(f"{R}/{sub}/scores.json"))["arms"]
    b = json.load(open(f"a_boot_{dev}.json"))
    places = sorted({a["candidate"] for a in s.values() if "candidate" in a})
    tally = dict(right=0, wrong=0, unresolved=0)
    for c in places:
        pick = "line" if s[f"h3l{c}_t1"]["mirror_mean"] >= s[f"h3d{c}_t1"]["mirror_mean"] else "old"
        line = []
        for t in range(1, 5):
            r = b[f"c{c}_t{t}_line-old"]
            if abs(r["z"]) < 2:
                tally["unresolved"] += 1; mark = "~"
            elif (r["diff"] > 0) == (pick == "line"):
                tally["right"] += 1; mark = "+"
            else:
                tally["wrong"] += 1; mark = "-"
            line.append(f"t{t} {r['diff']:+.3f} ({r['z']:+.1f}s) {mark}")
        print(f"{dev} place {c}: t1 mirror old {s[f'h3d{c}_t1']['mirror_mean']:.3f} line {s[f'h3l{c}_t1']['mirror_mean']:.3f} -> pick {pick} | " + "  ".join(line))
    print(f"{dev}: picks right {tally['right']}, wrong {tally['wrong']}, unresolved {tally['unresolved']}")
