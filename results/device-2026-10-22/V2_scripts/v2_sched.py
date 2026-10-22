"""Workplace V2b: each schedule alone (N2 and item 31), Python _ring_template_one against Rust schedule=..."""
import sys, importlib.util, numpy as np
exec(open(sys.argv[3]).read().split("rows = []")[0].replace("AI_FILE, OUT = sys.argv[1], sys.argv[2]", "AI_FILE, OUT = sys.argv[1], sys.argv[2]"))
tot = same = strict = oos = 0
for di, dname in enumerate(DEVICES):
    base = getattr(fp, dname)().target
    for k in range(6):
        rng = np.random.default_rng(SEED0 + 50 + 100 * di + k)
        tgt, info = inject(base, rng, k)
        for L in (2, 8, 16):
            qc = model(L, SEED0 + 77 + 1000 * di + 10 * k + L)
            for sch, fn in (("n2", ai.ring_rounds), ("q4", ai.ring_rounds_q4)):
                tot += 1
                try:
                    rs = RP.ring_template(qc, tgt, ai, schedule=sch)
                except RP.OutOfScope:
                    oos += 1
                    continue
                py = ai._ring_template_one(qc, tgt, rounds_fn=fn)
                d = RP.compare(py, rs, tol=0.0)
                same += int(d == [])
                strict += int(bool(strict_fixed(py, rs)))
                if d:
                    print(dname, k, L, sch, d[:3])
print("SCHED", dict(total=tot, identical_tol0=same, strict_bit_diffs=strict, out_of_scope=oos))
