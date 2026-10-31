import sys, numpy as np
sys.path.insert(0, '/tmp/claude-0/work/toqb')
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector, Pauli
from toqb import kising_echo as KE, kising_charge as KC
N=10; B=(4,5,6)
def build(bits, L, kind, eps, fix):
    qc=KE.circuit(bits,N,L,0.6,0.0)
    out=QuantumCircuit(N); incz=False; layer=0
    def xs():
        for q in range(0,N,2): out.x(q)
    for i in qc.data:
        nm=i.operation.name
        if nm in ('measure','barrier'): continue
        qs=[qc.find_bit(q).index for q in i.qubits]
        if nm=='cz' and not incz:
            incz=True; layer+=1
            if fix and layer%2==0: xs()
        if nm!='cz' and incz:
            incz=False
            if fix and layer%2==0: xs()
        out.append(i.operation,[out.qubits[q] for q in qs])
        if nm=='cz':
            if kind=='zzedge' and set(qs)&set(B): out.rzz(eps,qs[0],qs[1])
            if kind=='zz' and set(qs)<=set(B): out.rzz(eps,qs[0],qs[1])
            if kind=='rx':
                for q in qs:
                    if q in B: out.rx(eps,q)
    if incz and fix and layer%2==0: xs()
    return out
def zsig(kind,eps,L,fix):
    v=np.zeros(N)
    for inp in KC.INPUTS:
        bits=KC.input_bits(inp,N); zin=1-2*np.array(bits)
        sv=Statevector(build(bits,L,kind,eps,fix))
        for j in range(N):
            lab=['I']*N; lab[N-1-j]='Z'
            v[j]+=-zin[j]*sv.expectation_value(Pauli(''.join(lab))).real/4
    return v
Ls=[1,2,4,6,8,12]
for kind,eps in [(a,float(b)) for a,b in (x.split(':') for x in sys.argv[1:])]:
    for fix in (False,True):
        r=[]
        for L in Ls:
            v=zsig(kind,eps,L,fix); r.append((v[list(B)].mean(), v.mean()))
        print(f"{kind} {eps} fix={fix}: block "+' '.join(f"{x[0]:+.2f}" for x in r)+" | all "+' '.join(f"{x[1]:+.2f}" for x in r), flush=True)
