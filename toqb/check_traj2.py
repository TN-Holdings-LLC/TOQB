"""Checks the second trajectory engine (`toqb.traj2`) against TOQB's density-matrix engines on the same circuits.

    python -m toqb.check_traj2 [T]        (from the TOQB root; TOQB_XP=cupy for the GPU)

For compiled classifier circuits (n = 6, L = 8; both compilers' templates on FakeFez), two circuits of one structure:
the simulator's model (`fast_noise`, exact <Z>) and the stand-in (Aer's density matrix, exact p(clbit 0 = 1)) against
the trajectories' mean and shots. Prints |d| / se; passes when every |d| / se < 4.
"""
import sys
import time

import numpy as np

from toqb import s2r as S
from toqb import task_loop as TL
from toqb import traj2 as T2


def main(argv):
    T = int(argv[0]) if argv else 4000
    from qiskit_aer import AerSimulator
    from toqb.devices import get_device
    from toqb.fast_noise import FastNoisyDevice
    dev = get_device("fake:FakeFez")
    sim = FastNoisyDevice(dev.target)
    st = S.StandIn()
    eng = T2.Engine()
    print("backend", eng.xp.__name__, eng.dtype, flush=True)
    rng = np.random.default_rng(7)
    n, L = 6, 8
    worst = 0.0
    for spec in ("psfai:template", "qiskit:2:target:template"):
        arm = S.Arm(spec, dev)
        for j in range(3):
            th = rng.uniform(-1.5, 1.5, TL.n_params(n, L))
            x = rng.uniform(-1, 1, n)
            cs = [arm.compile(TL.model_circuit(TL.angle_list(th + d, x, n, L, 1.0), n, L)) for d in (0.0, 0.3)]
            for c in cs:
                c._toqb_scan = sim._scan(c)
            z_exact = 1 - 2 * np.array(sim.p1_fast(cs))
            r, _act, _nm, _rp = sim.noisy_circuit(cs[0])
            pl = T2.plan(cs[0], r, dev.target)
            A = np.stack([pl.angles(c) for c in cs])
            s = time.perf_counter()
            zt = eng.z_mean(pl, A, T, seed=11 + j)
            t_sim = time.perf_counter() - s
            d1 = np.abs(zt - z_exact).max() * np.sqrt(T)
            # the stand-in
            p1x = []
            for c in cs:
                rs, nms = st.prepared(c)
                rr = rs.copy()
                rr.remove_final_measurements()
                rr.save_density_matrix()
                rho = AerSimulator(method="density_matrix").run(rr, noise_model=nms).result().data()["density_matrix"]
                q0 = next(rs.find_bit(i.qubits[0]).index for i in rs.data
                          if i.operation.name == "measure" and rs.find_bit(i.clbits[0]).index == 0)
                p = np.real(np.diag(np.asarray(rho)))
                pre = sum(p[k] for k in range(len(p)) if (k >> q0) & 1)
                e = nms._local_readout_errors[(q0,)].probabilities
                p1x.append(pre * (1 - e[1][0]) + (1 - pre) * e[0][1])
            p1x = np.array(p1x)
            rs0, _ = st.prepared(cs[0])
            spl = T2.plan(cs[0], rs0, st.target, over=st.params["over"])
            SA = np.stack([spl.angles(c) for c in cs])
            zs = eng.z_mean(spl, SA, T, seed=21 + j)
            d2 = np.abs((1 - zs) / 2 - p1x).max() / (0.5 / np.sqrt(T))
            zz = eng.z_shots(spl, SA, T, seed=31 + j)
            d3 = (np.abs((1 - zz) / 2 - p1x) / np.sqrt(p1x * (1 - p1x) / T)).max()
            worst = max(worst, d1, d2, d3)
            print(f"{spec:26s} #{j} n {pl.n}: sim z {z_exact.round(4)} traj {zt.round(4)} ({d1:.1f} se, {t_sim:.2f} s); "
                  f"stand-in p1 {p1x.round(4)} traj {((1 - zs) / 2).round(4)} ({d2:.1f} se) shots "
                  f"{((1 - zz) / 2).round(4)} ({d3:.1f} se)", flush=True)
    print("PASS" if worst < 4 else "FAIL", f"largest {worst:.2f} se")
    return 0 if worst < 4 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
