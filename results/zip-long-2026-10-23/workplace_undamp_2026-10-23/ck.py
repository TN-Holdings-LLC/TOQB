import json,math,numpy as np
import sys
# usage: python ck.py RUNS_DIR
R=sys.argv[1].rstrip('/')+'/'
dl={('t11','template'):{500:.064,1000:.058,2000:.046},('t11','template_zip'):{500:.016,1000:.015,2000:.011,4000:-.002}}
def mcn(a,b):
    n10=int(np.sum(a&~b)); n01=int(np.sum(~a&b)); n=n10+n01; k=min(n10,n01)
    return n10,n01,min(1,2*sum(math.comb(n,i) for i in range(k+1))/2**n)
C={}
for a in ('template','template_zip'):
    r=json.load(open(R+f'L16_t11_s301-psfai_{a}.json')); y=np.array(r['test_labels'])
    for c in r['checkpoints']:
        z=1-2*np.array(c['rehearsal']['standin_p1']); C[(a,c['loop'])]=(z,y)
for L in (500,1000,2000):
    zq,y=C[('template',L)]; zz,_=C[('template_zip',L)]
    for kind in ('raw','und'):
        sq = zq if kind=='raw' else zq-dl[('t11','template')][L]
        sz = zz if kind=='raw' else zz-dl[('t11','template_zip')][L]
        cq=np.sign(sq)==y; cz=np.sign(sz)==y
        n10,n01,p=mcn(cz,cq)
        print(L,kind,'zip %.3f q31 %.3f gap %+.3f (%d/%d) p %.2g | q31 pred+1 %.2f'%(cz.mean(),cq.mean(),cz.mean()-cq.mean(),n10,n01,p,np.mean(sq>0)))
