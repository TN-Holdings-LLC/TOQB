"""Pre-run check of the 4 x 6 x 3 folded placement (2026-11-07; no device, no noise): at theta = pi/2 the job is
Clifford, so every stabilizer of the lattice state must hold on the placed sites and every bridge must be back in |0>,
for each candidate translation of a device record and t = 1, 2, 3. Same test as psf-os tests/test_grid3d.py
(test_placed_state_equals_the_lattice_state_clifford), at the size of the 2026-11-07 big run.

usage: python stab_check.py PSF_OS DEVICE_RECORD M N
"""
import sys

import numpy as np

sys.path.insert(0, sys.argv[1])
sys.path.insert(0, sys.argv[1] + "/tests")
from psf_os import device as Dv  # noqa: E402
from psf_os import grid3d as G  # noqa: E402
from test_grid3d import _clifford  # noqa: E402


def main():
    from qiskit import QuantumCircuit
    from qiskit.quantum_info import Pauli, StabilizerState
    dev = Dv.Device.load(sys.argv[2])
    L, M, N = 4, int(sys.argv[3]), int(sys.argv[4])
    offs = [(r0, c0) for _, r0, c0 in G.fold_offsets(M, N)]
    done, bad = 0, 0
    for t in (1, 2, 3):
        for r0c0 in offs:
            avoid = [o for o in offs if o != r0c0]
            try:
                qc, placed, used, _ = G.physical(dev, L, M, N, t, np.pi / 2, layout="fold", avoid=avoid)
            except G.Refused:
                continue
            n, m = L * M * N, {u: i for i, u in enumerate(used)}
            small = QuantumCircuit(len(used))
            for ins in qc.data:
                small.append(ins.operation, [m[qc.find_bit(q).index] for q in ins.qubits])
            ps = StabilizerState(_clifford(small))
            worst = 0.0
            for lab in StabilizerState(_clifford(G.logical(L, M, N, t, np.pi / 2))).clifford.to_labels(mode="S"):
                sign, body = lab[0], lab[1:]
                chars = ["I"] * len(used)
                for s in range(n):
                    chars[m[placed[s]]] = body[n - 1 - s]
                v = ps.expectation_value(Pauli("".join(reversed(chars))))
                worst = max(worst, abs(v - (1 if sign == "+" else -1)))
            data = {m[placed[s]] for s in range(n)}
            for q in set(range(len(used))) - data:
                z = ["I"] * len(used)
                z[q] = "Z"
                worst = max(worst, abs(ps.expectation_value(Pauli("".join(reversed(z)))) - 1))
            print(f"t{t} translation {r0c0} qubits {len(used)}: worst stabilizer deviation {worst:.1e}", flush=True)
            done += 1
            bad += worst > 1e-9
    print("STAB CHECK", "PASS" if bad == 0 and done else "FAIL", f"({done} placements)")


if __name__ == "__main__":
    main()
