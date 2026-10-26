# Cheapest single ring layer in the routing model, by Dijkstra from every start layout.
# Ops on a coupler: CZ (1, applies a ring edge), CZ+SWAP (2, applies it and swaps), SWAP (3), move into empty (2).
import heapq, itertools, sys
def cheapest(edges, nq, n):
    adj=[(a,b) for a,b in edges]
    ring={frozenset((i,(i+1)%n)):i for i in range(n)}
    full=(1<<n)-1
    dist={}; pq=[]
    for perm in itertools.permutations(range(nq), n):
        pl=[-1]*nq
        for node,q in enumerate(perm): pl[q]=node
        s=(tuple(pl),0); dist[s]=0; pq.append((0,s))
    heapq.heapify(pq)
    while pq:
        d,(pl,m)=heapq.heappop(pq)
        if dist.get((pl,m))!=d: continue
        if m==full: return d
        for a,b in adj:
            x,y=pl[a],pl[b]
            nxt=[]
            sw=list(pl); sw[a],sw[b]=y,x; sw=tuple(sw)
            if x>=0 and y>=0:
                e=ring.get(frozenset((x,y)))
                if e is not None and not m>>e&1:
                    nxt.append((1,pl,m|1<<e)); nxt.append((2,sw,m|1<<e))
                nxt.append((3,sw,m))
            elif x>=0 or y>=0:
                nxt.append((2,sw,m))
            for c,p2,m2 in nxt:
                s=(p2,m2); nd=d+c
                if nd<dist.get(s,1<<30): dist[s]=nd; heapq.heappush(pq,(nd,s))
def cyc(m): return [(i,(i+1)%m) for i in range(m)]
print("pendants: cycle m + leaves on hubs; bound n+k")
for m in (4,5,6):
    for k in range(1,m//2+1):
        if m+k>8: continue
        for hubs in itertools.combinations(range(m),k):
            if hubs[0]!=0: continue
            E=cyc(m)+[(h,m+j) for j,h in enumerate(hubs)]
            n=m+k; c=cheapest(E,n,n)
            adjh=any((b-a)%m in (1,m-1) for a,b in itertools.combinations(hubs,2))
            print(f"m={m} hubs={hubs} adjacent={adjh} n={n}: least {c}, n+k {n+k}", "OK" if c==n+k else "DIFF")
print("holes: cycle m, n nodes")
for m,n in ((6,4),(7,4),(8,6),(9,6),(12,8),(12,9),(12,10)):
    if m>9 and n>9: pass
    c=cheapest(cyc(m),m,n)
    print(f"m={m} n={n} h={m-n}: least {c}; n+2h {n+2*(m-n)}; zipper {5*n//2-4 if n%2==0 else (5*n-7)//2}")
    sys.stdout.flush()
