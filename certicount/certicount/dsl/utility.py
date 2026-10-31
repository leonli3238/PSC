"""Utility check (differential testing) of DSL programs on public synthetic graphs.

The sensitivity checker only says whether a program leaks; it does not say
whether the program computes the requested statistic (dropping the 0.5 of the
triangle program doubles the answer and the GS, and is still private). Here the
program is run without noise and without truncation (``D = dmax = n - 1``,
``G'`` = the graph itself) on random graphs and compared with an independent
brute-force counter. No private data is touched.
"""

from __future__ import annotations

import itertools
import math
import re
from dataclasses import dataclass, field
from typing import Callable

import numpy as np

from psc.graph import Graph

from .lang import Env, Interpreter, Program


def _brute_kstar(g: Graph, k: int) -> float:
    return float(sum(1 for u in range(g.n) for _ in itertools.combinations(g.neighbors(u), k)))


def _brute_triangles(g: Graph) -> float:
    return float(sum(
        1 for a, b, c in itertools.combinations(range(g.n), 3)
        if g.has_edge(a, b) and g.has_edge(b, c) and g.has_edge(a, c)
    ))


def reference_counter(task: str) -> Callable[[Graph], float]:
    """Independent brute-force implementation of a task (not the DSL program)."""
    if task == "degree":
        return lambda g: sum(len(g.adj[u]) for u in range(g.n)) / g.n
    if task == "triangle":
        return _brute_triangles
    if task == "degree-moment2":
        return lambda g: float(sum(len(g.adj[u]) ** 2 for u in range(g.n)))
    m = re.fullmatch(r"(\d+)-star", task)
    if m:
        k = int(m.group(1))
        return lambda g: _brute_kstar(g, k)
    raise ValueError(f"no reference counter for {task!r}")


def run_exact(program: Program, g: Graph) -> float:
    """The program's answer without noise or truncation on graph ``g``."""
    interp = Interpreter(program)
    rows = {u: frozenset(g.adj[u]) for u in range(g.n)}
    d = max(1, g.n - 1)
    total = sum(interp.local(Env(frozenset(g.adj[u]), u, rows, g.n, D=d, dmax=d)) for u in range(g.n))
    return interp.aggregate(total, g.n)


def random_graphs(count: int, seed: int = 0, n_range: tuple[int, int] = (5, 14)) -> list[Graph]:
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(count):
        n = int(rng.integers(n_range[0], n_range[1] + 1))
        p = float(rng.uniform(0.1, 0.9))
        out.append(Graph.from_edges(n, [(u, v) for u in range(n) for v in range(u + 1, n) if rng.random() < p]))
    return out


@dataclass
class UtilityReport:
    passed: bool
    graphs: int
    failures: list[dict] = field(default_factory=list)

    def feedback(self) -> str:
        if self.passed:
            return f"utility test passed on {self.graphs} graphs"
        f = self.failures[0]
        return (
            f"utility test failed on {len(self.failures)}/{self.graphs} random public graphs; e.g. a graph with "
            f"n={f['n']} and edges {f['edges']}: the program gives {f['program']:g}, the exact answer is {f['reference']:g}"
        )


def utility_test(program: Program, task: str, count: int = 30, seed: int = 0, rel_tol: float = 1e-9,
                 n_range: tuple[int, int] = (5, 14)) -> UtilityReport:
    ref = reference_counter(task)
    failures = []
    graphs = random_graphs(count, seed, n_range)
    for g in graphs:
        got, want = run_exact(program, g), ref(g)
        if not math.isclose(got, want, rel_tol=rel_tol, abs_tol=1e-9):
            failures.append({"n": g.n, "edges": g.edges[:20], "program": got, "reference": want})
    return UtilityReport(not failures, len(graphs), failures)
