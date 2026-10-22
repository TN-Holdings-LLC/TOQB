import sys, time, numpy as np
sys.argv=['x','4','2','1','1','/dev/null']
src=open('toy_e5.py').read().split('res = dict(')[0]
exec(src)
from qiskit.quantum_info import Statevector
import os; sys.path.insert(0, os.environ.get('TOQB_DIR', '.'))
from toqb import task_loop as TL
rng=np.random.default_rng(3); th=rng.uniform(-3,3,D); X=rng.uniform(-1,1,(5,N))
mine=z0(th,X)
ref=[]
for x in X:
    qc=TL.model_circuit(TL.angle_list(th,x,N,L,ENC),N,L); qc.remove_final_measurements()
    sv=Statevector.from_instruction(qc); ref.append(sv.expectation_value(__import__('qiskit').quantum_info.SparsePauliOp('I'*(N-1)+'Z')).real)
print('max diff', np.max(abs(mine-np.array(ref))))
