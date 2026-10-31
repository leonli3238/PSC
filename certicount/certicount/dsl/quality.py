"""Quality of a designed DSL program against the reference program of its task.

The design loop (:mod:`certicount.dsl.designer`) only accepts programs that parse,
have a finite, not obviously loose GS and pass a small utility test. A program
can pass all three and still be worse than the reference (e.g.
``project(P, 2 * D)`` doubles the threshold and multiplies the k-star GS), or
compute a different statistic on graphs the test did not cover. This module
measures, from public information only:

* ``same_as_reference`` -- structurally identical to the reference AST;
* ``split_match`` -- the program asks for the same DP steps (noisy graph,
  degree bound), so the budget split equals the reference split;
* ``gs_ratio`` -- derived GS / GS of the reference program at the same public
  bound (``1`` optimal, ``> 1`` more noise than needed);
* ``semantic_pass`` -- an independent utility test on more and larger random
  graphs (another seed than the design loop);
* ``sound`` -- the falsifier finds no flip that exceeds the derived GS.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field

from psc.graph import TaskRecord

from .falsifier import falsify
from .ground_truth import gs_ratio, reference_program
from .lang import Program
from .library import analyst_prompt
from .sensitivity import PublicParams, SensitivityError, derive
from .utility import reference_counter, utility_test


@dataclass
class DesignQuality:
    same_as_reference: bool
    split_match: bool
    gs_ratio: float | None
    gs_ratios: dict[int, float | None]
    semantic_pass: bool
    semantic_failures: int
    semantic_graphs: int
    sound: bool | None
    falsifier_max_delta: float | None
    problems: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def same_structure(a: Program, b: Program) -> bool:
    return (a.assigns, a.ret, a.aggregate, a.clamp_nonnegative) == (b.assigns, b.ret, b.aggregate, b.clamp_nonnegative)


def design_quality(
    program: Program, task: str, n: int, reference_bound: int, bounds: tuple[int, ...] = (5, 10, 20),
    utility_graphs: int = 100, utility_seed: int = 1, utility_n: tuple[int, int] = (5, 16),
    falsify_program: bool = True, falsify_n: int = 5, falsify_dmax: int = 3,
) -> DesignQuality:
    ref = reference_program(task)
    problems: list[str] = []
    ratios: dict[int, float | None] = {}
    for b in sorted({*bounds, reference_bound}):
        p = PublicParams(n, D=b, dmax=b)
        try:
            ratios[b] = gs_ratio(derive(program, p).gs, derive(ref, p).gs)
        except SensitivityError as exc:
            ratios[b] = None
            problems.append(f"D={b}: {exc}")
    rep = utility_test(program, task, count=utility_graphs, seed=utility_seed, n_range=utility_n)
    if not rep.passed:
        problems.append(rep.feedback())
    sound, delta = None, None
    if falsify_program:
        try:
            claimed = derive(program, PublicParams(falsify_n, falsify_dmax, falsify_dmax)).gs
            refuted, ce = falsify(program, claimed, n=falsify_n, dmax=falsify_dmax)
            sound, delta = not refuted, ce.max_delta
            if refuted:
                problems.append(f"falsifier: a flip changes the count by {ce.max_delta:g} > GS {claimed:g}")
        except SensitivityError as exc:
            problems.append(f"falsifier skipped: {exc}")
    return DesignQuality(
        same_as_reference=same_structure(program, ref),
        split_match=(program.uses_rows, program.needs_degree_bound) == (ref.uses_rows, ref.needs_degree_bound),
        gs_ratio=ratios.get(reference_bound), gs_ratios=ratios,
        semantic_pass=rep.passed, semantic_failures=len(rep.failures), semantic_graphs=rep.graphs,
        sound=sound, falsifier_max_delta=delta, problems=problems,
    )


def task_record(recs: dict[str, TaskRecord], dataset: str, task: str) -> TaskRecord:
    """The dataset's record of ``task``; out-of-library tasks reuse the graph
    with the analyst prompt and the brute-force answer of the task."""
    if task in recs:
        return recs[task]
    base = next(iter(recs.values()))
    g = base.graph()
    return TaskRecord(0, analyst_prompt(task, g.n), base.edges, g.n, g.m, reference_counter(task)(g), task, dataset)


def finite_mean(values) -> float | None:
    vals = [float(v) for v in values if v is not None and math.isfinite(float(v))]
    return sum(vals) / len(vals) if vals else None
