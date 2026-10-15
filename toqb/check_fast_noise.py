"""Checks the fast engine (toqb.fast_noise) against two references, on compiled model circuits of TOQB's loop.

    python -m toqb.check_fast_noise <out.json> [circuits per arm and size, default 20]

For each size (n = 6, L = 8 and n = 4, L = 2), each arm (PSF-Zero's template, Qiskit level 2's template and its
recompile arm) and random angles:

1. **Exact reference.** qiskit.quantum_info evolves the same noisy circuit instruction by instruction, with the
   errors taken from the noise model Aer is given. The engine's density matrix must agree to 1e-12.
2. **Aer.** Aer's density matrix on the same noisy circuit and noise model. Reported, with p1 of clbit 0 (readout
   included) required within 1e-6: Aer itself differs from the exact reference by about 1e-9 per element.
3. **Fast path.** The per-structure path that the loop uses must give the same p1 as the one-program-per-circuit
   path to 1e-12.

Needs $PSF_ZERO_REPO (and $PSF_COMPILE_FILE as for the loop).
"""
import json
import sys
import time

import numpy as np


def _reference_rho(fast, c):
    from qiskit.quantum_info import DensityMatrix, Operator, SuperOp
    r, act, nm, _ = fast.noisy_circuit(c)
    errs = nm._local_quantum_errors
    rho = DensityMatrix.from_label("0" * r.num_qubits)
    for i in r.data:
        name = i.operation.name
        qs = [r.find_bit(q).index for q in i.qubits]
        if name in ("measure", "delay", "barrier"):
            continue
        if name == "quantum_channel":
            rho = rho.evolve(SuperOp(i.operation._quantum_error), qs)
            continue
        rho = rho.evolve(Operator(i.operation), qs)
        e = errs.get(name, {}).get(tuple(qs))
        if e is not None:
            rho = rho.evolve(SuperOp(e), qs)
    n = r.num_qubits
    return rho.data.reshape((2,) * (2 * n)).transpose(
        list(range(n - 1, -1, -1)) + list(range(2 * n - 1, n - 1, -1))).reshape(2 ** n, 2 ** n)


def _engine_rho(fast, c):
    r, act, _, _ = fast.noisy_circuit(c)
    n, ops, _, _, pend = fast.program(r, act)
    rho = fast._evolve(n, [ops])
    for q in range(n):
        if pend[q] is not None:
            rho = fast._apply(rho, n, (q,), pend[q][None])
    return rho.reshape(2 ** n, 2 ** n)


def main(argv):
    from toqb.devices import get_device
    from toqb.fast_noise import FastNoisyDevice, check_against_aer
    from toqb.task_loop import angle_list, make_loop_arm, model_circuit, n_params
    out_file = argv[0]
    N = int(argv[1]) if len(argv) > 1 else 20
    dev = get_device("fake:FakeFez")
    rows = []
    for n, L in ((6, 8), (4, 2)):
        for spec in ("psfai:template", "qiskit:2:target:template", "qiskit:2:target:recompile"):
            arm = make_loop_arm(spec)
            arm.setup(dev.target)
            fast = FastNoisyDevice(dev.target)
            rng = np.random.default_rng(1000 * n + L)
            qcs = []
            for _ in range(N if spec.endswith("template") else max(2, N // 4)):
                x = rng.uniform(-1, 1, n)
                qcs.append(arm.compile_circuit(model_circuit(angle_list(rng.uniform(-np.pi, np.pi, n_params(n, L)),
                                                                        x, n, L, np.pi / 2), n, L)))
            t = time.perf_counter()
            ref = max(float(np.max(np.abs(_engine_rho(fast, c) - _reference_rho(fast, c)))) for c in qcs)
            aer_rho, aer_p1 = check_against_aer(fast, qcs)
            fp = float(np.max(np.abs(fast.p1_fast(qcs) - fast.p1_of(qcs))))
            row = dict(n=n, L=L, arm=spec, circuits=len(qcs), active_qubits=sorted({fast.noisy_circuit(c)[0].num_qubits
                                                                            for c in qcs}),
                       max_rho_vs_exact=ref, max_rho_vs_aer=aer_rho, max_p1_vs_aer=aer_p1, max_p1_fast_vs_program=fp,
                       ok=bool(ref <= 1e-12 and aer_p1 <= 1e-6 and fp <= 1e-12), seconds=time.perf_counter() - t)
            print(json.dumps(row), flush=True)
            rows.append(row)
    import qiskit
    import qiskit_aer
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(dict(qiskit=qiskit.__version__, aer=qiskit_aer.__version__, rows=rows,
                       all_ok=all(r["ok"] for r in rows)), f, indent=1)
    print("ALL OK" if all(r["ok"] for r in rows) else "FAILED")
    return 0 if all(r["ok"] for r in rows) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
