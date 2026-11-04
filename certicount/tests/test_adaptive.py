"""Degree-first adaptive execution (certicount.dsl.adaptive)."""

from __future__ import annotations

import math

import numpy as np
import pytest

from psc import rules
from psc.graph import Graph

from certicount.dsl.adaptive import (
    Candidate, SelectOptions, adaptive_run, bound_space, candidate_gs, count_table, deconvolve, default_index, execute,
    release_degrees, row_space, run_streams, select, synthetic_graph,
)
from certicount.dsl.lang import Env, Interpreter
from certicount.dsl.library import PROGRAMS

from test_dsl_eval import CU  # noqa: F401  (dataset records shared with the other tests)

FAST = SelectOptions(samples=300, sims=2)


def _transitivity(g: Graph) -> float:
    wedges = sum(d * (d - 1) / 2 for d in g.degrees())
    return 3 * g.count_triangles() / wedges if wedges else 0.0


def _swap_preserving_degrees(g: Graph, rng: np.random.Generator, swaps: int = 200) -> Graph:
    """Degree-preserving double edge swaps: another graph with the same degree sequence."""
    h = g.copy()
    for _ in range(swaps):
        edges = h.edges
        (a, b), (c, d) = (edges[k] for k in rng.choice(len(edges), 2, replace=False))
        if len({a, b, c, d}) == 4 and d not in h.adj[a] and b not in h.adj[c]:
            h.adj[a].discard(b), h.adj[b].discard(a), h.adj[c].discard(d), h.adj[d].discard(c)
            h.adj[a].add(d), h.adj[d].add(a), h.adj[c].add(b), h.adj[b].add(c)
    return h


def test_every_candidate_spends_exactly_the_budget():
    eps, eps2 = 2.0, 0.2
    tri, star = PROGRAMS["triangle"].parse(), PROGRAMS["3-star"].parse()
    for c in row_space(tri, 20, eps, eps2):
        assert 0 < c.eps1 < eps - eps2 and 1 <= c.bound <= 20
    assert [c.bound for c in bound_space(star, 7)] == list(range(1, 8))
    assert all(c.eps1 == 0 for c in bound_space(star, 7))
    assert default_index(row_space(tri, 20, eps, eps2), 20, 1.0) is not None
    assert bound_space(star, 7)[default_index(bound_space(star, 7), 7, 0.0)].bound == 7


def test_executor_matches_the_reproduction_rules():
    g = CU["triangle"].graph()
    n = g.n
    tri = PROGRAMS["triangle"].parse()
    st = run_streams(n, 0, 0)
    rel = release_degrees(g, 0.2, st, "triangle")
    for eps1, bound in ((1.0, rel.D), (0.6, max(1, rel.D // 2))):
        cache: dict = {}
        est = execute(g, Candidate(tri, bound, eps1), 2.0, rel, st, cache)
        rows = cache[eps1, bound]
        assert all(len(rows[u]) <= bound and all(u in rows[v] for v in rows[u]) for u in range(n))
        local = sum(rules.triangle_local_count(set(g.adj[i]), rows[i], rows) for i in range(n))
        noise = candidate_gs(tri, n, bound) / (2.0 - 0.2 - eps1) * st.laplace.sum()
        assert est == pytest.approx(max(0.0, (local + noise) / 3))
    star = PROGRAMS["3-star"].parse()
    interp = Interpreter(star)
    table = count_table(star, n, 5)
    assert all(table[len(g.adj[i])] == interp.local(Env(frozenset(g.adj[i]), i, {}, n, D=5, dmax=5)) for i in range(n))
    assert all(table[d] == math.comb(min(d, 5), 3) for d in range(n))


def test_selection_depends_on_the_released_degrees_only():
    g = CU["triangle"].graph()
    h = _swap_preserving_degrees(g, np.random.default_rng(0))
    assert h.degrees() == g.degrees() and h.count_triangles() != g.count_triangles()
    tri = PROGRAMS["triangle"].parse()
    runs = [adaptive_run(x, tri, 2.0, 0.2, "triangle", run_streams(x.n, 0, 3), np.random.default_rng(7), 1.0, opts=FAST)
            for x in (g, h)]
    assert runs[0].release.D == runs[1].release.D and np.array_equal(runs[0].release.y, runs[1].release.y)
    assert runs[0].candidate == runs[1].candidate
    assert np.array_equal(runs[0].selection.scores, runs[1].selection.scores)


def test_deconvolution_corrects_the_overshoot_of_the_noisy_maximum():
    rng = np.random.default_rng(1)
    n, eps2 = 200, 0.4
    y = 5 + rng.laplace(0.0, 1 / eps2, size=n)
    post = deconvolve(y, eps2, n)
    assert y.max() > 12  # the maximum of the noise overshoots
    # the NPMLE puts its mass at 5; an extreme report keeps a tiny atom of its own (MLE behaviour), so the
    # posterior of that node is pulled down but not all the way: conservative for the selection
    assert post.prior[4:7].sum() > 0.9 and abs(post.prior @ post.support - 5) < 0.5
    assert post.mean().max() < y.max() - 5
    samples = post.sample(rng, 50)
    assert samples.shape == (50, n) and samples.min() >= 0 and samples.max() <= n - 1


def test_selector_lowers_the_bound_only_without_a_real_hub():
    star = PROGRAMS["3-star"].parse()
    rng = np.random.default_rng(2)
    n = 120
    ring = [(u, (u + k) % n) for u in range(n) for k in (1, 2)]  # every degree 4
    hub = ring + [(0, v) for v in range(5, 65)]  # node 0 has degree 64
    chosen = {}
    for name, edges in (("no hub", ring), ("hub", hub)):
        g = Graph.from_edges(n, edges)
        st = run_streams(n, 0, 0, rows=False)
        rel = release_degrees(g, 0.4, st, "3-star")
        cands = bound_space(star, rel.D)
        sel = select(rel, n, 2.0, cands, star, rng, FAST)
        chosen[name] = cands[sel.index].bound / rel.D
    assert chosen["no hub"] < 0.7 and chosen["hub"] > 0.9


def test_margin_keeps_the_default():
    star = PROGRAMS["3-star"].parse()
    g = CU["3-star"].graph()
    st = run_streams(g.n, 0, 0, rows=False)
    rel = release_degrees(g, 0.4, st, "3-star")
    cands = bound_space(star, rel.D)
    d = default_index(cands, rel.D, 0.0)
    free = select(rel, g.n, 2.0, cands, star, np.random.default_rng(3), FAST, default=d)
    kept = select(rel, g.n, 2.0, cands, star, np.random.default_rng(3), SelectOptions(samples=300, margin=1.0), default=d)
    assert free.index == free.best != d and kept.index == d and kept.best == free.best


def test_synthetic_families_span_the_clustering():
    rng = np.random.default_rng(4)
    w = np.concatenate([np.full(80, 4.0), np.full(20, 10.0)])
    graphs = {f: synthetic_graph(w, f, rng) for f in ("chung-lu", "geometric", "threshold")}
    for g in graphs.values():
        assert abs(g.m - w.sum() / 2) < 0.25 * w.sum() / 2
    t = {f: _transitivity(g) for f, g in graphs.items()}
    assert t["chung-lu"] < 0.15 < t["geometric"] < t["threshold"]


def test_adaptive_run_is_reproducible():
    star = PROGRAMS["2-star"].parse()
    g = CU["2-star"].graph()
    a, b = (adaptive_run(g, star, 2.0, 0.4, "2-star", run_streams(g.n, 0, 5, rows=False), np.random.default_rng(9),
                         opts=FAST) for _ in range(2))
    assert a.estimate == b.estimate and a.candidate == b.candidate
