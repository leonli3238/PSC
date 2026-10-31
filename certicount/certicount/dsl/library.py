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

PROGRAMS: dict[str, ProgramSource] = {
    "degree": ProgramSource("return size(P)", "total / n"),
    "2-star": kstar_source(2),
    "3-star": kstar_source(3),
    "triangle": TRIANGLE,
    # out of the paper's library
    "4-star": kstar_source(4),
    "5-star": kstar_source(5),
    "degree-moment2": ProgramSource("return pow(size(project(P, D)), 2)"),
}
OUT_OF_LIBRARY: tuple[str, ...] = ("4-star", "5-star", "degree-moment2")

HAND_GS: dict[str, Callable[[PublicParams], float]] = {
    "degree": lambda p: 1.0,
    "2-star": lambda p: float(max(0, p.D - 1)),
    "3-star": lambda p: float(math.comb(max(0, p.D - 1), 2)),
    "4-star": lambda p: float(math.comb(max(0, p.D - 1), 3)),
    "5-star": lambda p: float(math.comb(max(0, p.D - 1), 4)),
    "triangle": lambda p: float(p.dmax - 1),
    "degree-moment2": lambda p: float(2 * p.D - 1) if p.D >= 1 else 0.0,
}

_EXT_DESCRIPTIONS = {
    "degree-moment2": (
        "The second moment of the degree distribution is the sum over all nodes of "
        "degree(node) * degree(node), where degree(node) is the number of edges connected to the node.",
        "What is the sum of the squared degrees of the graph?",
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
