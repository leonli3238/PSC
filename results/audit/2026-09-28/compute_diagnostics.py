"""Offline diagnostics; run from repository root:

PYTHONPATH=. .venv/bin/python results/audit/2026-09-28/compute_diagnostics.py

Reads the existing pilot and writes only this audit directory. No LLM calls.
"""

import json
import math
from pathlib import Path

import numpy as np

from psc.experiments import DATASETS, PAPER_TABLE2
from psc.graph import load_dataset
from psc.ground_truth import gt_psc, relative_error

OUT = Path('results/audit/2026-09-28')
OUT.mkdir(parents=True, exist_ok=True)
pilot = json.loads(Path('results/pilot/hy3-ioa_r3_v2/runs.json').read_text())
distribution = []
for dataset in ('CU', 'Do'):
    records = load_dataset('data', dataset)
    for task in ('degree', '2-star', '3-star', 'triangle'):
        graph = records[task].graph()
        traces = [gt_psc(graph, task, 2, np.random.default_rng([9131, i]), return_trace=True) for i in range(5000)]
        errors = np.array([relative_error(t.result, graph.ground_truth(task), graph.n) for t in traces])
        divisor = graph.n if task == 'degree' else 3 if task == 'triangle' else 1
        pilot_errors = [relative_error(r['extra']['validation']['rule_estimate'], r['truth'], graph.n) for r in pilot if (r['dataset'], r['task'], r['method']) == (dataset, task, 'PSC')]
        three_run_means = np.random.default_rng(119).choice(errors, size=(50000, 3)).mean(axis=1)
        row = {
            'dataset': dataset, 'task': task, 'runs': 5000,
            'seed_recipe': 'default_rng([9131, i]), i=0..4999',
            'mean_re': float(errors.mean()),
            'se_re': float(errors.std(ddof=1) / np.sqrt(len(errors))),
            'mean_raw_aggregate': float(np.mean([sum(t.raw_counts) / divisor for t in traces])),
            'zero_output_rate': float(np.mean([t.result == 0 for t in traces])),
            'pilot_paired_rule_re': float(np.mean(pilot_errors)),
            'three_run_mean_interval_95': np.quantile(three_run_means, [.025, .975]).tolist(),
            'pilot_percentile': float(np.mean(three_run_means <= np.mean(pilot_errors))),
            'resampling_note': 'Empirical distribution of means of 3 independent draws; bootstrap over 5000 code runs, 50000 groups, RNG seed 119. Not a CI for paper results.',
        }
        distribution.append(row)
        print(dataset, task, round(row['mean_re'], 6), flush=True)

rounding = []
for dataset in DATASETS:
    graph = load_dataset('data', dataset)['2-star'].graph()
    degrees = np.array(graph.degrees())
    rng = np.random.default_rng(94714)
    noisy_max = np.max(degrees[None, :] + rng.laplace(0, 2.5, size=(10000, graph.n)), axis=1)
    noise_sum = rng.laplace(size=(10000, graph.n)).sum(axis=1)
    for k in (2, 3):
        truth = graph.ground_truth(f'{k}-star')
        row = {'dataset': dataset, 'task': f'{k}-star', 'runs': 10000, 'seed': 94714, 'eps2': .4, 'eps3': 1.6, 'paper_gt_re': PAPER_TABLE2[f'{k}-star']['GT-PSC'][DATASETS.index(dataset)]}
        for name, operation in [('ceil', np.ceil), ('floor', np.floor)]:
            degree_bound = np.maximum(1, operation(noisy_max))
            clipped = np.minimum(degrees[None, :], degree_bound[:, None])
            raw = (clipped * (clipped - 1) / 2 if k == 2 else clipped * (clipped - 1) * (clipped - 2) / 6).sum(axis=1)
            sensitivity = degree_bound if k == 2 else degree_bound * (degree_bound - 1) / 2
            estimates = np.maximum(0, raw + sensitivity * noise_sum / 1.6)
            row[name + '_mean_re'] = float(np.abs(estimates - truth).mean() / truth)
        row['note'] = 'Paired analytic count simulation: k-star local count depends only on clipped degree; independent of which neighbors are retained. Diagnostic only; no production change.'
        rounding.append(row)

graph = load_dataset('data', 'EE')['triangle'].graph()
traces = [gt_psc(graph, 'triangle', 2, np.random.default_rng([9131, i]), return_trace=True) for i in range(5000)]
errors = np.array([relative_error(t.result, graph.ground_truth('triangle'), graph.n) for t in traces])
ee = {'dataset': 'EE', 'task': 'triangle', 'runs': 5000, 'seed_recipe': 'default_rng([9131, i])', 'mean_re': float(errors.mean()), 'se_re': float(errors.std(ddof=1) / math.sqrt(5000)), 'paper_gt_re': PAPER_TABLE2['triangle']['GT-PSC'][DATASETS.index('EE')], 'mean_raw_aggregate': float(np.mean([sum(t.raw_counts) / 3 for t in traces])), 'truth': graph.ground_truth('triangle')}
(OUT / 'ee_triangle_check.json').write_text(json.dumps(ee, indent=2) + '\n')
result = {'distribution_checks': distribution, 'rounding_ablation': rounding, 'ee_triangle_check': ee}
(OUT / 'diagnostics.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print('saved', OUT / 'diagnostics.json')
