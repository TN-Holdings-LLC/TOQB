# L layers with interleaving allowed: ring edge e may fire its (c+1)-th time iff c <= counts of both neighbouring ring edges
# (both its nodes have finished layer c, so their single-qubit gates of layer c+1 are in). Least total over all starts.
import heapq, itertools, sys
def least(edges, n, L):
    full=tuple([L]*n)
    ring={frozenset((i,(i+1)%n)):i for i in range(n)}
    dist={}; pq=[]
    for perm in itertools.permutations(range(n)):
        s=(perm,(0,)*n); dist[s]=0; pq.append((0,s))
    heapq.heapify(pq)
    while pq:
        d,(pl,c)=heapq.heappop(pq)
        if dist.get((pl,c))!=d: continue
        if c==full: return d
        for a,b in edges:
            x,y=pl[a],pl[b]
            sw=list(pl); sw[a],sw[b]=y,x; sw=tuple(sw)
            nx=[(3,sw,c)]
            e=ring.get(frozenset((x,y)))
            if e is not None and c[e]<L and c[e]<=c[(e-1)%n] and c[e]<=c[(e+1)%n]:
                c2=list(c); c2[e]+=1; c2=tuple(c2)
                nx+= [(1,pl,c2),(2,sw,c2)]
            for cost,p2,c2 in nx:
                s=(p2,c2); nd=d+cost
                if nd<dist.get(s,1<<30): dist[s]=nd; heapq.heappush(pq,(nd,s))
cyc=lambda m:[(i,(i+1)%m) for i in range(m)]
for m,hubs,L in ((4,(0,),2),(4,(0,),3),(4,(0,),4),(5,(0,),2),(5,(0,),3),(4,(0,2),2),(4,(0,2),3),(5,(0,2),2),(6,(0,),2)):
    E=cyc(m)+[(h,m+j) for j,h in enumerate(hubs)]; n=m+len(hubs)
    print(f"m={m} hubs={hubs} n={n} L={L}: least {least(E,n,L)}, L(n+k) {L*(n+len(hubs))}"); sys.stdout.flush()
