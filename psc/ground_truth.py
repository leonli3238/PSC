"""Pure-Python DP algorithms: GT-Naive, GT-PSC and GT-PSC-B (Section 4.1).

They implement exactly the same mechanisms the agents execute, but the
node-level reasoning is done in code instead of by an LLM.  The paper runs
each of them 1,000 times and uses the average as the ground truth.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

from . import rules
from .dp import (
    BudgetSplit,
    build_noisy_graph,
    flip_probability,
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


TRITR_BUDGETS = ("psc", "nam")
# NAM-DPRD TriTR: (degree projection, RR, Laplace) shares of eps
TRITR_NAM_RATIO = (0.1, 0.45, 0.45)


def tritr_budget(eps: float, task: str, budget: str = "psc", r1: float = 0.5, r2: float = 0.2) -> BudgetSplit:
    """``(eps1, eps2, eps3)`` = (RR, degree projection, Laplace), as for PSC.

    ``"psc"`` reuses the PSC split of the task; ``"nam"`` gives the projection
    and RR their TriTR shares and the rest to the Laplace reports.
    """
    if budget not in TRITR_BUDGETS:
        raise ValueError(f"budget must be one of {TRITR_BUDGETS}")
    spec = get_dp_framework(task)
    if budget == "psc":
        return split_budget(eps, spec.noisy_graph, spec.gs_optimization, r1, r2)
    proj, rr, _ = TRITR_NAM_RATIO
    eps1 = rr * eps if spec.noisy_graph else 0.0
    eps2 = proj * eps if spec.gs_optimization else 0.0
    return BudgetSplit(eps1, eps2, eps - eps1 - eps2)


def gt_tritr(
    graph: Graph,
    task: str,
    eps: float,
    rng: np.random.Generator,
    alpha: float = 0.0,
    budget: str = "psc",
    r1: float = 0.5,
    r2: float = 0.2,
    clamp: bool = True,
) -> float:
    """TriTR of NAM-DPRD for triangles, and the same per-node framework for the other tasks.

    Every user publishes ``d~_i = max(d_i + Lap(1/eps2), 0) + alpha`` and keeps at
    most ``floor(d~_i)`` of its neighbors. Triangle, two rounds: user ``i`` sends
    its projected bits ``a_ij`` (``j > i``) through RR(eps1); the curator
    publishes ``A^ = (A~ (e^eps1 + 1) - 1) / (e^eps1 - 1)``; user ``i`` reports
    ``sum_{j,k in N'(i)} clip(A^_jk, +-kappa) + Lap(2 kappa d~_i / eps3)`` with
    ``kappa = e^eps1 / (e^eps1 - 1)``, and the estimate is the total over 6.
    The upstream code sums over the unprojected neighbor list, which breaks the
    ``2 kappa d~_i`` sensitivity whenever ``d_i > d~_i``; here ``N'(i)`` is the
    projected list.

    Not in NAM-DPRD: a k-star user reports ``C(min(d_i, D_i), k) +
    Lap(C(D_i - 1, k - 1) / eps3)`` with ``D_i = floor(d~_i)``; degree has
    sensitivity 1 and no projection, so it coincides with GT-PSC. Like PSC,
    a negative total returns 0 when ``clamp``.
    """
    if alpha < 0:
        raise ValueError("alpha must be nonnegative")
    split = tritr_budget(eps, task, budget, r1, r2)
    n = graph.n
    deg = np.array(graph.degrees(), dtype=float)
    if task == "degree":
        result = (deg.sum() + rng.laplace(0.0, 1.0 / split.eps3, size=n).sum()) / n
        return max(0.0, result) if clamp else float(result)

    noisy_deg = np.maximum(deg + rng.laplace(0.0, 1.0 / split.eps2, size=n), 0.0) + alpha
    limits = np.floor(noisy_deg).astype(int)
    if task != "triangle":
        k = kstar_k(task)
        counts = sum(math.comb(min(int(d), int(t)), k) for d, t in zip(deg, limits))
        sens = np.array([math.comb(t - 1, k - 1) if t >= 1 else 0 for t in limits], dtype=float)
        result = counts + rng.laplace(0.0, sens / split.eps3).sum()
        return max(0.0, result) if clamp else float(result)

    proj = np.zeros((n, n))
    for i in range(n):
        proj[i, project_neighbor_list(graph.neighbors(i), int(limits[i]), rng)] = 1.0
    upper = np.triu(np.ones((n, n), dtype=bool), k=1)
    flips = (rng.random((n, n)) < flip_probability(split.eps1)) & upper
    noisy = np.where(flips, 1.0 - proj, proj) * upper
    noisy += noisy.T
    inv = -1.0 / math.expm1(-split.eps1) - 1.0  # 1 / (e^eps1 - 1) without overflow
    kappa = 1.0 + inv
    a_hat = np.clip(noisy * (1.0 + 2.0 * inv) - inv, -kappa, kappa)
    np.fill_diagonal(a_hat, 0.0)
    local = ((proj @ a_hat) * proj).sum(axis=1)
    result = (local.sum() + rng.laplace(0.0, 2.0 * kappa * noisy_deg / split.eps3).sum()) / 6.0
    return max(0.0, result) if clamp else float(result)


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
