"""S1 (post hoc, synthetic noise only; nothing judged): which errors does the mirror see, and why does the mirror model
over-correct at theta_x 0.8? A 10-qubit piece of the P6 patch, the P6 step (RX, RZ, then RZZ = CX RZ CX with
CX = H CZ H, two CZ per edge, P6's own layer order), the correction pipeline of gpu/corr_score.py (floor at
t 1,3,5,6,7,9,10; mirror U U^dagger at t 3, 5; forward t 1..9; a = median_q mean_{t=3,5} ln(mirror/F(2t))/(2t);
z_corr = z / (F exp(a t))), on an exact density-matrix simulator, under noise of strengths chosen here (no IBM
calibration numbers, no fake-device noise models):
  dep      two-qubit depolarizing p2 on every CZ, one-qubit p1 on every H and RX, readout flip e (all qubits)
  over     dep + RX over-rotation theta_x (1 + d) (the inverse in the mirror is the exact inverse: cancels)
  zzangle  dep + RZZ angle error theta_zz (1 + d) (as written: cancels in the mirror)
  static   dep + always-on ZZ: rzz(z) on every patch edge after every CZ slot (same sign in both halves)
  detune   dep + always-on Z: rz(w) on every qubit after every CZ slot
  partner  dep + one bad partner (label 23): amplitude damping g after every CZ slot and readout flip e_b on it
  partner_dead  dep + partner fully damped (g = 1): it sits in |0>, so its RZZ acts on its neighbours as a fixed RZ
Also 'none' (no noise; the pipeline must return the answer) and 'global' (global depolarizing, the case where the
mirror model is exact). Run: python notes/s1_2026-11-05/s1_sim.py OUT.json [s1|s2]; 's2' runs the S2 candidates
(+dd: an XX echo on the qubits idle in each CZ layer; +tw: Pauli twirling of every CZ with its slot, as its
infinite-frame limit) on the same noise.
Strengths: P2 was first 0.01 and set to 0.004 after one look, so that the depolarizing case loses about 1-1.5 % per
step, the size of the gate decay our own mirrors measured on 11-04 (no calibration numbers); the others were set once,
before any run, and not changed."""
import json, sys, time
import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Kraus, SparsePauliOp
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, depolarizing_error

LAYERS = [
    [(6, 7), (10, 11), (16, 23), (24, 25), (17, 27), (28, 29), (18, 31), (36, 41), (42, 43), (37, 45), (46, 47), (38, 49)],
    [(3, 4), (5, 6), (7, 8), (9, 10), (21, 22), (23, 24), (25, 26), (27, 28), (29, 30), (43, 44), (45, 46), (47, 48)],
    [(3, 16), (7, 17), (11, 18), (22, 23), (26, 27), (30, 31), (21, 36), (25, 37), (29, 38), (41, 42), (44, 45),
     (48, 49), (4, 5), (8, 9)],
]
S = [16, 17, 21, 22, 23, 24, 25, 26, 27, 28]
IDX = {q: i for i, q in enumerate(S)}
SL = [[(IDX[a], IDX[b]) for a, b in L if a in IDX and b in IDX] for L in LAYERS]
EDGES = [e for L in SL for e in L]
N = len(S)
TZ, TZZ = 0.1, 1.0
TXS = (0.53, 0.3, 0.8)
FLOOR_TS = (1, 3, 5, 6, 7, 9, 10)
P2, P1, E_RO = 0.004, 0.0005, 0.02
STRENGTH = dict(over=0.05, zzangle=0.05, static=0.02, detune=0.02, partner=0.3)
E_BAD = 0.4
BAD = IDX[23]


def base(m):
    return m.split("+")[0]


def opts(m):
    return set(m.split("+")[1:])


def pchan(p, k):
    """Pauli channel on k qubits: Z...Z with probability p (the twirled form of a Z...Z rotation by 2 asin(sqrt p))."""
    z = np.diag([1, -1])
    zz = z if k == 1 else np.kron(z, z)
    return Kraus([np.sqrt(1 - p) * np.eye(2 ** k), np.sqrt(p) * zz])


def step_ops(tx, m, floor=False):
    """One P6 step as a list of ops: ('rx'|'rz'|'h', q, angle) / ('cz', a, b) / ('slot', active qubits) after each
    CZ layer."""
    m = base(m)
    ops = []
    for q in range(N):
        if not floor:
            ops.append(("rx", q, tx * (1 + (STRENGTH["over"] if m == "over" else 0))))
        ops.append(("rz", q, TZ))
    tzz = TZZ * (1 + (STRENGTH["zzangle"] if m == "zzangle" else 0))
    for L in SL:
        for half in (0, 1):
            for a, b in L:
                if not floor:
                    ops.append(("h", b, 0))
                ops.append(("cz", a, b))
                if not floor:
                    ops.append(("h", b, 0))
            ops.append(("slot", frozenset(q for e in L for q in e)))
            if half == 0:
                for a, b in L:
                    ops.append(("rz", b, tzz))
    return ops


def inverse(ops):
    out = []
    for op in reversed(ops):
        if op[0] in ("rx", "rz"):
            out.append((op[0], op[1], -op[2]))
        else:
            out.append(op)
    return out


def emit(qc, ops, m):
    """Ops into the circuit; the always-on errors are added after every CZ slot, the same in U and U^dagger.
    Options: +tw: the always-on errors touching a qubit that is in the slot's CZ layer are replaced by their Pauli-
    twirled channel (the infinite-frame limit of twirling every CZ with its slot); +dd: every qubit not in the slot's
    layer gets an X after each slot (two per layer: an XX echo over the layer's two CZ slots)."""
    b0, op_ = base(m), opts(m)
    for op in ops:
        if op[0] == "rx":
            qc.rx(op[2], op[1])
        elif op[0] == "rz":
            qc.rz(op[2], op[1])
        elif op[0] == "h":
            qc.h(op[1])
        elif op[0] == "cz":
            qc.cz(op[1], op[2])
        elif op[0] == "slot":
            act = op[1]
            if b0 == "static":
                for a, b in EDGES:
                    if "tw" in op_ and (a in act or b in act):
                        qc.append(pchan(np.sin(STRENGTH["static"] / 2) ** 2, 2), [a, b])
                    else:
                        qc.rzz(STRENGTH["static"], a, b)
            if b0 == "detune":
                for q in range(N):
                    if "tw" in op_ and q in act:
                        qc.append(pchan(np.sin(STRENGTH["detune"] / 2) ** 2, 1), [q])
                    else:
                        qc.rz(STRENGTH["detune"], q)
            if b0 in ("partner", "partner_dead"):
                g = 1.0 if b0 == "partner_dead" else STRENGTH["partner"]
                k0 = np.array([[1, 0], [0, np.sqrt(1 - g)]])
                k1 = np.array([[0, np.sqrt(g)], [0, 0]])
                qc.append(Kraus([k0, k1]), [BAD])
            if "dd" in op_:
                for q in range(N):
                    if q not in act:
                        qc.x(q)


def save_z(qc, tag):
    for q in range(N):
        qc.save_expectation_value(SparsePauliOp("I" * (N - 1 - q) + "Z" + "I" * q), list(range(N)), label=f"{tag}_{q}")


def noise(m):
    m = base(m)
    if m in ("none", "global"):
        return None
    nm = NoiseModel()
    nm.add_all_qubit_quantum_error(depolarizing_error(P2, 2), ["cz"])
    nm.add_all_qubit_quantum_error(depolarizing_error(P1, 1), ["h", "rx", "x"])
    return nm


def readout(m):
    m = base(m)
    e = np.full(N, 0.0 if m in ("none", "global") else E_RO)
    if m in ("partner", "partner_dead"):
        e[BAD] = E_BAD
    return 1 - 2 * e


def run(qc, m):
    sim = AerSimulator(method="density_matrix" if base(m) != "none" else "statevector", noise_model=noise(m))
    return sim.run(qc).result().data()


def forward(tx, m, tmax=9, floor=False, ts=None):
    qc = QuantumCircuit(N)
    ts = ts or list(range(1, tmax + 1))
    for t in range(1, max(ts) + 1):
        emit(qc, step_ops(tx, m, floor), m)
        if t in ts:
            save_z(qc, f"t{t}")
    d = run(qc, m)
    r = readout(m)
    return {t: np.array([d[f"t{t}_{q}"] for q in range(N)]) * r for t in ts}


def mirror(tx, m, t):
    qc = QuantumCircuit(N)
    ops = [o for _ in range(t) for o in step_ops(tx, m)]
    emit(qc, ops, m)
    qc.barrier()
    emit(qc, inverse(ops), m)
    save_z(qc, "m")
    d = run(qc, m)
    return np.array([d[f"m_{q}"] for q in range(N)]) * readout(m)


GLOBAL_LAMBDA = 0.97  # per step, for 'global' only (applied analytically: forward x L^t, mirror x L^(2t), floor 1)


def pipeline(tx, m, ans):
    if base(m) == "global":
        f = {t: np.ones(N) for t in FLOOR_TS}
        z = {t: ans[t] * GLOBAL_LAMBDA ** t for t in ans}
        mir = {t: np.ones(N) * GLOBAL_LAMBDA ** (2 * t) for t in (3, 5)}
    else:
        f = forward(tx, m, floor=True, ts=list(FLOOR_TS))
        z = forward(tx, m)
        mir = {t: mirror(tx, m, t) for t in (3, 5)}
    ts = sorted(f)
    F = lambda t: np.array([np.interp(t, ts, [f[s][q] for s in ts]) for q in range(N)])
    z0 = np.mean([f[1], f[5], f[9]], axis=0)
    med = np.median(z0)
    mad = np.median(np.abs(z0 - med))
    keep = z0 >= med - max(5 * 1.4826 * mad, 0.05)
    aq = np.mean([0.5 * np.log(np.clip(mir[t] / np.maximum(F(2 * t), 0.05), 1e-3, 1)) / t for t in (3, 5)], axis=0)
    a = float(np.median(aq[keep]))
    out = dict(keep=keep.tolist(), a=a, mirror_per_step=float(np.exp(a)), floor={t: f[t].tolist() for t in f}, t={})
    for t in range(1, 10):
        y = z[t] / F(t)
        zc = y / np.exp(a * t)
        k = keep
        out["t"][t] = dict(answer_mean=float(ans[t][k].mean()), raw_mean=float(z[t][k].mean()), y_mean=float(y[k].mean()),
                           corr_mean=float(zc[k].mean()), z=z[t].tolist(), y=y.tolist(), zc=zc.tolist(),
                           mse_raw=float(np.mean((z[t][k] - ans[t][k]) ** 2)), mse_corr=float(np.mean((zc[k] - ans[t][k]) ** 2)))
    # forward per-step decay from y / answer (as s1_analyse: fit of log ratio over t 1..9, intercept free)
    tt = np.arange(1, 10)
    ratio = np.array([out["t"][t]["y_mean"] / out["t"][t]["answer_mean"] for t in tt])
    good = ratio > 0
    sl, ic = np.polyfit(tt[good], np.log(ratio[good]), 1)
    out["fwd_per_step"] = float(np.exp(sl))
    out["fwd_intercept"] = float(np.exp(ic))
    out["mse_raw_t1_9"] = float(np.mean([out["t"][t]["mse_raw"] for t in tt]))
    out["mse_corr_t1_9"] = float(np.mean([out["t"][t]["mse_corr"] for t in tt]))
    out["corr_diff"] = [out["t"][t]["corr_mean"] - out["t"][t]["answer_mean"] for t in tt]
    out["raw_diff"] = [out["t"][t]["raw_mean"] - out["t"][t]["answer_mean"] for t in tt]
    # neighbours of the bad partner against the rest (kept qubits only)
    nb = [IDX[q] for q in (16, 22, 24)]
    rest = [q for q in range(N) if q not in nb and q != BAD]
    res = lambda qs: float(np.mean([out["t"][t]["zc"][q] - ans[t][q] for t in range(5, 10) for q in qs]))
    out["corr_resid_t5_9"] = dict(nb23=res(nb), rest=res(rest))
    return out


MODELS = ["none", "global", "dep", "over", "zzangle", "static", "detune", "partner", "partner_dead"]
S2 = ["dep+dd", "dep+tw", "static+tw", "static+dd", "static+dd+tw", "detune+tw", "detune+dd", "detune+dd+tw",
      "over+dd+tw", "partner_dead+dd+tw"]


def main(path, which="s1"):
    t0 = time.time()
    models = MODELS if which == "s1" else S2
    R = dict(settings=dict(S=S, edges=[(S[a], S[b]) for a, b in EDGES], p2=P2, p1=P1, e_ro=E_RO, strength=STRENGTH,
                           e_bad=E_BAD, global_lambda=GLOBAL_LAMBDA, tz=TZ, tzz=TZZ), runs={})
    for tx in TXS:
        ans = forward(tx, "none")
        R["runs"].setdefault(str(tx), {})["answer"] = {t: ans[t].tolist() for t in ans}
        for m in models:
            o = pipeline(tx, m, ans)
            R["runs"][str(tx)][m] = o
            print(f"tx {tx} {m:13s} fwd/step {o['fwd_per_step']:.4f} mirror/step {o['mirror_per_step']:.4f} "
                  f"MSE raw {o['mse_raw_t1_9']:.5f} corr {o['mse_corr_t1_9']:.5f} ratio {o['mse_corr_t1_9'] / max(o['mse_raw_t1_9'], 1e-12):.3f} "
                  f"corr diff t9 {o['corr_diff'][-1]:+.3f} nb23 {o['corr_resid_t5_9']['nb23']:+.3f} rest {o['corr_resid_t5_9']['rest']:+.3f} "
                  f"({time.time() - t0:.0f} s)", flush=True)
    json.dump(R, open(path, "w"))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "s1")
