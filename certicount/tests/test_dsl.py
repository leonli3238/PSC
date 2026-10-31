"""DSL, sensitivity deriver, falsifier, utility test and design loop (Improvement 2)."""

from __future__ import annotations

import asyncio
import math

import numpy as np
import pytest

from psc import rules
from psc.dp import graph_projection, project_neighbor_list
from psc.graph import Graph
from psc.models import ModelConfig, create_formatter
from certicount.dsl import (
    HAND_GS, PROGRAMS, DSLError, Env, Facts, Interpreter, PublicParams, SensitivityError, certify, derive,
    parse_program, verify_certificate,
)
from certicount.dsl.designer import MockDesignerModel, design_program
from certicount.dsl.falsifier import falsify
from certicount.dsl.library import analyst_prompt
from certicount.dsl.utility import run_exact, utility_test


def _graph(n: int, p: float, seed: int) -> Graph:
    rng = np.random.default_rng(seed)
    return Graph.from_edges(n, [(u, v) for u in range(n) for v in range(u + 1, n) if rng.random() < p])


@pytest.mark.parametrize("task", list(PROGRAMS))
@pytest.mark.parametrize("bound", [1, 2, 3, 7, 16, 40])
def test_derived_gs_equals_hand_derivation(task, bound):
    if task == "triangle" and bound == 1:
        pytest.skip("dmax - 1 holds for dmax >= 2, see the next test")
    p = PublicParams(49, D=bound, dmax=bound)
    assert derive(PROGRAMS[task].parse(), p).gs == pytest.approx(HAND_GS[task](p))


def test_triangle_at_dmax_one_is_tighter_than_library_floor():
    # library: max(1, dmax - 1) = 1; the program's exact bound is 1/2
    assert derive(PROGRAMS["triangle"].parse(), PublicParams(49, 1, 1)).gs == 0.5


def test_triangle_facts_ablation_gives_dmax():
    tri = PROGRAMS["triangle"].parse()
    p = PublicParams(49, 16, 16)
    assert derive(tri, p).gs == 15
    assert derive(tri, p, Facts(symmetric_rows=False)).gs == 16
    assert derive(tri, p, Facts(self_not_in_private=False)).gs == 16


def test_unprojected_rows_use_n_minus_two():
    # no published degree bound: rows are only bounded by n - 1 (the paper's n - 2 without optimisation)
    assert derive(PROGRAMS["triangle"].parse(), PublicParams(49)).gs == 47


def test_interpreter_matches_reproduction_rules():
    rng = np.random.default_rng(3)
    g = _graph(30, 0.25, 1)
    noisy = graph_projection(_graph(30, 0.3, 2), 6, rng)
    rows = dict(enumerate(noisy.adj))
    tri, deg, ks = (Interpreter(PROGRAMS[t].parse()) for t in ("triangle", "degree", "3-star"))
    for i in range(g.n):
        real = frozenset(g.adj[i])
        env = Env(real, i, rows, g.n, D=6, dmax=6)
        assert tri.local(env) == rules.triangle_local_count(set(real), noisy.adj[i], noisy.adj)
        assert deg.local(env) == rules.update_degree(real)
        projected = frozenset(project_neighbor_list(sorted(real), 6, rng))
        env_k = Env(real, i, rows, g.n, D=6, dmax=6, projector=lambda s, k, pr=projected, r=real: pr if s == r else s)
        assert ks.local(env_k) == rules.update_kstar(projected, 3)


@pytest.mark.parametrize("task", list(PROGRAMS))
def test_falsifier_finds_no_counterexample_and_bound_is_tight(task):
    prog = PROGRAMS[task].parse()
    gs = derive(prog, PublicParams(5, 3, 3)).gs
    refuted, ce = falsify(prog, gs, n=5, dmax=3)
    assert not refuted
    assert ce.max_delta == pytest.approx(gs)


def test_falsifier_refutes_asymmetric_rows_and_unclipped_kstar():
    tri = PROGRAMS["triangle"].parse()
    refuted, ce = falsify(tri, 2.0, n=5, dmax=3, symmetric=False, samples=3000)
    assert refuted and ce.max_delta == 2.5  # D - 1/2, the asymmetric projection bound
    raw = parse_program("return comb(size(P), 3)")
    refuted, _ = falsify(raw, math.comb(2, 2), n=6, dmax=3)
    assert refuted  # claiming C(D-1, 2) without clipping the real list is wrong


@pytest.mark.parametrize("task", list(PROGRAMS))
def test_utility_test_passes_reference_programs(task):
    assert utility_test(PROGRAMS[task].parse(), task, count=15).passed


def test_utility_test_catches_missing_half():
    bad = parse_program("S = P & N(self)\nreturn sum(size(P & N(j)) for j in S)", "total / 3")
    rep = utility_test(bad, "triangle", count=15)
    assert not rep.passed and "utility test failed" in rep.feedback()
    g = _graph(10, 0.5, 0)
    assert run_exact(bad, g) == 2 * g.count_triangles()


@pytest.mark.parametrize("src, msg", [
    ("return size(P) / size(P)", "division by a private"),
    ("return comb(0.5 * size(P), 2)", "integer"),
])
def test_deriver_rejections(src, msg):
    with pytest.raises(SensitivityError, match=msg):
        derive(parse_program(src), PublicParams(49, 5, 5))


@pytest.mark.parametrize("src", [
    "return size(Q)", "x = 1", "import os\nreturn 1", "return size(P) + P", "return comb(size(P), D)",
    "return sum(size(N(j)) for j in P if j > 2)", "return eval('1')", "return N(self)",
])
def test_parser_rejects_programs_outside_the_language(src):
    with pytest.raises(DSLError):
        parse_program(src)


def test_reading_D_without_published_bound_is_rejected():
    with pytest.raises(SensitivityError, match="no degree bound"):
        derive(PROGRAMS["3-star"].parse(), PublicParams(49))


def test_unprojected_kstar_warns_and_is_loose():
    der = derive(parse_program("return comb(size(P), 3)"), PublicParams(49, 18, 18))
    assert der.gs == math.comb(47, 2) and der.warnings


def test_certificate_verification():
    prog = PROGRAMS["triangle"].parse()
    p = PublicParams(49, 16, 16)
    cert = certify(prog, p)
    assert verify_certificate(cert, prog, p)[0]
    from dataclasses import replace

    assert not verify_certificate(replace(cert, gs=1.0), prog, p)[0]
    assert not verify_certificate(cert, PROGRAMS["degree"].parse(), p)[0]
    assert not verify_certificate(cert, prog, PublicParams(49, 15, 15))[0]


def test_design_loop_rewrites_a_loose_draft():
    fmt = create_formatter(ModelConfig())
    res = asyncio.run(design_program(MockDesignerModel(flawed_first=True), fmt, analyst_prompt("4-star", 49), 49,
                                     PublicParams(49, 10, 10), task="4-star"))
    assert res.accepted and res.iterations == 2
    assert "too loose" in res.history[0]["feedback"]
    assert derive(res.program, PublicParams(49, 10, 10)).gs == math.comb(9, 3)


def test_design_loop_gives_up_after_max_iterations():
    class Silent(MockDesignerModel):
        async def __call__(self, messages, **kwargs):
            from certicount.dsl.designer import _text

            return _text("no program here")

    res = asyncio.run(design_program(Silent(), create_formatter(ModelConfig()), analyst_prompt("triangle", 49), 49,
                                     PublicParams(49, 10, 10), task="triangle", max_iterations=2))
    assert not res.accepted and res.iterations == 2
