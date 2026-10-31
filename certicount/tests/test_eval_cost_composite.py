"""Evaluation protocol, cost accounting and composite queries (contents 1, 5, 6)."""

from __future__ import annotations

import math

import numpy as np
import pytest

from psc.graph import load_dataset
from certicount import DATA_DIR, REPRO_ROOT
from certicount.composite import (
    PLANS, BudgetExceeded, PrivacyAccountant, allocate, check_plan, plan_from_keywords, run_composite, truth,
)
from certicount.cost import calls_per_run, transcript_costs
from certicount.evaluation import aggregation_factor, decompose, load_runs, report_interval

GPT41MINI = REPRO_ROOT / "results" / "exp1" / "gpt-4.1-mini-node_gpt-4.1-curator"


def test_report_interval_from_public_values():
    row = {"task": "degree", "truth": 4.0, "split": [0, 0, 2.0], "sensitivity": 1.0,
           "extra": {"mechanism_trace": {"noisy_counts": [4.0] * 50}}}
    iv = report_interval(row)
    # sd of the mean of 50 Lap(0.5): sqrt(2 * 50 * 0.25) / 50
    assert iv["centre"] == 4.0
    assert iv["half_width"] == pytest.approx(1.959964 * math.sqrt(25) / 50, rel=1e-5)
    assert iv["covers_truth"] and not iv["covers_zero"]
    assert report_interval({**row, "sensitivity": None}) is None
    assert aggregation_factor("triangle", 10) == pytest.approx(1 / 3)


@pytest.mark.skipif(not GPT41MINI.exists(), reason="reproduction results not available")
def test_decomposition_of_reproduction_runs():
    rows = load_runs(GPT41MINI / "gpt41mini-node_gpt41-curator_exp1_CU_degree_r10_PSC")
    stats = decompose(rows, 49)
    assert stats["runs"] == 10
    assert stats["relative_error"] == pytest.approx(stats["rule_relative_error"] + stats["delta_signed"])
    assert stats["relative_error"] == pytest.approx(stats["rule_relative_error"] - stats["lucky_gain"] + stats["llm_harm"])
    assert 0 <= stats["ci_covers_truth"] <= 1


@pytest.mark.skipif(not GPT41MINI.exists(), reason="reproduction results not available")
def test_transcript_costs_find_the_send_share():
    c = transcript_costs(GPT41MINI / "gpt41mini-node_gpt41-curator_exp1_CU_triangle_r10_PSC")
    send = next(r for r in c["rows"] if r["phase"] == "send")
    assert c["runs"] == 10 and send["calls"] == 490
    assert 0.2 < send["output_share"] < 0.3  # about 23 % of the output tokens


def test_call_model():
    assert calls_per_run(True, 49)["total"] == 2 * 49 + 3
    assert calls_per_run(False, 49)["total"] == 49 + 3
    assert calls_per_run(True, 49, send_by_code=True, aggregate_by_code=True)["total"] == 49 + 2
    assert calls_per_run(True, 49, execution="program", design_calls=0)["total"] == 0


def test_accountant_refuses_overspending():
    acct = PrivacyAccountant(1.0)
    acct.spend("a", 0.6)
    acct.reuse("a", "b")
    with pytest.raises(BudgetExceeded):
        acct.spend("c", 0.5)
    assert acct.spent == pytest.approx(0.6)


@pytest.mark.parametrize("plan", list(PLANS))
def test_composite_ledger_sums_to_epsilon(plan):
    g = load_dataset(DATA_DIR, "CU")["degree"].graph()
    r = run_composite(g, PLANS[plan], 2.0, np.random.default_rng(0))
    assert r["spent"] == pytest.approx(2.0)
    assert set(r["estimates"]) == {a for a, _ in PLANS[plan].subqueries}


def test_degree_is_answered_from_the_shared_noisy_degrees():
    alloc = allocate(PLANS["degree_and_3star"], 2.0)
    assert alloc["reported"] == ["S3"] and alloc["eps2"] == pytest.approx(0.4) and alloc["eps3"] == pytest.approx(1.6)
    g = load_dataset(DATA_DIR, "CU")["degree"].graph()
    r = run_composite(g, PLANS["degree_and_3star"], 2.0, np.random.default_rng(0))
    assert r["details"]["deg"]["eps"] == 0.0


def test_composite_estimates_converge_without_noise_bias_for_degree():
    g = load_dataset(DATA_DIR, "EE")["degree"].graph()
    est = [run_composite(g, PLANS["degree_and_3star"], 2.0, np.random.default_rng(i))["estimates"]["deg"] for i in range(200)]
    assert abs(np.mean(est) - truth(g, PLANS["degree_and_3star"])["deg"]) < 0.05


def test_plan_checks():
    assert plan_from_keywords("What is the clustering coefficient?").name == "clustering"
    plan = check_plan({"subqueries": [["T", "triangle"], ["W", "2-star"]], "combine": "3 * T / W"})
    assert plan.combine_value({"T": 2, "W": 6}) == 1.0
    for bad in ({"subqueries": [["T", "4-cycle"]]}, {"subqueries": [["T", "triangle"]], "combine": "__import__('os')"}, {}):
        with pytest.raises(ValueError):
            check_plan(bad)
