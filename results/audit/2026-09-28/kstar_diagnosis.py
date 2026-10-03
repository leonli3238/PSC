"""Independent k-star mechanism diagnostics, without API calls or source changes.

Run: .venv/bin/python results/audit/2026-09-28/kstar_diagnosis.py
The independent simulator uses degree vectors, not production count/GS rules.
Variants share standard degree/report Laplace draws. Diagnostic variants are
explicitly separated from the production mechanism; they do not reproduce an
unavailable author implementation or establish an end-to-end privacy proof.
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from psc.graph import load_dataset
from psc.ground_truth import gt_psc

OUT = Path(__file__).with_suffix('.json')
N = 50000
SEED = 9282026
DATASETS = ('CU', 'Do', 'ML', 'CS', 'EE', 'PM')
PAPER = {
    2: (.1062, .0585, .0444, .1210, .0295, .0284),
    3: (.8035, .3434, .2077, .5410, .1647, .1290),
}


def choose(d, k):
    if k == 2:
        return d * (d - 1) / 2
    return d * (d - 1) * (d - 2) / 6


def sample_stats(a):
    return {
        'mean': float(a.mean()),
        'se': float(a.std(ddof=1) / math.sqrt(a.size)),
    }


# Cross-check the closed form against existing production traces, including
# actually clipped degrees. This does not claim the production GS is optimal.
validation = []
for dataset in DATASETS:
    records = load_dataset(ROOT / 'data', dataset)
    for k in (2, 3):
        graph = records[f'{k}-star'].graph()
        d = np.array(graph.degrees())
        max_diff = 0.0
        clipped_cases = 0
        for i in range(100):
            t = gt_psc(graph, f'{k}-star', 2, np.random.default_rng([SEED, i]), return_trace=True)
            expected_raw = choose(np.minimum(d, t.d_hat_max), k)
            assert np.array_equal(expected_raw, t.raw_counts)
            expected_gs = t.d_hat_max if k == 2 else t.d_hat_max * (t.d_hat_max - 1) / 2
            assert expected_gs == t.sensitivity
            assert t.split.as_tuple() == (0.0, 0.4, 1.6)
            noise = np.array(t.noisy_counts) - np.array(t.raw_counts)
            estimate = max(0.0, float(expected_raw.sum() + noise.sum()))
            max_diff = max(max_diff, abs(estimate - t.result))
            clipped_cases += t.d_hat_max < d.max()
            assert math.isclose(estimate, t.result, rel_tol=1e-12, abs_tol=1e-8)
        validation.append({'dataset': dataset, 'k': k, 'checks': 100,
                           'clipped_cases': int(clipped_cases), 'max_abs_result_difference': max_diff})

rows = []
degree_rows = []
for dataset_index, dataset in enumerate(DATASETS):
    graph = load_dataset(ROOT / 'data', dataset)['2-star'].graph()
    degrees = np.array(graph.degrees())
    rng = np.random.default_rng([SEED, dataset_index])
    samples = {}
    degree_samples = []
    # Each variant is (name, epsilon2, round down, tighter GS, project, oracle).
    variants = [
        ('current', .4, False, False, True, False),
        ('floor', .4, True, False, True, False),
        ('tight_gs', .4, False, True, True, False),
        ('floor_and_tight_gs', .4, True, True, True, False),
        ('no_projection_diagnostic', .4, False, False, False, False),
        ('true_max_diagnostic', .4, False, False, True, True),
    ]
    variants.extend((f'eps2_{e2:.1f}', e2, False, False, True, False)
                    for e2 in (.2, .6, .8, 1.0, 1.2))
    for offset in range(0, N, 2048):
        size = min(2048, N - offset)
        degree_z = rng.laplace(size=(size, graph.n))
        report_z = rng.laplace(size=(size, graph.n)).sum(axis=1)
        for name, eps2, floor, tight, project, oracle in variants:
            if oracle:
                D = np.full(size, degrees.max())
            else:
                maxima = (degrees[None, :] + degree_z / eps2).max(axis=1)
                D = np.maximum(1, np.floor(maxima) if floor else np.ceil(maxima))
            if name == 'current':
                degree_samples.append(D)
            used_degrees = np.minimum(degrees[None, :], D[:, None]) if project else np.broadcast_to(degrees, (size, graph.n))
            for k in (2, 3):
                truth = float(choose(degrees, k).sum())
                raw = choose(used_degrees, k).sum(axis=1)
                g = np.maximum(0, D - 1) if tight else D
                gs = g if k == 2 else g * (g - 1) / 2
                b = gs / (2 - eps2)
                before = raw + b * report_z
                estimate = np.maximum(0, before)
                data = np.column_stack((
                    np.abs(estimate - truth) / truth,
                    (truth - raw) / truth,
                    np.abs(b * report_z) / truth,
                    before <= 0,
                    np.abs(before - truth) / truth,
                    b,
                    estimate,
                ))
                samples.setdefault((k, name), []).append(data)
    D = np.concatenate(degree_samples)
    degree_rows.append({
        'dataset': dataset, 'n': graph.n, 'm': graph.m,
        'true_max_degree': int(degrees.max()),
        'mean_D': float(D.mean()), 'D_quantiles_5_50_95': np.quantile(D, [.05, .5, .95]).tolist(),
        'fraction_D_below_true_max': float(np.mean(D < degrees.max())),
        'fraction_D_above_n_minus_1': float(np.mean(D > graph.n - 1)),
    })
    baseline = {k: np.concatenate(samples[(k, 'current')]) for k in (2, 3)}
    for (k, name), chunks in samples.items():
        a = np.concatenate(chunks)
        rows.append({
            'dataset': dataset, 'k': k, 'variant': name,
            'truth': float(choose(degrees, k).sum()),
            'paper_gt_re': PAPER[k][dataset_index],
            'relative_error': sample_stats(a[:, 0]),
            'paired_re_change_vs_current': sample_stats(a[:, 0] - baseline[k][:, 0]),
            'mean_projection_loss_relative_to_truth': float(a[:, 1].mean()),
            'mean_abs_reporting_noise_relative_to_truth': float(a[:, 2].mean()),
            'zero_output_fraction': float(a[:, 3].mean()),
            'mean_re_before_nonnegative_clamp': float(a[:, 4].mean()),
            'mean_report_scale': float(a[:, 5].mean()),
            'mean_estimate': float(a[:, 6].mean()),
        })
    print(dataset, 'D mean', round(D.mean(), 3), 'RE',
          [round(baseline[k][:, 0].mean(), 6) for k in (2, 3)], flush=True)

result = {
    'runs_per_dataset': N, 'seed': SEED,
    'sampling': 'default_rng([seed,dataset_index]); chunks of 2048; independent standard Laplace degree/report matrices shared across variants and k',
    'notes': [
        'No API calls; no production source, config or existing results changed.',
        'No-projection and true-max variants are diagnostic counterfactuals, not certified private replacements.',
        'Tight GS is the single-bit sensitivity C(D-1,k-1) of the ideal function C(min(d,D),k), for fixed public D.',
        'All budget variants preserve epsilon2+epsilon3=2; epsilon1=0.',
        'Separate projection/noise magnitudes are not additive relative errors.',
        'Paper provides point estimates; local standard errors do not give confidence intervals for paper values.',
    ],
    'source_sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                      for p in [ROOT / 'psc/dp.py', ROOT / 'psc/ground_truth.py',
                                ROOT / 'psc/library.py', ROOT / 'psc/rules.py',
                                *(ROOT / 'data' / f'{d}.json' for d in DATASETS)]},
    'production_closed_form_checks': validation,
    'degree_diagnostics': degree_rows,
    'ablation': rows,
}
OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print('Saved', OUT)
