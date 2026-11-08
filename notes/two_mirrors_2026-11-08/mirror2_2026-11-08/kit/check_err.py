"""The noiseless error gates equal RZZ / RX, and the noise model attaches nothing to them."""
import numpy as np
from qiskit.circuit.library import RZZGate, RXGate
from qiskit.quantum_info import Operator
import expsim3 as X
print("zz equal:", Operator(X._err_gate("zz", 0.02)).equiv(Operator(RZZGate(0.02))),
      " x equal:", Operator(X._err_gate("x", 0.01)).equiv(Operator(RXGate(0.01))))
tgt, t1s, t2s, base = X._base("inputs/fez_props_2026-11-07.json")
print("noise model basis gates with errors:", sorted(base.noise_instructions))
