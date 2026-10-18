"""Checks the trajectory engine (`toqb.traj`) against TOQB's density-matrix engines on the same noisy circuits.

    python -m toqb.check_traj [T]        (from the TOQB root; PSF-Zero's environment variables as for the loop)

For compiled classifier circuits (n = 6, L = 8; Qiskit level 2's and PSF-Zero's templates on FakeFez):
- the simulator's model (`fast_noise`, exact): <Z> on clbit 0 against the trajectories' mean of T;
- the stand-in (`s2r.StandIn`, Aer's density matrix): p(clbit 0 = 1) from Aer's exact density matrix against the
  trajectories' mean and against T trajectory shots.
Prints each difference in units of its standard error (|d| / se); the check passes when every |d| / se < 4.
"""
import sys
import time

import numpy as np

from toqb import s2r as S
from toqb import task_loop as TL
from toqb import traj as TJ


def main(argv):
    T = int(argv[0]) if argv else 4000
    from toqb.devices import get_device
    from toqb.fast_noise import FastNoisyDevice
    dev = get_device("fake:FakeFez")
    sim = FastNoisyDevice(dev.target)
    st = S.StandIn()
    eng = TJ.Engine()
    rng = np.random.default_rng(7)
    n, L = 6, 8
    worst = 0.0
    for spec in ("psfai:template", "qiskit:2:target:template"):
        arm = S.Arm(spec, dev)
        for j in range(3):
            th = rng.uniform(-1.5, 1.5, TL.n_params(n, L))
            x = rng.uniform(-1, 1, n)
            c = arm.compile(TL.model_circuit(TL.angle_list(th, x, n, L, 1.0), n, L))
            # the simulator's model
            c._toqb_scan = sim._scan(c)
            z_exact = 1 - 2 * sim.p1_fast([c])[0]
            r, act, nm, _ = sim.noisy_circuit(c)
            prog = TJ.program_from_aer(r, nm)
            s = time.perf_counter()
            zt = eng.z_traj([prog], T, seed=11 + j)[0]
            t_sim = time.perf_counter() - s
            se = 1.0 / np.sqrt(T)  # <Z> per trajectory is in [-1, 1]
            d1 = abs(zt - z_exact) / se
            # the stand-in
            rs, nms = st.prepared(c)
            from qiskit_aer import AerSimulator
            rr = rs.copy()
            rr.remove_final_measurements()
            rr.save_density_matrix()
            rho = AerSimulator(method="density_matrix").run(rr, noise_model=nms).result().data()["density_matrix"]
            q0 = next(rs.find_bit(i.qubits[0]).index for i in rs.data
                      if i.operation.name == "measure" and rs.find_bit(i.clbits[0]).index == 0)
            p = np.real(np.diag(np.asarray(rho)))
            p1_pre = sum(p[k] for k in range(len(p)) if (k >> q0) & 1)
            e = nms._local_readout_errors[(q0,)].probabilities
            p1_exact = p1_pre * (1 - e[1][0]) + (1 - p1_pre) * e[0][1]
            sp = TJ.program_from_aer(rs, nms)
            zs = eng.z_traj([sp], T, seed=21 + j)[0]
            d2 = abs((1 - zs) / 2 - p1_exact) / (0.5 / np.sqrt(T))
            cnt = eng.counts([sp], T, seed=31 + j)[0]
            p1_shots = sum(v for k, v in cnt.items() if k[-1] == "1") / T
            d3 = abs(p1_shots - p1_exact) / max(np.sqrt(p1_exact * (1 - p1_exact) / T), 1e-9)
            worst = max(worst, d1, d2, d3)
            print(f"{spec:26s} #{j} n_act {r.num_qubits}: sim z {z_exact:+.4f} traj {zt:+.4f} ({d1:.1f} se, "
                  f"{t_sim:.2f} s); stand-in p1 {p1_exact:.4f} traj {(1 - zs) / 2:.4f} ({d2:.1f} se) shots "
                  f"{p1_shots:.4f} ({d3:.1f} se)", flush=True)
    print("PASS" if worst < 4 else "FAIL", f"largest {worst:.2f} se")
    return 0 if worst < 4 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
