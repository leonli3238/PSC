"""Pure-Python DP algorithms: GT-Naive, GT-PSC and GT-PSC-B (Section 4.1).

They implement exactly the same mechanisms the agents execute, but the
node-level reasoning is done in code instead of by an LLM.  The paper runs
each of them 1,000 times and uses the average as the ground truth.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from . import rules
from .dp import (
    BudgetSplit,
    build_noisy_graph,
    graph_projection,
    laplace_noise,
    naive_budget,
    noisy_max_degree,
    project_neighbor_list,
    split_budget,
)
from .graph import Graph, kstar_k
from .library import get_dp_framework


@dataclass
class RunTrace:
    """Intermediate quantities of one PSC run (useful for debugging/tests)."""

    split: BudgetSplit
    sensitivity: float
    d_hat_max: int | None
    noisy_graph: Graph | None
    raw_counts: list[float]
    noisy_counts: list[float]
    result: float


def gt_naive(graph: Graph, task: str, eps: float, rng: np.random.Generator) -> float:
    """GT-Naive: RR noisy graph with the full budget, exact count on it."""
    split = naive_budget(eps)
    noisy = build_noisy_graph(graph, split.eps1, rng)
    return rules.naive_answer(task, graph.n, noisy.edges)


def gt_psc(
    graph: Graph,
    task: str,
    eps: float,
    rng: np.random.Generator,
    gs_optimization: bool = True,
    r1: float = 0.5,
    r2: float = 0.2,
    return_trace: bool = False,
) -> float | RunTrace:
    """GT-PSC (``gs_optimization=True``) / GT-PSC-B (``False``), Algorithm 3."""
    n = graph.n
    spec = get_dp_framework(task)
    split = split_budget(eps, spec.noisy_graph, spec.gs_optimization and gs_optimization, r1, r2)

    # Lines 5-6: noisy graph
    noisy = build_noisy_graph(graph, split.eps1, rng) if split.eps1 > 0 else None

    # Lines 7-8: global sensitivity optimisation
    d_hat_max: int | None = None
    if split.eps2 > 0:
        _, d_hat_max = noisy_max_degree(graph.degrees(), split.eps2, rng)
        if noisy is not None:
            noisy = graph_projection(noisy, d_hat_max, rng)
    sensitivity = spec.sensitivity(n, d_hat_max)

    # Lines 10-12: distributed execution (send + update)
    raw: list[float] = []
    if task == "triangle":
        assert noisy is not None
        for i in range(n):
            raw.append(rules.triangle_local_count(graph.adj[i], noisy.adj[i], noisy.adj))
    elif task == "degree":
        raw = [rules.update_degree(graph.adj[i]) for i in range(n)]
    else:
        k = kstar_k(task)
        for i in range(n):
            nbrs = graph.neighbors(i)
            if d_hat_max is not None:
                nbrs = project_neighbor_list(nbrs, d_hat_max, rng)
            raw.append(rules.update_kstar(nbrs, k))

    # Line 13: Laplace mechanism on each local count
    noisy_counts = [c + laplace_noise(sensitivity, split.eps3, rng) for c in raw]

    # Line 14: aggregation
    result = rules.aggregate(task, noisy_counts, n)
    if return_trace:
        return RunTrace(split, sensitivity, d_hat_max, noisy, raw, noisy_counts, result)
    return result


def relative_error(estimate: float, truth: float, n: int) -> float:
    """``|f_hat - f| / max(f, eta)`` with ``eta = 0.001 n`` (Section 4.1)."""
    eta = 0.001 * n
    return abs(estimate - truth) / max(truth, eta)


def average_relative_error(
    method,
    graph: Graph,
    task: str,
    eps: float,
    runs: int,
    seed: int = 0,
    **kwargs,
) -> tuple[float, list[float]]:
    """Run ``method(graph, task, eps, rng, **kwargs)`` ``runs`` times and
    return ``(mean relative error, estimates)``."""
    rng = np.random.default_rng(seed)
    truth = graph.ground_truth(task)
    ests = [float(method(graph, task, eps, rng, **kwargs)) for _ in range(runs)]
    errs = [relative_error(e, truth, graph.n) for e in ests]
    return float(np.mean(errs)), ests
