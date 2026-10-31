"""Under our floor_tight GT, how likely is a 10-run mean RE <= the paper's agent PSC value?"""
import sys, numpy as np
sys.path.insert(0, '.')
from psc.graph import load_dataset
from psc.experiments import PAPER_TABLE2
DS = ('CU','Do','ML','CS','EE'); Rn = 200000; e2, e3 = .4, 1.6
def cnt(x, k): return x*(x-1)/2 if k == 2 else x*(x-1)*(x-2)/6
rng = np.random.default_rng(11)
for k in (2, 3):
    out = []
    for i, ds in enumerate(DS):
        g = load_dataset('data', ds)['2-star'].graph(); n = g.n
        d = np.array([len(g.adj[v]) for v in range(n)], float); T = cnt(d, k).sum()
        D = np.floor(np.clip((d + rng.laplace(0, 1/e2, (Rn, n))).max(1), 0, n-1))
        A = cnt(np.minimum(d[None, :], D[:, None]), k).sum(1)
        gs = np.maximum(D-1, 0) if k == 2 else np.maximum(D-1, 0)*np.maximum(D-2, 0)/2
        re = np.abs(np.maximum(0, A + gs/e3*rng.laplace(0, 1, (Rn, n)).sum(1)) - T)/T
        m10 = re.reshape(-1, 10).mean(1)
        out.append(f"{ds} P={np.mean(m10 <= PAPER_TABLE2[f'{k}-star']['PSC'][i]):.3f}")
    print(f"{k}-star agent PSC:", "  ".join(out))
