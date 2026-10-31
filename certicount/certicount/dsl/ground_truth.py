"""Pure-code DP execution of DSL programs: GT-DSL and the paired reference of a design.

:func:`dp_execute` runs a program through the same DP steps as the
``execution="program"`` mode of :class:`certicount.framework.TrustedPSCFramework`
(budget split from the program, per-node RR, noisy degrees, projection, node
interpreter, Laplace report, aggregation) and consumes the random numbers in
the same order, so for a given ``rng`` and the same program both return the
same estimate (``tests/test_dsl_eval.py``). No model is called.

``GT-DSL`` (:func:`gt_dsl`) is this execution with the reference program of the
task (:data:`certicount.dsl.library.PROGRAMS`), i.e. what a perfect designer would
achieve. On the noise of the same run a designed program differs from GT-DSL
only through its design (local function, GS, budget split): the paired
difference of the two errors is the error the LLM designer adds.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

from psc.dp import graph_projection, laplace_noise, node_noisy_lower_row, project_neighbor_list, split_budget
from psc.graph import TASKS, Graph
from psc.mechanism import DEFAULT_MECHANISM, MechanismProfile, get_mechanism

from .lang import Env, Interpreter, Program, smallest_projector
from .library import HAND_GS, PROGRAMS
from .sensitivity import PublicParams, derive


@dataclass
class DSLTrace:
    estimate: float
    split: tuple[float, float, float]
    gs: float
    d_hat_max: int | None
    counts: list[float] = field(default_factory=list, repr=False)
    reports: list[float] = field(default_factory=list, repr=False)

    def to_dict(self) -> dict:
        return {"estimate": self.estimate, "split": list(self.split), "gs": self.gs, "d_hat_max": self.d_hat_max}


def degree_class(task: str | None, program: Program) -> str:
    """Task whose rounding the degree bound uses (as in the framework)."""
    if task in TASKS:
        return task
    return "triangle" if program.uses_rows else "3-star"


def dp_execute(
    graph: Graph, program: Program, eps: float, rng: np.random.Generator, task: str | None = None,
    mechanism: str | MechanismProfile = DEFAULT_MECHANISM, r1: float = 0.5, r2: float = 0.2,
) -> DSLTrace:
    """One DP run of ``program`` on ``graph`` (GS derived from the program)."""
    n = graph.n
    mech = get_mechanism(mechanism)
    cls = degree_class(task, program)
    split = split_budget(eps, program.uses_rows, program.needs_degree_bound, r1, r2)
    real = [sorted(int(x) for x in graph.adj[i]) for i in range(n)]

    noisy = None
    if split.eps1 > 0:  # Algorithm 1, node by node as the agents do it
        released = [(i, j) for i in range(n) for j in node_noisy_lower_row(i, real[i], split.eps1, rng)]
        noisy = Graph.from_edges(n, released)

    d_hat = None
    update = [list(r) for r in real]
    limits: list[int | None] = [None] * n
    if split.eps2 > 0:  # Algorithm 2
        reports = [len(real[i]) + laplace_noise(1.0, split.eps2, rng) for i in range(n)]
        d_hat = mech.degree_bound(reports, cls).projection_degree
        if noisy is not None:
            noisy = graph_projection(noisy, d_hat, rng)
        else:
            per_node = mech.node_projection_degrees(reports, d_hat, cls, split.eps2)
            limits = [d_hat] * n if per_node is None else [int(x) for x in per_node]
            update = [project_neighbor_list(real[i], limits[i], rng) for i in range(n)]

    params = PublicParams(n, D=d_hat, dmax=d_hat)
    gs = derive(program, params).gs
    rows = {i: frozenset(noisy.adj[i]) for i in range(n)} if noisy is not None else {}
    D = int(d_hat or 0)
    interp = Interpreter(program)

    def projector_of(i: int):
        own, kept, limit = frozenset(real[i]), frozenset(update[i]), limits[i]

        def projector(s: frozenset, k: int) -> frozenset:
            if s == own and k == limit:  # the projection drawn above (TrustedNodeAgent._projector)
                return kept
            return smallest_projector(s, k)

        return projector

    counts = [interp.local(Env(frozenset(real[i]), i, rows, n, D=D, dmax=D, projector=projector_of(i))) for i in range(n)]
    reports_out = [c + laplace_noise(gs, split.eps3, rng) for c in counts]
    estimate = interp.aggregate(float(sum(reports_out)), n)
    return DSLTrace(estimate, split.as_tuple(), gs, d_hat, counts, reports_out)


def reference_program(task: str) -> Program:
    if task not in PROGRAMS:
        raise KeyError(f"no reference program for {task!r}; known: {', '.join(PROGRAMS)}")
    return PROGRAMS[task].parse()


def gt_dsl(graph: Graph, task: str, eps: float, rng: np.random.Generator,
           mechanism: str | MechanismProfile = DEFAULT_MECHANISM, r1: float = 0.5, r2: float = 0.2) -> DSLTrace:
    """GT-DSL: the reference program of ``task`` executed in code."""
    return dp_execute(graph, reference_program(task), eps, rng, task, mechanism, r1, r2)


def hand_gs(task: str, d_hat: int | None, n: int) -> float | None:
    """Hand-derived GS of the reference program (for the record; equals the derivation)."""
    if task not in HAND_GS:
        return None
    try:
        return HAND_GS[task](PublicParams(n, D=d_hat, dmax=d_hat))
    except TypeError:
        return None


def gs_ratio(gs: float | None, reference: float | None) -> float | None:
    if gs is None or reference is None:
        return None
    if reference == 0:
        return 1.0 if gs == 0 else math.inf
    return gs / reference
