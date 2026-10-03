"""Invert the paper GT-PSC k-star numbers against candidate mechanisms.

Run: .venv/bin/python results/audit/2026-10-02/kstar_gap_inversion.py
For every candidate, ``alpha`` is the multiplier on the report Laplace scale
that makes the simulated mean RE equal the paper point. A mechanism that
matches the paper for both 2-star and 3-star needs alpha close to 1 for both.
All candidates share the same standard Laplace draws.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from psc.graph import load_dataset

OUT = Path(__file__).with_suffix('.json')
N = 20000
SEED = 1022026
EPS = 2.0
DATASETS = ('CU', 'Do', 'ML', 'CS', 'EE', 'PM')
PAPER = {
    2: dict(zip(DATASETS, (.1062, .0585, .0444, .1210, .0295, .0284))),
    3: dict(zip(DATASETS, (.8035, .3434, .2077, .5410, .1647, .1290))),
}


def comb(d, k):
    d = np.asarray(d, dtype=float)
    if k == 1:
        return np.maximum(d, 0)
    if k == 2:
        return np.maximum(d * (d - 1) / 2, 0)
    return np.maximum(d * (d - 1) * (d - 2) / 6, 0)


def candidates(n, dmax):
    """name -> (eps2, eps3, bound(raw_max) -> (D_proj, D_gs), gs(D_gs, k))."""
    floor_cap = lambda m: (np.floor(np.clip(m, 0, n - 1)), np.floor(np.clip(m, 0, n - 1)))
    tight = lambda D, k: comb(D - 1, k - 1)
    bound = lambda D, k: comb(D, k - 1)
    oracle = lambda m: (np.full_like(m, dmax), np.full_like(m, dmax))
    upstream = lambda m: (np.floor(np.clip(m, 0, n - 1)), np.clip(m, 0, n - 1))
    return {
        'floor_tight (current)': (0.4, 1.6, floor_cap, tight, 'max'),
        'floor_tight, eps3=2 (eps2 not deducted)': (0.4, 2.0, floor_cap, tight, 'max'),
        'oracle D=true max, tight, eps3=1.6': (0.4, 1.6, oracle, tight, 'max'),
        'oracle D=true max, C(D,k-1), eps3=2 (upstream NSType=1)': (0.0, 2.0, oracle, bound, 'max'),
        'upstream NSType=2: eps2=eps/10, continuous GS': (0.2, 1.8, upstream, bound, 'max'),
        'central noisy max: true max + one Lap, tight': (0.4, 1.6, floor_cap, tight, 'central'),
    }


def simulate(degrees, k, eps2, eps3, bound_fn, gs_fn, max_mode, z_deg, z_rep_sum):
    n = degrees.size
    truth = comb(degrees, k).sum()
    if eps2 > 0:
        if max_mode == 'central':
            raw = degrees.max() + z_deg[:, 0] / eps2
        else:
            raw = (degrees[None, :] + z_deg / eps2).max(axis=1)
    else:
        raw = np.full(z_deg.shape[0], float(degrees.max()))
    d_proj, d_gs = bound_fn(raw)
    counts = comb(np.minimum(degrees[None, :], d_proj[:, None]), k).sum(axis=1)
    base_noise = gs_fn(d_gs, k) / eps3 * z_rep_sum
    eta = 0.001 * n
    return counts, base_noise, truth, max(truth, eta)


def mean_re(counts, base_noise, truth, denom, alpha):
    est = np.maximum(0.0, counts + alpha * base_noise)
    return float(np.mean(np.abs(est - truth)) / denom)


def solve_alpha(counts, base_noise, truth, denom, target):
    lo, hi = 1e-3, 50.0
    if mean_re(counts, base_noise, truth, denom, lo) > target:
        return None
    for _ in range(60):
        mid = math.sqrt(lo * hi)
        if mean_re(counts, base_noise, truth, denom, mid) < target:
            lo = mid
        else:
            hi = mid
    return math.sqrt(lo * hi)


rows = []
for di, ds in enumerate(DATASETS):
    graph = load_dataset(ROOT / 'data', ds)['2-star'].graph()
    degrees = np.array(graph.degrees(), dtype=float)
    n = degrees.size
    rng = np.random.default_rng([SEED, di])
    z_deg = rng.laplace(0, 1, (N, n))
    z_rep_sum = rng.laplace(0, 1, (N, n)).sum(axis=1)
    for name, (eps2, eps3, bfn, gfn, mode) in candidates(n, degrees.max()).items():
        for k in (2, 3):
            c, b, t, den = simulate(degrees, k, eps2, eps3, bfn, gfn, mode, z_deg, z_rep_sum)
            re = mean_re(c, b, t, den, 1.0)
            alpha = solve_alpha(c, b, t, den, PAPER[k][ds])
            rows.append({'dataset': ds, 'k': k, 'candidate': name, 'mean_re': re,
                         'paper': PAPER[k][ds], 'alpha': alpha})

OUT.write_text(json.dumps({'runs': N, 'seed': SEED, 'rows': rows}, indent=1))

names = list(dict.fromkeys(r['candidate'] for r in rows))
for name in names:
    print(f'\n## {name}')
    print('| k | ' + ' | '.join(DATASETS) + ' | mean |')
    for k in (2, 3):
        sel = [r for r in rows if r['candidate'] == name and r['k'] == k]
        res = [r['mean_re'] for r in sel]
        al = [r['alpha'] for r in sel]
        print(f'| {k}-star RE | ' + ' | '.join(f'{x:.4f}' for x in res) + f' | {np.mean(res):.4f} |')
        print(f'| {k}-star alpha | ' + ' | '.join('n/a' if a is None else f'{a:.3f}' for a in al)
              + f" | {np.mean([a for a in al if a is not None]):.3f} |")
