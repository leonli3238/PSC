"""Reference (code) implementations of the send / update / aggregate rules.

These functions are the *exact* semantics of the rule texts stored in
:mod:`psc.library`.  They are used

1. by the pure-Python ground-truth algorithms ``GT-Naive`` / ``GT-PSC``
   (Section 4.1: "their DP algorithms implemented in Python"), and
2. by the offline :class:`~psc.mock_model.MockChatModel`, which emulates an
   LLM agent that follows the rules perfectly, so that the whole AgentScope
   pipeline can be exercised end-to-end without API access.
"""

from __future__ import annotations

import math
from typing import Iterable, Mapping, Sequence

from .graph import Graph, kstar_k


# -- Send -------------------------------------------------------------------


def send_message(node_id: int, noisy_neighbors: Iterable[int]) -> dict:
    """Triangle counting send rule: ``{Sender_ID, Sender_Neighbors}``.

    Only the *noisy* neighbor list is accessed here (Section 3, "Distributed
    Execution": the send function reads the noisy edge memory only).
    """
    return {"Sender_ID": int(node_id), "Sender_Neighbors": sorted(int(x) for x in noisy_neighbors)}


# -- Update -----------------------------------------------------------------


def update_degree(real_neighbors: Iterable[int]) -> float:
    return float(len(set(real_neighbors)))


def update_kstar(real_neighbors: Iterable[int], k: int) -> float:
    return float(math.comb(len(set(real_neighbors)), k))


def update_triangle(real_neighbors: Iterable[int], messages: Sequence[Mapping]) -> float:
    """Appendix E update rule: +0.5 per common neighbor for each message whose
    sender is a real neighbor."""
    nbrs = set(int(x) for x in real_neighbors)
    count = 0.0
    for msg in messages:
        sender = int(msg["Sender_ID"])
        if sender not in nbrs:
            continue
        common = nbrs.intersection(int(x) for x in msg["Sender_Neighbors"])
        count += 0.5 * len(common)
    return count


def triangle_local_count(real_neighbors: set[int], noisy_neighbors: set[int], noisy_adj: Sequence[set[int]]) -> float:
    """Set-based equivalent of :func:`update_triangle` when every noisy
    neighbor ``j`` of the node sends its noisy neighbor list ``noisy_adj[j]``."""
    count = 0.0
    for j in noisy_neighbors & real_neighbors:
        count += 0.5 * len(real_neighbors & noisy_adj[j])
    return count


def update(task: str, real_neighbors: Iterable[int], messages: Sequence[Mapping] | None = None) -> float:
    if task == "degree":
        return update_degree(real_neighbors)
    if task == "triangle":
        return update_triangle(real_neighbors, messages or [])
    return update_kstar(real_neighbors, kstar_k(task))


# -- Aggregate --------------------------------------------------------------


def aggregate(task: str, counts: Sequence[float], n: int) -> float:
    total = float(sum(counts))
    if task == "degree":
        result = total / n
    elif task == "triangle":
        result = total / 3.0
    else:
        result = total
    return max(0.0, result)


# -- Naive: exact count on the noisy graph ------------------------------------


def naive_answer(task: str, n: int, noisy_edges: Iterable[tuple[int, int]]) -> float:
    """What a perfect curator would answer given only the noisy edge list."""
    return Graph.from_edges(n, noisy_edges).ground_truth(task)
