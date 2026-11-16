"""The unbiased noisy adjacency matrix ``A`` of NAM-DPRD (Guo et al., arXiv 2507.06508).

Release (per-node degree bound first, then RR on the projected lists):

1. node ``i`` publishes ``y_i = d_i + Lap(1/ε2)`` and keeps at most ``D_i``
   neighbours (``D_i`` per node by edge clipping, or the global ``d̂max``);
2. node ``i`` perturbs the bits ``a_ij`` (``j > i``) of its *projected* list by
   randomized response with ``ε1`` and publishes them;
3. the curator publishes, for ``j != k``,

       A(j, k) = (ã_jk (e^ε1 + 1) - 1) / (e^ε1 - 1)  =  κ  if ã_jk = 1,  -1/(e^ε1 - 1)  if ã_jk = 0,

   with ``κ = e^ε1 / (e^ε1 - 1)``, and ``A(j, j) = 0``.

``E[A(j, k)]`` is the projected bit of the edge ``jk`` (reported by ``min(j, k)``).
``A`` is public (post-processing of step 2); a node's program reads it with
``A(j, k)`` (:mod:`certicount.dsl.lang`), the deriver bounds it by
``[-1/(e^ε1 - 1), κ]`` (:mod:`certicount.dsl.sensitivity`). Entry ``jk`` never
depends on the private list of a node ``i`` outside ``{j, k}``.
"""

from __future__ import annotations

import math
from typing import Callable

from psc.graph import Graph

Matrix = Callable[[int, int], float]

# ε1 of the design-time and falsifier checks (the default split: r1 = 0.5 of ε = 2);
# a run derives the GS again at its own ε1
REFERENCE_EPS1 = 1.0


def rr_constants(eps1: float) -> tuple[float, float]:
    """``(low, high)`` = ``(-1/(e^ε1 - 1), e^ε1/(e^ε1 - 1))``: the two values of an off-diagonal entry."""
    if not math.isfinite(eps1) or eps1 <= 0:
        raise ValueError("the unbiased matrix needs a positive eps1")
    inv = -1.0 / math.expm1(-eps1) - 1.0  # 1 / (e^eps1 - 1) without overflow
    return -inv, 1.0 + inv


def unbiased_matrix(noisy: Graph, eps1: float) -> Matrix:
    """``A`` of the released RR graph ``noisy`` (symmetric, zero diagonal)."""
    low, high = rr_constants(eps1)
    adj = [frozenset(noisy.adj[i]) for i in range(noisy.n)]

    def entry(j: int, k: int) -> float:
        if j == k:
            return 0.0
        return high if k in adj[j] else low

    return entry


def exact_matrix(graph: Graph) -> Matrix:
    """Noise-free counterpart (the expectation of ``A`` without projection): the 0/1 adjacency."""
    adj = [frozenset(graph.adj[i]) for i in range(graph.n)]
    return lambda j, k: 0.0 if j == k else (1.0 if k in adj[j] else 0.0)


def table_matrix(values: dict[tuple[int, int], float]) -> Matrix:
    """``A`` from explicit off-diagonal values (falsifier); missing pairs are 0."""
    return lambda j, k: 0.0 if j == k else values.get((min(j, k), max(j, k)), 0.0)
