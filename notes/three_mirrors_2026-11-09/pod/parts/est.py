# ETA probe: the same circuits as pod_three_mirrors.py, 10 trajectories each (one Aer thread), timed.
import sys, time
import three_mirrors as T, pod_three_mirrors as PT
from psf_os import device as Dv, grid3d as G
from psf_os.compile import RuleCompiler
layout, ts = sys.argv[1], [int(x) for x in sys.argv[2].split(",")]
dev = Dv.Device.load("dev"); rc = RuleCompiler(dev)
for t in ts:
    qc, placed, used, _, where = G.physical(dev, 4, 2, 2, t, 0.6, layout=layout, info=True)
    phys = [placed[s] for s in range(16)]; br = sorted(set(used) - set(phys))
    cu = T.compiled(dev, rc, qc, phys); rp, bp = T.parts(cu, set(br))
    circs = dict(F=T.mirror(rc, cu, phys), L=T.mirror(rc, rp, phys), Rt=T.mirror(rc, bp, phys), R=T.readout_only(dev, phys))
    for z in (0.0, 0.02):
        for k, c in circs.items():
            if k == "R" and z > 0: continue
            nq = T.compact(c, dev.couplers, z)[0].num_qubits
            t0 = time.time(); PT._task(((layout, t, z, k), c, dev.couplers, z, 10, 11)); dt = time.time() - t0
            print(f"{layout} t{t} z{z} {k}: {nq} qubits, 10 traj {dt:.1f} s -> per 100-traj chunk ~{dt*10:.0f} s", flush=True)
