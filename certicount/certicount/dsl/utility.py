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
    return float(sum(math.comb(len(g.neighbors(u)), k) for u in range(g.n)))


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


def run_exact(program: Program, g: Graph, truncate: bool = True) -> float:
    """The program's answer without noise on graph ``g`` (``G'`` = ``g``, ``D = dmax = n - 1``).

    ``truncate=False`` also turns ``project`` into the identity, so a program that
    lowers its threshold below ``D`` on purpose (a bias / noise trade-off) is still
    checked for computing the right statistic."""
    interp = Interpreter(program)
    rows = {u: frozenset(g.adj[u]) for u in range(g.n)}
    d = max(1, g.n - 1)
    kw = {} if truncate else {"projector": _no_projection}
    total = sum(interp.local(Env(frozenset(g.adj[u]), u, rows, g.n, D=d, dmax=d, **kw)) for u in range(g.n))
    return interp.aggregate(total, g.n)


def _no_projection(s: frozenset, k: int) -> frozenset:
    return s


def _graph(n: int, edges) -> Graph:
    return Graph.from_edges(n, list(edges))


def named_graphs() -> list[tuple[str, Graph]]:
    """Small graphs with a known structure; failures on them read as symptoms."""
    return [
        ("an empty graph (no edges)", _graph(5, [])),
        ("a single edge", _graph(5, [(0, 1)])),
        ("a path 0-1-2-3-4 (no triangle)", _graph(5, [(0, 1), (1, 2), (2, 3), (3, 4)])),
        ("a star with center 0 and 5 leaves (no triangle)", _graph(6, [(0, i) for i in range(1, 6)])),
        ("a 5-cycle (no triangle)", _graph(5, [(0, 1), (1, 2), (2, 3), (3, 4), (0, 4)])),
        ("a single triangle", _graph(5, [(0, 1), (1, 2), (0, 2)])),
        ("a triangle with a pendant edge", _graph(5, [(0, 1), (1, 2), (0, 2), (2, 3)])),
        ("two disjoint triangles", _graph(6, [(0, 1), (1, 2), (0, 2), (3, 4), (4, 5), (3, 5)])),
        ("a complete graph on 4 nodes", _graph(4, [(u, v) for u in range(4) for v in range(u + 1, 4)])),
        ("a complete graph on 6 nodes", _graph(6, [(u, v) for u in range(6) for v in range(u + 1, 6)])),
    ]


def sized_graphs(n: int, count: int = 3, seed: int = 1) -> list[Graph]:
    """Sparse random graphs with the real (public) number of nodes ``n``."""
    rng = np.random.default_rng(seed)
    out = []
    for avg in np.linspace(3.0, 10.0, count):
        p = min(0.9, float(avg) / max(1, n - 1))
        out.append(Graph.from_edges(n, [(u, v) for u in range(n) for v in range(u + 1, n) if rng.random() < p]))
    return out


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
        return f"utility test failed on {len(self.failures)}/{self.graphs} public test graphs. " + symptoms(self.failures)


def _describe(f: dict) -> str:
    where = f.get("name") or f"a random graph with n={f['n']} and edges {f['edges']}"
    return f"on {where} the program gives {f['program']:g}, the exact answer is {f['reference']:g}"


def symptoms(failures: list[dict]) -> str:
    """What goes wrong, in terms of observable behaviour (never the fix)."""
    named = [f for f in failures if f.get("name")]
    shown = (named or failures)[:3]
    out = ["Examples: " + "; ".join(_describe(f) for f in shown) + "."]
    zero = [f for f in failures if f["reference"] == 0 and f["program"] != 0]
    if zero:
        out.append(f"The program is non-zero on {len(zero)} graph(s) whose exact answer is 0, so it counts "
                   "something that is not the requested structure.")
    ratios = [f["program"] / f["reference"] for f in failures if f["reference"]]
    if ratios and max(ratios) - min(ratios) <= 1e-6 * max(1.0, abs(ratios[0])):
        out.append(f"On every failing graph the answer is exactly {ratios[0]:g} times the exact answer: "
                   "a constant factor (local formula or aggregate) is off.")
    elif failures and all(f["program"] > f["reference"] for f in failures):
        out.append("The program over-counts on every failing graph.")
    elif failures and all(f["program"] < f["reference"] for f in failures):
        out.append("The program under-counts on every failing graph.")
    sizes = {f["n"] for f in failures}
    big = [f for f in failures if f.get("sized")]
    if big and len(big) == len(failures):
        out.append(f"It is exact on all small graphs but wrong on graphs with n = {sorted(sizes)[0]} nodes: the "
                   "computation must not change with the number of nodes.")
    return " ".join(out)


def utility_test(program: Program, task: str, count: int = 30, seed: int = 0, rel_tol: float = 1e-9,
                 n_range: tuple[int, int] = (5, 14), public_n: int | None = None, truncate: bool = True,
                 named: bool = True) -> UtilityReport:
    """Differential test against the brute-force counter on named small graphs,
    ``count`` random graphs and (``public_n``) a few graphs with the real number
    of nodes -- a program cannot pass by switching its behaviour on ``n``."""
    ref = reference_counter(task)
    failures = []
    cases: list[tuple[str | None, Graph, bool]] = [(name, g, False) for name, g in (named_graphs() if named else [])]
    cases += [(None, g, False) for g in random_graphs(count, seed, n_range)]
    if public_n is not None and public_n > n_range[1]:
        cases += [(None, g, True) for g in sized_graphs(public_n)]
    for name, g, sized in cases:
        got, want = run_exact(program, g, truncate), ref(g)
        if not math.isclose(got, want, rel_tol=rel_tol, abs_tol=1e-9):
            failures.append({"n": g.n, "edges": g.edges[:20], "program": got, "reference": want,
                             "name": name, "sized": sized})
    return UtilityReport(not failures, len(cases), failures)
