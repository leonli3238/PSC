"""Differential privacy primitives used by the privacy controller.

* Warner's randomized response on the lower triangle of the adjacency matrix
  (Algorithm 1, ``BuildNoisyGraph``)
* Laplace mechanism calibrated to the global sensitivity (Definition 3)
* Global sensitivity optimisation via noisy max-degree + graph projection
  (Algorithm 2, ``GSOptimize``)
* Privacy budget allocation (Section 4.1)

Everything here is *code*, never delegated to an LLM: this is how the paper
addresses Challenge 1 (LLMs cannot be trusted to execute DP mechanisms).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, Sequence

import numpy as np

from .graph import Graph
from .mechanism import DegreeBound, MechanismProfile, get_mechanism


# ---------------------------------------------------------------------------
# Randomized response (Section 2.3)
# ---------------------------------------------------------------------------


def flip_probability(eps: float) -> float:
    """``p = 1 / (1 + e^eps)`` -- the probability of flipping one bit."""
    if eps > 700:  # exp overflow guard; p is numerically 0 anyway
        return 0.0
    return 1.0 / (1.0 + math.exp(eps))


def randomized_response_row(
    neighbor_bits: np.ndarray,
    eps: float,
    rng: np.random.Generator,
) -> np.ndarray:
    """Apply RR to a 0/1 vector (one neighbor list prefix)."""
    p = flip_probability(eps)
    flips = rng.random(neighbor_bits.shape[0]) < p
    return np.where(flips, 1 - neighbor_bits, neighbor_bits).astype(np.int8)


def node_noisy_lower_row(
    node_id: int,
    neighbors: Iterable[int],
    eps: float,
    rng: np.random.Generator,
) -> list[int]:
    """Algorithm 1, lines 2-4 executed *locally* by node agent ``node_id``.

    Perturbs the entries ``a_{i,j}`` with ``j < i`` of the node's neighbor
    list via RR and returns the noisy neighbors with smaller ids, which are
    the only edges the node releases (avoids the doubling issue).
    """
    if node_id == 0:
        return []
    bits = np.zeros(node_id, dtype=np.int8)
    for j in neighbors:
        if j < node_id:
            bits[j] = 1
    noisy = randomized_response_row(bits, eps, rng)
    return np.flatnonzero(noisy).tolist()


def build_noisy_graph(graph: Graph, eps: float, rng: np.random.Generator) -> Graph:
    """Algorithm 1 (``BuildNoisyGraph``) run by the curator over all nodes.

    Vectorised equivalent of calling :func:`node_noisy_lower_row` for every
    node and merging the released edges.
    """
    n = graph.n
    a = graph.adjacency_matrix()
    p = flip_probability(eps)
    lower = np.tril(np.ones((n, n), dtype=bool), k=-1)
    flips = (rng.random((n, n)) < p) & lower
    noisy_lower = np.where(flips, 1 - a, a) & lower
    return Graph.from_adjacency(noisy_lower | noisy_lower.T)


# ---------------------------------------------------------------------------
# Laplace mechanism (Definition 3)
# ---------------------------------------------------------------------------


def laplace_noise(sensitivity: float, eps: float, rng: np.random.Generator) -> float:
    """Sample ``Lap(GS_f / eps)``."""
    if not math.isfinite(eps) or eps <= 0:
        raise ValueError("privacy budget must be positive for Laplace mechanism")
    if not math.isfinite(sensitivity) or sensitivity < 0:
        raise ValueError("sensitivity must be finite and nonnegative")
    return float(rng.laplace(0.0, sensitivity / eps))


def laplace_mechanism(value: float, sensitivity: float, eps: float, rng: np.random.Generator) -> float:
    return value + laplace_noise(sensitivity, eps, rng)


# ---------------------------------------------------------------------------
# Global sensitivity optimisation (Algorithm 2)
# ---------------------------------------------------------------------------


def noisy_max_degree(degrees: Sequence[int], eps2: float, rng: np.random.Generator) -> tuple[list[float], int]:
    """Lines 1-4 of Algorithm 2.

    Each node reports ``deg + Lap(1/eps2)`` (degree has sensitivity 1); the
    privacy controller takes the maximum.  The estimate is rounded *up* to an
    integer so that the resulting projection threshold is conservative.
    """
    noisy = [d + laplace_noise(1.0, eps2, rng) for d in degrees]
    d_hat_max = max(1, int(math.ceil(max(noisy))))
    return noisy, d_hat_max


def estimate_degree_bound(
    degrees: Sequence[int], eps2: float, rng: np.random.Generator,
    task: str, mechanism: str | MechanismProfile,
) -> tuple[list[float], DegreeBound]:
    """Sample once; preserve both continuous maximum and projection threshold."""
    reports = [d + laplace_noise(1.0, eps2, rng) for d in degrees]
    return reports, get_mechanism(mechanism).degree_bound(reports, task)


def graph_projection(noisy_graph: Graph, d_max: int, rng: np.random.Generator) -> Graph:
    """``GraphProjection(G', d_max)`` (Algorithm 2, line 5).

    For every node whose degree in the noisy graph exceeds ``d_max`` only
    ``d_max`` randomly selected neighbors are retained.  Edges are removed
    symmetrically so the result is still an undirected graph in which every
    node has degree at most ``d_max``.
    """
    g = noisy_graph.copy()
    order = rng.permutation(g.n)
    for u in order:
        if len(g.adj[u]) > d_max:
            nbrs = sorted(g.adj[u])
            keep = set(rng.choice(nbrs, size=d_max, replace=False).tolist())
            for v in nbrs:
                if v not in keep:
                    g.adj[u].discard(v)
                    g.adj[v].discard(u)
    return g


def project_neighbor_list(neighbors: Sequence[int], d_max: int, rng: np.random.Generator) -> list[int]:
    """Project one (real) neighbor list to at most ``d_max`` neighbors.

    Used for tasks that do not build a noisy graph (k-star): the node agent
    computes its local count on a bounded neighbor list so that the
    sensitivity ``C(d_max, k-1)`` claimed by the DP framework library holds.
    """
    nbrs = sorted(neighbors)
    if len(nbrs) <= d_max:
        return nbrs
    return sorted(rng.choice(nbrs, size=d_max, replace=False).tolist())


# ---------------------------------------------------------------------------
# Budget allocation (Section 4.1, "Parameters")
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class BudgetSplit:
    eps1: float  # noisy graph construction
    eps2: float  # global sensitivity optimisation
    eps3: float  # reporting the local counts

    @property
    def total(self) -> float:
        return self.eps1 + self.eps2 + self.eps3

    def as_tuple(self) -> tuple[float, float, float]:
        return (self.eps1, self.eps2, self.eps3)


def split_budget(
    eps: float,
    need_noisy_graph: bool,
    need_gs_optimization: bool,
    r1: float = 0.5,
    r2: float = 0.2,
) -> BudgetSplit:
    """Split ``eps`` into ``(eps1, eps2, eps3)``.

    Default allocation of the paper: ``eps1 = 0.5 eps``,
    ``eps2 = 0.2 (eps - eps1)``, ``eps3 = eps - eps1 - eps2``.  Steps that are
    not required get budget 0 while the proportional allocation of the
    remaining steps is maintained.
    """
    if not math.isfinite(eps) or eps <= 0:
        raise ValueError("epsilon must be finite and positive")
    if not (0 <= r1 < 1 and 0 <= r2 < 1):
        raise ValueError("budget ratios must be in [0, 1)")
    if need_gs_optimization and r2 == 0:
        raise ValueError("GS optimization requires a positive r2")
    if need_noisy_graph and r1 == 0:
        raise ValueError("noisy graph construction requires a positive r1")
    eps1 = r1 * eps if need_noisy_graph else 0.0
    rest = eps - eps1
    eps2 = r2 * rest if need_gs_optimization else 0.0
    eps3 = rest - eps2
    return BudgetSplit(eps1, eps2, eps3)


def naive_budget(eps: float) -> BudgetSplit:
    """The Naive approach spends the whole budget on the noisy graph."""
    return BudgetSplit(eps, 0.0, 0.0)
