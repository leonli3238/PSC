"""Correctness tests for the PSC reproduction.

Run with ``python -m pytest tests -q`` (or ``python tests/test_psc.py``).
"""

from __future__ import annotations

import asyncio
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from psc import rules  # noqa: E402
from psc.dp import (  # noqa: E402
    build_noisy_graph,
    flip_probability,
    graph_projection,
    naive_budget,
    project_neighbor_list,
    split_budget,
)
from psc.framework import NaiveFramework, PSCFramework  # noqa: E402
from psc.graph import Graph, TaskRecord, task_prompt  # noqa: E402
from psc.ground_truth import gt_psc, relative_error  # noqa: E402
from psc.models import ModelConfig  # noqa: E402


def _toy_graph() -> Graph:
    # two triangles sharing node 2 plus a pendant node: (0,1,2), (2,3,4), 4-5
    return Graph.from_edges(6, [(0, 1), (0, 2), (1, 2), (2, 3), (2, 4), (3, 4), (4, 5)])


def _record(g: Graph, task: str) -> TaskRecord:
    return TaskRecord(
        index=1,
        input_prompt=task_prompt(task, g.n),
        edges=g.edge_string(),
        vertex_num=g.n,
        edge_num=g.m,
        answer=g.ground_truth(task),
        task=task,
        dataset="toy",
    )


# --------------------------------------------------------------------------
# graph statistics
# --------------------------------------------------------------------------


def test_graph_counts():
    g = _toy_graph()
    assert g.count_triangles() == 2
    assert g.count_kstars(2) == sum(math.comb(d, 2) for d in [2, 2, 4, 2, 3, 1])
    assert g.count_kstars(3) == math.comb(4, 3) + math.comb(3, 3)
    assert abs(g.average_degree() - 14 / 6) < 1e-12
    assert Graph.from_edge_string(g.n, g.edge_string()).edges == g.edges


# --------------------------------------------------------------------------
# DP primitives
# --------------------------------------------------------------------------


def test_budget_split_matches_paper():
    eps = 2.0
    s = split_budget(eps, need_noisy_graph=True, need_gs_optimization=True)
    assert s.as_tuple() == (1.0, 0.2, 0.8)  # 0.5e, 0.2(e-e1), rest
    s = split_budget(eps, need_noisy_graph=False, need_gs_optimization=True)
    assert np.allclose(s.as_tuple(), (0.0, 0.4, 1.6))
    s = split_budget(eps, need_noisy_graph=False, need_gs_optimization=False)
    assert s.as_tuple() == (0.0, 0.0, 2.0)
    s = split_budget(eps, need_noisy_graph=True, need_gs_optimization=False)
    assert s.as_tuple() == (1.0, 0.0, 1.0)
    assert naive_budget(eps).as_tuple() == (2.0, 0.0, 0.0)
    for s in [split_budget(eps, True, True), split_budget(eps, False, True)]:
        assert abs(s.total - eps) < 1e-12


def test_randomized_response_flip_rate():
    rng = np.random.default_rng(0)
    n = 300
    g = Graph.from_edges(n, [])  # empty graph -> every noisy edge is a flip
    eps = 1.0
    noisy = build_noisy_graph(g, eps, rng)
    total_entries = n * (n - 1) / 2
    observed = noisy.m / total_entries
    assert abs(observed - flip_probability(eps)) < 0.01
    # only lower-triangle entries are perturbed -> result is a simple graph
    assert all(u not in noisy.adj[u] for u in range(n))


def test_graph_projection_bounds_degree():
    rng = np.random.default_rng(1)
    g = build_noisy_graph(Graph.from_edges(60, []), 0.5, rng)
    assert g.max_degree() > 10
    proj = graph_projection(g, 10, rng)
    assert proj.max_degree() <= 10
    # symmetric
    for u in range(proj.n):
        for v in proj.adj[u]:
            assert u in proj.adj[v]
    assert len(project_neighbor_list(list(range(20)), 5, rng)) == 5
    assert project_neighbor_list([1, 2], 5, rng) == [1, 2]


# --------------------------------------------------------------------------
# rules
# --------------------------------------------------------------------------


def test_triangle_update_rule_example_from_appendix_e():
    msgs = [
        {"Sender_ID": 1, "Sender_Neighbors": [4, 5]},
        {"Sender_ID": 4, "Sender_Neighbors": [2, 5, 8]},
    ]
    assert rules.update_triangle([2, 4], msgs) == 0.5


def test_send_parser_accepts_node_prefixed_ids():
    from psc.agents.node_agent import _parse_send_payload
    from psc.prompts import extract_json

    # verbatim shape of a hy3-ioa reply that used to be dropped
    reply = 'Step 1: ...\n\n```json\n{\n  "Sender_ID": 26,\n  "Sender_Neighbors": ["Node 13", "Node 1", "node 6"]\n}\n```'
    expected = {"Sender_ID": 26, "Sender_Neighbors": [1, 6, 13]}
    assert _parse_send_payload(extract_json(reply)) == expected
    assert _parse_send_payload({"Sender_ID": "Node 26", "Sender_Neighbors": [13, "1", 6.0]}) == expected
    assert _parse_send_payload({"Sender_ID": 26, "Sender_Neighbors": []}) == {"Sender_ID": 26, "Sender_Neighbors": []}
    for bad in (["Node A"], ["Node 1, Node 2"], [1.5], [True], "Node 1, Node 2", None):
        assert _parse_send_payload({"Sender_ID": 26, "Sender_Neighbors": bad}) is None, bad


def test_triangle_rules_recover_exact_count_without_noise():
    g = _toy_graph()
    counts = []
    for i in range(g.n):
        msgs = [rules.send_message(j, g.adj[j]) for j in g.adj[i]]
        counts.append(rules.update_triangle(g.adj[i], msgs))
        assert counts[-1] == rules.triangle_local_count(g.adj[i], g.adj[i], g.adj)
    assert rules.aggregate("triangle", counts, g.n) == g.count_triangles()
    assert rules.aggregate("degree", [rules.update_degree(g.adj[i]) for i in range(g.n)], g.n) == g.average_degree()
    assert rules.aggregate("2-star", [rules.update_kstar(g.adj[i], 2) for i in range(g.n)], g.n) == g.count_kstars(2)


def test_relative_error_metric():
    assert relative_error(110, 100, 49) == 0.1
    # eta = 0.001 n protects against tiny truths
    assert relative_error(1.0, 0.0, 1000) == 1.0


# --------------------------------------------------------------------------
# agent pipeline (mock LLM) vs. pure python ground truth
# --------------------------------------------------------------------------


def _run(coro):
    return asyncio.run(coro)


def test_agent_pipeline_noise_free_limit_is_exact():
    """With a huge budget PSC agents must recover the exact statistics."""
    g = _toy_graph()
    cfg = ModelConfig(provider="mock")
    for task in ["degree", "2-star", "3-star", "triangle"]:
        res = _run(PSCFramework(cfg, seed=3).run(_record(g, task), eps=1e6))
        assert res.parse_failures == 0
        assert abs(res.estimate - g.ground_truth(task)) < 1e-3, (task, res.estimate)
        nv = _run(NaiveFramework(cfg, seed=3).run(_record(g, task), eps=1e6))
        assert abs(nv.estimate - g.ground_truth(task)) < 1e-3, (task, nv.estimate)


def test_agent_pipeline_matches_ground_truth_distribution():
    """Mock-LLM agents and GT-PSC are the same randomized algorithm, so their
    mean relative errors over many runs must agree."""
    g = _toy_graph()
    cfg = ModelConfig(provider="mock")
    task, eps, runs = "2-star", 2.0, 400
    truth = g.ground_truth(task)
    fw = PSCFramework(cfg, seed=11)
    agent_re = np.mean([relative_error(_run(fw.run(_record(g, task), eps)).estimate, truth, g.n) for _ in range(runs)])
    rng = np.random.default_rng(12)
    gt_re = np.mean([relative_error(gt_psc(g, task, eps, rng, mechanism=fw.mechanism), truth, g.n) for _ in range(runs)])
    assert abs(agent_re - gt_re) / max(gt_re, 1e-9) < 0.25, (agent_re, gt_re)


def test_llm_calls_and_budget_bookkeeping():
    g = _toy_graph()
    cfg = ModelConfig(provider="mock")
    res = _run(PSCFramework(cfg, seed=0).run(_record(g, "triangle"), eps=2.0))
    # 1 privacy controller + 1 curator design + n send + n update + 1 aggregate
    assert res.llm_calls == 2 * g.n + 3
    assert res.split == (1.0, 0.2, 0.8)
    # Appendix E DP framework library: "Sensitivity: degree-1"
    assert res.sensitivity == max(1, res.d_hat_max - 1)
    res = _run(PSCFramework(cfg, seed=0, gs_optimization=False).run(_record(g, "triangle"), eps=2.0))
    assert res.split == (1.0, 0.0, 1.0)
    assert res.sensitivity == g.n - 2  # Challenge 3: n - 2 without projection


def test_sensitivities_follow_paper():
    from psc.library import get_dp_framework

    n = 49
    assert get_dp_framework("degree").sensitivity(n, None) == 1
    assert get_dp_framework("2-star").sensitivity(n, None) == math.comb(n, 1)  # C(n, k-1)
    assert get_dp_framework("3-star").sensitivity(n, None) == math.comb(n, 2)
    assert get_dp_framework("2-star").sensitivity(n, 14) == math.comb(14, 1)  # C(d_max, k-1)
    assert get_dp_framework("3-star").sensitivity(n, 14) == math.comb(14, 2)
    assert get_dp_framework("triangle").sensitivity(n, None) == n - 2
    assert get_dp_framework("triangle").sensitivity(n, 14) == 13  # degree - 1


def test_naive_prompt_follows_raw_format():
    from psc.prompts import insert_edges_into_prompt, naive_answer_prompt

    p = task_prompt("2-star", 49)
    out = insert_edges_into_prompt(p, [(0, 1), (0, 2), (45, 47)])
    assert "Q: The nodes are numbered from 0 to 48. The edges are: (0, 1), (0, 2), (45, 47). What is the total number of 2-stars" in out
    assert "local edge differential privacy" in out  # original (V(G), Q) prompt kept
    full = naive_answer_prompt("2-star", p, 49, [(0, 1)])
    assert '"phase": "naive_answer"' in full


def test_non_dp_psc_and_single_llm_baselines_are_exact_with_perfect_reasoner():
    from psc.baselines import SingleLLMBaseline, build_example

    g = _toy_graph()
    cfg = ModelConfig(provider="mock")
    for task in ["degree", "2-star", "3-star", "triangle"]:
        res = _run(PSCFramework(cfg, seed=0, dp=False).run(_record(g, task), eps=2.0))
        assert res.method == "PSC-noDP" and res.sensitivity is None and res.split == (0.0, 0.0, 0.0)
        assert abs(res.estimate - g.ground_truth(task)) < 1e-9
        for style in ("raw", "refined"):
            res = _run(SingleLLMBaseline(cfg, style=style).run(_record(g, task)))
            assert abs(res.estimate - g.ground_truth(task)) < 1e-9
            assert res.llm_calls == 1
        ex = build_example(task)
        assert "Given a graph has 10 nodes and 38 edges." in ex and "Step 1" in ex and "Step 2" in ex


def test_structured_input_only_reaches_the_mock():
    from agentscope.formatter import OpenAIChatFormatter
    from agentscope.message import TextBlock
    from agentscope.model import ChatModelBase, ChatResponse

    from psc.models import chat
    from psc.prompts import node_update_prompt, strip_structured

    assert ModelConfig(provider="mock").use_structured_input
    assert not ModelConfig(provider="openai").use_structured_input
    assert ModelConfig(provider="openai", structured_input=True).use_structured_input

    class _Capture(ChatModelBase):
        def __init__(self):
            super().__init__(model_name="capture", stream=False)
            self.seen = ""

        async def __call__(self, messages, **kwargs):
            self.seen = messages[-1]["content"]
            if isinstance(self.seen, list):
                self.seen = "".join(b.get("text", "") for b in self.seen)
            return ChatResponse(content=[TextBlock(type="text", text='{"count": 1}')])

    prompt = node_update_prompt("degree", 5, [2, 4], [], "Update rule text", 0.0)
    model = _Capture()
    model.psc_structured_input = False
    _run(chat(model, OpenAIChatFormatter(), "sys", prompt))
    assert "<structured_input>" not in model.seen and "Update rule text" in model.seen
    assert model.seen == strip_structured(prompt)


def test_validation_counts_llm_mistakes_instead_of_hiding_them():
    from psc.mock_model import MockChatModel
    from psc.prompts import extract_structured

    g = _toy_graph()
    rec = _record(g, "triangle")

    # perfect reasoner: every node-level check passes, paired GT equals the estimate
    res = _run(PSCFramework(ModelConfig(provider="mock"), seed=0).run(rec, eps=2.0))
    v = res.extra["validation"]
    assert v["task_correct"] and v["aggregate_exact"]
    assert v["send_exact"] == v["update_exact"] == v["e2e_exact"] == g.n
    assert abs(v["rule_estimate"] - res.estimate) < 1e-9

    # a node model whose send replies are unparseable: nothing is sent
    class _BrokenSend(MockChatModel):
        async def __call__(self, messages, **kwargs):
            text = messages[-1]["content"]
            text = text if isinstance(text, str) else "".join(b.get("text", "") for b in text)
            if (extract_structured(text) or {}).get("phase") == "node_send":
                from agentscope.message import TextBlock
                from agentscope.model import ChatResponse

                return ChatResponse(content=[TextBlock(type="text", text="I cannot do that.")])
            return await super().__call__(messages, **kwargs)

    fw = PSCFramework(ModelConfig(provider="mock"), seed=0)
    fw.factory.node_model = _BrokenSend()
    res = _run(fw.run(rec, eps=1e6))
    v = res.extra["validation"]
    assert res.parse_failures == g.n and v["send_exact"] == 0
    assert v["update_exact"] == g.n  # the update rule itself was followed ...
    assert v["e2e_exact"] < g.n  # ... but on an empty inbox, so counts are wrong
    assert abs(res.estimate) < 1e-3 and abs(v["rule_estimate"] - 2.0) < 1e-3

    nv = _run(NaiveFramework(ModelConfig(provider="mock"), seed=0).run(rec, eps=2.0))
    assert abs(nv.extra["validation"]["rule_estimate"] - nv.estimate) < 1e-9


def test_parallel_runs_are_reproducible_and_overlap(monkeypatch):
    from psc.experiments import run_agent_experiment
    from psc.mock_model import MockChatModel

    data = Path(__file__).resolve().parents[1] / "data"
    original = MockChatModel.__call__
    in_flight = peak = 0

    async def slow_call(self, *args, **kwargs):
        nonlocal in_flight, peak
        in_flight += 1
        peak = max(peak, in_flight)
        await asyncio.sleep(0.01)
        try:
            return await original(self, *args, **kwargs)
        finally:
            in_flight -= 1

    monkeypatch.setattr(MockChatModel, "__call__", slow_call)

    def run(parallel: int):
        nonlocal peak
        peak = 0
        cfg = ModelConfig(provider="mock", parallel_runs=parallel)
        _, per_run = asyncio.run(run_agent_experiment(
            data, cfg, ["CU"], ["degree", "triangle"], [2.0], {"Naive": 3, "PSC": 2}, ("Naive", "PSC"), log=lambda _: None,
        ))
        return [(r["method"], r["task"], r["estimate"], r["noisy_edges"]) for r in per_run], peak

    sequential, peak1 = run(1)
    parallel, peak4 = run(4)
    assert sequential == parallel  # run i always uses run_rng(seed, i)
    assert len(sequential) == 10
    assert peak4 > peak1 and peak4 <= 4 + 8  # runs overlap; node calls stay capped by max_concurrency


def test_model_config_from_env_file_and_config_file():
    import os
    import tempfile

    keys = ("PSC_PROVIDER", "PSC_CONFIG", "OPENAI_API_KEY", "OPENAI_BASE_URL")
    saved = {k: os.environ.pop(k, None) for k in keys}
    try:
        with tempfile.TemporaryDirectory() as d:
            conf, env = Path(d) / "config.toml", Path(d) / ".env"
            conf.write_text(
                'provider = "openai"\nmax_concurrency = 4\n'
                '[openai]\nnode_model = "node-x"\ncurator_model = "curator-y"\n'
                '[dashscope]\nnode_model = "q-small"\n',
            )
            env.write_text("OPENAI_API_KEY=sk-from-dotenv\nOPENAI_BASE_URL=\n")

            cfg = ModelConfig.from_env(config_path=conf, env_path=env)
            assert (cfg.provider, cfg.node_model, cfg.curator_model) == ("openai", "node-x", "curator-y")
            assert cfg.max_concurrency == 4 and cfg.api_key == "sk-from-dotenv" and cfg.base_url is None

            # CLI flags win over the file; another provider picks its own section
            assert ModelConfig.from_env(config_path=conf, env_path=env, node_model="cli").node_model == "cli"
            ds = ModelConfig.from_env("dashscope", config_path=conf, env_path=env)
            assert (ds.node_model, ds.curator_model) == ("q-small", "qwen-plus")

            conf.write_text('[openai]\nnode_modle = "typo"\n')
            try:
                ModelConfig.from_env(config_path=conf, env_path=None)
            except ValueError as e:
                assert "node_modle" in str(e)
            else:
                raise AssertionError("typo in config file must be rejected")
    finally:
        for k, v in saved.items():
            os.environ.pop(k, None)
            if v is not None:
                os.environ[k] = v


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"{name}: ok")
