"""GT-DSL, paired design error and design quality (goal 2 of the DSL evaluation)."""

from __future__ import annotations

import asyncio
import importlib.util
from pathlib import Path

import numpy as np
import pytest

from psc.graph import load_dataset
from psc.models import ModelConfig
from certicount import DATA_DIR
from certicount.dsl import PROGRAMS, parse_program
from certicount.dsl.designer import design_reference_params
from certicount.dsl.ground_truth import dp_execute, gs_ratio, gt_dsl, hand_gs
from certicount.dsl.quality import design_quality, task_record
from certicount.framework import TrustedPSCFramework, TrustOptions

CU = load_dataset(DATA_DIR, "CU")
TASKS = ["degree", "3-star", "triangle", "4-star", "degree-moment2"]


def rng(i: int) -> np.random.Generator:
    return np.random.default_rng([0, i])


@pytest.mark.parametrize("task", TASKS)
@pytest.mark.parametrize("source", ["library", "design"])
def test_gt_dsl_equals_program_mode_on_identical_noise(task, source):
    rec = task_record(CU, "CU", task)
    fw = TrustedPSCFramework(ModelConfig(), TrustOptions(execution="program", program_source=source))
    for i in range(3):
        res = asyncio.run(fw.run(rec, 2.0, rng=rng(i)))
        tr = gt_dsl(rec.graph(), task, 2.0, rng(i))
        trace = res.extra["mechanism_trace"]
        assert tr.counts == pytest.approx(trace["raw_counts"])
        assert sum(tr.reports) == pytest.approx(trace["report_sum_before_clamp"], abs=1e-9)
        assert tr.estimate == pytest.approx(res.estimate, abs=1e-9)
        assert (tr.gs, tr.d_hat_max, tr.split) == (res.sensitivity, res.d_hat_max, res.split)


@pytest.mark.parametrize("task", TASKS)
def test_reference_gs_is_the_hand_derivation(task):
    g = task_record(CU, "CU", task).graph()
    for i in range(3):
        tr = gt_dsl(g, task, 2.0, rng(i))
        assert tr.gs == pytest.approx(hand_gs(task, tr.d_hat_max, g.n))


def test_suboptimal_design_is_caught_by_gs_ratio_and_paired_error():
    loose = parse_program("return comb(size(project(P, 2 * D)), 3)")
    n = 49
    q = design_quality(loose, "3-star", n, int(design_reference_params(n).D))
    # passes every check of the design loop, but the GS is several times the reference
    assert q.semantic_pass and q.sound and q.split_match and not q.same_as_reference
    assert q.gs_ratio == pytest.approx(171 / 36)  # C(19, 2) / C(9, 2) at D = 10
    g = CU["3-star"].graph()
    for i in range(5):
        a, b = dp_execute(g, loose, 2.0, rng(i), "3-star"), gt_dsl(g, "3-star", 2.0, rng(i))
        assert a.d_hat_max == b.d_hat_max and gs_ratio(a.gs, b.gs) > 1


def test_reference_programs_have_perfect_quality():
    for task in PROGRAMS:
        q = design_quality(PROGRAMS[task].parse(), task, 49, 10)
        assert q.same_as_reference and q.split_match and q.semantic_pass and q.sound
        assert all(r == pytest.approx(1.0) for r in q.gs_ratios.values())


def test_semantic_error_is_caught():
    doubled = parse_program("S = P & N(self)\nreturn sum(size(P & N(j)) for j in S)", "total / 3")
    q = design_quality(doubled, "triangle", 49, 10)
    assert not q.semantic_pass and q.gs_ratio == pytest.approx(2.0)


def _script(name: str):
    path = Path(__file__).resolve().parents[1] / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_code_modes_of_the_comparison_script():
    mod = _script("run_execution_compare")
    for mode in mod.CODE_MODES:
        res = mod.run_code(mode, CU["3-star"], 2.0, rng(0))
        assert res.llm_calls == 0 and np.isfinite(res.estimate)
    tr = gt_dsl(CU["3-star"].graph(), "3-star", 2.0, rng(0))
    assert mod.run_code("gt-dsl", CU["3-star"], 2.0, rng(0)).estimate == pytest.approx(tr.estimate)
    assert not mod.supported("naive", "4-star") and mod.supported("gt-dsl", "4-star")
