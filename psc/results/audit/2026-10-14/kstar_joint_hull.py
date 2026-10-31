"""Joint feasibility test: can ONE k-uniform common-D mechanism produce the paper's
(2-star, 3-star) pair on the same graph?  Family: any distribution of a shared integer
threshold D (independent of report noise), any eps3 <= 2, GS tight C(D-1,k-1) or bound
C(D,k-1), local clipping on or off, iid per-node Laplace, sum, final clamp.
A random D makes the pair a mixture of fixed-D pairs, so the achievable set is the
convex hull of {(RE3(D), RE2(D))}."""
import math, runpy, sys
import numpy as np
sys.path.insert(0, '.')
from psc.graph import load_dataset
R = runpy.run_path('results/research/2026-09-28-author-implementation/research_mechanism.py')
exact_re, count, PAPER, DATASETS = R['exact_re'], R['count'], R['PAPER'], R['DATASETS']

def hull(pts):
    pts = sorted(set(map(tuple, pts)))
    def cross(o, a, b): return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
    lo = []
    for p in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0: lo.pop()
        lo.append(p)
    return lo  # lower hull, x ascending

def lower_at(lo, x):
    if x < lo[0][0] or x > lo[-1][0]: return math.inf
    for a, b in zip(lo, lo[1:]):
        if a[0] <= x <= b[0]:
            return a[1] if b[0] == a[0] else a[1] + (b[1]-a[1])*(x-a[0])/(b[0]-a[0])
    return lo[-1][1]

def gs(D, k, mode):
    return np.array([math.comb(max(0, int(d)-(mode == 'tight')), k-1) for d in D], float)

print("ds   paper(RE2,RE3)   min RE2 reachable at paper RE3 (best config)   ratio")
for idx, ds in enumerate(DATASETS):
    g = load_dataset('data', ds)['2-star'].graph(); n = g.n
    d = np.array([len(g.adj[i]) for i in range(n)], float)
    T = {k: count(d, k).sum() for k in (2, 3)}
    Ds = np.arange(1, n)
    best = (math.inf, None)
    for e3 in np.linspace(0.1, 2.0, 39):
        for mode in ('tight', 'bound'):
            for clip in (True,):
                re = {}
                for k in (2, 3):
                    A = np.array([count(np.minimum(d, D) if clip else d, k).sum() for D in Ds])
                    re[k] = exact_re(A, T[k], gs(Ds, k, mode)/e3, n)
                y = lower_at(hull(np.c_[re[3], re[2]]), PAPER[3][idx])
                if y < best[0]: best = (y, (round(float(e3), 2), mode, clip))
    print(f"{ds}  ({PAPER[2][idx]:.4f}, {PAPER[3][idx]:.4f})   {best[0]:.4f}  eps3={best[1][0]} {best[1][1]} clip={best[1][2]}   {best[0]/PAPER[2][idx]:.2f}x")
