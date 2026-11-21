"""CS9: extension tasks (statistics PSC never ran) and the leak-checked prompt core ``generic``."""

from __future__ import annotations

import itertools

import numpy as np
import pytest

import certicount  # noqa: F401
from certicount.dsl.designer import (CHECKLIST, GENERIC, GENERIC_REWRITES, GENERIC_TEMPLATES, design_prompt,
                                     dsl_reference, read_draft)
from certicount.dsl.library import (EXTENSION_TASKS, HAND_GS, NODE_PROGRAMS, PROGRAMS, RELEASE_PAIRS,
                                    analyst_prompt, infer_program_task)
from certicount.dsl.prompt_spec import GUARDED_TASKS, core_leak_check, fragment_instances, given_tasks, load_spec
from certicount.dsl.sensitivity import PublicParams, derive
from certicount.dsl.utility import random_graphs, reference_counter, utility_test
from certicount.dsl.designer import falsifier_feedback


def _perm_4cycles(g) -> float:
    return sum(1 for a, b, c, d in itertools.permutations(range(g.n), 4)
               if g.has_edge(a, b) and g.has_edge(b, c) and g.has_edge(c, d) and g.has_edge(d, a)) / 8


def _tri(g):
    return [t for t in itertools.combinations(range(g.n), 3)
            if g.has_edge(t[0], t[1]) and g.has_edge(t[1], t[2]) and g.has_edge(t[0], t[2])]


def test_counters_equal_definitions():
    for g in random_graphs(40, seed=9, n_range=(4, 9)):
        tris = _tri(g)
        assert reference_counter("4-cycle")(g) == _perm_4cycles(g)
        assert reference_counter("triangle-node")(g) == len({v for t in tris for v in t})
        assert reference_counter("triangle-edge")(g) == len({e for a, b, c in tris for e in ((a, b), (b, c), (a, c))})
        assert reference_counter("degree-ge3")(g) == sum(1 for u in range(g.n) if len(g.adj[u]) >= 3)


@pytest.mark.parametrize("task", EXTENSION_TASKS)
def test_expert_programs_compute_the_task_and_are_certified(task):
    for prog in {PROGRAMS[task].parse(), NODE_PROGRAMS[task].parse()}:
        assert utility_test(prog, task, count=40).passed
        assert falsifier_feedback(prog) is None
        for b in (1, 2, 5, 10):
            p = PublicParams(49, D=b, dmax=b, eps1=1.0)
            assert derive(prog, p).gs == pytest.approx(HAND_GS[task](p))


def test_release_pairs_read_rows_and_matrix():
    for task, pair in RELEASE_PAIRS.items():
        rows, matrix = pair["rows"].parse(), pair["matrix"].parse()
        assert rows.uses_rows and not rows.uses_matrix and matrix.uses_matrix and not matrix.uses_rows
        assert utility_test(rows, task, count=20).passed and utility_test(matrix, task, count=20).passed


def test_analyst_prompts_give_no_formula_and_the_mock_finds_the_task():
    for task in EXTENSION_TASKS:
        text = analyst_prompt(task, 77)
        assert "0 to 76" in text and "C(" not in text and "*" not in text
        assert infer_program_task(text) == task


# ---------------------------------------------------------------- prompt core "generic"
def test_core_leak_check_flags_v1_alt_and_passes_generic():
    assert {"degree", "2-star", "3-star", "degree-moment2"} <= given_tasks()
    assert not set(EXTENSION_TASKS) & given_tasks() and "triangle" not in given_tasks()
    alt = {(lk["fragment"], lk["task"]) for lk in core_leak_check("v1-alt")}
    assert ("0.5 * sum(size(S & N(v)) for v in S)", "triangle") in alt
    assert ("0.5 * sum(size(S - N(v)) - 1 for v in S)", "open-wedge") in alt
    assert core_leak_check("generic") == () and core_leak_check("v1") == ()
    assert set(EXTENSION_TASKS) <= set(GUARDED_TASKS)


def test_generic_core_shows_exactly_its_checked_fragments():
    for _, dsl, _ in GENERIC_REWRITES:
        assert f"->  {dsl}" in GENERIC
    assert GENERIC_TEMPLATES == tuple(d for _, d, _ in GENERIC_REWRITES)
    assert "N(v)" not in GENERIC and "project(P, D)" not in GENERIC
    assert fragment_instances("size(S & T)") == ["size(P & P)", "size(P & project(P, D))",
                                                 "size(project(P, D) & P)", "size(project(P, D) & project(P, D))"]
    prompt = design_prompt(analyst_prompt("triangle-edge", 77), 77, [], True, load_spec("generic"), "rows")
    assert dsl_reference("generic", True) in prompt and prompt.index(CHECKLIST) < prompt.index("Reply with")
    assert load_spec("generic").core == "generic" and load_spec("generic").digest != load_spec("v1-alt").digest


def test_generic_hints_carry_no_pair_formula():
    cond = "```dsl\nreturn sum(1 for a in P for b in P if a < b)\n```\naggregate: total"
    power = "```dsl\nreturn size(P) ** 2\n```\naggregate: total"
    fb = read_draft(cond, core="generic")[1]["feedback"]
    assert "size(S & T)" in fb and "N(v)" not in fb
    assert "pow(x, k)" in read_draft(power, core="generic")[1]["feedback"]


def test_four_cycle_is_certified_but_noisy():
    """The deriver's bound grows as D * dmax: the system certifies the program, the simulated choice
    is what decides whether it is usable."""
    prog = PROGRAMS["4-cycle"].parse()
    assert derive(prog, PublicParams(453, D=10, dmax=10, eps1=1.0)).gs == pytest.approx(109.0)
    assert np.isfinite(derive(prog, PublicParams(453, D=10, dmax=10, eps1=1.0)).gs)


def test_gt_naive_covers_every_counted_task():
    from psc.dp import build_noisy_graph
    from psc.ground_truth import gt_naive as psc_gt_naive

    from certicount.dsl.ground_truth import gt_naive

    g = random_graphs(1, seed=3, n_range=(12, 12))[0]
    assert gt_naive(g, "triangle", 2.0, np.random.default_rng(5)) == psc_gt_naive(g, "triangle", 2.0,
                                                                                    np.random.default_rng(5))
    for task in ("open-wedge", *EXTENSION_TASKS):
        noisy = build_noisy_graph(g, 2.0, np.random.default_rng(5))
        assert gt_naive(g, task, 2.0, np.random.default_rng(5)) == reference_counter(task)(noisy)
