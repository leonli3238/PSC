"""Reference programs: the three library tasks and out-of-library tasks.

``HAND_GS`` holds the hand-derived sensitivities the deriver must reproduce
(acceptance criterion of the proposal: ``1``, ``C(D-1, 2)``, ``dmax - 1``).
``TASK_TEXT`` gives analyst prompts for the out-of-library tasks in the format
of :func:`psc.graph.task_prompt` (Appendix A of the paper).
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Callable

from psc.graph import TASKS as LIBRARY_TASKS, task_prompt

from .lang import Program, parse_program
from .matrix import rr_constants
from .sensitivity import PublicParams


@dataclass(frozen=True)
class ProgramSource:
    local: str
    aggregate: str = "total"

    def parse(self) -> Program:
        return parse_program(self.local, self.aggregate)


def kstar_source(k: int, projected: bool = True) -> ProgramSource:
    arg = "size(project(P, D))" if projected else "size(P)"
    return ProgramSource(f"return comb({arg}, {k})")


TRIANGLE = ProgramSource("S = P & N(self)\nreturn 0.5 * sum(size(P & N(j)) for j in S)", "total / 3")
# NAM-DPRD's TriTR local statistic: the unbiased matrix summed over the pairs of the
# node's projected list (each triangle counted 6 times over ordered pairs and corners)
TRIANGLE_MATRIX = ProgramSource("Q = project(P, D)\nreturn sum(sum(A(j, k) for k in Q) for j in Q)", "total / 6")
# Open wedges (paths u - c - w whose ends u, w are not adjacent), counted at the centre c:
# for every projected neighbour j, the other projected neighbours not joined to j in the noisy
# graph (j itself is in Q - N(j), hence the - 1), each wedge seen from both ends. A training
# task of the prompt evolution that reads the release like the triangle does, so the triangle
# can stay held out (as 3-star / 5-star are held out from 2-star / 4-star).
OPEN_WEDGE = ProgramSource("Q = project(P, D)\nreturn 0.5 * sum(size(Q - N(j)) - 1 for j in Q)")
OPEN_WEDGE_MATRIX = ProgramSource(
    "Q = project(P, D)\nreturn comb(size(Q), 2) - 0.5 * sum(sum(A(j, k) for k in Q) for j in Q)")
# Rows triangle of the per-node architecture: the projected list against the noisy rows (the library
# TRIANGLE reads N(self), which the own-row check rejects there).
TRIANGLE_ROWS = ProgramSource("Q = project(P, D)\nreturn 0.5 * sum(size(Q & N(j)) for j in Q)", "total / 3")

# Extension tasks (CS9): statistics of other kinds than the PSC library, which PSC never ran. Expert
# programs for the paired comparison only: they never reach the curator's prompt
# (prompt_spec.GUARDED_TASKS, prompt_spec.core_leak_check).
#   degree-ge3     nodes of degree >= 3: an indicator of the private degree, no release
#   triangle-node  nodes on at least one triangle: an indicator of a substructure count (rows / matrix)
#   triangle-edge  edges on at least one triangle: indicators per neighbour, each edge seen from both ends
#   4-cycle        4-cycles: two hops through the noisy rows (certified, but the GS is about D * dmax)
DEGREE_GE3 = ProgramSource("return clip(size(P) - 2, 0, 1)")
TRIANGLE_NODE = ProgramSource("Q = project(P, D)\nreturn clip(sum(size(Q & N(v)) for v in Q), 0, 1)")
TRIANGLE_NODE_MATRIX = ProgramSource("Q = project(P, D)\nreturn clip(sum(sum(A(v, w) for w in Q) for v in Q), 0, 1)")
TRIANGLE_EDGE = ProgramSource("Q = project(P, D)\nreturn 0.5 * sum(clip(size(Q & N(v)), 0, 1) for v in Q)")
TRIANGLE_EDGE_MATRIX = ProgramSource(
    "Q = project(P, D)\nreturn 0.5 * sum(clip(sum(A(v, w) for w in Q), 0, 1) for v in Q)")
# pairs (v, w) of projected neighbours (both orders, v = w included), common noisy neighbours minus this
# node itself; a 4-cycle is counted at each of its 4 nodes
FOUR_CYCLE = ProgramSource(
    "Q = project(P, D)\n"
    "return 0.5 * sum(sum(size(N(v) & N(w)) for w in Q) for v in Q) - 0.5 * sum(size(N(v)) for v in Q) "
    "- comb(size(Q), 2)", "total / 4")
EXTENSION_TASKS: tuple[str, ...] = ("degree-ge3", "triangle-node", "triangle-edge", "4-cycle")

PROGRAMS: dict[str, ProgramSource] = {
    "degree": ProgramSource("return size(P)", "total / n"),
    "2-star": kstar_source(2),
    "3-star": kstar_source(3),
    "triangle": TRIANGLE,
    # out of the paper's library
    "4-star": kstar_source(4),
    "5-star": kstar_source(5),
    "degree-moment2": ProgramSource("return pow(size(project(P, D)), 2)"),
    "open-wedge": OPEN_WEDGE,
    "degree-ge3": DEGREE_GE3,
    "triangle-node": TRIANGLE_NODE,
    "triangle-edge": TRIANGLE_EDGE,
    "4-cycle": FOUR_CYCLE,
}
OUT_OF_LIBRARY: tuple[str, ...] = ("4-star", "5-star", "degree-moment2", "open-wedge", *EXTENSION_TASKS)

# Reference programs of the per-node architecture (``node_bounds``): edge clipping for
# every task, and NAM-DPRD's unbiased matrix for triangles; the other tasks keep PROGRAMS.
NODE_PROGRAMS: dict[str, ProgramSource] = {**PROGRAMS, "triangle": TRIANGLE_MATRIX, "open-wedge": OPEN_WEDGE_MATRIX,
                                           "triangle-node": TRIANGLE_NODE_MATRIX,
                                           "triangle-edge": TRIANGLE_EDGE_MATRIX}
# Expert program of each release for the tasks that have both (GT-Select, scripts/run_gt_select.py)
RELEASE_PAIRS: dict[str, dict[str, ProgramSource]] = {
    "triangle": {"rows": TRIANGLE_ROWS, "matrix": TRIANGLE_MATRIX},
    "open-wedge": {"rows": OPEN_WEDGE, "matrix": OPEN_WEDGE_MATRIX},
    "triangle-node": {"rows": TRIANGLE_NODE, "matrix": TRIANGLE_NODE_MATRIX},
    "triangle-edge": {"rows": TRIANGLE_EDGE, "matrix": TRIANGLE_EDGE_MATRIX},
}


def reference_source(task: str, node_bounds: bool = False) -> ProgramSource:
    table = NODE_PROGRAMS if node_bounds else PROGRAMS
    if task not in table:
        raise KeyError(f"no reference program for {task!r}; known: {', '.join(table)}")
    return table[task]


def matrix_triangle_gs(D: int, eps1: float) -> float:
    """Hand derivation of the GS of :data:`TRIANGLE_MATRIX` at bound ``D``.

    ``f(Q) = sum_{j,k in Q} A(j, k)``, ``A`` in ``[low, high]`` (``low = -1/(e^ε1 - 1)``,
    ``high = 1 + 1/(e^ε1 - 1)``), ``A(j, j) = 0``. A flip of one bit of ``P`` adds
    one vertex to ``Q`` (``|Q| <= D - 1`` before) or, when ``|Q| = D``, replaces a
    kept vertex ``w`` by ``v``; then ``f(Q') - f(Q) = 2 sum_{k in Q - w} (A(v, k) - A(w, k))``,
    so ``GS = 2 (D - 1)(high - low) = 2 (D - 1)(1 + 2/(e^ε1 - 1))``.

    NAM-DPRD's own calibration ``2 κ d~_i`` (``κ = high``, ``d~_i >= D``; used by
    :func:`psc.ground_truth.gt_tritr`) covers the addition but not the
    replacement: it is below this value for ``D >= 4`` when ``d~_i`` is close to ``D``
    (``tests/test_matrix.py`` gives the witness)."""
    low, high = rr_constants(eps1)
    return 2.0 * max(0, D - 1) * (high - low)


HAND_GS: dict[str, Callable[[PublicParams], float]] = {
    "degree": lambda p: 1.0,
    "2-star": lambda p: float(max(0, p.D - 1)),
    "3-star": lambda p: float(math.comb(max(0, p.D - 1), 2)),
    "4-star": lambda p: float(math.comb(max(0, p.D - 1), 3)),
    "5-star": lambda p: float(math.comb(max(0, p.D - 1), 4)),
    "triangle": lambda p: float(p.dmax - 1),
    "degree-moment2": lambda p: float(2 * p.D - 1) if p.D >= 1 else 0.0,
    # OPEN_WEDGE: a swap of one projected neighbour moves the entering and the leaving summand within
    # [0, D - 1] (j is in Q - N(j)) and each of the D - 1 common ones by at most 1, times 0.5. The
    # two-term form comb(size(Q), 2) - 0.5 * sum(size(N(j) & Q) ...) gets 2 (D - 1): the bounds of
    # the two terms add up although the terms move together.
    "open-wedge": lambda p: float(max(0, p.D - 1)),
    # extension tasks (rows and matrix programs alike: the clip bounds decide)
    "degree-ge3": lambda p: 1.0,  # one flip moves size(P) by 1, the indicator by at most 1
    # an indicator; with D = 1 the list Q = {v} has no pair, the count is always 0
    "triangle-node": lambda p: 1.0 if p.D >= 2 else 0.0,
    # an entering (or swapped) neighbour moves its own term and, for each of the other D - 1, one
    # indicator, each by at most 1, times 0.5
    "triangle-edge": lambda p: 0.5 * p.D,
    # term by term (the deriver's bound, not tight): an entering u adds 0.5 (2 (D - 1) + 1) dmax to the pair
    # sum, 0.5 dmax to the diagonal and D - 1 to comb(size(Q), 2)
    "4-cycle": lambda p: float(p.D * p.dmax + p.D - 1),
}

_EXT_DESCRIPTIONS = {
    "degree-moment2": (
        "The second moment of the degree distribution is the sum over all nodes of "
        "degree(node) * degree(node), where degree(node) is the number of edges connected to the node.",
        "What is the sum of the squared degrees of the graph?",
    ),
    "open-wedge": (
        "A wedge is a path of length two: a center node together with two of its neighbors. A wedge is "
        "open if its two end nodes are not connected by an edge. Every open wedge is counted once, at its "
        "center node.",
        "What is the total number of open wedges in the graph?",
    ),
    # extension tasks: the statistic in graph terms only, no formula (unlike the k-star prompts)
    "degree-ge3": (
        "The degree of a node is the number of edges connected to it.",
        "How many nodes of the graph have degree at least 3?",
    ),
    "triangle-node": (
        "A triangle consists of three nodes, each connected to the other two by an edge. A node belongs to a "
        "triangle if it is one of the triangle's three nodes.",
        "How many nodes of the graph belong to at least one triangle?",
    ),
    "triangle-edge": (
        "A triangle consists of three nodes, each connected to the other two by an edge. An edge belongs to a "
        "triangle if it is one of the triangle's three edges.",
        "How many edges of the graph belong to at least one triangle?",
    ),
    "4-cycle": (
        "A 4-cycle consists of four distinct nodes a, b, c, d and the four edges a-b, b-c, c-d and d-a; the "
        "edges a-c and b-d may or may not exist. A 4-cycle is the same cycle whichever of its nodes it starts "
        "from and in whichever direction it is traversed.",
        "What is the total number of 4-cycles in the graph?",
    ),
}


def kstar_text(k: int) -> tuple[str, str]:
    return (
        f"For each node, the number of {k}-stars centered at that node is the number of unordered "
        f"{k}-subsets of its neighbors, i.e. C(degree(node), {k}). The total number of {k}-stars in "
        f"the graph is the sum of {k}-stars centered at each node.",
        f"What is the total number of {k}-stars in the graph?",
    )


def analyst_prompt(task: str, n: int) -> str:
    """Analyst prompt for any supported task (library tasks: the paper's prompt)."""
    if task in LIBRARY_TASKS:
        return task_prompt(task, n)
    m = re.fullmatch(r"(\d+)-star", task)
    if m:
        desc, q = kstar_text(int(m.group(1)))
    elif task in _EXT_DESCRIPTIONS:
        desc, q = _EXT_DESCRIPTIONS[task]
    else:
        raise ValueError(f"no analyst prompt for task {task!r}")
    return (
        f"{desc} Each node may hide its edge information under the local edge differential privacy "
        f"framework. Q: The nodes are numbered from 0 to {n - 1}. {q}"
    )


def infer_program_task(prompt: str) -> str | None:
    """Keyword match used by the offline mock designer only."""
    p = prompt.lower()
    if "4-cycle" in p:
        return "4-cycle"
    if "at least one triangle" in p:
        return "triangle-edge" if "how many edges" in p else "triangle-node"
    if "degree at least 3" in p:
        return "degree-ge3"
    if "open wedge" in p:
        return "open-wedge"
    if "squared degree" in p or "second moment" in p:
        return "degree-moment2"
    m = re.search(r"(\d+)-stars?", p)
    if m:
        return f"{m.group(1)}-star"
    if "triangle" in p:
        return "triangle"
    if "degree" in p:
        return "degree"
    return None
