"""Graph container, substructure counting tasks and the unified dataset format.

The dataset format follows Appendix A of the paper::

    {
      "index": 1,
      "input_prompt": "... Q: The nodes are numbered from 0 to 48. What is ...?",
      "edges": "(0, 1) (0, 2) ...",
      "vertex_num": 49,
      "edge_num": 107,
      "answer": 421
    }
"""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np

# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------

TASKS: tuple[str, ...] = ("degree", "2-star", "3-star", "triangle")
# Default for experiment scripts. 2-star stays runnable via --tasks, but its
# GT-PSC mechanism is not aligned with the paper (see docs/PSC_REPRODUCTION_REPORT.md, part 4).
DEFAULT_TASKS: tuple[str, ...] = ("degree", "triangle", "3-star")

# Natural-language task descriptions (Section 2.2 / Appendix A).  Every task
# prompt ends with "Q: The nodes are numbered from 0 to n-1. <question>" so
# that the curator agent only receives ``(V(G), Q)`` under edge LDP.
_TASK_DESCRIPTIONS = {
    "degree": (
        "The degree of a node is the number of edges connected to it. "
        "The average degree of the graph is the sum of the degrees of all "
        "nodes divided by the number of nodes."
    ),
    "2-star": (
        "For each node, the number of 2-stars centered at that node is the "
        "number of unordered pairs of its neighbors. This can be calculated "
        "as degree(node) * (degree(node) - 1) / 2, where degree(node) is the "
        "number of edges connected to the node. The total number of 2-stars "
        "in the graph is the sum of 2-stars centered at each node."
    ),
    "3-star": (
        "For each node, the number of 3-stars centered at that node is the "
        "number of unordered triples of its neighbors. This can be "
        "calculated as degree(node) * (degree(node) - 1) * (degree(node) - 2) "
        "/ 6, where degree(node) is the number of edges connected to the "
        "node. The total number of 3-stars in the graph is the sum of 3-stars "
        "centered at each node."
    ),
    "triangle": (
        "A triangle consists of three nodes, each connected to the other two "
        "by an edge. The total number of triangles in the graph is the number "
        "of such node triples."
    ),
}

_TASK_QUESTIONS = {
    "degree": "What is the average degree of the graph?",
    "2-star": "What is the total number of 2-stars in the graph?",
    "3-star": "What is the total number of 3-stars in the graph?",
    "triangle": "What is the total number of triangles in the graph?",
}

LDP_NOTICE = (
    "Each node may hide its edge information under the local edge "
    "differential privacy framework."
)


def task_prompt(task: str, n: int, ldp: bool = True) -> str:
    """Build the ``input_prompt`` string of a task (Appendix A format)."""
    if task not in TASKS:
        raise ValueError(f"Unknown task {task!r}, expected one of {TASKS}")
    parts = [_TASK_DESCRIPTIONS[task]]
    if ldp:
        parts.append(LDP_NOTICE)
    parts.append(
        f"Q: The nodes are numbered from 0 to {n - 1}. {_TASK_QUESTIONS[task]}",
    )
    return " ".join(parts)


def infer_task_from_prompt(prompt: str) -> str:
    """Rule-based fallback used when an LLM fails to identify the task."""
    p = prompt.lower()
    if "triangle" in p:
        return "triangle"
    if "3-star" in p or "3 star" in p or "three-star" in p:
        return "3-star"
    if "2-star" in p or "2 star" in p or "two-star" in p:
        return "2-star"
    if "degree" in p:
        return "degree"
    raise ValueError("Cannot infer the substructure counting task from prompt")


def kstar_k(task: str) -> int:
    """Return ``k`` for a ``k-star`` task."""
    m = re.fullmatch(r"(\d+)-star", task)
    if not m:
        raise ValueError(f"{task!r} is not a k-star task")
    return int(m.group(1))


# ---------------------------------------------------------------------------
# Graph
# ---------------------------------------------------------------------------


@dataclass
class Graph:
    """A simple undirected, unweighted graph with nodes ``0..n-1``."""

    n: int
    adj: list[set[int]] = field(repr=False)

    # -- construction -----------------------------------------------------
    @classmethod
    def from_edges(cls, n: int, edges: Iterable[tuple[int, int]]) -> "Graph":
        adj: list[set[int]] = [set() for _ in range(n)]
        for u, v in edges:
            if u == v:
                continue
            adj[u].add(v)
            adj[v].add(u)
        return cls(n=n, adj=adj)

    @classmethod
    def from_edge_string(cls, n: int, edge_string: str) -> "Graph":
        return cls.from_edges(n, parse_edge_string(edge_string))

    @classmethod
    def from_adjacency(cls, matrix: np.ndarray) -> "Graph":
        n = matrix.shape[0]
        rows, cols = np.nonzero(np.triu(matrix, k=1))
        return cls.from_edges(n, zip(rows.tolist(), cols.tolist()))

    # -- basic properties -------------------------------------------------
    @property
    def edges(self) -> list[tuple[int, int]]:
        return [(u, v) for u in range(self.n) for v in sorted(self.adj[u]) if u < v]

    @property
    def m(self) -> int:
        return sum(len(s) for s in self.adj) // 2

    def degree(self, u: int) -> int:
        return len(self.adj[u])

    def degrees(self) -> list[int]:
        return [len(s) for s in self.adj]

    def max_degree(self) -> int:
        return max(self.degrees()) if self.n else 0

    def neighbors(self, u: int) -> list[int]:
        return sorted(self.adj[u])

    def has_edge(self, u: int, v: int) -> bool:
        return v in self.adj[u]

    def adjacency_matrix(self) -> np.ndarray:
        a = np.zeros((self.n, self.n), dtype=np.int8)
        for u in range(self.n):
            for v in self.adj[u]:
                a[u, v] = 1
        return a

    def copy(self) -> "Graph":
        return Graph(n=self.n, adj=[set(s) for s in self.adj])

    # -- substructure counting --------------------------------------------
    def average_degree(self) -> float:
        return 2.0 * self.m / self.n if self.n else 0.0

    def local_triangles(self, u: int) -> int:
        """Number of triangles that contain node ``u``."""
        nb = self.adj[u]
        cnt = 0
        for v in nb:
            cnt += len(nb & self.adj[v])
        return cnt // 2

    def count_triangles(self) -> int:
        """Exact global triangle count (1/3 * sum of local counts)."""
        if self.n <= 300:
            return sum(self.local_triangles(u) for u in range(self.n)) // 3
        a = self.adjacency_matrix().astype(np.int64)
        return int(np.einsum("ij,ij->", a @ a, a)) // 6

    def count_kstars(self, k: int) -> int:
        return sum(math.comb(d, k) for d in self.degrees())

    def ground_truth(self, task: str) -> float:
        if task == "degree":
            return self.average_degree()
        if task == "triangle":
            return float(self.count_triangles())
        return float(self.count_kstars(kstar_k(task)))

    # -- text encodings ---------------------------------------------------
    def edge_string(self) -> str:
        return " ".join(f"({u}, {v})" for u, v in self.edges)

    def __repr__(self) -> str:  # pragma: no cover - cosmetic
        return f"Graph(n={self.n}, m={self.m})"


def parse_edge_string(edge_string: str) -> list[tuple[int, int]]:
    """Parse ``"(0, 1) (0, 2)"`` into ``[(0, 1), (0, 2)]``."""
    return [
        (int(a), int(b))
        for a, b in re.findall(r"\(\s*(\d+)\s*,\s*(\d+)\s*\)", edge_string)
    ]


def relabel_edges(edges: Sequence[tuple]) -> tuple[int, list[tuple[int, int]]]:
    """Relabel arbitrary node ids to ``0..n-1`` (ordered by first appearance
    of the sorted id set) and drop self loops / duplicates."""
    ids = sorted({x for e in edges for x in e})
    mapping = {x: i for i, x in enumerate(ids)}
    out: set[tuple[int, int]] = set()
    for u, v in edges:
        a, b = mapping[u], mapping[v]
        if a == b:
            continue
        out.add((min(a, b), max(a, b)))
    return len(ids), sorted(out)


# ---------------------------------------------------------------------------
# Dataset records (Appendix A)
# ---------------------------------------------------------------------------


@dataclass
class TaskRecord:
    """One substructure counting instance in the unified dataset format."""

    index: int
    input_prompt: str
    edges: str
    vertex_num: int
    edge_num: int
    answer: float
    task: str
    dataset: str

    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "input_prompt": self.input_prompt,
            "edges": self.edges,
            "vertex_num": self.vertex_num,
            "edge_num": self.edge_num,
            "answer": self.answer,
            "task": self.task,
            "dataset": self.dataset,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "TaskRecord":
        return cls(**{k: d[k] for k in cls.__dataclass_fields__})  # type: ignore[arg-type]

    def graph(self) -> Graph:
        return Graph.from_edge_string(self.vertex_num, self.edges)


def build_records(name: str, graph: Graph, start_index: int = 1) -> list[TaskRecord]:
    """Create one record per task for a dataset."""
    records = []
    edge_str = graph.edge_string()
    for i, task in enumerate(TASKS):
        records.append(
            TaskRecord(
                index=start_index + i,
                input_prompt=task_prompt(task, graph.n),
                edges=edge_str,
                vertex_num=graph.n,
                edge_num=graph.m,
                answer=graph.ground_truth(task),
                task=task,
                dataset=name,
            ),
        )
    return records


def save_records(records: list[TaskRecord], path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump([r.to_dict() for r in records], f, indent=2)


def load_records(path: str | Path) -> list[TaskRecord]:
    with Path(path).open("r", encoding="utf-8") as f:
        return [TaskRecord.from_dict(d) for d in json.load(f)]


def load_dataset(data_dir: str | Path, name: str) -> dict[str, TaskRecord]:
    """Load ``{task: record}`` for a dataset abbreviation such as ``"CU"``."""
    recs = load_records(Path(data_dir) / f"{name}.json")
    return {r.task: r for r in recs}
