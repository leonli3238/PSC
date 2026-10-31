"""Fresh-seed validation and knob sensitivity for the 2-star candidates.

Run: .venv/bin/python results/audit/2026-10-02/kstar_dp_validate.py
Uses the same mechanism family as kstar_dp_search.py, on seeds never used for
selection. 3-star stays on floor_tight (r2=0.2, delta=0, c=inf, combine off).
"""

from __future__ import annotations

import json
import math

import numpy as np

from kstar_dp_search import DATASETS, PAPER, Data, cfg_name, evaluate

SEED, RUNS = 99017, 20000
CANDIDATES = [
    (0.2, 0.0, math.inf, False),   # floor_tight
    (0.2, 1.0, 3.0, True),         # tuning best
    (0.3, 1.5, 2.0, True),
    (0.2, 0.0, 2.0, True),         # only per-node threshold + combine
    (0.2, 1.0, 3.0, False),
    (0.25, 1.0, 2.0, True),
    (0.4, 1.5, 2.0, False),
]
SENSITIVITY_C = (1.0, 2.0, 3.0, 4.0, 5.0, 8.0, math.inf)


def main():
    datas = [Data(ds, SEED, RUNS) for ds in DATASETS]
    out = {'seed': SEED, 'runs': RUNS, 'candidates': [], 'c_sensitivity': []}
    print('| 2-star config | ' + ' | '.join(DATASETS) + ' | mean abs log gap | max |')
    print('|---|' + '---|' * (len(DATASETS) + 2))
    for cfg in CANDIDATES:
        cells, g, mg = evaluate(datas, cfg, tasks=(2,))
        out['candidates'].append({'cfg': cfg_name(cfg), 'mean_log_gap': g, 'max_log_gap': mg,
                                  'cells': {ds: cells[(ds, 2)] for ds in DATASETS}})
        print(f'| {cfg_name(cfg)} | ' + ' | '.join(
            f'{cells[(ds, 2)][0]:.4f} ({cells[(ds, 2)][0] / PAPER[2][ds] - 1:+.0%})' for ds in DATASETS)
            + f' | {g:.3f} | {mg:.3f} |')
    print('\nc sensitivity at r2=0.2, delta=1.0, combine on:')
    for c in SENSITIVITY_C:
        cfg = (0.2, 1.0, c, True)
        cells, g, mg = evaluate(datas, cfg, tasks=(2,))
        out['c_sensitivity'].append({'c': None if math.isinf(c) else c, 'mean_log_gap': g, 'max_log_gap': mg,
                                     'cells': {ds: cells[(ds, 2)][0] for ds in DATASETS}})
        print(f'  c={c}: ' + ', '.join(f'{ds} {cells[(ds, 2)][0] / PAPER[2][ds] - 1:+.0%}' for ds in DATASETS)
              + f'  mean|log gap|={g:.3f}')
    with open(__file__.replace('.py', '.json'), 'w') as f:
        json.dump(out, f, indent=1)


if __name__ == '__main__':
    main()
