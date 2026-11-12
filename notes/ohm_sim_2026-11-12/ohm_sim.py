"""Ohm on the FakeFez simulator: a 1D chain against the honeycomb lattice as it is, 24 qubits each (home VS Claude,
2026-11-12, for home Claude's instruction of 13:50 CET). A desk estimate: FakeFez's noise model as it comes (nothing
adjusted to tonight's fez / kingston), not declared, no device job.

Placement (from the coupling map and fixed rules only; no error number is looked at):
  chain: start at qubit 0 and walk along the row (q -> q + 1); at the row's end take the bridge qubit down to the next
    row and walk back (q -> q - 1); stop at 24 qubits. Wall in the middle: chain positions 0-11 left, 12-23 right.
  honeycomb: rows 0 and 1 (qubits 0.. and 20..), columns 0..c with c grown until the two rows' qubits in that range and
    the bridges between them make 24 (c = 10: 22 row qubits + bridges 16, 17). Labels sorted by (column, row 0 /
    bridge / row 1); the first 12 are the left half (the wall at the middle of the columns, 12 / 12).
One cycle: chain = fSim on the even bonds, then the odd bonds (as gpu/ohm_answers.py); honeycomb = every bond of the
patch once, in colour order, the colours by a greedy edge colouring in the fixed order of the sorted bonds (bonds of
one colour share no qubit). Gate fSim(pi/4, pi/2) (tonight's A1). Strings as gpu/ohm_answers.strings (m 0.5, K 6 and
their complements, seed 20261112); bit k of a string = label k. Cycles 3 and 6.
Each circuit is compiled for FakeFez (transpile, CZ basis, initial layout fixed to the chosen qubits, no routing,
optimization_level 1); its CZ count and CZ depth are recorded.
  exact: the compiled circuit itself (measurements dropped, restricted to its 24 qubits), noiseless statevector;
  noisy: AerSimulator.from_backend(FakeFez()) on the compiled circuit, as noise TRAJECTORIES instead of 1000 shots
    (owner's choice, 2026-11-12: 1000 noisy shots of 24 qubits take about an hour per circuit): each trajectory gives
    the exact <Z_k> of its final state (save_expectation_value, pershot), with FakeFez's readout asymmetry applied in
    closed form, <Z>_read = (1 - a - b) <Z> + (b - a), a = p(1|0), b = p(0|1); the trajectory is then measured once
    (readout error from the noise model), so TRAJ trajectories also give TRAJ shots for the kept share (reference);
  floor: measure only, the same 24 qubits, noisy, 1000 shots: the share of shots with at least one 1.
Scores as gpu/ohm_score.py (M from the right half; READS: M MSE <= half the mean square; AGREES 0.2; per-qubit READS;
W, W of the fully mixed state, p = (W - W_exact) / (W_mixed - W_exact); exponent log2(W(6) / W(3))) and the share of
shots that keep the number of |1> (as notes/ohm_postsel_2026-11-12; from the TRAJ shots, reference only).
Every task's result is appended to OUT/tasks.jsonl as soon as it is done; `score` reads that file.
usage: python ohm_sim.py run OUT [--traj 40] [--workers N]      python ohm_sim.py score OUT
       python ohm_sim.py test OUT                                 (one trajectory of one circuit, and the exact)"""
import json
import os
import sys
import time
import zlib
from concurrent.futures import ProcessPoolExecutor, as_completed

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "gpu"))
import ohm_answers as OA  # noqa: E402

N, K, M_POL, SEED, CYCLES, FLOOR_SHOTS = 24, 6, 0.5, 20261112, (3, 6), 1000
THETA, PHI = np.pi / 4, np.pi / 2
AGREE = 0.2
SHAPES = ("chain", "honeycomb")


def edges_of(backend):
    return {tuple(sorted(e)) for e in backend.coupling_map.get_edges()}


def chain_layout(E):
    nb = {}
    for a, b in E:
        nb.setdefault(a, set()).add(b)
        nb.setdefault(b, set()).add(a)
    path, d = [0], +1
    while len(path) < N:
        q = path[-1]
        if q + d in nb[q] and q + d not in path:
            path.append(q + d)
            continue
        free = sorted(x for x in nb[q] if x not in path)
        if not free:
            raise RuntimeError("chain rule stuck")
        b = free[0]                       # the bridge qubit
        path.append(b)
        path.append(sorted(x for x in nb[b] if x not in path)[0])
        d = -d
    return path[:N]


def honeycomb_layout(E):
    rows = (0, 20)                      # row 0 starts at qubit 0, row 1 at qubit 20 (16 qubits each on Heron r2)
    bridges = {}
    for a, b in E:                      # a bridge qubit (16-19) joins column c of row 0 and column c of row 1
        for x, y in ((a, b), (b, a)):
            if 16 <= x < 20:
                bridges.setdefault(x, set()).add(y)
    for c in range(16):
        qs = [(col, 0, rows[0] + col) for col in range(c + 1)] + [(col, 2, rows[1] + col) for col in range(c + 1)]
        for bq, ends in bridges.items():
            col = min(ends)
            if col <= c and max(ends) == rows[1] + col:
                qs.append((col, 1, bq))
        if len(qs) >= N:
            break
    if len(qs) != N:
        raise RuntimeError(f"honeycomb rule gives {len(qs)} qubits")
    return [q for _, _, q in sorted(qs)]


def colour(bonds):
    col = {}
    for e in bonds:
        used = {col[f] for f in col if set(f) & set(e)}
        col[e] = min(c for c in range(len(bonds)) if c not in used)
    return [[e for e in bonds if col[e] == c] for c in range(max(col.values()) + 1)]


def layers_of(shape, phys, E):
    idx = {q: k for k, q in enumerate(phys)}
    if shape == "chain":
        return [[(k, k + 1) for k in range(par, N - 1, 2)] for par in (0, 1)]
    bonds = sorted(tuple(sorted((idx[a], idx[b]))) for a, b in E if a in idx and b in idx)
    return colour(bonds)


def logical(layers, cycles, bits):
    """Logical circuit on N qubits (qubit k = label k), measured into clbit k."""
    from qiskit import QuantumCircuit
    from qiskit.circuit.library import UnitaryGate
    G = UnitaryGate(OA.fsim(THETA, PHI), label="fsim")
    qc = QuantumCircuit(N, N)
    for k, b in enumerate(bits):
        if b:
            qc.x(k)
    for _ in range(cycles):
        for lay in layers:
            for a, b in lay:
                qc.append(G, [a, b])
    qc.measure(range(N), range(N))
    return qc


def compile_(qc, phys, backend):
    from qiskit import transpile
    return transpile(qc, backend=backend, initial_layout=phys, routing_method="none", optimization_level=1,
                     seed_transpiler=1)


def restrict(cqc, phys):
    """The compiled circuit on its N qubits only (label order), without measurements."""
    from qiskit import QuantumCircuit
    pos = {cqc.qubits[q]: k for k, q in enumerate(phys)}
    out = QuantumCircuit(N)
    for ins in cqc.data:
        if ins.operation.name in ("measure", "barrier", "delay"):
            continue
        out.append(ins.operation, [pos[q] for q in ins.qubits])
    return out


def readout(backend, phys):
    """Per label: (a, b) = (p(read 1 | prep 0), p(read 0 | prep 1)) from FakeFez's properties."""
    p = backend.properties()
    out = []
    for q in phys:
        qp = p.qubit_property(q)
        a, b = qp.get("prob_meas1_prep0", (None,))[0], qp.get("prob_meas0_prep1", (None,))[0]
        if a is None or b is None:
            a = b = p.readout_error(q)
        out.append((a, b))
    return np.array(out)


# ---- worker side
_W = {}


def _init():
    from qiskit_ibm_runtime.fake_provider import FakeFez
    from qiskit_aer import AerSimulator
    be = FakeFez()
    E = edges_of(be)
    lay = {"chain": chain_layout(E), "honeycomb": honeycomb_layout(E)}
    _W.update(be=be, E=E, lay=lay, strs=dict(OA.strings(N, K, M_POL, SEED)),
              noisy=AerSimulator.from_backend(be, max_parallel_threads=1, max_parallel_shots=1),
              ideal=AerSimulator(method="statevector", max_parallel_threads=1),
              ro={s: readout(be, lay[s]) for s in SHAPES})


def _circuit(shape, t, name):
    phys = _W["lay"][shape]
    layers = layers_of(shape, phys, _W["E"])
    cqc = compile_(logical(layers, t, _W["strs"][name]), phys, _W["be"])
    return cqc, phys, len(layers)


def task(job):
    from qiskit import QuantumCircuit, ClassicalRegister
    from qiskit.quantum_info import Pauli
    if not _W:
        _init()
    t0 = time.time()
    kind = job["kind"]
    if kind == "floor":
        phys = _W["lay"][job["shape"]]
        fq = QuantumCircuit(N, N)
        fq.measure(range(N), range(N))
        cnt = _W["noisy"].run(compile_(fq, phys, _W["be"]), shots=FLOOR_SHOTS, seed_simulator=7).result().get_counts()
        return dict(job, any_one=sum(c for k, c in cnt.items() if "1" in k) / FLOOR_SHOTS, shots=FLOOR_SHOTS,
                    seconds=round(time.time() - t0, 1))
    shape, t, name = job["shape"], job["t"], job["name"]
    cqc, phys, nl = _circuit(shape, t, name)
    if kind == "exact":
        c = restrict(cqc, phys)
        for k in range(N):
            lab = ["I"] * N
            lab[N - 1 - k] = "Z"
            c.save_expectation_value(Pauli("".join(lab)), list(range(N)), label=f"z{k}")
        d = _W["ideal"].run(c, shots=1).result().data()
        z = [float(np.real(d[f"z{k}"])) for k in range(N)]
        return dict(job, z=z, cz=int(cqc.count_ops().get("cz", 0)),
                    cz_layers=int(cqc.depth(filter_function=lambda i: i.operation.name == "cz")),
                    fsim_layers_per_cycle=nl, seconds=round(time.time() - t0, 1))
    # one noise trajectory: exact <Z_k> of its final state, then one measured shot
    c = cqc.remove_final_measurements(inplace=False)
    nq = c.num_qubits
    for k, q in enumerate(phys):
        lab = ["I"] * nq
        lab[nq - 1 - q] = "Z"
        c.save_expectation_value(Pauli("".join(lab)), list(range(nq)), label=f"z{k}", pershot=True)
    cr = ClassicalRegister(N, "m")
    c.add_register(cr)
    for k, q in enumerate(phys):
        c.measure(q, cr[k])
    seed = zlib.crc32(f"{shape}_{t}_{name}_{job['j']}".encode())
    r = _W["noisy"].run(c, shots=1, seed_simulator=seed).result()
    d = r.data()
    z = np.array([float(np.real(d[f"z{k}"][0])) for k in range(N)])
    ro = _W["ro"][shape]
    z = z * (1 - ro[:, 0] - ro[:, 1]) + (ro[:, 1] - ro[:, 0])
    (key,) = r.get_counts().keys()
    return dict(job, z=z.tolist(), shot=key.replace(" ", ""), seconds=round(time.time() - t0, 1))


def cpu_quota():
    try:
        q, p = open("/sys/fs/cgroup/cpu.max").read().split()
        if q != "max":
            return max(1, int(int(q) / int(p)))
    except Exception:
        pass
    return len(os.sched_getaffinity(0))


def run(out, traj, workers):
    os.makedirs(out, exist_ok=True)
    names = [n for n, _ in OA.strings(N, K, M_POL, SEED)]
    fn = os.path.join(out, "tasks.jsonl")
    done = set()
    if os.path.exists(fn):
        for line in open(fn):
            r = json.loads(line)
            done.add((r["kind"], r.get("shape"), r.get("t"), r.get("name"), r.get("j")))
    jobs = [dict(kind="floor", shape=s) for s in SHAPES]
    jobs += [dict(kind="exact", shape=s, t=t, name=n) for s in SHAPES for t in CYCLES for n in names]
    jobs += [dict(kind="traj", shape=s, t=t, name=n, j=j) for j in range(traj) for t in sorted(CYCLES, reverse=True)
             for s in SHAPES for n in names]
    jobs = [j for j in jobs if (j["kind"], j.get("shape"), j.get("t"), j.get("name"), j.get("j")) not in done]
    t0 = time.time()
    print(f"start {time.strftime('%F %T')}  tasks {len(jobs)} (already done {len(done)})  traj {traj}  workers {workers}",
          flush=True)
    n = 0
    with ProcessPoolExecutor(workers, initializer=_init) as ex, open(fn, "a") as f:
        futs = [ex.submit(task, j) for j in jobs]
        for fu in as_completed(futs):
            r = fu.result()
            f.write(json.dumps(r) + "\n")
            f.flush()
            n += 1
            if n % 50 == 0 or n == len(jobs) or r["kind"] != "traj":
                print(f"{n}/{len(jobs)} at {time.time() - t0:.0f} s (last: {r['kind']} {r.get('shape')} t{r.get('t')} "
                      f"{r['seconds']} s)", flush=True)
    print(f"wall {time.time() - t0:.0f} s\n== RUN FINISHED", flush=True)


def score(out):
    names = [n for n, _ in OA.strings(N, K, M_POL, SEED)]
    strs = dict(OA.strings(N, K, M_POL, SEED))
    rows = [json.loads(line) for line in open(os.path.join(out, "tasks.jsonl"))]
    from qiskit_ibm_runtime.fake_provider import FakeFez
    E = edges_of(FakeFez())
    lay = {"chain": chain_layout(E), "honeycomb": honeycomb_layout(E)}
    right = list(range(N // 2, N))
    ks = sorted({n[1:] for n in names})
    res = dict(note="desk estimate; FakeFez noise model as it comes (nothing adjusted); 24 qubits; noise by trajectories",
               layouts=lay, shapes={}, circuits={})
    for shape in SHAPES:
        fl = [r for r in rows if r["kind"] == "floor" and r["shape"] == shape]
        phys = lay[shape]
        sh = res["shapes"][shape] = dict(qubits=phys, floor_share_any_one=fl[0]["any_one"] if fl else None,
                                         bonds_per_cycle=sum(len(x) for x in layers_of(shape, phys, E)))
        m0s = {n: sum(strs[n][N // 2:]) for n in names}
        W_mixed = float(np.mean([(m0s["c" + k] - m0s["s" + k]) / 2 for k in ks]))
        sh["W_mixed"] = W_mixed
        for t in CYCLES:
            c = {}
            for n in names:
                ex = [r for r in rows if r["kind"] == "exact" and r["shape"] == shape and r["t"] == t and r["name"] == n]
                tr = [r for r in rows if r["kind"] == "traj" and r["shape"] == shape and r["t"] == t and r["name"] == n]
                if not ex or not tr:
                    continue
                ze, Zt = np.array(ex[0]["z"]), np.array([r["z"] for r in tr])
                zn = Zt.mean(0)
                bits, m0 = strs[n], sum(strs[n][k] for k in right)
                Mf = lambda z: float(((1 - z[right]) / 2).sum() - m0)
                Mt = np.array([Mf(z) for z in Zt])
                n0 = sum(bits)
                kept = float(np.mean([r["shot"].count("1") == n0 for r in tr]))
                mse_z, msq_z = float(np.mean((zn - ze) ** 2)), float(np.mean(ze ** 2))
                c[n] = dict(cz=ex[0]["cz"], cz_layers=ex[0]["cz_layers"], fsim_layers_per_cycle=ex[0]["fsim_layers_per_cycle"],
                            M=Mf(zn), M_exact=Mf(ze), M_se=float(Mt.std(ddof=1) / np.sqrt(len(Mt))) if len(Mt) > 1 else None,
                            z_reads=bool(mse_z <= msq_z / 2), z_mse=mse_z, traj=len(tr), kept_share=kept,
                            total_z_exact=float(ze.sum()), total_z_initial=float(N - 2 * n0))
                res["circuits"][f"{shape}_t{t}_{n}"] = c[n]
            if len(c) < len(names):
                sh[f"t{t}"] = dict(incomplete=f"{len(c)}/{len(names)} circuits")
                continue
            d = np.array([c[n]["M"] - c[n]["M_exact"] for n in names])
            ex_ = np.array([c[n]["M_exact"] for n in names])
            mse, msq = float(np.mean(d ** 2)), float(np.mean(ex_ ** 2))
            W = float(np.mean([(c["s" + k]["M"] - c["c" + k]["M"]) / 2 for k in ks]))
            We = float(np.mean([(c["s" + k]["M_exact"] - c["c" + k]["M_exact"]) / 2 for k in ks]))
            sh[f"t{t}"] = dict(mse=mse, mean_square=msq, mse_over_msq=mse / msq, reads=bool(mse <= msq / 2),
                               agrees=int(np.sum(np.abs(d) <= AGREE)), circuits=len(names),
                               z_reads=int(sum(c[n]["z_reads"] for n in names)), W=W, W_exact=We,
                               p=(W - We) / (W_mixed - We), kept_mean=float(np.mean([c[n]["kept_share"] for n in names])),
                               traj_min=int(min(c[n]["traj"] for n in names)),
                               M_se_mean=float(np.mean([c[n]["M_se"] for n in names])),
                               cz_mean=float(np.mean([c[n]["cz"] for n in names])),
                               cz_layers_max=int(max(c[n]["cz_layers"] for n in names)),
                               fsim_layers_per_cycle=c[names[0]]["fsim_layers_per_cycle"],
                               worst_total_z=float(max(abs(c[n]["total_z_exact"] - c[n]["total_z_initial"]) for n in names)))
        t3, t6 = (sh.get(f"t{t}") for t in CYCLES)
        if t3 and t6 and "W" in t3 and "W" in t6:
            f = np.log(CYCLES[1] / CYCLES[0])
            sh["exponent"] = dict(noisy=float(np.log(t6["W"] / t3["W"]) / f) if t3["W"] > 0 and t6["W"] > 0 else None,
                                  exact=float(np.log(t6["W_exact"] / t3["W_exact"]) / f))
        print(f"== {shape}: qubits {phys}; floor share with a 1 {sh['floor_share_any_one']}; W_mixed {W_mixed:.3f}")
        for t in CYCLES:
            r = sh[f"t{t}"]
            if "incomplete" in r:
                print(f"{shape} t{t}: incomplete {r['incomplete']}")
                continue
            print(f"{shape} t{t}: M MSE/msq {r['mse_over_msq']:.3f} ({'READS' if r['reads'] else 'DOES NOT READ'}), "
                  f"AGREES {r['agrees']}/{r['circuits']}, per-qubit READS {r['z_reads']}/{r['circuits']}, W {r['W']:.3f} "
                  f"(exact {r['W_exact']:.3f}), p {r['p']:.3f}, kept {r['kept_mean']:.3f} (from {r['traj_min']} shots), "
                  f"M SE {r['M_se_mean']:.3f}; CZ {r['cz_mean']:.0f}, CZ layers {r['cz_layers_max']}, fSim layers per "
                  f"cycle {r['fsim_layers_per_cycle']}; exact total Z vs initial worst {r['worst_total_z']:.1e}")
        if "exponent" in sh:
            e = sh["exponent"]
            print(f"{shape}: exponent log2(W6/W3) noisy {e['noisy']}, exact {e['exact']:.3f}")
    json.dump(res, open(os.path.join(out, "ohm_sim.json"), "w"), indent=1)


def test(out):
    os.makedirs(out, exist_ok=True)
    _init()
    for shape in SHAPES:
        phys = _W["lay"][shape]
        print(shape, phys, "layers per cycle", [len(x) for x in layers_of(shape, phys, _W["E"])], flush=True)
        for kind in ("exact", "traj"):
            r = task(dict(kind=kind, shape=shape, t=3, name="s00", j=0))
            z = np.array(r["z"])
            print(f"  {kind}: total Z {z.sum():+.3f} (initial {N - 2 * sum(_W['strs']['s00'])}), "
                  f"{r.get('cz', '')} CZ, {r.get('cz_layers', '')} layers, shot {r.get('shot', '')}, {r['seconds']} s",
                  flush=True)
    print(task(dict(kind="floor", shape="chain")))


if __name__ == "__main__":
    cmd, out = sys.argv[1], sys.argv[2]
    arg = lambda k, dflt: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else dflt
    if cmd == "run":
        run(out, int(arg("--traj", "40")), int(arg("--workers", str(cpu_quota()))))
    elif cmd == "score":
        score(out)
    else:
        test(out)
