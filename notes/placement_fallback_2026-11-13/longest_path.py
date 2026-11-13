"""The longest simple path on a device record's usable graph (failed qubits, ends of failed couplers and failed couplers
removed: psf_os.chain.health with suspect=True, the user entrance's judgement), by CP-SAT (exact, with a proven bound):
does a chain of n sites exist at all? (workplace, 2026-11-13; reads the coupling graph and failed marks only).
usage: python longest_path.py DEV_DIR [--seconds 120]"""
import collections
import sys

from ortools.sat.python import cp_model

sys.path.insert(0, "/home/claude/w119/psf-os")
from psf_os import chain as CH, device as Dv  # noqa: E402


def longest(dev, seconds=120, suspect=True):
    q_ok, e_ok = CH.health(dev, suspect)
    adj = collections.defaultdict(set)
    for a, b in dev.couplers:
        if e_ok(a, b):
            adj[a].add(b)
            adj[b].add(a)
    nodes = sorted(adj)
    idx = {q: k + 1 for k, q in enumerate(nodes)}          # 0 is the dummy node (start and end of the path)
    m = cp_model.CpModel()
    arcs, use = [], {}
    for q in nodes:
        i = idx[q]
        skip = m.NewBoolVar(f"skip{q}")
        arcs.append((i, i, skip))
        use[q] = skip.Not()
        s, t = m.NewBoolVar(f"s{q}"), m.NewBoolVar(f"t{q}")
        arcs += [(0, i, s), (i, 0, t)]
        for x in adj[q]:
            arcs.append((i, idx[x], m.NewBoolVar(f"a{q}_{x}")))
    m.AddCircuit(arcs)
    m.Maximize(sum(use.values()))
    sol = cp_model.CpSolver()
    sol.parameters.max_time_in_seconds = seconds
    sol.parameters.num_workers = 2
    st = sol.Solve(m)
    return dict(status=sol.StatusName(st), best=int(sol.ObjectiveValue()), bound=int(sol.BestObjectiveBound()),
                usable=len(nodes))


if __name__ == "__main__":
    dev = Dv.Device.load(sys.argv[1])
    sec = float(sys.argv[sys.argv.index("--seconds") + 1]) if "--seconds" in sys.argv else 120
    print(dev.name, longest(dev, sec))
