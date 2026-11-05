"""Degree-first adaptive execution: release the noisy degrees, then choose the
bound, the budget split and the program from them.

PSC fixes the split (ε1, ε2, ε3) in advance and projects to the noisy maximum
degree ``D``. Here the noisy degrees ``y`` (ε2, Algorithm 2 lines 1-3) are
released first. A selector that sees only public values (``n``, ε, ε2, ``y``,
``D``) chooses a :class:`Candidate`: a DSL program, a bound ``B`` that replaces
``D`` for the projection and the GS, and ε1 (the RR budget of a program that
reads ``N``). The remaining steps then run with ε3 = ε − ε2 − ε1.

Privacy: ``y`` is ε2-edge LDP. The choice is post-processing of ``y`` and every
candidate spends exactly ε − ε2 on the remaining steps, so a run is ε-edge LDP
by adaptive sequential composition of pure DP (the privacy loss of every step
is bounded by its ε whatever the history, and the bounds always sum to ε). The
GS of the chosen program is derived at ``B`` by the deriver, as in the program
mode.

Selection is a Bayesian decision on public data. The degree distribution is
deconvolved from ``y`` (NPMLE under the known Laplace noise) and every node gets
its empirical-Bayes posterior. Each candidate is scored by simulating the steps
after the release, conditional on the released ``D``, on synthetic inputs drawn
from that posterior:

* a program that does not read ``N`` depends on ``|P|`` only (every set it can
  form is ``P``, a projection of ``P`` or empty), so its local count is a table
  ``f(d)`` computed with the interpreter, and the score is a Monte Carlo average
  over posterior degree sequences;
* a program that reads ``N`` also depends on the structure, which ``y`` does not
  reveal: it is simulated on synthetic graphs with posterior degrees from three
  families (no, moderate and strong clustering) whose scores are combined by a
  geometric mean (a structural prior).

Runs use common random numbers (:class:`Streams`: degree noise, RR uniforms,
projection seed and Laplace noise), so the selected candidate, the PSC default
and every other candidate are compared on identical noise.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable, Sequence

import numpy as np

from psc.dp import flip_probability, graph_projection
from psc.graph import Graph
from psc.ground_truth import relative_error
from psc.mechanism import DEFAULT_MECHANISM, MechanismProfile, get_mechanism

from .lang import Env, Interpreter, Program
from .sensitivity import PublicParams, derive
from .utility import run_exact

ETA = 1e-3  # floor of the relative-error denominator, in units of n (psc.ground_truth.relative_error)
FAMILIES = ("chung-lu", "geometric", "threshold")


@dataclass(frozen=True)
class Candidate:
    """A program, its bound ``B`` (replaces ``D``) and the RR budget ``eps1``.

    ``key`` names the candidate across runs (its bound may differ per run)."""

    program: Program
    bound: int
    eps1: float = 0.0
    key: tuple = ()


@dataclass
class Streams:
    """Common random numbers of one run, shared by every candidate."""

    degree: np.ndarray  # standard Laplace: y_i = d_i + degree_i / eps2
    laplace: np.ndarray  # standard Laplace: report_i = count_i + GS / eps3 * laplace_i
    uniform: np.ndarray | None  # node i flips a_ij (j < i) if uniform[i, j] < p(eps1)
    projection_seed: int

    @classmethod
    def draw(cls, n: int, rng: np.random.Generator, rows: bool = True) -> "Streams":
        return cls(rng.laplace(size=n), rng.laplace(size=n), rng.random((n, n)) if rows else None,
                   int(rng.integers(2**62)))


def run_streams(n: int, seed: int, run: int, rows: bool = True) -> Streams:
    return Streams.draw(n, np.random.default_rng([seed, run, 1]), rows)


@dataclass(frozen=True)
class Release:
    """Public output of the degree step."""

    y: np.ndarray
    D: int
    eps2: float


def release_degrees(graph: Graph, eps2: float, st: Streams, degree_class: str,
                    mechanism: str | MechanismProfile = DEFAULT_MECHANISM) -> Release:
    """Every node publishes ``d_i + Lap(1/eps2)``; ``D`` is the mechanism's bound
    (``degree_class`` decides the rounding, as in the framework)."""
    y = np.asarray(graph.degrees(), dtype=float) + st.degree / eps2
    D = get_mechanism(mechanism).degree_bound([float(x) for x in y], degree_class).projection_degree
    return Release(y, int(D), eps2)


# ---------------------------------------------------------------------------
# Execution of one candidate (the code path of the program mode)
# ---------------------------------------------------------------------------

_GS: dict[tuple, float] = {}
_INTERPRETERS: dict[str, Interpreter] = {}


def _interpreter(program: Program) -> Interpreter:
    if program.digest not in _INTERPRETERS:
        _INTERPRETERS[program.digest] = Interpreter(program)
    return _INTERPRETERS[program.digest]


def candidate_gs(program: Program, n: int, bound: int) -> float:
    key = (program.digest, n, bound)
    if key not in _GS:
        _GS[key] = derive(program, PublicParams(n, D=bound, dmax=bound)).gs
    return _GS[key]


def _noisy_rows(graph: Graph, eps1: float, bound: int, st: Streams, cache: dict) -> dict[int, frozenset]:
    """Rows of the RR graph (node i perturbs a_ij for j < i) projected to ``bound``."""
    if (eps1, bound) in cache:
        return cache[eps1, bound]
    if eps1 not in cache:
        n = graph.n
        a = np.zeros((n, n), dtype=bool)
        for u in range(n):
            a[u, list(graph.adj[u])] = True
        lower = np.tril(a ^ (st.uniform < flip_probability(eps1)), k=-1)
        i, j = np.nonzero(lower)
        cache[eps1] = Graph.from_edges(n, zip(i.tolist(), j.tolist()))
    projected = graph_projection(cache[eps1], bound, np.random.default_rng(st.projection_seed))
    cache[eps1, bound] = {u: frozenset(projected.adj[u]) for u in range(graph.n)}
    return cache[eps1, bound]


def ranked_projector(st: Streams, n: int) -> Callable[[frozenset, int], frozenset]:
    """``project(S, k)`` keeps the ``k`` elements of ``S`` that come first in a public
    random order of the node ids, drawn once per run (from the projection seed).

    Any fixed order keeps the projections of neighbouring sets one replacement
    apart, as the deriver assumes, and the size of every set a program forms from
    ``P`` alone still depends on ``|P|`` only (:func:`count_table`). Unlike the
    smallest ids, the kept neighbours do not depend on how the dataset numbers
    its nodes."""
    rank = np.empty(n, dtype=np.int64)
    rank[np.random.default_rng([st.projection_seed, 1]).permutation(n)] = np.arange(n)

    def projector(s: frozenset, k: int) -> frozenset:
        k = max(0, int(k))
        return s if len(s) <= k else frozenset(sorted(s, key=rank.__getitem__)[:k])

    return projector


def execute(graph: Graph, cand: Candidate, eps: float, rel: Release, st: Streams, cache: dict | None = None) -> float:
    """Estimate of ``cand`` on ``graph`` after the release ``rel``, with the
    run's streams. ``cache`` (one per graph and streams) shares the RR graph
    between candidates with the same ``eps1``."""
    n = graph.n
    eps3 = eps - rel.eps2 - cand.eps1
    if eps3 <= 0:
        raise ValueError(f"no budget left for the reports (eps1 = {cand.eps1:g}, eps2 = {rel.eps2:g})")
    prog = cand.program
    interp = _interpreter(prog)
    if prog.uses_rows:
        cache = {} if cache is None else cache
        rows = _noisy_rows(graph, cand.eps1, cand.bound, st, cache)
        if "projector" not in cache:
            cache["projector"] = ranked_projector(st, n)
        proj = cache["projector"]
        total = sum(interp.local(Env(frozenset(graph.adj[i]), i, rows, n, D=cand.bound, dmax=cand.bound, projector=proj))
                    for i in range(n))
    else:  # depends on |P| only
        table = count_table(prog, n, cand.bound)
        total = float(sum(table[len(graph.adj[i])] for i in range(n)))
    total += candidate_gs(prog, n, cand.bound) / eps3 * float(st.laplace.sum())
    return interp.aggregate(total, n)


# ---------------------------------------------------------------------------
# Public degree posterior
# ---------------------------------------------------------------------------


@dataclass
class DegreePosterior:
    """NPMLE of the degree distribution from the noisy degrees, and the
    empirical-Bayes posterior of every node (support ``0 .. n-1``)."""

    prior: np.ndarray  # (K,)
    post: np.ndarray  # (n, K)

    @property
    def support(self) -> np.ndarray:
        return np.arange(self.prior.size)

    def mean(self) -> np.ndarray:
        return self.post @ self.support

    def sample(self, rng: np.random.Generator, size: int) -> np.ndarray:
        """``size`` degree sequences, nodes independent given the prior: ``(size, n)``."""
        cdf = np.cumsum(self.post, axis=1)
        u = rng.random((size, self.post.shape[0]))
        out = np.empty(u.shape, dtype=np.int64)
        for i in range(self.post.shape[0]):
            out[:, i] = np.searchsorted(cdf[i], u[:, i] * cdf[i, -1])
        return np.minimum(out, self.prior.size - 1)


def deconvolve(y: np.ndarray, eps2: float, n: int, iters: int = 500, tol: float = 1e-8) -> DegreePosterior:
    """EM for the NPMLE of the degree distribution under ``y = d + Lap(1/eps2)``."""
    support = np.arange(n, dtype=float)
    dist = np.abs(np.asarray(y, dtype=float)[:, None] - support[None, :]) * eps2
    like = np.exp(-(dist - dist.min(axis=1, keepdims=True)))  # row scaling cancels in the posterior
    prior = np.full(n, 1.0 / n)
    for _ in range(iters):
        post = like * prior
        post /= post.sum(axis=1, keepdims=True)
        new = post.mean(axis=0)
        done = np.abs(new - prior).max() < tol
        prior = new
        if done:
            break
    post = like * prior
    post /= post.sum(axis=1, keepdims=True)
    return DegreePosterior(prior, post)


# ---------------------------------------------------------------------------
# Synthetic graphs (structural prior of programs that read N)
# ---------------------------------------------------------------------------


def synthetic_graph(degrees: Sequence[float], family: str, rng: np.random.Generator) -> Graph:
    """A random graph whose expected degrees follow ``degrees``.

    ``chung-lu``: p_uv = min(1, c w_u w_v / W) (little clustering);
    ``geometric`` / ``threshold``: a 1-D geometric inhomogeneous random graph,
    p_uv = min(1, (c w_u w_v / (W n r_uv))^2) or 1[c w_u w_v / (W n r_uv) >= 1]
    with r_uv the circular distance of uniform positions (moderate / strong
    clustering). ``c`` is fitted so that the expected number of edges is sum(w) / 2."""
    w = np.maximum(np.asarray(degrees, dtype=float), 0.0)
    n = w.size
    target = w.sum() / 2
    if target < 0.5:
        return Graph.from_edges(n, [])
    iu = np.triu_indices(n, 1)
    base = (np.outer(w, w) / w.sum())[iu]
    if family == "chung-lu":
        prob = lambda c: np.minimum(1.0, c * base)  # noqa: E731
    elif family in ("geometric", "threshold"):
        x = rng.random(n)
        r = np.abs(x[:, None] - x[None, :])[iu]
        base = base / (n * np.maximum(np.minimum(r, 1.0 - r), 1e-12))
        if family == "geometric":
            prob = lambda c: np.minimum(1.0, (c * base) ** 2)  # noqa: E731
        else:
            prob = lambda c: (c * base >= 1.0).astype(float)  # noqa: E731
    else:
        raise ValueError(f"unknown graph family {family!r}; choose from {FAMILIES}")
    lo, hi = 0.0, 1.0
    while prob(hi).sum() < target and hi < 1e12:
        hi *= 2
    for _ in range(60):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if prob(mid).sum() < target else (lo, mid)
    p = prob(hi)
    keep = rng.random(p.size) < p
    return Graph.from_edges(n, zip(iu[0][keep].tolist(), iu[1][keep].tolist()))


# ---------------------------------------------------------------------------
# Selection
# ---------------------------------------------------------------------------


@dataclass
class SelectOptions:
    samples: int = 1000  # posterior degree sequences (programs that do not read N)
    families: tuple[str, ...] = FAMILIES
    graphs: int = 1  # synthetic graphs per family (programs that read N)
    sims: int = 4  # DP simulations per synthetic graph
    em_iters: int = 500
    # keep the default candidate unless the best one is predicted to be at least
    # this much better (relative score): guards against Monte Carlo noise and
    # against a structural prior that does not fit the graph
    margin: float = 0.0


@dataclass
class Selection:
    index: int
    scores: np.ndarray
    posterior_max: float  # largest posterior-mean degree (diagnostic)
    best: int = -1  # the best-scoring candidate (differs from index when the margin keeps the default)

    def to_dict(self) -> dict:
        return {"index": self.index, "best": self.best, "score": float(self.scores[self.index]),
                "posterior_max": self.posterior_max}


_TABLES: dict[tuple, np.ndarray] = {}


def count_table(program: Program, n: int, bound: int) -> np.ndarray:
    """Local count of a program that does not read ``N`` for ``|P| = 0 .. n-1``."""
    key = (program.digest, n, bound)
    if key not in _TABLES:
        interp = _interpreter(program)
        _TABLES[key] = np.array([interp.local(Env(frozenset(range(1, d + 1)), 0, {}, n, D=bound, dmax=bound))
                                 for d in range(n)])
    return _TABLES[key]


def _affine(program: Program, n: int) -> tuple[float, float]:
    interp = _interpreter(program)
    b = interp.aggregate_raw(0.0, n)
    a = interp.aggregate_raw(1.0, n) - b
    if not math.isclose(interp.aggregate_raw(1000.0, n), 1000.0 * a + b, rel_tol=1e-9, abs_tol=1e-9):
        raise ValueError(f"the aggregate {program.aggregate_source!r} is not affine in total")
    return a, b


def _score_degrees(rel: Release, n: int, eps: float, cands: Sequence[Candidate], exact: Program,
                   post: DegreePosterior, rng: np.random.Generator, samples: int) -> np.ndarray:
    deg = post.sample(rng, samples)
    hist = np.zeros((samples, n))
    np.add.at(hist, (np.repeat(np.arange(samples), n), deg.ravel()), 1.0)
    a, b = _affine(exact, n)
    truth = a * (hist @ count_table(exact, n, n - 1)) + b
    z = rng.laplace(size=(samples, n)).sum(axis=1)
    totals = hist @ np.stack([count_table(c.program, n, c.bound) for c in cands], axis=1)
    scales = np.array([candidate_gs(c.program, n, c.bound) / (eps - rel.eps2 - c.eps1) for c in cands])
    coef = np.array([_affine(c.program, n) for c in cands])
    est = coef[:, 0] * (totals + z[:, None] * scales) + coef[:, 1]
    clamp = np.array([c.program.clamp_nonnegative for c in cands])
    est = np.where(clamp, np.maximum(est, 0.0), est)
    return (np.abs(est - truth[:, None]) / np.maximum(truth, ETA * n)[:, None]).mean(axis=0)


def _score_graphs(rel: Release, n: int, eps: float, cands: Sequence[Candidate], exact: Program,
                  post: DegreePosterior, rng: np.random.Generator, opts: SelectOptions) -> np.ndarray:
    per_family = []
    for family in opts.families:
        acc, count = np.zeros(len(cands)), 0
        for _ in range(opts.graphs):
            g = synthetic_graph(post.sample(rng, 1)[0], family, rng)
            truth = run_exact(exact, g)
            for _ in range(opts.sims):
                st, cache = Streams.draw(n, rng), {}
                acc += [relative_error(execute(g, c, eps, rel, st, cache), truth, n) for c in cands]
                count += 1
        per_family.append(acc / count)
    return np.exp(np.log(np.maximum(np.array(per_family), 1e-12)).mean(axis=0))


def select(rel: Release, n: int, eps: float, cands: Sequence[Candidate], exact: Program,
           rng: np.random.Generator, opts: SelectOptions | None = None, default: int | None = None) -> Selection:
    """Choose a candidate from public values only (the release, ``n``, ε and the
    programs). ``exact`` is a program that computes the statistic exactly without
    truncation (it passed the utility test); it gives the truth of synthetic inputs.
    ``default`` (index of the PSC setting) is kept unless the best candidate beats
    it by ``opts.margin``."""
    opts = opts or SelectOptions()
    if not cands:
        raise ValueError("no candidate")
    post = deconvolve(rel.y, rel.eps2, n, opts.em_iters)
    if any(c.program.uses_rows for c in cands) or exact.uses_rows:
        scores = _score_graphs(rel, n, eps, cands, exact, post, rng, opts)
    else:
        scores = _score_degrees(rel, n, eps, cands, exact, post, rng, opts.samples)
    best = int(np.argmin(scores))
    index = best
    if default is not None and scores[best] > (1.0 - opts.margin) * scores[default]:
        index = default
    return Selection(index, scores, float(post.mean().max()), best)


# ---------------------------------------------------------------------------
# Candidate spaces
# ---------------------------------------------------------------------------

THRESHOLD_FACTORS = (1.0, 0.85, 0.7, 0.55, 0.4)  # fixed factors of D (static tuning, as in search.py)
ROW_FACTORS = (1.0, 0.75, 0.5, 0.35)
EPS1_GRID = (0.4, 0.6, 0.8, 1.0, 1.2, 1.4)


def bound_space(program: Program, D: int) -> list[Candidate]:
    """Every integer bound ``1 .. D`` (programs that do not read ``N``)."""
    return [Candidate(program, B, 0.0, ("B", B)) for B in range(1, max(1, D) + 1)]


def factor_space(program: Program, D: int, factors: Sequence[float] = THRESHOLD_FACTORS) -> list[Candidate]:
    return [Candidate(program, max(1, math.floor(f * D)), 0.0, ("factor", f)) for f in factors]


def row_space(program: Program, D: int, eps: float, eps2: float, factors: Sequence[float] = ROW_FACTORS,
              eps1_grid: Sequence[float] = EPS1_GRID) -> list[Candidate]:
    """Projection bounds ``round(f D)`` x RR budgets that leave a positive ε3."""
    return [Candidate(program, max(1, round(f * D)), e1, ("factor", f, "eps1", e1))
            for f in factors for e1 in eps1_grid if eps - eps2 - e1 > 1e-9]


def program_space(program: Program, D: int, eps: float, eps2: float) -> list[Candidate]:
    """The settings the selector may choose for one program."""
    return row_space(program, D, eps, eps2) if program.uses_rows else bound_space(program, D)


def pool_space(programs: Sequence[Program], D: int, eps: float, eps2: float) -> list[Candidate]:
    """The settings of every program of a pool; the key starts with the program's
    index, so the first program's settings (the PSC default included) come first."""
    return [Candidate(c.program, c.bound, c.eps1, ("program", k, *c.key))
            for k, prog in enumerate(programs) for c in program_space(prog, D, eps, eps2)]


@dataclass
class AdaptiveRun:
    release: Release
    selection: Selection
    candidate: Candidate
    estimate: float
    extra: dict = field(default_factory=dict)


def default_index(cands: Sequence[Candidate], D: int, eps1: float) -> int | None:
    """Index of the PSC setting (bound ``D``, RR budget ``eps1``) in a candidate list."""
    return next((k for k, c in enumerate(cands) if c.bound == D and math.isclose(c.eps1, eps1)), None)


def choose(scores: np.ndarray, subset: Sequence[int], default: int | None, margin: float) -> tuple[int, int]:
    """``(chosen, best)`` within ``subset`` of a scored candidate list, with the margin rule of
    :func:`select` (candidate scores do not depend on the other candidates, so one selection over a
    union of pools gives the selection of every pool)."""
    best = min(subset, key=lambda k: scores[k])
    if default is not None and scores[best] > (1.0 - margin) * scores[default]:
        return default, best
    return best, best


def adaptive_run(graph: Graph, program: Program, eps: float, eps2: float, degree_class: str, st: Streams,
                 rng: np.random.Generator, eps1_default: float = 0.0,
                 space: Callable[[int], list[Candidate]] | None = None, opts: SelectOptions | None = None,
                 mechanism: str | MechanismProfile = DEFAULT_MECHANISM) -> AdaptiveRun:
    """One degree-first run: release, select (public), execute the choice.
    ``eps1_default``: RR budget of the PSC setting (kept unless beaten by the margin)."""
    rel = release_degrees(graph, eps2, st, degree_class, mechanism)
    if space is None:
        space = (lambda D: row_space(program, D, eps, eps2)) if program.uses_rows else (lambda D: bound_space(program, D))
    cands = space(rel.D)
    sel = select(rel, graph.n, eps, cands, program, rng, opts, default_index(cands, rel.D, eps1_default))
    cand = cands[sel.index]
    return AdaptiveRun(rel, sel, cand, execute(graph, cand, eps, rel, st))
