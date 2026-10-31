"""Which total eps (PSC split eps2:eps3 = 1:4, floor_tight) reproduces each paper k-star cell?"""
import sys, numpy as np
sys.path.insert(0, '.')
from psc.graph import load_dataset
PAPER = {2: [.1062,.0585,.0444,.1210,.0295,.0284], 3: [.8035,.3434,.2077,.5410,.1647,.1290]}
DS = ('CU','Do','ML','CS','EE','PM'); Rn = 20000
def cnt(x, k): return x*(x-1)/2 if k == 2 else x*(x-1)*(x-2)/6
rng = np.random.default_rng(5)
grid = np.round(np.arange(1.5, 4.51, 0.05), 2)
for k in (2, 3):
    out = []
    for i, ds in enumerate(DS):
        g = load_dataset('data', ds)['2-star'].graph(); n = g.n
        d = np.array([len(g.adj[v]) for v in range(n)], float); T = cnt(d, k).sum()
        Z1, Z2 = rng.laplace(0, 1, (Rn, n)), rng.laplace(0, 1, (Rn, n)).sum(1)
        res = []
        for e in grid:
            e2, e3 = .2*e, .8*e
            D = np.floor(np.clip((d + Z1/e2).max(1), 0, n-1))
            A = cnt(np.minimum(d[None, :], D[:, None]), k).sum(1)
            gs = np.maximum(D-1, 0) if k == 2 else np.maximum(D-1, 0)*np.maximum(D-2, 0)/2
            res.append((np.abs(np.maximum(0, A + gs/e3*Z2) - T)/T).mean())
        out.append(f"{ds}={grid[np.argmin(np.abs(np.array(res)-PAPER[k][i]))]:.2f}")
    print(f"{k}-star: eps matching paper ->", "  ".join(out))
