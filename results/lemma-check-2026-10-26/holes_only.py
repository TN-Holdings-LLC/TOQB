import sys; sys.argv=['x']
src=open('layer_bound.py').read().split('def cyc')[0]
exec(src)
cyc=lambda m:[(i,(i+1)%m) for i in range(m)]
for m,n in ((6,4),(7,4),(8,6),(8,5),(9,6),(12,8),(12,9)):
    c=cheapest(cyc(m),m,n)
    print(f"m={m} n={n} h={m-n}: least {c}; n+2h {n+2*(m-n)}; zipper {5*n//2-4 if n%2==0 else (5*n-7)//2}"); sys.stdout.flush()
