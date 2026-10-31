import math, sys, numpy as np
sys.path.insert(0,'.')
from psc.graph import load_dataset
PAPER={2:[.1062,.0585,.0444,.1210,.0295,.0284],3:[.8035,.3434,.2077,.5410,.1647,.1290]}
rng=np.random.default_rng(7); eps2,eps3=.4,1.6; R=200000
def cnt(d,k): return d*(d-1)/2 if k==2 else d*(d-1)*(d-2)/6
for i,ds in enumerate(('CU','Do','ML','CS','EE','PM')):
    g=load_dataset('data',ds)['2-star'].graph(); n=g.n
    d=np.array([len(g.adj[v]) for v in range(n)],float)
    D=np.floor(np.clip((d+rng.laplace(0,1/eps2,(R,n))).max(1),0,n-1))
    S=rng.laplace(0,1,(R,n)).sum(1)
    out=[]
    for k in (2,3):
        T=cnt(d,k).sum(); A=cnt(np.minimum(d[None,:],D[:,None]),k).sum(1)
        gsv=np.maximum(D-1,0) if k==2 else np.maximum(D-1,0)*np.maximum(D-2,0)/2
        re=np.abs(np.maximum(0,A+gsv/eps3*S)-T)/T
        se=re.std()/math.sqrt(1000)
        out.append(f"{k}-star mean={re.mean():.4f} SE(1000runs)={se:.4f} paper={PAPER[k][i]:.4f} z={(PAPER[k][i]-re.mean())/se:+.1f}")
    print(ds,' | '.join(out))
