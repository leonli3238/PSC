"""Pure-Python DP algorithms: GT-Naive, GT-PSC and GT-PSC-B (Section 4.1).

They implement exactly the same mechanisms the agents execute, but the
node-level reasoning is done in code instead of by an LLM.  The paper runs
each of them 1,000 times and uses the average as the ground truth.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from . import rules
from .dp import (
    BudgetSplit,
    build_noisy_graph,
    graph_projection,
    laplace_noise,
    naive_budget,
    estimate_degree_bound,
    project_neighbor_list,
    split_budget,
)
from .graph import Graph, kstar_k
from .library import get_dp_framework
from .mechanism import MechanismProfile, get_mechanism


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
    mechanism: str = "legacy"
    noisy_degree_reports: list[float] = field(default_factory=list)
    noisy_max_degree: float | None = None
    sensitivity_degree: float | None = None
    node_projection_degrees: list[int] | None = None
    node_sensitivities: list[float] | None = None

    def audit_dict(self) -> dict:
        return {
            "mechanism": self.mechanism,
            "split": self.split.as_tuple(),
            "noisy_degree_reports": self.noisy_degree_reports,
            "noisy_max_degree": self.noisy_max_degree,
            "sensitivity_degree": self.sensitivity_degree,
            "d_hat_max": self.d_hat_max,
            "sensitivity": self.sensitivity,
            "laplace_scale": self.sensitivity / self.split.eps3,
            "node_projection_degrees": self.node_projection_degrees,
            "node_laplace_scales": (
                [s / self.split.eps3 for s in self.node_sensitivities]
                if self.node_sensitivities is not None else None
            ),
            "raw_counts": self.raw_counts,
            "noisy_counts": self.noisy_counts,
            "report_noise": [r - c for r, c in zip(self.noisy_counts, self.raw_counts)],
            "report_sum_before_clamp": float(sum(self.noisy_counts)),
            "result": self.result,
        }


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
    mechanism: str | MechanismProfile = "legacy",
) -> float | RunTrace:
    """GT-PSC / GT-PSC-B, Algorithm 3.

    The low-level helper keeps the legacy default for historical audit scripts.
    Experiment runners explicitly pass their selected profile (floor_tight by
    default), as does the agent framework.
    """
    n = graph.n
    profile = get_mechanism(mechanism)
    spec = get_dp_framework(task)
    split = split_budget(eps, spec.noisy_graph, spec.gs_optimization and gs_optimization, r1, r2)

    # Lines 5-6: noisy graph
    noisy = build_noisy_graph(graph, split.eps1, rng) if split.eps1 > 0 else None

    # Lines 7-8: global sensitivity optimisation
    d_hat_max: int | None = None
    degree_reports: list[float] = []
    bound = None
    node_degrees: list[int] | None = None
    if split.eps2 > 0:
        degree_reports, bound = estimate_degree_bound(graph.degrees(), split.eps2, rng, task, profile)
        d_hat_max = bound.projection_degree
        if noisy is not None:
            noisy = graph_projection(noisy, d_hat_max, rng)
        else:
            per_node = profile.node_projection_degrees(degree_reports, d_hat_max, task, split.eps2)
            node_degrees = None if per_node is None else [int(x) for x in per_node]
    sensitivity = spec.sensitivity(n, d_hat_max, profile, bound.sensitivity_degree if bound else None)
    node_sens = None if node_degrees is None else [spec.sensitivity(n, D, profile) for D in node_degrees]

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
            limit = node_degrees[i] if node_degrees is not None else d_hat_max
            if limit is not None:
                nbrs = project_neighbor_list(nbrs, limit, rng)
            raw.append(rules.update_kstar(nbrs, k))

    # Line 13: Laplace mechanism on each local count
    scales = node_sens if node_sens is not None else [sensitivity] * n
    noisy_counts = [c + laplace_noise(s, split.eps3, rng) for c, s in zip(raw, scales)]

    # Line 14: aggregation
    result = rules.aggregate(task, noisy_counts, n)
    if return_trace:
        return RunTrace(
            split, sensitivity, d_hat_max, noisy, raw, noisy_counts, result,
            profile.name, degree_reports, bound.raw_max if bound else None,
            bound.sensitivity_degree if bound else None, node_degrees, node_sens,
        )
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
