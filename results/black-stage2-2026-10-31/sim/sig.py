import sys, numpy as np
sys.path.insert(0, '/tmp/claude-0/work/toqb')
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector, Pauli
from toqb import kising_echo as KE, kising_charge as KC
N=10; B=(4,5,6)
def inject(qc, kind, eps):
    out = QuantumCircuit(N)
    for i in qc.data:
        if i.operation.name in ('measure','barrier'): continue
        qs=[qc.find_bit(q).index for q in i.qubits]
        out.append(i.operation,[out.qubits[q] for q in qs])
        if i.operation.name=='cz':
            if kind=='rz':
                for q in qs:
                    if q in B: out.rz(eps,q)
            if kind=='ry':
                for q in qs:
                    if q in B: out.ry(eps,q)
            if kind=='rx':
                for q in qs:
                    if q in B: out.rx(eps,q)
            if kind=='zz' and set(qs)<=set(B): out.rzz(eps,qs[0],qs[1])
            if kind=='zzedge' and len(set(qs)&set(B))>=1: out.rzz(eps,qs[0],qs[1])
    return out
def vec(kind,eps,L):
    v=np.zeros((3,N))
    for inp in KC.INPUTS:
        bits=KC.input_bits(inp,N); zin=1-2*np.array(bits)
        qc=inject(KE.circuit(bits,N,L,0.6,0.0),kind,eps)
        sv=Statevector(qc)
        for k,P in enumerate('XYZ'):
            for j in range(N):
                lab=['I']*N; lab[N-1-j]=P
                v[k,j]+= -zin[j]*sv.expectation_value(Pauli(''.join(lab))).real/4
    return v
Ls=[1,2,3,4,6,8,10,12]
for kind,eps in [(a,float(b)) for a,b in (x.split(':') for x in sys.argv[1:])]:
    rat=[]; 
    for L in Ls:
        v=vec(kind,eps,L); rest=[j for j in range(N) if j not in B and min(abs(j-b) for b in B)>1] 
        rat.append(v[2][list(B)].mean()/max(v[2][rest].mean(),1e-9))
        if L==6:
            r=np.sqrt((v**2).sum(0)); tf=np.sqrt(v[0]**2+v[1]**2)/np.maximum(r,1e-9)
            l12=(r[list(B)].mean()/r[rest].mean(), tf[list(B)].mean())
    print(f"{kind} {eps}: ratio over D2..24 "+' '.join(f"{x:+.2f}" for x in rat)+f" | |v| ratio D12 {l12[0]:.2f}, transverse {l12[1]:.2f}", flush=True)
