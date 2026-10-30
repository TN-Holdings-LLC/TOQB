"""QELM prototype (2026-10-29; design: psf-zero docs/design/search-free-quantum-classifier-design-2026-10-29.md).

A search-free quantum classifier: a fixed data circuit on TOQB's ring (no trainable angles), local features <X_q>,
<Y_q>, <Z_q> of every qubit, and one ordinary least-squares solve. This module is a REHEARSAL on simulators: a
noiseless reference and a noisy stand-in (Aer density matrix with a fake backend's public noise model, exact by
backward light cones). Nothing here is a device result, and nothing is chosen from its numbers: the settings are the
design memo's proposals (owner decisions pending).

    python -m toqb.qelm check                    # circuit / basis / light-cone checks
    python -m toqb.qelm teacher OUT_DIR [--n 20 --L 19]          # task A: inputs, noiseless features, teacher labels
    python -m toqb.qelm predict OUT_DIR [--lstar fold:rule=56.5,fold:zipcyc=15.1,qiskit:2:blind:template=26.4]
    python -m toqb.qelm run OUT_DIR [--task breast|teacher] [--standin aer|toqb] [--T 64] [--L 1 --enc pi/4]
                        [--device fake:FakeMarrakesh | file:FETCH/target.pkl] [--arms fold:rule,fold:zipcyc,...]
    python -m toqb.qelm score OUT_DIR
"""
from __future__ import annotations

import json
import math
import os
import sys
import time

import numpy as np

from toqb import task_loop as TL

N, L, ENC = 20, 2, math.pi / 2
N_TRAIN, N_TEST, SPLIT_SEED = 128, 200, 0
BASES = ("X", "Y", "Z")
SHOTS = 250
SUBSAMPLE = (16, 32, 64, 125, 250)
SHOT_SEED = 20261029
REPS = 400


# ------------------------------------------------------------------------------------------------ data

def data(n=N):
    """breast_cancer: fixed split (seed 0), standardised and PCA on the training points only, scaled to [-1, 1] by the
    training range and clipped. Labels +1 (benign) / -1 (malignant)."""
    from sklearn.datasets import load_breast_cancer
    from sklearn.decomposition import PCA
    d = load_breast_cancer()
    X, y = d.data, np.where(d.target == 1, 1.0, -1.0)
    p = np.random.default_rng(SPLIT_SEED).permutation(len(y))
    tr, te = p[:N_TRAIN], p[N_TRAIN:N_TRAIN + N_TEST]
    mu, sd = X[tr].mean(0), X[tr].std(0)
    Z = (X - mu) / sd
    pca = PCA(n_components=n).fit(Z[tr])
    P = pca.transform(Z)
    lo, hi = P[tr].min(0), P[tr].max(0)
    S = np.clip(2 * (P - lo) / (hi - lo) - 1, -1, 1)
    return S[tr], y[tr], S[te], y[te]


# ------------------------------------------------------------------------------------------------ circuit

def angles(x, basis, n=N, L=L, enc=ENC):
    """The model_circuit angle list: per layer RY(enc x_q), then RY(0), RZ(enc x_q) per qubit, then the CZ ring; the
    basis rotation is the last layer's RZ (+pi/2 for Y; RZ commutes with the CZ ring) and the final RY (X: -pi/2,
    Y: +pi/2, Z: 0), so that measuring Z gives <X_q>, <Y_q> or <Z_q>."""
    a = []
    for k in range(L):
        last = k == L - 1
        a += [enc * float(x[q]) for q in range(n)]
        for q in range(n):
            a += [0.0, enc * float(x[q]) + (math.pi / 2 if (last and basis == "Y") else 0.0)]
    fin = {"X": -math.pi / 2, "Y": math.pi / 2, "Z": 0.0}[basis]
    return a + [fin] * n


def circuit(x, basis, n=N, L=L, enc=ENC):
    return TL.model_circuit(angles(x, basis, n, L, enc), n, L)


def features_noiseless(X, n=N, L=L, batch=8, enc=ENC):
    """(P, 3n): <X_q>, <Y_q>, <Z_q> (q = 0..n-1, in that block order) of the data state, by a batched statevector."""
    X = np.atleast_2d(X)
    b = np.arange(2 ** n)
    zq = np.stack([1.0 - 2.0 * ((b >> q) & 1) for q in range(n)], axis=1)
    ring = np.ones(2 ** n)
    for q in range(n):
        ring *= np.where(((b >> q) & 1) & ((b >> ((q + 1) % n)) & 1), -1.0, 1.0)
    out = np.zeros((len(X), 3 * n))
    for s in range(0, len(X), batch):
        xb = X[s:s + batch]
        B = len(xb)
        psi = np.zeros((B, 2 ** n), complex)
        psi[:, 0] = 1
        for _ in range(L):
            for q in range(n):
                v = psi.reshape(B, 2 ** (n - 1 - q), 2, 2 ** q)
                a = enc * xb[:, q]
                c, sn = np.cos(a / 2)[:, None, None], np.sin(a / 2)[:, None, None]
                a0 = v[:, :, 0, :].copy()
                v[:, :, 0, :] = c * a0 - sn * v[:, :, 1, :]
                v[:, :, 1, :] = sn * a0 + c * v[:, :, 1, :]
            ph = np.exp(-0.5j * (enc * xb) @ zq.T)  # RZ(enc x_q) on every qubit: (B, 2^n)
            psi *= ph * ring[None, :]
        p = np.abs(psi) ** 2
        out[s:s + B, 2 * n:] = p @ zq
        for q in range(n):
            v = psi.reshape(B, 2 ** (n - 1 - q), 2, 2 ** q)
            w = np.sum(np.conj(v[:, :, 0, :]) * v[:, :, 1, :], axis=(1, 2))
            out[s:s + B, q] = 2 * w.real
            out[s:s + B, n + q] = 2 * w.imag
    return out


# ------------------------------------------------------------------------------------------------ task A (teacher)

A_L = 19  # depth_formula(56.5, 26.4) = 18.9 (marrakesh n = 20, 2026-10-29); kingston's 81.3 / 22.0 gives 19.7
A_SEED_X, A_SEED_W = 20261030, 20261031
A_POOL, A_GAMMA_FRAC = 520, 0.25  # pool: 328 needed / P(|s| >= 0.25 sd) = 0.80 for a normal s, x 1.25 margin


def depth_formula(lstar_rule, lstar_other):
    """The depth at which lambda_rule^2 - lambda_other^2 is largest, with lambda = exp(-L / L*) per arm:
    L = a b ln(a / b) / (2 (a - b)) for L* = a (rule) and b (the other arm)."""
    a, b = float(lstar_rule), float(lstar_other)
    return a * b * math.log(a / b) / (2 * (a - b))


def _feat_chunk(args):
    X, n, L, enc = args
    return features_noiseless(X, n, L, enc=enc)


def features_parallel(X, n, L, enc=ENC, procs=None):
    procs = procs or int(os.environ.get("QELM_PROCS", os.cpu_count() or 1))
    if procs <= 1 or len(X) < 2 * procs:
        return features_noiseless(X, n, L, enc=enc)
    from multiprocessing import Pool
    parts = np.array_split(np.asarray(X), procs)
    with Pool(procs) as pool:
        return np.vstack(pool.map(_feat_chunk, [(p_, n, L, enc) for p_ in parts]))


def teacher_task(n=N, L=A_L, enc=ENC, pool=A_POOL, gamma_frac=A_GAMMA_FRAC, seed_x=A_SEED_X, seed_w=A_SEED_W):
    """Task A (home's instruction 2026-10-30): inputs x uniform in [-1, 1]^n (seed_x), the classifier's own noiseless
    features f0(x) (3n), a teacher w ~ N(0, I) (seed_w), labels sign(w . (f0 - mu)) with mu the pool's mean feature
    vector (centred, so that the classes are balanced in expectation); points with |w . (f0 - mu)| < gamma are
    dropped, gamma = gamma_frac x sd(w . f0) over the pool. The first N_TRAIN kept points train, the next N_TEST test.
    Nothing is redrawn: if fewer than N_TRAIN + N_TEST points are kept, it stops."""
    X = np.random.default_rng(seed_x).uniform(-1, 1, (pool, n))
    w = np.random.default_rng(seed_w).normal(size=3 * n)
    F = features_parallel(X, n, L, enc)
    mu = F.mean(axis=0)  # centred teacher: without it the features' means bias sign(w . f0) to one class (seen: 81 %)
    s = (F - mu) @ w
    gamma = gamma_frac * float(np.std(s))
    keep = np.flatnonzero(np.abs(s) >= gamma)
    if len(keep) < N_TRAIN + N_TEST:
        raise SystemExit(f"STOP: {len(keep)} points kept of {pool}; {N_TRAIN + N_TEST} needed (no redraw)")
    k = keep[:N_TRAIN + N_TEST]
    y = np.sign(s[k])
    return dict(X=X[k], F=F[k], y=y, w=w, mu=mu, gamma=gamma, kept=int(len(keep)), pool=pool, F_pool=F, X_pool=X,
                feature_sd=float(np.std(F)), feature_sd_by_basis=[float(np.std(F[:, i * n:(i + 1) * n])) for i in range(3)])


def write_teacher(out, n=N, L=A_L, enc=ENC):
    """noiseless.json for task A in the format `score` reads (plus the inputs, w and gamma)."""
    os.makedirs(out, exist_ok=True)
    f0 = os.path.join(out, "noiseless.json")
    if os.path.exists(f0):
        raise SystemExit(f"STOP: {f0} exists")
    t0 = time.perf_counter()
    T = teacher_task(n, L, enc)
    rec = dict(kind="qelm_noiseless", task="A_teacher", n=n, L=L, enc=enc, n_train=N_TRAIN, n_test=N_TEST,
               split_seed=None, seed_x=A_SEED_X, seed_w=A_SEED_W, pool=T["pool"], kept=T["kept"], gamma=T["gamma"],
               gamma_frac=A_GAMMA_FRAC, w=T["w"].tolist(), mu=T["mu"].tolist(), X=T["X"].tolist(), features=T["F"].tolist(),
               X_pool=T["X_pool"].tolist(), features_pool=T["F_pool"].tolist(),
               y_train=T["y"][:N_TRAIN].tolist(), y_test=T["y"][N_TRAIN:].tolist(), feature_sd=T["feature_sd"],
               feature_sd_by_basis=T["feature_sd_by_basis"], wall_s=time.perf_counter() - t0)
    json.dump(rec, open(f0, "w"))
    print(f"task A: n {n}, L {L}: kept {T['kept']} of {T['pool']} (gamma {T['gamma']:.4f}), feature sd {T['feature_sd']:.4f} "
          f"(X, Y, Z {', '.join(f'{v:.4f}' for v in T['feature_sd_by_basis'])}), {rec['wall_s']:.0f} s", flush=True)
    return rec


# ------------------------------------------------------------------------------------------------ classifier

def ols_fit(F, y):
    A = np.c_[np.ones(len(F)), F]
    return np.linalg.lstsq(A, y, rcond=None)[0]


def ols_predict(w, F):
    return np.c_[np.ones(len(F)), F] @ w


def accuracy(z, y):
    return float(np.mean(np.sign(z) == y))


def correct(z, y):
    return (np.sign(z) == y).astype(int)


# ------------------------------------------------------------------------------------------------ noisy stand-in

def measured_map(c):
    return {c.find_bit(i.clbits[0]).index: c.find_bit(i.qubits[0]).index for i in c.data if i.operation.name == "measure"}


DIAG = ("rz", "cz", "z", "s", "sdg", "t", "tdg")


def canonical_diagonal_order(c):
    """The same circuit, re-emitted in ASAP levels of a dependency graph in which diagonal gates (rz, cz, ...) that
    meet on a qubit with no non-diagonal gate between them are left unordered (they commute); within a level the
    two-qubit diagonal gates are emitted in greedy parallel layers. The unitary is unchanged (checked). A compiler's
    sequential CZ order would otherwise make the backward light cone run around the whole ring. Applied identically
    to every arm before the noisy stand-in; it changes only the order in which the stand-in applies the noise of
    commuting gates, as a scheduler running them in parallel would. Barriers are dropped."""
    from qiskit import QuantumCircuit
    gates = []
    for ins in c.data:
        if ins.operation.name in ("barrier", "delay"):
            continue
        gates.append((ins.operation, [c.find_bit(q).index for q in ins.qubits],
                      [c.find_bit(x).index for x in ins.clbits], ins.operation.name in DIAG))
    last_nd, since, level = {}, {}, []
    for op, qs, cs, diag in gates:
        preds = []
        for q in qs:
            if q in last_nd:
                preds.append(last_nd[q])
            if not diag:
                preds += since.get(q, [])
        lv = 1 + max((level[p] for p in preds), default=-1)
        k = len(level)
        level.append(lv)
        for q in qs:
            if diag:
                since.setdefault(q, []).append(k)
            else:
                last_nd[q] = k
                since[q] = []
    out = QuantumCircuit(*c.qregs, *c.cregs)
    by = {}
    for k, g in enumerate(gates):
        by.setdefault(level[k], []).append(g)
    for lv in sorted(by):
        gs = by[lv]
        rest = [g for g in gs if not (g[3] and len(g[1]) > 1)]
        twos = [g for g in gs if g[3] and len(g[1]) > 1]
        layers = []
        for g in twos:
            for lay in layers:
                if not lay[0].intersection(g[1]):
                    lay[0].update(g[1])
                    lay[1].append(g)
                    break
            else:
                layers.append((set(g[1]), [g]))
        for op, qs, cs, _ in rest + [g for lay in layers for g in lay[1]]:
            out.append(op, qs, cs)
    return out


def cone_circuit(c, phys):
    """The compiled circuit reduced to the backward light cone of physical qubit `phys` (exact for any observable
    of that qubit under local gate noise), ending with save_probabilities on it."""
    from qiskit import QuantumCircuit
    import qiskit_aer  # noqa: F401  (registers save_probabilities)
    cone, keep = {phys}, []
    for ins in reversed(c.data):
        nm = ins.operation.name
        if nm in ("measure", "barrier", "delay"):
            continue
        qs = [c.find_bit(q).index for q in ins.qubits]
        if cone.intersection(qs):
            keep.append((ins.operation, qs))
            cone.update(qs)
    qc = QuantumCircuit(c.num_qubits)
    for op, qs in reversed(keep):
        qc.append(op, qs)
    qc.save_probabilities([phys])
    return qc, len(cone)


def readout_errors(backend):
    """{physical qubit: (P(1 | prepared 0), P(0 | prepared 1))} from the backend's public properties."""
    pr = backend.properties()
    out = {}
    for q in range(backend.num_qubits):
        try:
            out[q] = (float(pr.qubit_property(q, "prob_meas1_prep0")[0]), float(pr.qubit_property(q, "prob_meas0_prep1")[0]))
        except Exception:  # noqa: BLE001 - symmetric fallback from the readout error
            e = float(pr.readout_error(q))
            out[q] = (e, e)
    return out


def standin_p1(circuits, backend, nm=None):
    """For each compiled circuit and each clbit: P(read 1), exact (density matrix on the light cone) with the
    backend's noise model, readout assignment errors applied. Returns (len(circuits), n) and the cone sizes."""
    from qiskit_aer import AerSimulator
    from qiskit_aer.noise import NoiseModel
    nm = nm or NoiseModel.from_backend(backend)
    sim = AerSimulator(method="density_matrix", noise_model=nm, fusion_enable=False)
    ro = readout_errors(backend)
    jobs, idx, cones = [], [], []
    for i, c in enumerate(circuits):
        for cl, ph in sorted(measured_map(c).items()):
            qc, k = cone_circuit(c, ph)
            jobs.append(qc)
            idx.append((i, cl, ph))
            cones.append(k)
    res = sim.run(jobs, shots=1).result()
    n = max(cl for _, cl, _ in idx) + 1
    P = np.zeros((len(circuits), n))
    for j, (i, cl, ph) in enumerate(idx):
        pr = res.data(j)["probabilities"]
        p1 = float(pr[1]) if len(pr) > 1 else 0.0
        e10, e01 = ro[ph]
        P[i, cl] = p1 * (1 - e01) + (1 - p1) * e10
    return P, cones


def standin_toqb_p1(circuits, T=64, seed=20261030, standin=None):
    """For each compiled circuit and each clbit: P(read 1) on TOQB's stand-in (toqb.s2r.StandIn: the published
    marrakesh calibration with T1 / T2 on scheduled idles, static ZZ, over-rotation, readout), the mean over T
    trajectories (toqb.traj2; TOQB_XP=cupy on a GPU). Circuits of one structure run as one batch."""
    from toqb import kising_echo as E
    from toqb import s2r as S
    from toqb import traj2 as T2
    st = standin or S.StandIn(t12=0.3, over=0.01, zz_hz=1e4, seed=20261017)
    eng = T2.Engine()
    groups = {}
    for i, c in enumerate(circuits):
        rr, _nm = st.prepared(c)
        pl = T2.plan(c, rr, st.target, over=st.params["over"])
        key = (len(pl.steps), tuple(pl.slot_keys), tuple(pl.act))
        groups.setdefault(key, (pl, []))[1].append(i)
    out = None
    for g, (pl, idx) in enumerate(groups.values()):
        A = np.stack([pl.angles(circuits[i]) for i in idx])
        z = E.z_all(eng, pl, A, T, seed + 7919 * g)
        if out is None:
            out = np.zeros((len(circuits), z.shape[1]))
        out[idx] = (1 - z) / 2
    return out


def sample_counts(p1, shots, seed):
    return np.random.default_rng(seed).binomial(shots, np.clip(p1, 0, 1))


def subsample(k1, shots, S, seed):
    """S of the `shots` shots without replacement: the number of ones among them."""
    if S == shots:
        return k1.copy()
    rng = np.random.default_rng(seed)
    return rng.hypergeometric(k1, shots - k1, S)


# ------------------------------------------------------------------------------------------------ run

def build_features(arm_spec, device_spec, Xall, n=N, L=L, enc=ENC):
    from toqb import s2r as S
    from toqb.devices import get_device
    dev = get_device(device_spec)
    A = S.Arm(arm_spec, dev)
    cs, maps = [], set()
    for x in Xall:
        for bs in BASES:
            c = canonical_diagonal_order(A.compile(circuit(x, bs, n, L, enc)))
            cs.append(c)
            maps.add(tuple(sorted(measured_map(c).items())))
    return cs, maps, A


def run(out, device="fake:FakeMarrakesh", arms=("fold:rule", "fold:zipcyc", "qiskit:2:blind:template"),
        standin="aer", T=64, task="breast", L_=None, enc=ENC, n=N):
    """Features on a stand-in for each arm. task "breast": the w71 data (or B with L_ = 1, enc = pi / 4); task
    "teacher": the inputs of OUT/noiseless.json (write_teacher first). standin "aer": the fake backend's Aer model,
    exact on light cones (shallow circuits only); "toqb": TOQB's stand-in by trajectories (any depth; a pod)."""
    os.makedirs(out, exist_ok=True)
    f0 = os.path.join(out, "noiseless.json")
    if task == "teacher":
        r0 = json.load(open(f0))
        Xall, Lr, enc, n = np.array(r0["X"]), r0["L"], r0["enc"], r0["n"]
    else:
        Lr = L if L_ is None else L_
        Xtr, ytr, Xte, yte = data(n)
        Xall = np.vstack([Xtr, Xte])
        reuse = False
        if os.path.exists(f0):
            old = json.load(open(f0))
            reuse = (old["n"] == n and old["L"] == Lr and old.get("enc", ENC) == enc
                     and old["split_seed"] == SPLIT_SEED and len(old["features"]) == len(Xall))
        if reuse:
            print("noiseless features: reused", flush=True)
        else:
            t0 = time.perf_counter()
            F0 = features_parallel(Xall, n, Lr, enc)
            rec0 = dict(kind="qelm_noiseless", task="breast", n=n, L=Lr, enc=enc, n_train=N_TRAIN, n_test=N_TEST,
                        split_seed=SPLIT_SEED, X=Xall.tolist(), features=F0.tolist(), y_train=ytr.tolist(),
                        y_test=yte.tolist(), wall_s=time.perf_counter() - t0)
            json.dump(rec0, open(f0, "w"))
            print(f"noiseless features {F0.shape} in {rec0['wall_s']:.0f} s", flush=True)
    backend = None
    if standin == "aer":
        from qiskit_ibm_runtime import fake_provider
        backend = getattr(fake_provider, device.split(":")[1])()
    for ai, arm in enumerate(arms):
        fo = os.path.join(out, f"standin_{arm.replace(':', '_')}.json")
        if os.path.exists(fo):
            print(f"{arm}: exists, skipped", flush=True)
            continue
        t0 = time.perf_counter()
        cs, maps, A = build_features(arm, device, Xall, n, Lr, enc)
        if standin == "aer":
            P1, cones = standin_p1(cs, backend)  # rows: point-major, basis-minor
        else:
            P1, cones = standin_toqb_p1(cs, T), [None]
        k1 = sample_counts(P1, SHOTS, SHOT_SEED + 1000 * ai)
        ops = cs[0].count_ops()
        rec = dict(kind="qelm_standin", arm=arm, device=device, standin=standin, T=T if standin == "toqb" else None,
                   shots=SHOTS, shot_seed=SHOT_SEED + 1000 * ai, p1=P1.tolist(), k1=k1.tolist(),
                   cones=[min(cones), max(cones)] if cones[0] is not None else None, measured_maps=len(maps),
                   cz_per_circuit=int(ops.get("cz", 0)), wall_s=time.perf_counter() - t0)
        json.dump(rec, open(fo, "w"))
        print(f"{arm}: {len(cs)} circuits, cz {rec['cz_per_circuit']}, stand-in {standin}, measured maps {len(maps)}, "
              f"{rec['wall_s']:.0f} s", flush=True)


def predict(out, lstar, S_list=SUBSAMPLE, reps=REPS):
    """Task A's declared predictions: each arm's test accuracy band when every feature is lambda f0 with
    lambda = exp(-L / L*_arm) (L*: the noise wall's records), read with S binomial shots. No device data."""
    r0 = json.load(open(os.path.join(out, "noiseless.json")))
    F0 = np.array(r0["features"])
    ytr, yte = np.array(r0["y_train"]), np.array(r0["y_test"])
    F0tr, F0te = F0[:N_TRAIN], F0[N_TRAIN:]
    m = F0.shape[1]
    res = dict(L=r0["L"], lstar=lstar, ceiling=accuracy(ols_predict(ols_fit(F0tr, ytr), F0te), yte), arms={})
    for ai, (arm, Ls) in enumerate(lstar.items()):
        lam = math.exp(-r0["L"] / Ls)
        res["arms"][arm] = dict(lam=lam, bands={})
        for si, S in enumerate(S_list):
            res["arms"][arm]["bands"][S] = predicted_band(F0tr, F0te, ytr, yte, np.zeros(m), np.full(m, lam), S,
                                                          reps=reps, seed=100 * ai + si)
    json.dump(res, open(os.path.join(out, "predict.json"), "w"), indent=1)
    print(f"ceiling (noiseless) {res['ceiling']:.3f}")
    for arm, v in res["arms"].items():
        print(f"{arm}: lambda {v['lam']:.3f}: " + "; ".join(f"S {S}: {b[0]:.3f} [{b[1]:.3f}, {b[2]:.3f}]"
                                                           for S, b in v["bands"].items()))
    return res


# ------------------------------------------------------------------------------------------------ score

def device_features(k1, S, n=N):
    """(P, 3n) features from counts arranged (P * 3, n) point-major, basis-minor: 1 - 2 k1 / S."""
    v = 1 - 2 * np.asarray(k1, float) / S
    P = v.shape[0] // 3
    v = v.reshape(P, 3, n)
    return np.concatenate([v[:, 0, :], v[:, 1, :], v[:, 2, :]], axis=1)


def affine_fit(Fd, F0):
    """Per feature j: Fd_j = a_j + lam_j F0_j (least squares on the given points)."""
    lam, a = np.zeros(F0.shape[1]), np.zeros(F0.shape[1])
    for j in range(F0.shape[1]):
        A = np.c_[np.ones(len(F0)), F0[:, j]]
        a[j], lam[j] = np.linalg.lstsq(A, Fd[:, j], rcond=None)[0]
    return a, lam


def predicted_band(F0tr, F0te, ytr, yte, a, lam, S, reps=REPS, seed=0, level=0.99):
    """Test accuracy of OLS when every feature is a_j + lam_j f_j read with S binomial shots (the design's model)."""
    rng = np.random.default_rng(seed)
    mtr, mte = np.clip(a + lam * F0tr, -1, 1), np.clip(a + lam * F0te, -1, 1)
    acc = []
    for _ in range(reps):
        ftr = 1 - 2 * rng.binomial(S, (1 - mtr) / 2) / S
        fte = 1 - 2 * rng.binomial(S, (1 - mte) / 2) / S
        acc.append(accuracy(ols_predict(ols_fit(ftr, ytr), fte), yte))
    lo, hi = np.quantile(acc, [(1 - level) / 2, (1 + level) / 2])
    return float(np.mean(acc)), float(lo), float(hi)


def mcnemar_two_sided(ca, cb):
    from scipy.stats import binomtest
    b, c = int(np.sum((ca == 1) & (cb == 0))), int(np.sum((ca == 0) & (cb == 1)))
    return b, c, (1.0 if b + c == 0 else float(binomtest(b, b + c, 0.5).pvalue))


def score(out):
    import glob
    r0 = json.load(open(os.path.join(out, "noiseless.json")))
    F0 = np.array(r0["features"])
    n = int(r0["n"])
    ytr, yte = np.array(r0["y_train"]), np.array(r0["y_test"])
    F0tr, F0te = F0[:N_TRAIN], F0[N_TRAIN:]
    if "X" in r0:
        Xall = np.array(r0["X"])
        Xtr, Xte = Xall[:N_TRAIN], Xall[N_TRAIN:]
    else:
        Xtr, _, Xte, _ = data()
    md = ["# QELM prototype on simulators (REHEARSAL: noiseless reference and a fake-backend stand-in; not a device "
          "result; nothing chosen from these numbers)", ""]
    base_raw = accuracy(ols_predict(ols_fit(Xtr, ytr), Xte), yte)
    base_q = accuracy(ols_predict(ols_fit(F0tr, ytr), F0te), yte)
    md += [f"- R1 baselines: least squares on the raw inputs {base_raw:.3f}; on the noiseless quantum "
           f"features (this model's ceiling) {base_q:.3f}", ""]
    res = dict(base_raw=base_raw, base_q=base_q, arms={})
    md += ["| arm | CZ / circuit | median lambda (X, Y, Z) | Q1 chi2/dof median, share > 2 | " +
           " | ".join(f"S {S}: acc [99 % band]" for S in SUBSAMPLE) + " |",
           "|---|---|---|---|" + "---|" * len(SUBSAMPLE)]
    corr = {}
    for f in sorted(glob.glob(os.path.join(out, "standin_*.json"))):
        r = json.load(open(f))
        k1 = np.array(r["k1"])
        Fd = device_features(k1, SHOTS, n)
        a, lam = affine_fit(Fd[:N_TRAIN], F0tr)
        m = np.clip(a + lam * F0tr, -1, 1)
        var = np.maximum(1 - m ** 2, 1e-6) / SHOTS
        chi = np.mean((Fd[:N_TRAIN] - m) ** 2 / var, axis=0)
        lam_b = [float(np.median(lam[i * n:(i + 1) * n])) for i in range(3)]
        cells, ar = [], dict(lambda_median=lam_b, chi2_median=float(np.median(chi)),
                             chi2_share_gt2=float(np.mean(chi > 2)), acc={}, band={}, inside={})
        for si, S in enumerate(SUBSAMPLE):
            kS = subsample(k1, SHOTS, S, SHOT_SEED + 7 * S)
            FdS = device_features(kS, S, n)
            z = ols_predict(ols_fit(FdS[:N_TRAIN], ytr), FdS[N_TRAIN:])
            acc = accuracy(z, yte)
            mean, lo, hi = predicted_band(F0tr, F0te, ytr, yte, a, lam, S, seed=11 + si)
            ar["acc"][S], ar["band"][S], ar["inside"][S] = acc, (mean, lo, hi), lo <= acc <= hi
            corr.setdefault(S, {})[r["arm"]] = correct(z, yte)
            cells.append(f"{acc:.3f} [{lo:.3f}, {hi:.3f}]{'' if lo <= acc <= hi else ' OUT'}")
        res["arms"][r["arm"]] = ar
        md.append(f"| {r['arm']} | {r['cz_per_circuit']} | {lam_b[0]:.3f}, {lam_b[1]:.3f}, {lam_b[2]:.3f} | "
                  f"{ar['chi2_median']:.2f}, {ar['chi2_share_gt2']:.2f} | " + " | ".join(cells) + " |")
    arms = list(res["arms"])
    md += ["", "Paired differences (McNemar, two-sided; first arm right only / second arm right only, p):", ""]
    for S in SUBSAMPLE:
        row = []
        for i in range(len(arms)):
            for j in range(i + 1, len(arms)):
                b, c, p = mcnemar_two_sided(corr[S][arms[i]], corr[S][arms[j]])
                row.append(f"{arms[i]} vs {arms[j]}: {b} / {c}, p {p:.2g}")
        md.append(f"- S {S}: " + "; ".join(row))
    json.dump(res, open(os.path.join(out, "qelm_score.json"), "w"), indent=1, default=str)
    open(os.path.join(out, "qelm_score.md"), "w").write("\n".join(md) + "\n")
    print("\n".join(md))


# ------------------------------------------------------------------------------------------------ checks

def _compact(c, like=None):
    """The circuit on its active qubits only (the active set of `like` if given), for unitary comparisons."""
    from qiskit import QuantumCircuit
    ref = like if like is not None else c
    act = sorted({ref.find_bit(q).index for i in ref.data for q in i.qubits
                  if i.operation.name not in ("barrier", "delay", "measure")})
    pos = {q: k for k, q in enumerate(act)}
    out = QuantumCircuit(len(act))
    for i in c.data:
        if i.operation.name in ("barrier", "delay", "measure"):
            continue
        out.append(i.operation, [pos[c.find_bit(q).index] for q in i.qubits])
    return out


def check():
    """(1) features_noiseless equals Qiskit's statevector measured through the basis circuits; (2) the light-cone
    reduction equals the full density-matrix simulation of a compiled circuit (n = 8, rule arm, FakeMarrakesh)."""
    from qiskit.quantum_info import Statevector
    n, Lc = 5, 2
    rng = np.random.default_rng(3)
    X = rng.uniform(-1, 1, (3, n))
    F = features_noiseless(X, n, Lc, batch=2)
    worst1 = 0.0
    for i, x in enumerate(X):
        for bi, bs in enumerate(BASES):
            qc = circuit(x, bs, n, Lc).remove_final_measurements(inplace=False)
            sv = Statevector(qc)
            for q in range(n):
                z = 1 - 2 * sv.probabilities([q])[1]
                worst1 = max(worst1, abs(z - F[i, bi * n + q]))
    from qiskit_aer import AerSimulator
    from qiskit_aer.noise import NoiseModel
    from qiskit_ibm_runtime.fake_provider import FakeMarrakesh
    from toqb import s2r as S
    from toqb.devices import get_device
    be = FakeMarrakesh()
    nm = NoiseModel.from_backend(be)
    A = S.Arm("fold:rule", get_device("fake:FakeMarrakesh"))
    n8 = 8
    x = rng.uniform(-1, 1, n8)
    worst2, worst3 = 0.0, 0.0
    for bs in BASES:
        c0 = A.compile(circuit(x, bs, n8, 2))
        c = canonical_diagonal_order(c0)
        from qiskit.quantum_info import Operator
        u0 = Operator(_compact(c0.remove_final_measurements(inplace=False)))
        u1 = Operator(_compact(c.remove_final_measurements(inplace=False), like=c0))
        worst3 = max(worst3, float(np.max(np.abs(u0.data - u1.data))))
        mm = measured_map(c)
        full = c.remove_final_measurements(inplace=False)
        full.save_probabilities([mm[q] for q in range(n8)])
        pr = AerSimulator(method="density_matrix", noise_model=nm, fusion_enable=False).run(full, shots=1).result().data(0)["probabilities"]
        pr = np.asarray(pr)
        P1c, _ = standin_p1([c], be, nm)
        ro = readout_errors(be)
        for q in range(n8):
            p1 = float(sum(pr[k] for k in range(len(pr)) if (k >> q) & 1))
            e10, e01 = ro[mm[q]]
            worst2 = max(worst2, abs(p1 * (1 - e01) + (1 - p1) * e10 - P1c[0, q]))
    # the cone reduction is exact in principle; Aer's density-matrix runs of different widths agree to ~2e-9 in P(1)
    # (seen: 1.8e-9, with and without gate fusion), far below the shot noise of a feature (0.06 at 250 shots)
    ok = bool(worst1 < 1e-10 and worst2 < 1e-6 and worst3 < 1e-10)
    return dict(features_vs_qiskit=float(worst1), cone_vs_full=float(worst2), reorder_unitary_diff=float(worst3), ok=ok)


def main(argv):
    if not argv or argv[0] not in ("check", "run", "score", "teacher", "predict"):
        print(__doc__)
        return 2
    if argv[0] == "check":
        r = check()
        print(json.dumps(r))
        return 0 if r["ok"] else 1
    a = argv[1:]
    get = lambda k, d=None: a[a.index(k) + 1] if k in a else d  # noqa: E731
    if argv[0] == "teacher":
        write_teacher(a[0], int(get("--n", N)), int(get("--L", A_L)))
        return 0
    if argv[0] == "predict":
        ls = dict(kv.split("=") for kv in (get("--lstar") or "fold:rule=56.5,fold:zipcyc=15.1,qiskit:2:blind:template=26.4").split(","))
        predict(a[0], {k: float(v) for k, v in ls.items()})
        return 0
    if argv[0] == "run":
        arms = tuple(get("--arms", "fold:rule,fold:zipcyc,qiskit:2:blind:template").split(","))
        enc = get("--enc")
        enc = ENC if enc is None else (math.pi / 4 if enc == "pi/4" else float(enc))
        run(a[0], get("--device", "fake:FakeMarrakesh"), arms, get("--standin", "aer"), int(get("--T", 64)),
            get("--task", "breast"), None if get("--L") is None else int(get("--L")), enc, int(get("--n", N)))
        return 0
    score(a[0])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
