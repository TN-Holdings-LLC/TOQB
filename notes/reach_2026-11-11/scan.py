"""Reach scan: tree width and cost of the diagonal light-cone network for deeper steps / bigger observables
(Eagle graph, IBM 2023 circuit). Search only; no values computed. usage: python scan.py NAME:OBS:T:EX ... --max-time S"""
import json, math, sys, time
sys.path.insert(0, "/tmp/claude-0/work/toqb/gpu")
import cotengra as ctg
import utility_tn_diag as WD, utility_tn as T, utility_exact as UE
edges = UE.eagle_edges()
OB = {"z62": {62: "Z"}, "z106": {106: "Z"}, "w10": UE.W10, "w17": UE.W17, "w17b": T.W17B}
mt = float(sys.argv[sys.argv.index("--max-time") + 1])
for spec in [a for a in sys.argv[1:] if ":" in a]:
    name, t, ex = spec.split(":"); t = int(t); ex = ex == "x"
    inputs, output, size, slots, nq = WD.network_diag(OB[name], t, ex, edges)
    t0 = time.time()
    opt = ctg.HyperOptimizer(methods=["kahypar", "greedy"], max_time=mt, max_repeats=10**6, minimize="flops",
                             parallel=2, progbar=False)
    tree = opt.search(inputs, output, size)
    rec = dict(obs=name, t=t, extra_rx=ex, cone=nq, tensors=len(inputs), width=round(tree.contraction_width(), 1),
               log10_cost=round(math.log10(tree.contraction_cost()), 2), search_s=round(time.time() - t0))
    print(json.dumps(rec), flush=True)
