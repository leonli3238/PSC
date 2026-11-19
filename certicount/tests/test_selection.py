"""CS7: release rounds, own-row check, simulated choice, run-time choice, normalised GS ratio, A fuzz."""

from __future__ import annotations

import asyncio

import numpy as np
import pytest

from psc.graph import Graph
from psc.models import ModelConfig, create_formatter

from certicount.dsl.designer import (OWN_ROW_FEEDBACK, DesignOptions, MockDesignerModel, design_candidates,
                                     design_prompt, design_reference_params, draft_stage, reads_own_row,
                                     release_feedback, static_feedback)
from certicount.dsl.falsifier import check_derivation
from certicount.dsl.fuzz import fuzz, summarize
from certicount.dsl.ground_truth import degree_release, dp_execute, estimate_gs
from certicount.dsl.lang import parse_program
from certicount.dsl.noisy_gate import holme_kim
from certicount.dsl.quality import design_quality
from certicount.dsl.selection import (SimOptions, budget_split, execute_selected, runtime_choice,
                                      select_program)

TRI_N = parse_program("Q = project(P, D)\nreturn 0.5 * sum(size(N(v) & Q) for v in Q)", "total / 3")
TRI_A = parse_program("Q = project(P, D)\nreturn sum(sum(A(j, k) for k in Q) for j in Q)", "total / 6")
TRI_OWN = parse_program("S = P & N(self)\nreturn 0.5 * sum(size(P & N(j)) for j in S)", "total / 3")
STAR = parse_program("return comb(size(project(P, D)), 3)")
STAR_A_SELF = parse_program("s = sum(A(self, y) for y in project(P, D))\nreturn s * (s - 1) * (s - 2) / 6")
PROMPT = "Count the number of triangles in the graph."


def test_own_row_and_release_checks():
    assert reads_own_row(TRI_OWN) and reads_own_row(STAR_A_SELF)
    assert reads_own_row(parse_program("return sum(A(j, self) for j in project(P, D))"))
    assert not reads_own_row(TRI_N) and not reads_own_row(TRI_A) and not reads_own_row(STAR)
    assert release_feedback(TRI_A, "rows") and release_feedback(TRI_N, "matrix")
    assert release_feedback(STAR, "rows") is None and release_feedback(STAR, "matrix") is None
    assert static_feedback(TRI_OWN, DesignOptions(own_row=True)) == OWN_ROW_FEEDBACK
    assert static_feedback(TRI_OWN, DesignOptions()) is None
    assert draft_stage("rejected: " + OWN_ROW_FEEDBACK) == "own_row"
    assert draft_stage("rejected: " + release_feedback(TRI_A, "rows")) == "release"


def test_release_note_only_in_release_rounds():
    plain = design_prompt(PROMPT, 49, [], matrix=True)
    rows = design_prompt(PROMPT, 49, [], matrix=True, release="rows")
    assert "This design round" not in plain
    assert "do not use A(...)" in rows and '"release": "rows"' in rows


def test_gs_ratio_counts_the_aggregate_factor():
    # the same estimator with the factor 1/6 in the program or in the aggregate
    inside = parse_program("Q = project(P, D)\nreturn sum(sum(A(j, k) for k in Q) for j in Q) / 6", "total")
    q_out = design_quality(TRI_A, "triangle", 49, 10, falsify_program=False, utility_graphs=10, node_bounds=True)
    q_in = design_quality(inside, "triangle", 49, 10, falsify_program=False, utility_graphs=10, node_bounds=True)
    assert q_out.gs_ratio == pytest.approx(1.0) and q_in.gs_ratio == pytest.approx(1.0)
    assert q_in.gs_ratio_raw == pytest.approx(1 / 6)
    assert estimate_gs(inside, 6.0, 49) == pytest.approx(estimate_gs(TRI_A, 36.0, 49))


def _graph(n=40, seed=3) -> Graph:
    return holme_kim(n, 3, 0.5, np.random.default_rng(seed))


def test_given_degree_reports_reproduce_the_run():
    g = _graph()
    split = budget_split(TRI_A, 2.0)
    for prog in (TRI_A, STAR):
        rng_a, rng_b = np.random.default_rng(5), np.random.default_rng(5)
        a = dp_execute(g, prog, 2.0, rng_a, "triangle", node_bounds=True, alpha=5.0)
        eps2 = budget_split(prog, 2.0).eps2
        b = dp_execute(g, prog, 2.0, rng_b, "triangle", node_bounds=True, alpha=5.0,
                       degree_reports=degree_release(g, eps2, rng_b))
        assert a.estimate == b.estimate  # the matrix / P-only path draws the degrees first
    assert split.eps2 == budget_split(TRI_N, 2.0).eps2  # one degree release serves both releases


def test_selection_fixes_the_split_and_leaves_the_release_to_the_run():
    g = _graph()
    opts = SimOptions(g.n, alpha=5.0, avg_degrees=(6.0,), reps=3, useless=None)
    sel = select_program([TRI_N, TRI_A, STAR], "triangle", opts)
    assert sel.chosen in (0, 1) and sorted(sel.runtime) == [0, 1]  # STAR: other split, never an alternative
    tr, idx, scores = execute_selected(g, [TRI_N, TRI_A, STAR], sel, "triangle", opts, np.random.default_rng(1))
    assert idx in (0, 1) and len(scores) == 2
    # the run-time choice reads only the published degrees: same reports, same choice
    reports = degree_release(g, budget_split(TRI_A, 2.0).eps2, np.random.default_rng(1))
    assert runtime_choice([TRI_N, TRI_A], "triangle", reports, opts)[0] == sel.runtime.index(idx)
    if idx == 1:  # the matrix program runs on the very noise of a plain run
        assert tr.estimate == dp_execute(g, TRI_A, 2.0, np.random.default_rng(1), "triangle", node_bounds=True,
                                         alpha=5.0).estimate


def test_useless_candidates_are_never_chosen():
    g = _graph()
    sel = select_program([STAR], "triangle", SimOptions(g.n, alpha=5.0, avg_degrees=(6.0,), reps=2, useless=1.0))
    assert sel.chosen is None and not sel.rows[0]["usable"]


@pytest.mark.parametrize("n,expected", [(49, "rows"), (453, "matrix")])
def test_design_candidates_with_the_mock_curator(n, expected):
    fmt = create_formatter(ModelConfig())
    sim = SimOptions(n, alpha=5.0, avg_degrees=(8.0,), reps=3)
    res, progs, sel = asyncio.run(design_candidates(MockDesignerModel(), fmt, PROMPT, n, design_reference_params(n),
                                                    "triangle", sim, options=DesignOptions(own_row=True)))
    assert res.accepted and len(progs) == 2 and res.llm_calls == 2
    chosen = progs[sel.chosen]
    assert ("matrix" if chosen.uses_matrix else "rows") == expected
    assert {c["releases"][0] for c in res.selection["candidates"]} == {"rows", "matrix"}
    star, sprogs, _ = asyncio.run(design_candidates(MockDesignerModel(), fmt, "Count the number of 3-stars in the "
                                                    "graph.", n, design_reference_params(n), "3-star", sim))
    assert star.accepted and len(sprogs) == 1  # the same P-only program from both rounds is one candidate
    assert star.selection["candidates"][0]["releases"] == ["rows", "matrix"]


def test_matrix_programs_and_own_bounds_never_refute_the_deriver():
    settings = ((5, 3, None), (6, 3, 40, 2), (6, 3, 40, 5))
    cases = list(fuzz(60, seed=1, settings=settings, matrix=1.0))
    bad = [c.to_dict() for c in cases if c.refuted or c.failed]
    assert not bad, bad[:2]
    rows = summarize(cases, settings)
    assert rows[0]["reads_matrix"] >= 0.8 * len(cases) and rows[1]["D"] == 2
    assert check_derivation(TRI_A, 6, 3, 40, D=2).gs is not None
