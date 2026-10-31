import sys, numpy as np
sys.path.insert(0, '/tmp/claude-0/work/toqb')
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector, Pauli
from toqb import kising_echo as KE, kising_charge as KC
N=10; B=(4,5,6)
def build(bits, L, kind, eps, sites):
    base=KE.circuit(bits,N,L,0.6,0.0)
    qc=KE.frame_flip(base,N,sites) if sites else base
    out=QuantumCircuit(N)
    for i in qc.data:
        nm=i.operation.name
        if nm in ('measure','barrier'): continue
        qs=[qc.find_bit(q).index for q in i.qubits]
        out.append(i.operation,[out.qubits[q] for q in qs])
        if nm=='cz':
            if kind=='zzedge' and set(qs)&set(B): out.rzz(eps,qs[0],qs[1])
            if kind=='zzall': out.rzz(eps,qs[0],qs[1])
    return out
def zsig(kind,eps,L,sites):
    v=np.zeros(N)
    for inp in KC.INPUTS:
        bits=KC.input_bits(inp,N); zin=1-2*np.array(bits)
        sv=Statevector(build(bits,L,kind,eps,sites))
        for j in range(N):
            lab=['I']*N; lab[N-1-j]='Z'; v[j]+=-zin[j]*sv.expectation_value(Pauli(''.join(lab))).real/4
    return v
Ls=[1,2,4,6,8,12]; rest=[0,1,8,9]
for kind,eps in (('zzedge',0.0),('zzedge',0.2),('zzedge',0.4),('zzall',0.2)):
    for lab,sites in (('off',None),('local 4,6',[4,6]),('global',list(range(0,N,2)))):
        r=[zsig(kind,eps,L,sites) for L in Ls]
        print(f"{kind} {eps} {lab}: block "+' '.join(f"{v[list(B)].mean():+.2f}" for v in r)+" | far "+' '.join(f"{v[rest].mean():+.2f}" for v in r), flush=True)
