"""Paired degree-vector evaluation of the k-star mechanism candidates.

Neighbor selection cannot change k-star counts after degree clipping. This
evaluator therefore avoids materializing projected graphs. Profiles share
standard Laplace draws; production consumes additional RNG for neighbor
selection, so equality is distributional, not equality by production seed.
"""
from __future__ import annotations

from typing import Callable, Sequence

import numpy as np

from .graph import load_dataset
from .mechanism import MECHANISMS, get_mechanism


def compare_profiles(
    data: str, datasets: Sequence[str], runs: int, seed: int,
    profiles: Sequence[str] = MECHANISMS, eps: float = 2.0,
    log: Callable[[str], None] = print,
) -> tuple[list[dict], list[dict]]:
    from .experiments import error_statistics, paper_value

    if runs < 2 or eps <= 0:
        raise ValueError("comparison requires runs >= 2 and positive epsilon")
    rows = []
    for dataset_index, ds in enumerate(datasets):
        graph = load_dataset(data, ds)["2-star"].graph()
        degree = np.array(graph.degrees(), dtype=float)
        rng = np.random.default_rng([seed, dataset_index])
        estimates = {(p, k, opt): [] for p in profiles for k in (2, 3) for opt in (False, True)}
        for offset in range(0, runs, 1024):
            size = min(1024, runs - offset)
            noisy = degree[None, :] + rng.laplace(0, 1 / (.2 * eps), size=(size, graph.n))
            report = rng.laplace(size=(size, graph.n))
            report_sum = report.sum(axis=1)
            for profile_name in profiles:
                profile = get_mechanism(profile_name)
                # Shared production parameter policy, independent polynomial counts.
                bounds = [profile.degree_bound(v.tolist(), "2-star") for v in noisy]
                D = np.array([b.projection_degree for b in bounds])
                for optimized in (False, True):
                    for k in (2, 3):
                        node_D = (profile.node_projection_degrees(noisy, D[:, None], f"{k}-star", .2 * eps)
                                  if optimized else None)
                        if node_D is not None:
                            used = np.minimum(degree[None, :], node_D)
                        else:
                            used = np.minimum(degree[None, :], D[:, None]) if optimized else degree[None, :]
                        raw = (used * (used - 1) / 2 if k == 2 else used * (used - 1) * (used - 2) / 6).sum(axis=1)
                        eps3 = .8 * eps if optimized else eps
                        if node_D is not None:
                            node_gs = np.vectorize(lambda d: profile.kstar_sensitivity(k, graph.n, int(d)))(node_D)
                            noise = (node_gs / eps3 * report).sum(axis=1)
                        else:
                            if optimized:
                                gs = np.array([profile.kstar_sensitivity(k, graph.n, b.projection_degree, b.sensitivity_degree) for b in bounds])
                            else:
                                gs = profile.kstar_sensitivity(k, graph.n, None)
                            noise = gs / eps3 * report_sum
                        values = np.maximum(0, raw + noise)
                        estimates[(profile_name, k, optimized)].append(values)
        for (profile, k, optimized), chunks in estimates.items():
            values = np.concatenate(chunks)
            method, task = "GT-PSC" if optimized else "GT-PSC-B", f"{k}-star"
            truth = graph.ground_truth(task)
            paper = paper_value(task, method, ds) if eps == 2 else None
            rows.append({
                "mechanism": profile, "dataset": ds, "task": task, "method": method,
                "runs": runs, "seed": seed, "eps": eps, "truth": truth,
                "paper": paper, "mean_estimate": float(values.mean()),
                **error_statistics(values, truth, graph.n, paper),
            })
        log(f"[alignment] {ds}: {runs} paired draws, {len(profiles)} profiles")
    ranking = []
    for profile in profiles:
        known = [r for r in rows if r["mechanism"] == profile and r["paper_log_gap"] is not None]
        main = [r for r in known if r["method"] == "GT-PSC"]
        auxiliary = [r for r in known if r["method"] == "GT-PSC-B"]
        if not main:
            continue
        ranking.append({
            "mechanism": profile,
            "table2_log_gap": float(np.mean([r["paper_log_gap"] for r in main])),
            "table3_pscb_log_gap": float(np.mean([r["paper_log_gap"] for r in auxiliary])) if auxiliary else None,
            "joint_log_gap": float(np.mean([r["paper_log_gap"] for r in known])),
            "mean_relative_gap": float(np.mean([r["paper_relative_gap"] for r in known])),
            "max_relative_gap": max(r["paper_relative_gap"] for r in known),
            "cells": len(known),
        })
    ranking.sort(key=lambda r: r["joint_log_gap"])
    return rows, ranking
