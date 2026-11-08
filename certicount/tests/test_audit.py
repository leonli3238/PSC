"""Tests of the LLM node sensitivity audit (:mod:`certicount.audit`)."""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import certicount  # noqa: E402,F401  (puts ../psc-reproduction on sys.path)
from psc import rules  # noqa: E402
from psc.agents.node_agent import parse_update_reply  # noqa: E402
from certicount.audit import (  # noqa: E402
    Flip,
    NodeInput,
    PairSpec,
    analyze_pair,
    candidate_flips,
    cp_lower,
    cp_upper,
    epsilon_from_counts,
    epsilon_lower_bound,
    laplace_draw,
    mechanism_outputs,
    parse_update_prompt,
    projection_bound,
    rule_delta,
    select_flips,
    select_test,
    summarize,
)
from psc.dp import graph_projection  # noqa: E402
from psc.graph import Graph  # noqa: E402
from psc.library import get_algorithm  # noqa: E402
from psc.prompts import strip_structured  # noqa: E402

TASKS = ("degree", "3-star", "triangle")


def _random_graph(n: int, p: float, seed: int) -> Graph:
    rng = np.random.default_rng(seed)
    return Graph.from_edges(n, [(u, v) for u in range(n) for v in range(u + 1, n) if rng.random() < p])


def _inputs(task: str, seed: int = 0, n: int = 30) -> tuple[list[NodeInput], int | None, float]:
    """Node inputs as the PSC pipeline builds them, with ``(bound, GS)``."""
    rng = np.random.default_rng(seed)
    real = _random_graph(n, 0.2, seed)
    spec = get_algorithm(task)
    if task == "triangle":
        d_max = 6
        noisy = graph_projection(_random_graph(n, 0.3, seed + 1), d_max, rng)
        gs = d_max - 1.0
        out = []
        for i in range(n):
            msgs = tuple((j, tuple(sorted(noisy.adj[j]))) for j in sorted(noisy.adj[i]))
            out.append(NodeInput(task, i, tuple(real.neighbors(i)), msgs, spec.update, spec.state_var, 0.0))
        return out, None, gs
    if task == "degree":
        return [NodeInput(task, i, tuple(real.neighbors(i)), (), spec.update, spec.state_var, 0.0)
                for i in range(n)], None, 1.0
    D = 6
    out = [NodeInput(task, i, tuple(sorted(real.neighbors(i))[:D]), (), spec.update, spec.state_var, 0.0)
           for i in range(n)]
    return out, D, float(math.comb(D - 1, 2))


@pytest.mark.parametrize("task", TASKS)
def test_prompt_round_trip(task):
    inputs, _, _ = _inputs(task)
    for inp in inputs:
        assert parse_update_prompt(task, strip_structured(inp.prompt())) == inp


def test_prompt_round_trip_empty_lists():
    spec = get_algorithm("triangle")
    inp = NodeInput("triangle", 3, (), ((1, ()),), spec.update, spec.state_var, 0.0)
    assert parse_update_prompt("triangle", strip_structured(inp.prompt())) == inp
    inp = NodeInput("triangle", 3, (), (), spec.update, spec.state_var, 0.0)
    assert parse_update_prompt("triangle", strip_structured(inp.prompt())) == inp


def test_prompt_round_trip_rejects_edited_prompt():
    inputs, _, _ = _inputs("degree")
    text = strip_structured(inputs[0].prompt()).replace("Connected to:\n", "Connected to:\n 99,")
    with pytest.raises(ValueError):
        parse_update_prompt("degree", text)


@pytest.mark.parametrize("task", TASKS)
def test_every_neighbouring_input_respects_gs(task):
    """Self-check of the neighbouring relation: the rule function never moves by more than GS."""
    n = 30
    inputs, bound, gs = _inputs(task, n=n)
    for inp in inputs:
        flips = candidate_flips(inp, n, bound)
        if bound is not None and len(inp.neighbors) >= bound:
            flips += [Flip("replace", v, inp.neighbors[0]) for v in range(n) if v != inp.node_id and v not in inp.neighbors]
        for f in flips:
            after = f.apply(inp.neighbors)
            assert bound is None or len(after) <= bound
            assert abs(rule_delta(inp, f)) <= gs + 1e-9

@pytest.mark.parametrize("task", TASKS)
def test_selected_flips_are_distinct_valid_and_labelled(task):
    n = 30
    inputs, bound, _ = _inputs(task, n=n)
    rng = np.random.default_rng(0)
    for inp in inputs:
        flips = select_flips(inp, n, bound, 4, rng)
        assert 1 <= len(flips) <= 4
        assert len({f.key for f in flips}) == len(flips)
        assert flips[0].strategy == "S1"
        assert {f.strategy for f in flips} <= {"S1", "S2"}
        if task == "degree":
            assert all(f.strategy == "S1" for f in flips)
        for f in flips:
            assert inp.node_id not in f.apply(inp.neighbors)


@pytest.mark.parametrize("task", ("3-star", "triangle"))
def test_worst_case_flip_maximises_the_rule_change(task):
    n = 30
    inputs, bound, _ = _inputs(task, n=n)
    rng = np.random.default_rng(0)
    for inp in inputs:
        flips = select_flips(inp, n, bound, 2, rng)
        s2 = [f for f in flips if f.strategy == "S2"]
        cands = candidate_flips(inp, n, bound)
        if not s2 or not cands:
            continue
        best = max(abs(rule_delta(inp, f)) for f in cands)
        assert abs(rule_delta(inp, s2[0])) == pytest.approx(best)


def test_kstar_full_list_uses_replacement():
    spec = get_algorithm("3-star")
    inp = NodeInput("3-star", 0, (1, 2, 3, 4), (), spec.update, spec.state_var, 0.0)
    flips = select_flips(inp, 10, 4, 6, np.random.default_rng(1))
    assert all(f.op in ("remove", "replace") for f in flips)
    assert any(f.op == "replace" for f in flips)
    assert projection_bound("degree", 4) is None and projection_bound("triangle", 4) is None
    assert projection_bound("3-star", 4) == 4


def test_clopper_pearson_bounds():
    assert cp_lower(10, 10, 0.05) == pytest.approx(0.05 ** (1 / 10), rel=1e-6)
    assert cp_upper(0, 10, 0.05) == pytest.approx(1 - 0.05 ** (1 / 10), rel=1e-6)
    assert cp_lower(0, 10, 0.05) == 0.0 and cp_upper(10, 10, 0.05) == 1.0
    lo, hi = cp_lower(5, 20, 0.025), cp_upper(5, 20, 0.025)
    assert lo < 0.25 < hi
    # large n: no overflow, exact closed form at k = 0
    assert cp_upper(0, 5000, 0.05) == pytest.approx(1 - 0.05 ** (1 / 5000), rel=1e-5)


def test_epsilon_from_counts_is_jagielski_bound():
    n, a = 200, 0.05
    assert epsilon_from_counts(n, n, 0, n, a) == pytest.approx(math.log(cp_lower(n, n, a / 2) / cp_upper(0, n, a / 2)))
    assert epsilon_from_counts(0, n, 0, n, a) == -math.inf
    assert epsilon_from_counts(100, n, 100, n, a) < 0


def test_laplace_draws_are_reproducible_and_independent():
    assert laplace_draw("k", "eval", 3) == laplace_draw("k", "eval", 3)
    draws = [laplace_draw("k", "eval", r) for r in range(4000)]
    assert len(set(draws)) == len(draws)
    assert np.mean(np.abs(draws)) == pytest.approx(1.0, abs=0.06)  # E|Lap(1)| = 1
    assert laplace_draw("k", "select", 3) != laplace_draw("k", "eval", 3)


def _trials(values, phase, start=0):
    return [{"value": v, "status": "json", "phase": phase, "rep": start + i} for i, v in enumerate(values)]


def test_bound_never_exceeds_the_true_epsilon_of_an_exact_mechanism():
    """f(x) = 3, f(x') = 4, GS 1, ε3 2: the mechanism is exactly 2-DP, so ε_lb ≤ 2
    must fail with probability at most α (here: never over 20 seeds)."""
    b = 0.5
    for seed in range(20):
        z = mechanism_outputs(_trials([3.0] * 20, "select"), "x", b, seed)
        z2 = mechanism_outputs(_trials([4.0] * 20, "select"), "x2", b, seed)
        e = mechanism_outputs(_trials([3.0] * 1000, "eval"), "x", b, seed)
        e2 = mechanism_outputs(_trials([4.0] * 1000, "eval"), "x2", b, seed)
        eps_lb, test, counts = epsilon_lower_bound(z, z2, e, e2, 0.05)
        assert 0.0 <= eps_lb <= 2.0 and test is not None and counts["n_num"] == 1000


def test_bound_detects_an_edge_dependent_error():
    """L(x') = f(x') + 2 on the neighbour only: true loss 6 > ε3 = 2."""
    b = 0.5
    z = mechanism_outputs(_trials([3.0] * 20, "select"), "x", b)
    z2 = mechanism_outputs(_trials([6.0] * 20, "select"), "x2", b)
    e = mechanism_outputs(_trials([3.0] * 500, "eval"), "x", b)
    e2 = mechanism_outputs(_trials([6.0] * 500, "eval"), "x2", b)
    eps_lb, test, _ = epsilon_lower_bound(z, z2, e, e2, 0.05)
    assert 2.0 < eps_lb <= 6.0
    assert select_test(z, z2, 0.05) == test


def _spec(task="degree", gs=1.0, f_x=3.0, f_x2=4.0) -> PairSpec:
    return PairSpec(
        pair_id="p", source="s", dataset="CU", task=task, run=1, node_id=0, x_key="a", x2_key="b",
        flip={"op": "add", "vertex": 5, "removed": None, "note": ""}, strategy="S1", gs=gs, eps=(0.0, 0.0, 2.0),
        bound=None, degree=3, degree2=4, messages=0, valid_messages=0, valid_messages2=0, f_x=f_x, f_x2=f_x2,
        prompt_chars=100,
    )


def _both(values, values2, n_sel=20, n_eval=400):
    x = _trials([values[0]] * n_sel, "select") + _trials([values[0]] * n_eval, "eval")
    x2 = _trials([values2[0]] * n_sel, "select") + _trials([values2[0]] * n_eval, "eval")
    return x, x2


def test_analyze_pair_requires_both_phases():
    row = analyze_pair(_spec(), _trials([3, 3, 3], "select"), _trials([4, 4, 4], "select"))
    assert row["eps_lb"] is None and row["violation"] is None and row["group"] == "random"


def test_analyze_pair_exact_and_violating_models():
    ok = analyze_pair(_spec(), *_both([3.0], [4.0]))
    assert ok["eps_lb"] is not None and ok["eps_lb"] <= 2.0 and ok["violation"] is False
    assert ok["exec_error"] == 0 and ok["exec_error2"] == 0 and ok["delta_llm_max"] == 1
    bad = analyze_pair(_spec(), *_both([3.0], [6.0]))
    assert bad["violation"] is True and bad["eps_lb"] > 2.0 and bad["exec_error2"] == 1.0
    assert bad["counts"]["n_num"] == 400 and bad["test"] is not None


def test_input_independent_errors_are_not_violations():
    """L = f + U with U = ±1 independent of the input is post-processing of a
    2-DP mechanism: the lower bound must stay below ε3."""
    rng = np.random.default_rng(0)
    u = lambda n: list(rng.choice([-1.0, 1.0], size=n))  # noqa: E731
    x = _trials([3.0 + d for d in u(20)], "select") + _trials([3.0 + d for d in u(1000)], "eval")
    x2 = _trials([4.0 + d for d in u(20)], "select") + _trials([4.0 + d for d in u(1000)], "eval")
    row = analyze_pair(_spec(), x, x2)
    assert row["delta_llm_max"] == 3 and row["violation"] is False and row["eps_lb"] <= 2.0


def test_summary_counts_violations():
    rows = [analyze_pair(_spec(), *_both([3.0], [4.0])), analyze_pair(_spec(), *_both([3.0], [6.0])),
            analyze_pair(_spec(), _trials([3], "select"), _trials([4], "select"))]
    (s,) = summarize(rows, ("dataset",))
    assert s["pairs"] == 3 and s["tested"] == 2 and s["violations"] == 1
    assert s["eps_lb_max"] == rows[1]["eps_lb"]
    assert "total_eps_lower_bound" not in s


def test_parse_update_reply_matches_node_agent():
    assert parse_update_reply('```json\n{"Degree": 4}\n```', "Degree") == (4.0, "json")
    assert parse_update_reply("the degree is 4", "Degree") == (4.0, "number")
    assert parse_update_reply("", "Degree") == (None, "failed")


def _load_script():
    import importlib.util

    spec_ = importlib.util.spec_from_file_location(
        "audit_script", Path(__file__).resolve().parents[1] / "scripts" / "run_sensitivity_audit.py")
    script = importlib.util.module_from_spec(spec_)
    spec_.loader.exec_module(script)
    return script


def _degree_plan(script, n=12, pairs=2):
    inputs, _, _ = _inputs("degree", n=n)
    rng = np.random.default_rng(0)
    plan = {"inputs": {}, "pairs": [], "checks": {}}
    for inp in inputs:
        k = script._input_key(inp)
        plan["inputs"][k] = script._input_dict(inp)
        for j, f in enumerate(select_flips(inp, n, None, pairs, rng)):
            inp2 = inp.with_neighbors(f.apply(inp.neighbors))
            k2 = script._input_key(inp2)
            plan["inputs"][k2] = script._input_dict(inp2)
            s = _spec(f_x=inp.rule_value(), f_x2=inp2.rule_value())
            s.x_key, s.x2_key, s.pair_id, s.node_id, s.strategy = k, k2, f"n{inp.node_id}p{j}", inp.node_id, f.strategy
            plan["pairs"].append(s.to_dict())
    return plan


@pytest.mark.parametrize("rate", (0.0, 1.0))
def test_mock_audit_end_to_end_has_no_false_violation(tmp_path, rate):
    """The rule-following mock and the mock with input-independent ±1 slips are
    both ε3-DP after the Laplace noise: no pair may be reported as a violation."""
    import asyncio

    from psc.models import ModelConfig

    script = _load_script()
    plan = _degree_plan(script)
    jobs = script.trial_jobs(plan, 10, 60)
    cfg = ModelConfig(provider="mock", mock_error_rate=rate)
    asyncio.run(script.sample_inputs(cfg, plan, jobs, tmp_path, "test"))
    rows = script.analyze(plan, script._load_samples(tmp_path / "samples.jsonl"), "mock", 0.05)
    assert len(rows) == len(plan["pairs"])
    assert all(r["alpha_pair"] == pytest.approx(0.05 / len(rows)) for r in rows)
    assert not any(r["violation"] for r in rows)
    if rate == 0.0:
        assert all(r["exec_error"] == 0 and r["exec_error2"] == 0 for r in rows)


def test_audit_end_to_end_detects_an_edge_dependent_model(tmp_path, monkeypatch):
    """A model that reports 3·|P|: every flip moves it by 3 > GS = 1, so the true
    loss is 6 > ε3 = 2."""
    import asyncio
    import json

    from psc.models import ModelConfig

    script = _load_script()
    plan = _degree_plan(script)

    async def fake_chat(model, formatter, system, prompt, agent=None):
        inp = parse_update_prompt("degree", strip_structured(prompt))
        return json.dumps({inp.state_var: 3 * len(inp.neighbors)})

    monkeypatch.setattr(script, "chat", fake_chat)
    jobs = script.trial_jobs(plan, 10, 300)
    asyncio.run(script.sample_inputs(ModelConfig(provider="mock"), plan, jobs, tmp_path, "test"))
    rows = script.analyze(plan, script._load_samples(tmp_path / "samples.jsonl"), "fake", 0.05)
    assert rows and all(r["violation"] for r in rows)
    assert all(2.0 < r["eps_lb"] <= 6.0 for r in rows)
