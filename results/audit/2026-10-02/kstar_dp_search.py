"""Search DP-valid k-star mechanisms whose GT error approximates the paper.

Run: .venv/bin/python results/audit/2026-10-02/kstar_dp_search.py

Every candidate is a two-round edge-LDP protocol with total budget eps=2:
  round 1 (eps2 = r2*eps): node i publishes y_i = d_i + Lap(1/eps2)
  public post-processing of all y:
      M   = clip(max_i y_i, 0, n-1)
      D   = max(1, floor(M - delta/eps2))                 (global threshold)
      D_i = min(D, max(0, floor(y_i + c/eps2)))           (c = inf -> D_i = D)
  round 2 (eps3 = eps - eps2): node i publishes
      z_i = C(min(d_i, D_i), k) + Lap(C(D_i - 1, k - 1) / eps3)
  estimator A = sum_i z_i
  estimator B = sum_i p_k(y_i)   (unbiased Laplace-moment polynomial, free reuse of round 1)
  combine: est = w A + (1-w) B, w = vB / (vA + vB) from public plug-in variances
           (combine off -> est = A); final est = max(0, est)

For fixed D_i, |C(min(d+1,D_i),k) - C(min(d,D_i),k)| <= C(D_i-1,k-1), so round 2 is
eps3-edge-LDP; D_i depends only on published y, so sequential composition gives
eps2 + eps3 = eps. B and the weights are post-processing. The configuration
(r2, delta, c, combine) is shared by both tasks and all datasets.
"""

from __future__ import annotations

import itertools
import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from psc.graph import load_dataset

OUT = Path(__file__).with_suffix('.json')
EPS = 2.0
DATASETS = ('CU', 'Do', 'ML', 'CS', 'EE', 'PM')
PAPER = {
    2: dict(zip(DATASETS, (.1062, .0585, .0444, .1210, .0295, .0284))),
    3: dict(zip(DATASETS, (.8035, .3434, .2077, .5410, .1647, .1290))),
}
TUNE_SEED, TUNE_RUNS = 20261002, 3000
VALID_SEED, VALID_RUNS = 77001, 20000


def comb(d, k):
    d = np.asarray(d, dtype=float)
    if k == 1:
        return np.maximum(d, 0.0)
    if k == 2:
        return np.maximum(d * (d - 1) / 2, 0.0)
    return np.maximum(d * (d - 1) * (d - 2) / 6, 0.0)


def poly_estimate(y, k, b):
    if k == 2:
        return y * (y - 1) / 2 - b * b
    return y * (y - 1) * (y - 2) / 6 - b * b * (y - 1)


def poly_variance(d, k, b):
    """Var[p_k(d + L)], L ~ Lap(b), closed form from Laplace moments."""
    if k == 2:
        return 2 * b**2 * (d - 0.5) ** 2 + 5 * b**4
    a1 = (3 * d**2 - 6 * d + 2) / 6 - b**2
    a2 = (d - 1) / 2
    a3 = 1 / 6
    return 2 * b**2 * a1**2 + 48 * a1 * a3 * b**4 + 20 * a2**2 * b**4 + 720 * a3**2 * b**6


class Data:
    def __init__(self, name, seed, runs):
        g = load_dataset(ROOT / 'data', name)['2-star'].graph()
        self.name = name
        self.d = np.array(g.degrees(), dtype=float)
        self.n = self.d.size
        rng = np.random.default_rng([seed, DATASETS.index(name)])
        self.zdeg = rng.laplace(0, 1, (runs, self.n))
        self.zrep = rng.laplace(0, 1, (runs, self.n))
        self.truth = {k: float(comb(self.d, k).sum()) for k in (2, 3)}


def run(data: Data, k, r2, delta, c, combine):
    eps2 = r2 * EPS
    eps3 = EPS - eps2
    b = 1 / eps2
    d, n = data.d, data.n
    y = d[None, :] + b * data.zdeg
    m = np.clip(y.max(axis=1), 0, n - 1)
    D = np.maximum(1.0, np.floor(m - delta * b))[:, None]
    if math.isinf(c):
        Di = np.broadcast_to(D, y.shape)
    else:
        Di = np.minimum(D, np.maximum(0.0, np.floor(y + c * b)))
    gs = comb(Di - 1, k - 1)
    scale = gs / eps3
    est_a = (comb(np.minimum(d[None, :], Di), k) + scale * data.zrep).sum(axis=1)
    if combine:
        est_b = poly_estimate(y, k, b).sum(axis=1)
        va = (2 * scale**2).sum(axis=1)
        vb = poly_variance(np.clip(y, 0, n - 1), k, b).sum(axis=1)
        w = vb / (va + vb)
        est = w * est_a + (1 - w) * est_b
    else:
        est = est_a
    est = np.maximum(0.0, est)
    t = data.truth[k]
    re = np.abs(est - t) / max(t, 0.001 * n)
    return float(re.mean()), float(re.std(ddof=1) / math.sqrt(re.size))


def evaluate(datas, cfg, tasks=(2, 3)):
    """``cfg`` is one shared tuple, or a dict {k: tuple} for per-task mechanisms."""
    per_task = cfg if isinstance(cfg, dict) else {k: cfg for k in tasks}
    cells = {}
    for data in datas:
        for k in tasks:
            cells[(data.name, k)] = run(data, k, *per_task[k])
    gaps = [math.log(cells[(ds, k)][0] / PAPER[k][ds]) for ds in DATASETS for k in tasks]
    return cells, float(np.mean(np.abs(gaps))), float(np.max(np.abs(gaps)))


GRID = {
    'r2': (0.1, 0.15, 0.2, 0.3, 0.4),
    'delta': (-1.0, 0.0, 0.5, 1.0, 1.5, 2.0, 3.0),
    'c': (math.inf, 1.0, 2.0, 3.0, 5.0, 8.0),
    'combine': (False, True),
}
REFERENCE = {
    'floor_tight (current default)': (0.2, 0.0, math.inf, False),
}


TASK_GRID = {
    'r2': (0.1, 0.15, 0.2, 0.25, 0.3, 0.4, 0.5),
    'delta': (-1.0, 0.0, 0.5, 1.0, 1.5, 2.0, 3.0),
    'c': (math.inf, 0.0, 0.5, 1.0, 2.0, 3.0, 5.0, 8.0, 12.0),
    'combine': (False, True),
}


def cfg_name(cfg):
    if isinstance(cfg, dict):
        return '; '.join(f'{k}-star: {cfg_name(v)}' for k, v in sorted(cfg.items()))
    r2, delta, c, combine = cfg
    return f"r2={r2}, delta={delta}, c={'inf' if math.isinf(c) else c}, combine={'on' if combine else 'off'}"


def main():
    tune = [Data(ds, TUNE_SEED, TUNE_RUNS) for ds in DATASETS]
    results = []
    for cfg in itertools.product(*GRID.values()):
        _, mean_gap, max_gap = evaluate(tune, cfg)
        results.append((mean_gap, max_gap, cfg))
    results.sort(key=lambda x: x[0])
    by_max = sorted(results, key=lambda x: x[1])

    per_task = {}
    for k in (2, 3):
        scored = []
        for cfg in itertools.product(*TASK_GRID.values()):
            _, mean_gap, max_gap = evaluate(tune, cfg, tasks=(k,))
            scored.append((mean_gap, max_gap, cfg))
        scored.sort(key=lambda x: x[0])
        per_task[k] = scored
        print(f'{k}-star top 8 on tuning seeds:')
        for g, mg, c in scored[:8]:
            print(f'  {g:.3f}  max {mg:.3f}  {cfg_name(c)}')

    picks = {
        'per-task best (tuning)': {k: per_task[k][0][2] for k in (2, 3)},
        'per-task: 2-star best, 3-star current': {2: per_task[2][0][2], 3: REFERENCE['floor_tight (current default)']},
        'best mean |log gap| (tuning)': results[0][2],
        'best max |log gap| (tuning)': by_max[0][2],
    }
    # Best member of each structural sub-family, to attribute what each component buys.
    for label, pred in {
        'best global-threshold only (c=inf, combine off)': lambda c: math.isinf(c[2]) and not c[3],
        'best with combine only (c=inf)': lambda c: math.isinf(c[2]) and c[3],
        'best per-node threshold only (combine off)': lambda c: not math.isinf(c[2]) and not c[3],
    }.items():
        picks[label] = next(r[2] for r in results if pred(r[2]))
    picks.update(REFERENCE)

    valid = [Data(ds, VALID_SEED, VALID_RUNS) for ds in DATASETS]
    report = {'tuning': {'seed': TUNE_SEED, 'runs': TUNE_RUNS, 'grid_size': len(results),
                         'top10': [{'cfg': cfg_name(c), 'mean_log_gap': g, 'max_log_gap': mg}
                                   for g, mg, c in results[:10]],
                         'per_task_top10': {f'{k}-star': [{'cfg': cfg_name(c), 'mean_log_gap': g, 'max_log_gap': mg}
                                                          for g, mg, c in per_task[k][:10]] for k in (2, 3)}},
              'validation': {'seed': VALID_SEED, 'runs': VALID_RUNS, 'picks': {}}}
    for label, cfg in picks.items():
        cells, mean_gap, max_gap = evaluate(valid, cfg)
        report['validation']['picks'][label] = {
            'cfg': cfg_name(cfg), 'mean_log_gap': mean_gap, 'max_log_gap': max_gap,
            'cells': {f'{ds}/{k}-star': {'re': cells[(ds, k)][0], 'se': cells[(ds, k)][1],
                                          'paper': PAPER[k][ds]}
                      for ds in DATASETS for k in (2, 3)},
        }
        print(f'\n## {label}: {cfg_name(cfg)}  mean|log gap|={mean_gap:.3f} max={max_gap:.3f}')
        print('| task | ' + ' | '.join(DATASETS) + ' | avg |')
        for k in (2, 3):
            res = [cells[(ds, k)][0] for ds in DATASETS]
            pap = [PAPER[k][ds] for ds in DATASETS]
            print(f'| {k}-star | ' + ' | '.join(f'{r:.4f} ({r / p - 1:+.0%})' for r, p in zip(res, pap))
                  + f' | {np.mean(res):.4f} vs {np.mean(pap):.4f} |')
    print('\nTop 10 on tuning seeds:')
    for g, mg, c in results[:10]:
        print(f'  {g:.3f}  max {mg:.3f}  {cfg_name(c)}')
    OUT.write_text(json.dumps(report, indent=1))


if __name__ == '__main__':
    main()
