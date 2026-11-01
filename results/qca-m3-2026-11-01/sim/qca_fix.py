import sys, numpy as np
sys.path.insert(0, '/tmp/claude-0/work/toqb')
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector
from toqb import kising_echo as KE
N=10; B=(4,5,6)
def qca(bits, layers):
    qc=QuantumCircuit(N)
    for q,b in enumerate(bits):
        if b: qc.x(q)
    for _ in range(layers):
        for q in range(N): qc.h(q)
        for q in range(N): qc.cz(q,(q+1)%N)
    return qc
def noisy(qc, eps):
    out=QuantumCircuit(N)
    for i in qc.data:
        qs=[qc.find_bit(q).index for q in i.qubits]
        out.append(i.operation,[out.qubits[q] for q in qs])
        if i.operation.name=='cz' and set(qs)&set(B): out.rzz(eps,qs[0],qs[1])
    return out
rng=np.random.default_rng(1)
for eps in (0.0,0.1,0.2):
    for lab,sites in (('off',None),('local 4,6',[4,6]),('global',list(range(0,N,2)))):
        acc=[]
        for k in range(4):
            bits=list(rng.integers(0,2,N))
            qc=qca(bits,N)          # period N: ideal output = input bits
            if sites: qc=KE.frame_flip(qc,N,sites)
            p=Statevector(noisy(qc,eps)).probabilities_dict()
            key=''.join(str(b) for b in reversed(bits))
            acc.append(p.get(key,0.0))
        print(f"eps {eps} {lab}: probability of the right bitstring {np.mean(acc):.3f}")
