"""The two knowledge libraries of the PSC framework (Section 3 / Appendix E).

* :data:`ALGORITHM_LIBRARY` -- distributed algorithms (send / update /
  aggregate rules) that the **curator agent** instantiates for a task.
* :data:`DP_FRAMEWORK_LIBRARY` -- DP frameworks (sensitivity, whether a noisy
  graph is needed, whether the global sensitivity can be optimised) that the
  **privacy controller** queries to determine the DP parameters.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable

from .graph import TASKS, kstar_k

# ---------------------------------------------------------------------------
# Distributed algorithm library
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AlgorithmSpec:
    task: str
    title: str
    problem: str
    state: str
    message: str
    initialization: str
    send: str
    update: str
    aggregate: str
    needs_messages: bool  # whether the Send round is required

    def describe(self) -> str:
        parts = [
            f"Distributed Algorithm for {self.title}",
            f"Problem: {self.problem}",
            f"State:\n{self.state}",
            f"Message:\n{self.message}",
            f"Initialization:\n{self.initialization}",
            f"Send:\n{self.send}",
            f"Update:\n{self.update}",
            f"Aggregation:\n{self.aggregate}",
        ]
        return "\n\n".join(parts)


_TRIANGLE_ALGO = AlgorithmSpec(
    task="triangle",
    title="Triangle Counting",
    problem=(
        "Count the total number of triangles in a given graph G (a triangle "
        "consists of three nodes, each connected to the other two)."
    ),
    state=(
        "1. `Triangle_Count`: The number of triangles this node participates in.\n"
        "2. `Triangles`: A list of detected triangles, each represented as an unordered set."
    ),
    message=(
        "1. `Sender_ID`: The sender node's ID.\n"
        "2. `Sender_Neighbors`: The list of the sender's neighbors."
    ),
    initialization="Step 1: Set `Triangle_Count` to 0.",
    send=(
        "For each node, the input is its Node ID, its State and its Neighbor "
        "Information (the list of nodes it is connected to).\n"
        "Step 1: For each neighbor, construct the message:\n"
        "  1. `Sender_ID`: <node_id>\n"
        "  2. `Sender_Neighbors`: <neighbor_list>\n"
        "Example: Node 5 connected to A, B constructs the message "
        "{`Sender_ID`: 5, `Sender_Neighbors`: [A, B]} and sends it to A and to B."
    ),
    update=(
        "For each node, the input is its Node ID, its State, its Neighbor "
        "Information (<neighbor_list>) and the Received Messages.\n"
        "Step 1: For each received message, extract `Sender_ID`. If `Sender_ID` "
        "is not in <neighbor_list>, discard the message; otherwise, proceed.\n"
        "Step 2: Extract `Sender_Neighbors` from the message. Identify the common "
        "neighbors between yourself and `Sender_ID` by finding which nodes in "
        "`Sender_Neighbors` also appear in <neighbor_list>.\n"
        "Step 3: For each common neighbor `C`, increment `Triangle_Count` by 0.5, "
        "because a triangle will be counted twice.\n"
        "Example: Node 5 with neighbors [2, 4] receives {Sender_ID: 1, "
        "Sender_Neighbors: [4, 5]} and {Sender_ID: 4, Sender_Neighbors: [2, 5, 8]}. "
        "Node 1 is not a neighbor, discard. Node 4 is a neighbor; the common "
        "neighbors are [2], so `Triangle_Count` increases by 0.5. Output state: "
        "`Triangle_Count`: 0.5."
    ),
    aggregate=(
        "To determine the final result, sum the results of the distributed "
        "execution, then divide this value by 3. If the calculated result is "
        "negative, return 0 instead. Compute and return the final result as a "
        "single number only."
    ),
    needs_messages=True,
)

_DEGREE_ALGO = AlgorithmSpec(
    task="degree",
    title="Average Degree",
    problem="Compute the average degree of a given graph G.",
    state="1. `Degree`: The number of neighbors of this node.",
    message="No message is required for this task.",
    initialization="Step 1: Set `Degree` to 0.",
    send="No message needs to be sent for this task.",
    update=(
        "For each node, the input is its Node ID, its State and its Neighbor "
        "Information (<neighbor_list>).\n"
        "Step 1: Count the number of distinct nodes in <neighbor_list> and set "
        "`Degree` to this number.\n"
        "Example: Node 5 with neighbors [2, 4, 7] outputs `Degree`: 3."
    ),
    aggregate=(
        "To determine the final result, sum the results of the distributed "
        "execution and divide this value by the number of nodes in the graph. "
        "If the calculated result is negative, return 0 instead. Compute and "
        "return the final result as a single number only."
    ),
    needs_messages=False,
)


def _kstar_algo(k: int) -> AlgorithmSpec:
    formula = {
        2: "degree * (degree - 1) / 2",
        3: "degree * (degree - 1) * (degree - 2) / 6",
    }.get(k, f"C(degree, {k}) = degree! / ({k}! * (degree - {k})!)")
    example_deg = 4
    example_val = math.comb(example_deg, k)
    return AlgorithmSpec(
        task=f"{k}-star",
        title=f"{k}-star Counting",
        problem=(
            f"Count the total number of {k}-stars in a given graph G (a {k}-star "
            f"consists of a central node connected to {k} other nodes)."
        ),
        state=f"1. `Star_Count`: The number of {k}-stars centered at this node.",
        message="No message is required for this task.",
        initialization="Step 1: Set `Star_Count` to 0.",
        send="No message needs to be sent for this task.",
        update=(
            "For each node, the input is its Node ID, its State and its Neighbor "
            "Information (<neighbor_list>).\n"
            "Step 1: Let degree be the number of distinct nodes in <neighbor_list>.\n"
            f"Step 2: If degree < {k}, set `Star_Count` to 0. Otherwise set "
            f"`Star_Count` to C(degree, {k}) = {formula}.\n"
            f"Example: Node 5 with neighbors [1, 2, 4, 7] has degree {example_deg}, "
            f"so `Star_Count` = C({example_deg}, {k}) = {example_val}."
        ),
        aggregate=(
            "To determine the final result, sum the results of the distributed "
            "execution. If the calculated result is negative, return 0 instead. "
            "Compute and return the final result as a single number only."
        ),
        needs_messages=False,
    )


ALGORITHM_LIBRARY: dict[str, AlgorithmSpec] = {
    "degree": _DEGREE_ALGO,
    "2-star": _kstar_algo(2),
    "3-star": _kstar_algo(3),
    "triangle": _TRIANGLE_ALGO,
}


def algorithm_library_summary() -> str:
    lines = ["Available distributed algorithms in the library:"]
    for task, spec in ALGORITHM_LIBRARY.items():
        lines.append(f"- `{task}`: {spec.title} -- {spec.problem}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# DP framework library
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DPFrameworkSpec:
    task: str
    title: str
    sensitivity_text: str  # human readable, e.g. "degree" or "C(d_max, k-1)"
    noisy_graph: bool  # does the algorithm need the RR noisy graph?
    gs_optimization: bool  # can the global sensitivity be optimised (Alg. 2)?
    _sensitivity: Callable[[int, int | None], float]

    def sensitivity(self, n: int, d_hat_max: int | None) -> float:
        """Global sensitivity ``GS_f`` for ``n`` nodes.

        ``d_hat_max`` is the optimised maximum degree (``None`` when the
        optimisation is disabled, in which case the worst-case bound in
        ``n`` from the paper is used).
        """
        return float(self._sensitivity(n, d_hat_max))

    def describe(self) -> str:
        return (
            f"{self.title}\n"
            "These are the parameters you need for computing this statistic of a "
            "given graph under edge local differential privacy.\n"
            f"Sensitivity: {self.sensitivity_text}\n"
            f"Noisy_Graph: {'yes' if self.noisy_graph else 'no'}\n"
            f"GS_Optimization: {'yes' if self.gs_optimization else 'no'}"
        )


def _triangle_gs(n: int, d_hat_max: int | None) -> float:
    """Triangle sensitivity.

    Appendix E (DP framework library entry for triangle counting) states
    ``Sensitivity: degree-1``: with the projected maximum degree ``d_max``
    the sensitivity is ``d_max - 1``; without projection the maximum degree
    is ``n - 1`` and the sensitivity is ``n - 2`` (Challenge 3).  Both follow
    the same ``max_degree - 1`` pattern.  A floor of 1 keeps the Laplace
    scale positive when ``d_max <= 1``.
    """
    d = d_hat_max if d_hat_max is not None else n - 1
    return float(max(1, d - 1))


def _kstar_gs_factory(k: int) -> Callable[[int, int | None], float]:
    def _gs(n: int, d_hat_max: int | None) -> float:
        d = d_hat_max if d_hat_max is not None else n
        return float(math.comb(int(d), k - 1))

    return _gs


DP_FRAMEWORK_LIBRARY: dict[str, DPFrameworkSpec] = {
    "degree": DPFrameworkSpec(
        task="degree",
        title="Average Degree",
        sensitivity_text="1",
        noisy_graph=False,
        gs_optimization=False,
        _sensitivity=lambda n, d: 1.0,
    ),
    "2-star": DPFrameworkSpec(
        task="2-star",
        title="2-star Counting",
        sensitivity_text="C(d_max, 1) = d_max (n without optimisation)",
        noisy_graph=False,
        gs_optimization=True,
        _sensitivity=_kstar_gs_factory(2),
    ),
    "3-star": DPFrameworkSpec(
        task="3-star",
        title="3-star Counting",
        sensitivity_text="C(d_max, 2) (C(n, 2) without optimisation)",
        noisy_graph=False,
        gs_optimization=True,
        _sensitivity=_kstar_gs_factory(3),
    ),
    "triangle": DPFrameworkSpec(
        task="triangle",
        title="Triangle Counting",
        sensitivity_text="degree-1, i.e. d_max - 1 (n - 2 without optimisation)",
        noisy_graph=True,
        gs_optimization=True,
        _sensitivity=_triangle_gs,
    ),
}


def dp_library_summary() -> str:
    lines = ["Available DP frameworks in the library:"]
    for task, spec in DP_FRAMEWORK_LIBRARY.items():
        lines.append(
            f"- `{task}`: {spec.title}; sensitivity {spec.sensitivity_text}; "
            f"noisy graph {'required' if spec.noisy_graph else 'not required'}; "
            f"GS optimisation {'available' if spec.gs_optimization else 'not available'}",
        )
    return "\n".join(lines)


def get_algorithm(task: str) -> AlgorithmSpec:
    if task not in ALGORITHM_LIBRARY:
        raise KeyError(f"no distributed algorithm for task {task!r}; known: {TASKS}")
    return ALGORITHM_LIBRARY[task]


def get_dp_framework(task: str) -> DPFrameworkSpec:
    if task not in DP_FRAMEWORK_LIBRARY:
        raise KeyError(f"no DP framework for task {task!r}; known: {TASKS}")
    return DP_FRAMEWORK_LIBRARY[task]


def kstar_of(task: str) -> int | None:
    try:
        return kstar_k(task)
    except ValueError:
        return None
