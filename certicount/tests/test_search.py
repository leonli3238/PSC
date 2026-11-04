"""Tests of the fixed metrics, the design loop changes and the accuracy search."""

from __future__ import annotations

import asyncio
import math

import numpy as np
import pytest

from psc.experiments import run_rng
from psc.models import ModelConfig, create_formatter

from certicount.dsl.designer import (
    MockDesignerModel, design_prompt, design_reference_params, design_with_restarts, read_draft, render_attempt,
)
from certicount.dsl.ground_truth import dp_execute, gt_dsl, noise_ratio
from certicount.dsl.lang import DSLError, Interpreter, parse_budget, parse_program
from certicount.dsl.library import PROGRAMS, analyst_prompt
from certicount.dsl.search import SearchOptions, score_program, search_program, tune_reference, tuning_candidates
from certicount.dsl.utility import utility_test
from certicount.framework import TrustedPSCFramework, TrustOptions

from test_dsl_eval import CU  # noqa: F401  (dataset records shared with the other tests)

FMT = create_formatter(ModelConfig())
FAST = SearchOptions(rounds=2, proposals=2, sims=5, avg_degrees=(4.0,), families=("er",))


def test_budget_line_is_parsed_validated_and_part_of_the_program():
    assert parse_budget(None) is None and parse_budget("r1=0.3, r2=0.2") == (0.3, 0.2)
    for bad in ("r1=0.3", "r1=1.5, r2=0.2", "x=1"):
        with pytest.raises(DSLError):
            parse_budget(bad)
    a = parse_program("return size(P)", "total / n")
    b = parse_program("return size(P)", "total / n", budget="r1=0.3, r2=0.1")
    assert a.digest != b.digest and "budget: r1=0.3, r2=0.1" in b.text()
    assert b.budget_fractions(0.5, 0.2) == (0.3, 0.1) and a.budget_fractions(0.5, 0.2) == (0.5, 0.2)


def test_aggregate_coefficient_and_noise_ratio_include_the_aggregate():
    n = CU["triangle"].vertex_num
    assert Interpreter(PROGRAMS["triangle"].parse()).aggregate_coefficient(n) == pytest.approx(1 / 3)
    assert Interpreter(PROGRAMS["degree"].parse()).aggregate_coefficient(n) == pytest.approx(1 / n)
    # 2-star written as deg*(deg-1) with total/2: GS doubles, the noise in the estimate does not
    g = CU["2-star"].graph()
    doubled = parse_program("deg = size(project(P, D))\nreturn deg * (deg - 1)", "total / 2")
    tr, ref = dp_execute(g, doubled, 2.0, run_rng(0, 0), "2-star"), gt_dsl(g, "2-star", 2.0, run_rng(0, 0))
    assert tr.gs > 1.9 * ref.gs
    assert noise_ratio(tr.final_noise_scale, ref.final_noise_scale) < 1.2


def test_program_budget_changes_the_split():
    g = CU["triangle"].graph()
    src = PROGRAMS["triangle"]
    prog = parse_program(src.local, src.aggregate, budget="r1=0.3, r2=0.2")
    tr = dp_execute(g, prog, 2.0, run_rng(0, 0), "triangle")
    assert tr.split[0] == pytest.approx(0.6)


def test_utility_test_closes_the_n_loophole_and_reports_symptoms():
    gaming = parse_program("deg = size(project(P, min(D, max(8, 27 - n))))\nreturn comb(deg, 3)")
    assert utility_test(gaming, "3-star").passed  # small graphs only: the old loophole
    rep = utility_test(gaming, "3-star", public_n=49)
    assert not rep.passed and all(f["sized"] for f in rep.failures)
    assert "number of nodes" in rep.feedback()
    two_star = parse_program("return comb(size(P), 2)", "total / 3")
    fb = utility_test(two_star, "triangle").feedback()
    assert "no triangle" in fb and "exact answer is 0" in fb and "not the requested structure" in fb


def test_threshold_programs_pass_only_without_truncation():
    low = parse_program("return comb(size(project(P, D * 0.7)), 3)")
    assert not utility_test(low, "3-star").passed
    assert utility_test(low, "3-star", truncate=False).passed


def test_history_is_rendered_without_nested_fences_and_duplicates_are_rejected():
    _, entry = read_draft("I think\n```dsl\nreturn {self}\n```\naggregate: total")
    assert entry["program"] == "return {self}" and "not a valid program" in entry["feedback"]
    _, raw = read_draft("no code here ```")
    text = render_attempt(1, raw)
    assert text.count("```") == 0 and "no program could be read" in text
    prompt = design_prompt(analyst_prompt("3-star", 49), 49, [entry])
    assert "Not supported" in prompt and prompt.count("```dsl") == 2  # the attempt and the format


def test_restarts_are_independent_and_recorded():
    n = 49
    res = asyncio.run(design_with_restarts(MockDesignerModel(flawed_first=True), FMT, analyst_prompt("3-star", n), n,
                                           design_reference_params(n), task="3-star", max_iterations=2, restarts=3))
    assert res.accepted and res.restarts == 1 and res.llm_calls == 2
    res = asyncio.run(design_with_restarts(MockDesignerModel(flawed_first=True), FMT, analyst_prompt("3-star", n), n,
                                           design_reference_params(n), task="3-star", max_iterations=1, restarts=3))
    assert not res.accepted and res.restarts == 3 and len(res.attempts) == 3 and res.llm_calls == 3


def test_program_mode_validates_against_itself():
    fw = TrustedPSCFramework(ModelConfig(provider="mock"), TrustOptions(execution="program"))
    res = asyncio.run(fw.run(CU["triangle"], 2.0, rng=run_rng(0, 0)))
    v = res.extra["validation"]
    assert v["checked_against"] == "program" and v["rule_estimate"] == res.estimate and v["e2e_exact"] == v["nodes"]
    assert "library" in v
    tr = res.extra["mechanism_trace"]
    assert tr["aggregate_coefficient"] == pytest.approx(1 / 3)
    assert tr["final_noise_scale"] == pytest.approx(res.sensitivity / res.split[2] / 3)


def test_codeagg_is_not_labelled_as_the_paper_psc():
    assert TrustOptions(execution="llm", binding=False, validate=False, aggregate_by_code=True).label == "PSC[llm+codeagg]"
    assert TrustOptions(execution="llm", binding=False, validate=False).label == "PSC"


def test_search_finds_a_program_at_least_as_good_as_its_first_one():
    n = CU["3-star"].vertex_num
    res = asyncio.run(search_program(MockDesignerModel(), FMT, analyst_prompt("3-star", n), n, "3-star", FAST))
    assert res.accepted and res.mode == "search" and res.llm_calls == 4
    scores = [h["score"]["score"] for h in res.history if h.get("score")]
    assert res.score["score"] == pytest.approx(min(scores))
    ref = score_program(PROGRAMS["3-star"].parse(), "3-star", n, FAST)
    assert res.score["score"] <= ref["score"] + 1e-12


def test_search_mode_through_the_framework_uses_the_chosen_program():
    import dataclasses
    opts = TrustOptions(execution="program", design_mode="search", search=dataclasses.asdict(FAST))
    fw = TrustedPSCFramework(ModelConfig(provider="mock"), opts)
    res = asyncio.run(fw.run(CU["3-star"], 2.0, rng=run_rng(0, 0)))
    design = res.extra["trust"]["design"]
    assert design["mode"] == "search" and design["score"]["score"] > 0 and math.isfinite(res.estimate)


def test_tuned_reference_is_not_worse_than_the_reference():
    n = CU["3-star"].vertex_num
    assert len(tuning_candidates("3-star")) == 15 and len(tuning_candidates("degree")) == 1
    tuned = tune_reference("3-star", n, FAST)
    assert tuned.score["score"] <= tuned.reference_score["score"] + 1e-12
    assert np.isfinite(dp_execute(CU["3-star"].graph(), tuned.program, 2.0, run_rng(0, 0), "3-star").estimate)
