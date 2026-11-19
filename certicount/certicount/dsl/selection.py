"""Choice among certified candidate programs by simulating the whole release on public graphs.

The curator writes one program per release of the per-node architecture
(:func:`certicount.dsl.designer.design_candidates`): one that may read the noisy rows
``N(...)`` (RR of the full lists, then projection; biased, small GS) and one that may
read the unbiased matrix ``A(...)`` (projection, then RR of the projected lists; unbiased,
GS about ``2 e^ε1/(e^ε1 - 1)`` times larger). Which one is more accurate depends on the
graph: on PM (453 nodes) the matrix triangle count has RE 0.13 and the row count 1.5, on
CU / Do (49 / 62 nodes) the order is reversed (0.55 / 0.47 against 1.05 / 0.73), because
the Laplace noise of a small graph outweighs the bias of the rows.

Every candidate has passed the design checks (parse, derived GS, exact utility test,
falsifier); the system then runs each through the same DP pipeline as a real run
(:func:`certicount.dsl.ground_truth.dp_execute`: noisy degrees, per-node bounds, RR /
matrix release, projection, Laplace, aggregation) and keeps the most accurate one, in
two steps:

1. design time (:func:`select_program`): public Holme-Kim graphs with the public number
   of nodes, a grid of average degrees and two clustering levels; smallest geometric mean
   of the simulated relative error. This fixes the budget split (e.g. a program on ``P``
   alone against one that reads a release: their ``ε2`` differ).
2. run time (:func:`runtime_choice`, :func:`execute_selected`): if several usable
   candidates share the chosen split (the row and the matrix programs of one statistic),
   the run publishes its noisy degrees first (the ``ε2`` step they share) and the system
   picks among them on Chung-Lu graphs with those expected degrees. On CU / Do / PM
   triangles this picked the better release in 18 of 18 releases; the design-time grid,
   which knows ``n`` only, got Do wrong (a near tie on the grid, 0.43 against 0.70 on Do).

Both steps read ``n``, ε, the budget split, α, the published noisy degrees and fixed
seeds only: post-processing of public information, no budget. Each run still re-derives
the GS of the program it runs (:func:`certicount.dsl.sensitivity.verify_certificate`).

``useless``: a candidate whose score is at least this value is never chosen (with the
default 1.0 it is on average no better than answering 0 on the public graphs); if no
candidate is below it the design fails. This replaces the noise-free gate
(:mod:`certicount.dsl.noisy_gate`) and the min-GS rule, which judged a program by its bias
alone or by its GS alone.
"""

from __future__ import annotations

import math
import statistics as st
from dataclasses import asdict, dataclass
from functools import lru_cache

import numpy as np

from psc.dp import BudgetSplit, split_budget
from psc.ground_truth import relative_error
from psc.graph import Graph
from psc.mechanism import DEFAULT_MECHANISM

from .ground_truth import DSLTrace, degree_release, dp_execute
from .lang import Interpreter, Program
from .noisy_gate import holme_kim
from .utility import reference_counter


@dataclass(frozen=True)
class SimOptions:
    """Public settings of the simulated release (those of the deployment) and of the graphs."""

    n: int
    eps: float = 2.0
    node_bounds: bool = True
    alpha: float = 0.0
    mechanism: str = DEFAULT_MECHANISM
    r1: float = 0.5
    r2: float = 0.2
    avg_degrees: tuple[float, ...] = (4.0, 8.0, 16.0)
    triads: tuple[float, ...] = (0.1, 0.6)
    reps: int = 8
    seed: int = 11
    useless: float | None = 1.0

    def to_dict(self) -> dict:
        d = asdict(self)
        d["avg_degrees"], d["triads"] = list(self.avg_degrees), list(self.triads)
        return d


@lru_cache(maxsize=16)
def simulation_graphs(n: int, avg_degrees: tuple[float, ...], triads: tuple[float, ...],
                      seed: int) -> tuple[tuple[str, Graph], ...]:
    """Holme-Kim graphs on the public ``n``: ``m = avg_degree / 2`` edges per new node."""
    out = []
    for d in avg_degrees:
        m = max(1, min(n - 1, round(d / 2)))
        for p in triads:
            rng = np.random.default_rng([seed, n, m, round(100 * p)])
            out.append((f"Holme-Kim(n={n}, m={m}, p={p:g})", holme_kim(n, m, p, rng)))
    return tuple(out)


@lru_cache(maxsize=64)
def _truths(task: str, n: int, avg_degrees: tuple[float, ...], triads: tuple[float, ...],
            seed: int) -> tuple[float, ...]:
    count = reference_counter(task)
    return tuple(float(count(g)) for _, g in simulation_graphs(n, avg_degrees, triads, seed))


_SIM_CACHE: dict[tuple, dict] = {}


def simulate(program: Program, task: str, opts: SimOptions) -> dict:
    """Simulated accuracy of ``program``: per graph the mean relative error over
    ``opts.reps`` releases and the noise-free bias; ``score`` is the geometric mean of the
    per-graph errors (lower is better). Cached by program and settings."""
    key = (program.digest, task, opts)
    if key in _SIM_CACHE:
        return _SIM_CACHE[key]
    graphs = simulation_graphs(opts.n, opts.avg_degrees, opts.triads, opts.seed)
    truths = _truths(task, opts.n, opts.avg_degrees, opts.triads, opts.seed)
    interp = Interpreter(program)
    rows, error = [], None
    for (name, g), truth in zip(graphs, truths):
        res, free = [], []
        for i in range(opts.reps):
            try:
                tr = dp_execute(g, program, opts.eps, np.random.default_rng([opts.seed, 2, i]), task,
                                opts.mechanism, opts.r1, opts.r2, opts.node_bounds, opts.alpha)
            except (ArithmeticError, ValueError, TypeError, KeyError, OverflowError) as exc:
                error = f"{type(exc).__name__}: {exc}"
                break
            res.append(relative_error(tr.estimate, truth, g.n))
            free.append(interp.aggregate(float(sum(tr.counts)), g.n))
        if error:
            break
        rows.append({"graph": name, "truth": truth, "relative_error": st.mean(res),
                     "noise_free_bias": relative_error(st.mean(free), truth, g.n)})
    if error:
        out = {"score": math.inf, "error": error, "per_graph": rows}
    else:
        out = {"score": math.exp(st.mean(math.log(max(r["relative_error"], 1e-12)) for r in rows)),
               "noise_free_bias": st.mean(r["noise_free_bias"] for r in rows), "per_graph": rows}
    _SIM_CACHE[key] = out
    return out


def budget_split(program: Program, eps: float, r1: float = 0.5, r2: float = 0.2) -> BudgetSplit:
    """The split a run of ``program`` uses (as :func:`certicount.dsl.ground_truth.dp_execute`)."""
    a, b = program.budget_fractions(r1, r2)
    return split_budget(eps, program.uses_release, program.needs_degree_bound, a, b)


@dataclass
class Selection:
    """``chosen``: the design-time choice (index of the candidate list, ``None``: no usable
    candidate). ``runtime``: the usable candidates with the same budget split as ``chosen``
    and a degree release (``ε2 > 0``); with two or more, each run picks one of them after its
    noisy degrees are published (:func:`runtime_choice`), otherwise ``[chosen]``."""

    chosen: int | None
    runtime: list[int]
    rows: list[dict]

    def to_dict(self) -> dict:
        return {"chosen": self.chosen, "runtime": self.runtime, "candidates": self.rows}


def select_program(programs: list[Program], task: str, opts: SimOptions) -> Selection:
    """Design-time choice on the public Holme-Kim graphs (smallest score below
    ``opts.useless``), and the alternatives left to the run-time choice."""
    rows = []
    for i, prog in enumerate(programs):
        sim = simulate(prog, task, opts)
        usable = math.isfinite(sim["score"]) and (opts.useless is None or sim["score"] < opts.useless)
        rows.append({"index": i, "score": sim["score"], "noise_free_bias": sim.get("noise_free_bias"),
                     "usable": usable, "error": sim.get("error"),
                     "split": list(budget_split(prog, opts.eps, opts.r1, opts.r2).as_tuple()),
                     "per_graph": [{k: r[k] for k in ("graph", "relative_error")} for r in sim["per_graph"]]})
    usable = [r for r in rows if r["usable"]]
    if not usable:
        return Selection(None, [], rows)
    best = min(usable, key=lambda r: (r["score"], r["index"]))
    same = [r["index"] for r in usable if r["split"] == best["split"]]
    runtime = same if best["split"][1] > 0 and len(same) > 1 else [best["index"]]
    return Selection(best["index"], runtime, rows)


# ---------------------------------------------------------------------------
# Run-time choice from the published noisy degrees
# ---------------------------------------------------------------------------


def chung_lu(weights: np.ndarray, rng: np.random.Generator) -> Graph:
    """Chung-Lu graph: edge ``uv`` with probability ``min(1, w_u w_v / sum(w))``."""
    n = len(weights)
    total = float(weights.sum())
    if n < 2 or total <= 0:
        return Graph.from_edges(n, [])
    iu = np.triu_indices(n, 1)
    prob = np.minimum(1.0, weights[iu[0]] * weights[iu[1]] / total)
    keep = rng.random(len(prob)) < prob
    return Graph.from_edges(n, list(zip(iu[0][keep].tolist(), iu[1][keep].tolist())))


_RUNTIME_CACHE: dict[tuple, tuple[int, list[float]]] = {}


def runtime_reps(n: int) -> int:
    """Releases per Chung-Lu graph: more on small graphs (cheap, and their errors vary more)."""
    return max(4, min(32, 2000 // max(1, n)))


def runtime_choice(programs: list[Program], task: str, reports: list[float], opts: SimOptions,
                   graphs: int = 3, reps: int | None = None) -> tuple[int, list[float]]:
    """``(index, scores)``: the candidate with the smallest simulated error on ``graphs``
    Chung-Lu graphs whose expected degrees are the published ``max(y_i, 0)`` (``reps``
    releases each, default :func:`runtime_reps`). Reads only the degree release of this run
    (public) and fixed seeds: it never consumes the run's noise."""
    reps = runtime_reps(len(reports)) if reps is None else reps
    key = (tuple(p.digest for p in programs), task, tuple(round(float(y), 9) for y in reports), opts, graphs, reps)
    if key in _RUNTIME_CACHE:
        return _RUNTIME_CACHE[key]
    weights = np.clip(np.asarray(reports, dtype=float), 0.0, None)
    count = reference_counter(task)
    tests = []
    for k in range(graphs):
        g = chung_lu(weights, np.random.default_rng([opts.seed, 3, k]))
        tests.append((g, float(count(g))))
    scores = []
    for prog in programs:
        errs = []
        for g, truth in tests:
            try:
                errs.append(st.mean(
                    relative_error(dp_execute(g, prog, opts.eps, np.random.default_rng([opts.seed, 4, i]), task,
                                              opts.mechanism, opts.r1, opts.r2, opts.node_bounds, opts.alpha).estimate,
                                   truth, g.n) for i in range(reps)))
            except (ArithmeticError, ValueError, TypeError, KeyError, OverflowError):
                errs.append(math.inf)
        scores.append(math.exp(st.mean(math.log(max(e, 1e-12)) for e in errs)) if all(map(math.isfinite, errs))
                      else math.inf)
    out = (min(range(len(programs)), key=lambda i: (scores[i], i)), scores)
    _RUNTIME_CACHE[key] = out
    return out


def execute_selected(graph: Graph, programs: list[Program], sel: Selection, task: str, opts: SimOptions,
                     rng: np.random.Generator) -> tuple[DSLTrace, int, list[float] | None]:
    """One DP run with the selection: ``(trace, index of the program run, run-time scores)``.
    With run-time alternatives the run first publishes the noisy degrees (the ``ε2`` step all
    alternatives share), picks the program from them, then continues with the same reports."""
    if sel.chosen is None:
        raise ValueError("no usable candidate")
    if len(sel.runtime) < 2:
        prog = programs[sel.chosen]
        return (dp_execute(graph, prog, opts.eps, rng, task, opts.mechanism, opts.r1, opts.r2, opts.node_bounds,
                           opts.alpha), sel.chosen, None)
    alts = [programs[i] for i in sel.runtime]
    split = budget_split(alts[0], opts.eps, opts.r1, opts.r2)
    reports = degree_release(graph, split.eps2, rng)
    k, scores = runtime_choice(alts, task, reports, opts)
    tr = dp_execute(graph, alts[k], opts.eps, rng, task, opts.mechanism, opts.r1, opts.r2, opts.node_bounds,
                    opts.alpha, degree_reports=reports)
    return tr, sel.runtime[k], scores
