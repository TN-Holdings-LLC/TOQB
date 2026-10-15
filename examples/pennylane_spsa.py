"""Train a small classifier from PennyLane on TOQB's compiled device, and see what it would cost on IBM hardware.

    PSF_ZERO_REPO=<a PSF-Zero checkout> python examples/pennylane_spsa.py [compiler] [steps]

compiler: "psfai:template" (default), "qiskit:2:target:template", ... (see toqb.task_loop.make_loop_arm).
The model and data are TOQB's loop task (toqb.task_loop); only PennyLane's own API is used to train it.
"""
import math
import sys

import pennylane as qml
from pennylane import numpy as pnp

from toqb.pennylane_device import CompiledDevice
from toqb.task_loop import model_ops, n_params, teacher_data

compiler = sys.argv[1] if len(sys.argv) > 1 else "psfai:template"
steps = int(sys.argv[2]) if len(sys.argv) > 2 else 10
task = dict(n=4, layers=2, enc=math.pi / 2, teacher_seed=4, teacher_gap=0.2, n_train=64, n_test=24)
n, L, enc = task["n"], task["layers"], task["enc"]
Xtr, ytr, Xte, yte = teacher_data(task)
dev = CompiledDevice(wires=n, compiler=compiler, seed=1)


@qml.set_shots(400)
@qml.qnode(dev)
def model(theta, x):
    angles, k = [], 0
    for _ in range(L):
        angles += [enc * x[q] for q in range(n)]
        for q in range(n):
            angles += [theta[k], theta[k + 1]]
            k += 2
    angles += [theta[k + q] for q in range(n)]
    model_ops(angles, n, L)  # created inside the QNode, so queued
    return qml.expval(qml.PauliZ(0))


def loss(theta):
    return sum((1 - y * model(theta, x)) / 2 for x, y in zip(Xtr[:8], ytr[:8])) / 8


opt = qml.SPSAOptimizer(maxiter=steps, a=3.0, c=0.2, A=2)
theta = pnp.array(pnp.random.default_rng(11).uniform(-0.5, 0.5, n_params(n, L)), requires_grad=True)
with qml.Tracker(dev) as tracker:
    for k in range(steps):
        theta, value = opt.step_and_cost(loss, theta)
        print(f"step {k + 1}: loss {float(value):.3f}", flush=True)
acc = sum((1.0 if float(model(theta, x)) * y > 0 else 0.0) for x, y in zip(Xte, yte)) / len(yte)
t = tracker.totals
print(f"{compiler}: test accuracy {acc:.3f}; training: {t['executions']} circuits, compile {t['compile_s']:.2f} s, "
      f"QPU {t['qpu_s']:.1f} s, ${t['usd']:.2f} in batch mode")
