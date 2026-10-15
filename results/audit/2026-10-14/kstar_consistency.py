import math, runpy, sys
import numpy as np
sys.path.insert(0, '.')
from psc.graph import load_dataset
R = runpy.run_path('results/research/2026-09-28-author-implementation/research_mechanism.py')
exact_re, count, PAPER, DATASETS = R['exact_re'], R['count'], R['PAPER'], R['DATASETS']
def brentq(f,a,b):
    fa=f(a)
    for _ in range(60):
        m=(a+b)/2; fm=f(m)
        if (fm>0)==(fa>0): a,fa=m,fm
        else: b=m
    return (a+b)/2

def gs(D, k, mode):
    D = np.asarray(D)
    if mode == 'tight': return np.array([math.comb(max(0, int(d)-1), k-1) for d in D], float)
    return np.array([math.comb(int(d), k-1) for d in D], float)

rng = np.random.default_rng(1)
eps2, eps3 = 0.4, 1.6
print("ds  n  dmax |  k  ours(floor_tight)  paper  scale-mult-c  fixedD*(eps3=1.6)  fixedD*(eps3=2)  RE@D=dmax,eps=2")
for idx, ds in enumerate(DATASETS):
    g = load_dataset('data', ds)['2-star'].graph()
    d = np.array([len(g.adj[i]) for i in range(g.n)], float); n = g.n; dmax = int(d.max())
    M = (d[None, :] + rng.laplace(0, 1/eps2, size=(100000, n))).max(1)
    Dsamp = np.floor(np.clip(M, 0, n-1)).astype(int)
    Ds, cnt = np.unique(Dsamp, return_counts=True); p = cnt/cnt.sum()
    for k in (2, 3):
        T = count(d, k).sum()
        A = np.array([count(np.minimum(d, D), k).sum() for D in Ds])
        b = gs(Ds, k, 'tight')/eps3
        ours = float(p @ exact_re(A, T, b, n))
        f = lambda c: float(p @ exact_re(A, T, c*b, n)) - PAPER[k][idx]
        c = brentq(f, 0.05, 3)
        def fixedD(e3):
            allD = np.arange(1, n)
            Aall = np.array([count(np.minimum(d, D), k).sum() for D in allD])
            re = exact_re(Aall, T, gs(allD, k, 'tight')/e3, n)
            return int(allD[np.argmin(np.abs(re-PAPER[k][idx]))]), float(re.min()), int(allD[np.argmin(re)])
        f16, f2 = fixedD(1.6), fixedD(2.0)
        print(f"{ds} {n:4d} {dmax:4d} | {k}  {ours:.4f}  {PAPER[k][idx]:.4f}  c={c:.3f}  D*={f16[0]}  D*={f2[0]} (min RE {f2[1]:.4f} @D={f2[2]})  meanD={p@Ds:.1f}")
