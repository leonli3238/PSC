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
    epsilon_lower_bound,
    parse_update_prompt,
    privacy_loss,
    projection_bound,
    rule_delta,
    select_flips,
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
        for f in flips:
            assert f.strategy in ("S1", "S2", "S3", "S4")
            f.apply(inp.neighbors)
            assert inp.node_id not in f.apply(inp.neighbors)


def test_kstar_full_list_uses_replacement():
    spec = get_algorithm("3-star")
    inp = NodeInput("3-star", 0, (1, 2, 3, 4), (), spec.update, spec.state_var, 0.0)
    flips = select_flips(inp, 10, 4, 6, np.random.default_rng(1))
    assert all(f.op in ("remove", "replace") for f in flips)
    assert any(f.op == "replace" and f.strategy == "S4" for f in flips)
    assert projection_bound("degree", 4) is None and projection_bound("triangle", 4) is None
    assert projection_bound("3-star", 4) == 4


def test_privacy_loss_deterministic_and_rule():
    b = 2.5
    assert privacy_loss([3.0], [7.0], b) == pytest.approx(4.0 / b)
    assert privacy_loss([3.0, 3.0], [3.0], b) == pytest.approx(0.0)
    # mixtures never exceed the loss of their farthest pair and are symmetric
    ys, ys2 = [0.0, 1.0, 5.0], [2.0, 2.0, 9.0]
    loss = privacy_loss(ys, ys2, b)
    assert loss == pytest.approx(privacy_loss(ys2, ys, b))
    assert loss <= max(abs(a - c) for a in ys for c in ys2) / b + 1e-12
    # the sup is attained at a support point or a tail: no grid point beats it
    from certicount.audit import mixture_logpdf
    grid = np.linspace(-50, 60, 20001)
    assert max(abs(mixture_logpdf(z, ys, b) - mixture_logpdf(z, ys2, b)) for z in grid) <= loss + 1e-9


@pytest.mark.parametrize("task", TASKS)
def test_rule_function_loss_is_at_most_eps3(task):
    n, eps3 = 30, 0.8
    inputs, bound, gs = _inputs(task, n=n)
    for inp in inputs:
        for f in candidate_flips(inp, n, bound):
            y, y2 = inp.rule_value(), inp.with_neighbors(f.apply(inp.neighbors)).rule_value()
            assert privacy_loss([y], [y2], gs / eps3) <= eps3 + 1e-9


def test_clopper_pearson_bounds():
    assert cp_lower(10, 10, 0.05) == pytest.approx(0.05 ** (1 / 10), rel=1e-6)
    assert cp_upper(0, 10, 0.05) == pytest.approx(1 - 0.05 ** (1 / 10), rel=1e-6)
    assert cp_lower(0, 10, 0.05) == 0.0 and cp_upper(10, 10, 0.05) == 1.0
    lo, hi = cp_lower(5, 20, 0.025), cp_upper(5, 20, 0.025)
    assert lo < 0.25 < hi


def test_epsilon_lower_bound():
    b = 1.0
    # identical deterministic outputs: nothing to detect
    eps, _ = epsilon_lower_bound([4.0] * 3, [4.0] * 3, [4.0] * 200, [4.0] * 200, b)
    assert eps == 0.0
    # a large deterministic gap is certified, but never above the true loss
    eps, ev = epsilon_lower_bound([0.0] * 3, [10.0] * 3, [0.0] * 200, [10.0] * 200, b)
    assert 2.0 < eps <= 10.0 and ev is not None
    # more evaluation samples give a tighter bound
    eps_small, _ = epsilon_lower_bound([0.0] * 3, [10.0] * 3, [0.0] * 30, [10.0] * 30, b)
    assert eps_small < eps


def _spec(task="degree", gs=1.0, f_x=3.0, f_x2=4.0) -> PairSpec:
    return PairSpec(
        pair_id="p", source="s", dataset="CU", task=task, run=1, node_id=0, x_key="a", x2_key="b",
        flip={"op": "add", "vertex": 5, "removed": None, "note": ""}, strategy="S1", gs=gs, eps=(0.0, 0.0, 2.0),
        bound=None, degree=3, degree2=4, messages=0, valid_messages=0, valid_messages2=0, f_x=f_x, f_x2=f_x2,
        prompt_chars=100,
    )


def _samples(values, phase="main", status="json"):
    return [{"value": v, "status": status, "phase": phase} for v in values]


def test_analyze_pair_classification():
    ok = analyze_pair(_spec(), _samples([3, 3, 3]), _samples([4, 4, 4]))
    assert not ok["robust_violation"] and not ok["suspect"] and ok["eps_emp"] == pytest.approx(2.0)
    bad = analyze_pair(_spec(), _samples([3, 3, 3]), _samples([6, 6, 6]))
    assert bad["robust_violation"] and bad["eps_emp"] == pytest.approx(6.0) and bad["exec_error2"] == 1.0
    jitter = analyze_pair(_spec(), _samples([3, 3, 3]), _samples([4, 4, 7]))
    assert not jitter["robust_violation"] and jitter["jitter2"] and jitter["suspect"]
    followed = analyze_pair(
        _spec(), _samples([3, 3, 3]) + _samples([3] * 100, "followup"), _samples([6, 6, 6]) + _samples([6] * 100, "followup"),
    )
    assert followed["eps_lb"] is not None and followed["confirmed"]


def test_parse_update_reply_matches_node_agent():
    assert parse_update_reply('```json\n{"Degree": 4}\n```', "Degree") == (4.0, "json")
    assert parse_update_reply("the degree is 4", "Degree") == (4.0, "number")
    assert parse_update_reply("", "Degree") == (None, "failed")


def test_mock_audit_end_to_end(tmp_path):
    """The rule-following mock never violates GS; an error-injecting mock is caught."""
    import asyncio

    from psc.models import ModelConfig
    import importlib.util

    spec_ = importlib.util.spec_from_file_location("audit_script", Path(__file__).resolve().parents[1] / "scripts" / "run_sensitivity_audit.py")
    script = importlib.util.module_from_spec(spec_)
    spec_.loader.exec_module(script)

    inputs, _, _ = _inputs("degree", n=12)
    rng = np.random.default_rng(0)
    plan = {"inputs": {}, "pairs": [], "checks": {}}
    for inp in inputs:
        k = script._input_key(inp)
        plan["inputs"][k] = script._input_dict(inp)
        for j, f in enumerate(select_flips(inp, 12, None, 3, rng)):
            inp2 = inp.with_neighbors(f.apply(inp.neighbors))
            k2 = script._input_key(inp2)
            plan["inputs"][k2] = script._input_dict(inp2)
            s = _spec(f_x=inp.rule_value(), f_x2=inp2.rule_value())
            s.x_key, s.x2_key, s.pair_id, s.node_id, s.strategy = k, k2, f"n{inp.node_id}p{j}", inp.node_id, f.strategy
            plan["pairs"].append(s.to_dict())
    jobs = [(k, rep, "main") for k in plan["inputs"] for rep in range(2)]
    for rate, expect_violation in ((0.0, False), (1.0, True)):
        out = tmp_path / f"rate{rate}"
        out.mkdir()
        cfg = ModelConfig(provider="mock", mock_error_rate=rate)
        asyncio.run(script.sample_inputs(cfg, plan, jobs, out, "test"))
        rows = script.analyze(plan, script._load_samples(out / "samples.jsonl"), "mock", 0.05)
        assert len(rows) == len(plan["pairs"])
        if not expect_violation:
            assert all(r["exec_error"] == 0 and r["exec_error2"] == 0 for r in rows)
            assert not any(r["robust_violation"] or r["suspect"] for r in rows)
            assert all(r["eps_emp"] <= 2.0 + 1e-9 for r in rows)
        else:
            assert any(r["robust_violation"] or r["suspect"] for r in rows)
