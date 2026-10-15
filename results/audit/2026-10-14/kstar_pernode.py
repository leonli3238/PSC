"""k-uniform per-node thresholds (same rule for 2-star and 3-star):
D_i = min(D, floor(y_i + m/eps2)), report C(min(d_i,D_i),k) + Lap(C(D_i-1,k-1)/eps3).
m=inf is current floor_tight. Prints ours/paper RE ratio per dataset."""
import math, sys, numpy as np
sys.path.insert(0, '.')
from psc.graph import load_dataset
PAPER = {2: [.1062,.0585,.0444,.1210,.0295,.0284], 3: [.8035,.3434,.2077,.5410,.1647,.1290]}
DS = ('CU','Do','ML','CS','EE','PM'); eps2, eps3, Rn = .4, 1.6, 20000
def cnt(x, k): return x*(x-1)/2 if k == 2 else x*(x-1)*(x-2)/6
rng = np.random.default_rng(3)
data = {}
for ds in DS:
    g = load_dataset('data', ds)['2-star'].graph(); n = g.n
    d = np.array([len(g.adj[v]) for v in range(n)], float)
    y = d + rng.laplace(0, 1/eps2, (Rn, n))
    D = np.floor(np.clip(y.max(1), 0, n-1))[:, None]
    data[ds] = (d, y, D, rng.laplace(0, 1, (Rn, n)))
print("margin m |" + "".join(f" {ds:>11}" for ds in DS) + " |   avg2   avg3   (ratio ours/paper: 2-star/3-star)")
for m in (math.inf, 10, 6, 4, 3, 2, 1, 0):
    row, avg = [], {2: [], 3: []}
    for i, ds in enumerate(DS):
        d, y, D, L = data[ds]
        Di = D if math.isinf(m) else np.minimum(D, np.maximum(0, np.floor(y + m/eps2)))
        r = {}
        for k in (2, 3):
            T = cnt(d, k).sum()
            A = cnt(np.minimum(d[None, :], Di), k).sum(1)
            gsi = np.maximum(Di-1, 0) if k == 2 else np.maximum(Di-1, 0)*np.maximum(Di-2, 0)/2
            est = np.maximum(0, A + (gsi/eps3*L).sum(1))
            r[k] = (np.abs(est-T)/T).mean(); avg[k].append(r[k])
        row.append(f" {r[2]/PAPER[2][i]:.2f}/{r[3]/PAPER[3][i]:.2f}")
    print(f"{m:>8} |" + "".join(row) + f" | {np.mean(avg[2]):.4f} {np.mean(avg[3]):.4f}")
print("paper avg                                                                            0.0647 0.3649")
