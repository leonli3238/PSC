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

from .clipping import edge_clipping_bounds
from .lang import Env, Interpreter, Program, node_projector, smallest_projector
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
    aggregate_coefficient: float = 1.0
    node_gs: list[float] | None = field(default=None, repr=False)  # per-node bounds only; ``gs`` is their max

    @property
    def final_noise_scale(self) -> float:
        """Laplace scale of one report as seen in the estimate: ``|c| · GS / ε3`` (largest GS)."""
        return final_noise_scale(self.aggregate_coefficient, self.gs, self.split[2])

    def to_dict(self) -> dict:
        d = {"estimate": self.estimate, "split": list(self.split), "gs": self.gs, "d_hat_max": self.d_hat_max,
             "aggregate_coefficient": self.aggregate_coefficient, "final_noise_scale": self.final_noise_scale}
        if self.node_gs is not None:
            d["node_gs_mean"] = float(np.mean(self.node_gs))
        return d


def final_noise_scale(coefficient: float, gs: float | None, eps3: float) -> float | None:
    if gs is None:
        return None
    if not eps3:
        return 0.0 if gs == 0 else math.inf
    return abs(coefficient) * gs / eps3


def degree_class(task: str | None, program: Program) -> str:
    """Task whose rounding the degree bound uses (as in the framework)."""
    if task in TASKS:
        return task
    return "triangle" if program.uses_rows else "3-star"


def dp_execute(
    graph: Graph, program: Program, eps: float, rng: np.random.Generator, task: str | None = None,
    mechanism: str | MechanismProfile = DEFAULT_MECHANISM, r1: float = 0.5, r2: float = 0.2,
    node_bounds: bool = False, alpha: float = 0.0,
) -> DSLTrace:
    """One DP run of ``program`` on ``graph`` (GS derived from the program).

    ``r1`` / ``r2`` are the default budget fractions; a program that sets its own
    ``budget`` uses that instead (as the framework does). ``node_bounds``: every
    node clips its list to its own bound ``D_i`` (edge clipping, Imola et al.
    2022, :mod:`certicount.dsl.clipping`) and reports with the GS at ``D_i``."""
    n = graph.n
    mech = get_mechanism(mechanism)
    cls = degree_class(task, program)
    r1, r2 = program.budget_fractions(r1, r2)
    split = split_budget(eps, program.uses_rows, program.needs_degree_bound, r1, r2)
    real = [sorted(int(x) for x in graph.adj[i]) for i in range(n)]

    noisy = None
    if split.eps1 > 0:  # Algorithm 1, node by node as the agents do it
        released = [(i, j) for i in range(n) for j in node_noisy_lower_row(i, real[i], split.eps1, rng)]
        noisy = Graph.from_edges(n, released)

    d_hat = None
    # one projection order per node (TrustedNodeAgent.bound_degree); identity without a bound
    projectors = [smallest_projector] * n
    limits: list[int] | None = None
    if split.eps2 > 0:  # Algorithm 2
        reports = [len(real[i]) + laplace_noise(1.0, split.eps2, rng) for i in range(n)]
        d_hat = mech.degree_bound(reports, cls).projection_degree
        if noisy is not None:
            noisy = graph_projection(noisy, d_hat, rng)
        if node_bounds:
            limits = edge_clipping_bounds(reports, alpha)
        elif noisy is None:
            per_node = mech.node_projection_degrees(reports, d_hat, cls, split.eps2)
            limits = [d_hat] * n if per_node is None else [int(x) for x in per_node]
        if limits is not None:
            for i in range(n):
                kept = project_neighbor_list(real[i], limits[i], rng)
                projectors[i] = node_projector(n, real[i], kept, rng)

    rows = {i: frozenset(noisy.adj[i]) for i in range(n)} if noisy is not None else {}
    dmax = int(d_hat or 0)
    node_D = limits if node_bounds and limits is not None else [dmax] * n
    gs_of: dict[int, float] = {}
    for D in set(node_D):
        gs_of[D] = derive(program, PublicParams(n, D=D if d_hat is not None else None,
                                                dmax=d_hat)).gs
    node_gs = [gs_of[D] for D in node_D]
    interp = Interpreter(program)
    counts = [interp.local(Env(frozenset(real[i]), i, rows, n, D=node_D[i], dmax=dmax, projector=projectors[i]))
              for i in range(n)]
    reports_out = [c + laplace_noise(g, split.eps3, rng) for c, g in zip(counts, node_gs)]
    estimate = interp.aggregate(float(sum(reports_out)), n)
    return DSLTrace(estimate, split.as_tuple(), max(node_gs), d_hat, counts, reports_out,
                    interp.aggregate_coefficient(n), node_gs if node_bounds else None)


def reference_program(task: str) -> Program:
    if task not in PROGRAMS:
        raise KeyError(f"no reference program for {task!r}; known: {', '.join(PROGRAMS)}")
    return PROGRAMS[task].parse()


def gt_dsl(graph: Graph, task: str, eps: float, rng: np.random.Generator,
           mechanism: str | MechanismProfile = DEFAULT_MECHANISM, r1: float = 0.5, r2: float = 0.2,
           node_bounds: bool = False, alpha: float = 0.0) -> DSLTrace:
    """GT-DSL: the reference program of ``task`` executed in code (``node_bounds``:
    with per-node edge clipping, :mod:`certicount.dsl.clipping`)."""
    return dp_execute(graph, reference_program(task), eps, rng, task, mechanism, r1, r2, node_bounds, alpha)


def hand_gs(task: str, d_hat: int | None, n: int) -> float | None:
    """Hand-derived GS of the reference program (for the record; equals the derivation)."""
    if task not in HAND_GS:
        return None
    try:
        return HAND_GS[task](PublicParams(n, D=d_hat, dmax=d_hat))
    except TypeError:
        return None


def gs_ratio(gs: float | None, reference: float | None) -> float | None:
    """GS / reference GS. Ignores the aggregation coefficient and the budget split:
    use :func:`noise_ratio` to compare the noise that reaches the estimate."""
    if gs is None or reference is None:
        return None
    if reference == 0:
        return 1.0 if gs == 0 else math.inf
    return gs / reference


def noise_ratio(scale: float | None, reference: float | None) -> float | None:
    """Final noise scale ``|c| · GS / ε3`` of a design over the reference's (1 = same noise)."""
    return gs_ratio(scale, reference)
