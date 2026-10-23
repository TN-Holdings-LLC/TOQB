import json,math,numpy as np
import sys
# usage: python pair.py RUNS_DIR UNDAMP_FINAL_DIR
R=sys.argv[1].rstrip('/')+'/'; U=sys.argv[2].rstrip('/')+'/'
def mcn(a,b):  # a,b bool correct arrays; exact two-sided binomial on discordant
    n10=int(np.sum(a&~b)); n01=int(np.sum(~a&b)); n=n10+n01
    if n==0: return n10,n01,1.0
    k=min(n10,n01); p=sum(math.comb(n,i) for i in range(k+1))/2**n
    return n10,n01,min(1.0,2*p)
def holm(ps):
    o=sorted(range(len(ps)),key=lambda i:ps[i]); m=len(ps); adj=[0]*m; run=0
    for r,i in enumerate(o): run=max(run,min(1,(m-r)*ps[i])); adj[i]=run
    return adj
rows=[];P={'raw':[],'und':[]}
for t in ('t11','t12','t13'):
    d={}
    for a in ('template','template_zip'):
        b=f'L16_{t}_s301-psfai_{a}'
        r=json.load(open(R+b+'.json')); u=json.load(open(U+b+'.json'))['points'][0]
        z=1-2*np.array(r['rehearsal']['standin_p1']); y=np.array(r['test_labels'])
        d[a]=(z,y,u['lam'],u['delta'])
    assert np.array_equal(d['template'][1],d['template_zip'][1])
    y=d['template'][1]
    out={'t':t}
    for kind in ('raw','und'):
        c={}
        for a,(z,_,lam,dl) in d.items():
            s = z if kind=='raw' else (z-dl)
            c[a]=np.sign(s)==y
        n10,n01,p=mcn(c['template_zip'],c['template'])
        out[kind]=(c['template_zip'].mean(),c['template'].mean(),n10,n01,p); P[kind].append(p)
    # fraction predicted +1 (class balance check)
    out['frac_pos']={a:(float(np.mean(np.sign(d[a][0])>0)), float(np.mean(np.sign(d[a][0]-d[a][3])>0))) for a in d}
    out['label_pos']=float(np.mean(y>0))
    rows.append(out)
for k in P: 
    for r,h in zip(rows,holm(P[k])): r[k]=r[k]+(h,)
for r in rows:
    print(r['t'],'labels +1 frac %.3f'%r['label_pos'],'pred+1 raw/und', {a:tuple(round(x,3) for x in v) for a,v in r['frac_pos'].items()})
    for k in ('raw','und'):
        zp,q,n10,n01,p,h=r[k]; print('   %s exact acc zip %.3f q31 %.3f gap %+.3f  zip-only-correct %d q31-only %d  p %.2g holm %.2g'%(k,zp,q,zp-q,n10,n01,p,h))
