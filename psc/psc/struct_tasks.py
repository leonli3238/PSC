"""判定类图任务（open-wedge / degree-ge3 / triangle-edge / triangle-node）。

这些任务挂在论文 Naive 基线（Section 2.4）的机制上：`eps` 全部用于
Algorithm 1 的随机响应噪声图 ``G'``，LLM 只看到 ``(V(G), Q)`` 与 ``G'`` 的
边表，一次性给出答案，不做多智能体分解。

本模块只负责任务本身：自然语言描述、实例（目标节点 / 边）的选取、真值、
答案解析，以及"完美 curator"在同一张噪声图上的答案（即 GT-Naive），
因此 agent 侧与纯代码侧共用同一套语义。
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from itertools import combinations

import numpy as np

from .graph import LDP_NOTICE, Graph
from .prompts import (
    ANSWER_INSTRUCTION,
    NAIVE_PROMPTS,
    NO_REASONING_INSTRUCTION,
    extract_json,
    extract_number,
    insert_edges_into_prompt,
    structured_block,
)

STRUCT_TASKS: tuple[str, ...] = ("open-wedge", "degree-ge3", "triangle-edge", "triangle-node")

ANSWER_KINDS: dict[str, str] = {
    "open-wedge": "count",
    "degree-ge3": "yes_no",
    "triangle-edge": "yes_no",
    "triangle-node": "yes_no",
}

_DESCRIPTIONS: dict[str, str] = {
    "open-wedge": (
        "An open wedge is an unordered pair of edges that share exactly one "
        "endpoint, where the two other endpoints are not connected by an edge."
    ),
    "degree-ge3": (
        "The degree of a node is the number of edges connected to it."
    ),
    "triangle-edge": (
        "A triangle consists of three nodes, each connected to the other two by "
        "an edge. An edge belongs to a triangle if and only if its two endpoints "
        "have a common neighbor."
    ),
    "triangle-node": (
        "A triangle consists of three nodes, each connected to the other two by "
        "an edge. A node is part of a triangle if and only if two of its "
        "neighbors are connected to each other."
    ),
}


def answer_kind(task: str) -> str:
    if task not in ANSWER_KINDS:
        raise ValueError(f"unknown structured task {task!r}, expected one of {STRUCT_TASKS}")
    return ANSWER_KINDS[task]


def _question(task: str, target: int | list[int] | tuple[int, int] | None) -> str:
    if task == "open-wedge":
        return "How many open wedges does the graph contain?"
    if task == "degree-ge3":
        return f"Is the degree of node {int(target)} at least 3?"
    if task == "triangle-edge":
        u, v = (int(x) for x in target)  # type: ignore[misc]
        return f"Does edge ({u}, {v}) belong to at least one triangle?"
    if task == "triangle-node":
        return f"Is node {int(target)} part of at least one triangle?"
    raise ValueError(task)


def struct_task_prompt(
    task: str, n: int, target: int | list[int] | tuple[int, int] | None, ldp: bool = True,
) -> str:
    """Appendix-A style ``(V(G), Q)`` prompt for a structured task."""
    if task not in STRUCT_TASKS:
        raise ValueError(f"unknown structured task {task!r}, expected one of {STRUCT_TASKS}")
    parts = [_DESCRIPTIONS[task]]
    if ldp:
        parts.append(LDP_NOTICE)
    parts.append(f"Q: The nodes are numbered from 0 to {n - 1}. {_question(task, target)}")
    return " ".join(parts)


# ---------------------------------------------------------------------------
# Truth
# ---------------------------------------------------------------------------


def count_open_wedges(graph: Graph) -> int:
    """``sum_v C(d_v, 2) - 3T``: every triangle closes one wedge at each of its
    three corners, so subtracting them leaves the open wedges."""
    return sum(math.comb(d, 2) for d in graph.degrees()) - 3 * graph.count_triangles()


def answer_on_graph(
    graph: Graph, task: str, target: int | list[int] | tuple[int, int] | None,
) -> float | str:
    """Exact answer to ``task`` on ``graph`` (truth on G, GT-Naive on G')."""
    if task == "open-wedge":
        return float(count_open_wedges(graph))
    if task == "degree-ge3":
        return "yes" if graph.degree(int(target)) >= 3 else "no"  # type: ignore[arg-type]
    if task == "triangle-edge":
        u, v = (int(x) for x in target)  # type: ignore[misc]
        return "yes" if graph.has_edge(u, v) and bool(graph.adj[u] & graph.adj[v]) else "no"
    if task == "triangle-node":
        v = int(target)  # type: ignore[arg-type]
        return "yes" if any(w in graph.adj[u] for u, w in combinations(graph.adj[v], 2)) else "no"
    raise ValueError(task)


def naive_answer_on_edges(
    task: str, n: int, edges: list[tuple[int, int]], target: int | list[int] | tuple[int, int] | None,
) -> float | str:
    """What a perfect curator answers from the noisy edge list alone."""
    return answer_on_graph(Graph.from_edges(n, edges), task, target)


def is_correct(predicted: float | str | None, truth: float | str) -> bool:
    if predicted is None:
        return False
    if isinstance(truth, str):
        return predicted == truth
    return abs(float(predicted) - truth) < 1e-6


# ---------------------------------------------------------------------------
# Instances
# ---------------------------------------------------------------------------


def _pick_balanced(positive: list, negative: list, rng: np.random.Generator):
    """Draw from the smaller class 50 % of the time so the labels stay balanced."""
    if not positive:
        return negative[int(rng.integers(len(negative)))]
    if not negative:
        return positive[int(rng.integers(len(positive)))]
    pool = positive if rng.random() < 0.5 else negative
    return pool[int(rng.integers(len(pool)))]


def choose_target(graph: Graph, task: str, rng: np.random.Generator):
    if task == "open-wedge":
        return None
    if task == "degree-ge3":
        return int(_pick_balanced(
            [v for v in range(graph.n) if graph.degree(v) >= 3],
            [v for v in range(graph.n) if graph.degree(v) < 3],
            rng,
        ))
    if task == "triangle-edge":
        positive, negative = [], []
        for u, v in graph.edges:
            (positive if graph.adj[u] & graph.adj[v] else negative).append([u, v])
        return list(_pick_balanced(positive, negative, rng))
    if task == "triangle-node":
        positive = [v for v in range(graph.n) if answer_on_graph(graph, task, v) == "yes"]
        negative = [v for v in range(graph.n) if answer_on_graph(graph, task, v) != "yes"]
        return int(_pick_balanced(positive, negative, rng))
    raise ValueError(task)


@dataclass
class StructRecord:
    """One instance of a structured task on one dataset."""

    dataset: str
    task: str
    n: int
    target: int | list[int] | None
    answer: float | str
    input_prompt: str
    edge_string: str

    def graph(self) -> Graph:
        return Graph.from_edge_string(self.n, self.edge_string)

    def to_dict(self) -> dict:
        return {
            "dataset": self.dataset,
            "task": self.task,
            "n": self.n,
            "target": self.target,
            "answer": self.answer,
            "input_prompt": self.input_prompt,
        }


def build_record(dataset: str, graph: Graph, task: str, rng: np.random.Generator) -> StructRecord:
    target = choose_target(graph, task, rng)
    return StructRecord(
        dataset=dataset,
        task=task,
        n=graph.n,
        target=target,
        answer=answer_on_graph(graph, task, target),
        input_prompt=struct_task_prompt(task, graph.n, target),
        edge_string=graph.edge_string(),
    )


# ---------------------------------------------------------------------------
# Prompt and answer parsing
# ---------------------------------------------------------------------------


def struct_naive_prompt(record: StructRecord, noisy_edges: list[tuple[int, int]], style: str = "paper") -> str:
    """Naive (Section 2.4): the noisy edge list is pasted into ``(V(G), Q)``.

    ``style`` follows :data:`psc.prompts.NAIVE_PROMPTS`; ``paper`` sends no
    system prompt and no answer-format instruction, ``cot`` asks for a JSON
    answer after step-by-step reasoning.
    """
    if style not in NAIVE_PROMPTS:
        raise ValueError(f"unknown naive prompt {style!r}, expected one of {NAIVE_PROMPTS}")
    payload = {
        "phase": "naive_struct",
        "task": record.task,
        "n": record.n,
        "target": record.target,
        "edges": [[int(u), int(v)] for u, v in noisy_edges],
    }
    if style == "paper":
        instruction = ""
    elif style == "paper-direct":
        instruction = f"{NO_REASONING_INSTRUCTION}\n\n"
    else:
        instruction = f'{ANSWER_INSTRUCTION} Required key: "result" (a number, "yes" or "no").\n\n'
    return (
        f"{insert_edges_into_prompt(record.input_prompt, noisy_edges)}\n\n"
        f"{instruction}"
        f"{structured_block(payload)}"
    )


_YES_NO = re.compile(r"\b(yes|no)\b", re.IGNORECASE)
_TRUE_FALSE = re.compile(r"\b(true|false)\b", re.IGNORECASE)


def parse_answer(task: str, text: str) -> float | str | None:
    """Parse a reply into the task's answer type; ``None`` when unparseable."""
    if not text:
        return None
    if answer_kind(task) == "count":
        return extract_number(text)
    payload = extract_json(text) or {}
    for key in ("result", "answer"):
        if key not in payload:
            continue
        value = payload[key]
        if isinstance(value, bool):
            return "yes" if value else "no"
        token = str(value).strip().lower().strip('".')
        if token in ("yes", "no"):
            return token
        if token in ("true", "false"):
            return "yes" if token == "true" else "no"
    matches = [m.lower() for m in _YES_NO.findall(text)] or [
        ("yes" if m.lower() == "true" else "no") for m in _TRUE_FALSE.findall(text)
    ]
    return matches[-1] if matches else None
