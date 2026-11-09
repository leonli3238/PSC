"""Tests of the degree violation probe (:mod:`certicount.probe`,
:mod:`certicount.probe_client`, ``scripts/run_degree_probe.py``)."""

from __future__ import annotations

import asyncio
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import certicount  # noqa: E402,F401
from agentscope.message import Msg  # noqa: E402
from certicount import probe_client  # noqa: E402
from certicount.audit import Flip  # noqa: E402
from certicount.probe import (  # noqa: E402
    GS,
    all_flips,
    as_trials,
    build_plan,
    check_plan,
    degree_input,
    digit_similar,
    digit_variants,
    flip_tags,
    load_graph,
    targeted_flips,
    violation_category,
)
from certicount.probe_client import InfraError, MockProbeClient, OpenAIProbeClient, load_jsonl, missing_jobs, run_jobs  # noqa: E402
from psc.agents import node_agent as na  # noqa: E402
from psc.library import get_algorithm  # noqa: E402
from psc.models import ModelConfig, create_formatter  # noqa: E402
from psc.prompts import NODE_SYSTEM, strip_structured  # noqa: E402

SCRIPT = ROOT / "scripts" / "run_degree_probe.py"


@pytest.fixture(scope="module")
def pm():
    return load_graph("PM")


# ---------------------------------------------------------------------------
# prompts and requests are PSC's
# ---------------------------------------------------------------------------


def test_prompt_matches_node_agent(pm, monkeypatch):
    node = max(range(pm.n), key=pm.degree)
    seen = {}

    async def fake_chat(model, formatter, system, user, agent=None):
        seen.update(system=system, user=user)
        return '```json\n{"Degree": 3}\n```'

    monkeypatch.setattr(na, "chat", fake_chat)
    agent = na.NodeAgent(node, pm.neighbors(node), model=None, formatter=None)
    asyncio.run(agent._update("degree", get_algorithm("degree").update))
    inp = degree_input(node, pm.neighbors(node))
    assert seen["user"] == inp.prompt()
    assert seen["system"] == NODE_SYSTEM.format(node_id=node)
    assert inp.state == 0.0 and inp.messages == () and inp.rule_value() == pm.degree(node)


def _vllm_cfg(**kw) -> ModelConfig:
    cfg = ModelConfig(provider="vllm", node_model="Qwen3-1.7B", api_key="EMPTY", node_base_url="http://127.0.0.1:9/v1",
                      temperature=0.0, max_retries=2, retry_backoff=0.0)
    cfg.extra = {"extra_body": {"chat_template_kwargs": {"enable_thinking": False}}, "max_tokens": 4096}
    for k, v in kw.items():
        setattr(cfg, k, v)
    return cfg


class _FakeCompletions:
    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = []

    async def create(self, **kw):
        self.calls.append(kw)
        r = self.replies.pop(0)
        if isinstance(r, Exception):
            raise r
        msg = SimpleNamespace(content=r, reasoning_content=None)
        return SimpleNamespace(
            id="req-1", choices=[SimpleNamespace(message=msg, finish_reason="stop")],
            usage=SimpleNamespace(prompt_tokens=100, completion_tokens=7),
        )


def _client(replies, **kw):
    c = OpenAIProbeClient(_vllm_cfg(**kw))
    fake = _FakeCompletions(replies)
    c.client = SimpleNamespace(chat=SimpleNamespace(completions=fake))
    return c, fake


def test_openai_request_matches_psc_chat(pm):
    node = 5
    inp = degree_input(node, pm.neighbors(node))
    c, fake = _client(['```json\n{"Degree": 4}\n```'])
    system = NODE_SYSTEM.format(node_id=node)
    reply = asyncio.run(c.complete(system, inp.prompt(), "k"))
    call = fake.calls[0]
    expected = asyncio.run(create_formatter(_vllm_cfg()).format(
        [Msg("system", system, "system"), Msg("user", strip_structured(inp.prompt()), "user")]))
    assert call["messages"] == expected
    assert "structured_input" not in json.dumps(call["messages"])
    assert call["temperature"] == 0.0 and call["max_tokens"] == 4096 and call["stream"] is False
    assert call["extra_body"] == {"chat_template_kwargs": {"enable_thinking": False}}
    assert call["model"] == "Qwen3-1.7B"
    assert reply.finish_reason == "stop" and reply.completion_tokens == 7 and reply.request_id == "req-1"


def test_openai_retries_and_infra_error():
    class APIConnectionError(Exception):
        pass

    c, fake = _client(["", "  ", '{"Degree": 2}'])
    r = asyncio.run(c.complete("s", "u", "k"))
    assert r.text == '{"Degree": 2}' and r.attempts == 3
    c, _ = _client(["", "", ""])
    assert asyncio.run(c.complete("s", "u", "k")).text == ""  # empty after all attempts: a model answer
    c, _ = _client([APIConnectionError("down")] * 3)
    with pytest.raises(InfraError):
        asyncio.run(c.complete("s", "u", "k"))
    c, _ = _client([ValueError("bad request")])
    with pytest.raises(ValueError):
        asyncio.run(c.complete("s", "u", "k"))


def test_guided_json_override():
    from certicount.probe_client import guided_json_schema

    c = OpenAIProbeClient(_vllm_cfg(), {"extra_body": {"guided_json": guided_json_schema()}})
    assert c.kwargs["extra_body"]["chat_template_kwargs"] == {"enable_thinking": False}
    assert c.kwargs["extra_body"]["guided_json"]["required"] == ["Degree"]


# ---------------------------------------------------------------------------
# flips and plan
# ---------------------------------------------------------------------------


def test_digit_similarity():
    assert digit_similar(12, 112) and digit_similar(12, 121) and digit_similar(12, 21) and digit_similar(12, 13)
    assert not digit_similar(12, 12) and not digit_similar(12, 345) and not digit_similar(5, 123)
    vs = digit_variants(12, 453)
    assert {112, 121, 120, 21, 13, 2, 1}.issubset(vs) and all(0 <= v < 453 for v in vs) and 12 not in vs


def test_flips_are_single_bit_and_tagged(pm):
    import numpy as np

    node = max(range(pm.n), key=pm.degree)
    nb = pm.neighbors(node)
    flips = all_flips(nb, node, pm.n)
    assert len(flips) == pm.n - 1 and all(f.vertex != node for f in flips)
    for f in flips:
        assert len(set(f.apply(nb)) ^ set(nb)) == 1
    t = targeted_flips(nb, node, pm.n, np.random.default_rng(0))
    assert 30 <= len(t) <= 40 and len({f.vertex for f in t}) == len(t)
    assert {"P", "C", "S", "R"} <= {f.strategy for f in t}
    tags = flip_tags([1, 2, 3, 10, 11, 50], 7, Flip("add", 12))
    assert "consecutive" in tags and "digit_sim" in tags
    assert "len_boundary" in flip_tags(list(range(1, 10)), 0, Flip("add", 20))


def test_plan_valid(pm):
    plan = build_plan(pm, "PM", seed=0, mid_nodes=5, low_nodes=3, hub_flips=None, random_per_node=1)
    check_plan(plan)
    hubs = plan["nodes"]["hub"]
    assert len(hubs) == sum(d > 30 for d in pm.degrees()) == 18
    assert sum(p["family"] == "E" for p in plan["pairs"]) == 18 * (pm.n - 1)
    assert sum(p["random_ref"] for p in plan["pairs"]) == 18 + 5 + 3
    ls = [p for p in plan["pairs"] if p["family"] == "L"]
    assert ls and all(p["degree2"] % 10 == 0 and p["degree"] == p["degree2"] - 1 for p in ls)
    assert all(p["kind"] == "constructed" for p in plan["pairs"] if p["family"] in ("L", "X"))
    assert all(abs(p["f_x2"] - p["f_x"]) == GS for p in plan["pairs"])
    bad = json.loads(json.dumps(plan))
    bad["pairs"][0]["x2_key"] = bad["pairs"][0]["x_key"]
    with pytest.raises(ValueError):
        check_plan(bad)


# ---------------------------------------------------------------------------
# trials, classification, resume
# ---------------------------------------------------------------------------


def test_screen_trials_never_eval():
    scr = [{"value": 3.0, "status": "json", "phase": "screen", "rep": r} for r in range(3)]
    sel = [{"value": 3.0, "status": "json", "phase": "select", "rep": r} for r in range(3)]
    ev = [{"value": 3.0, "status": "json", "phase": "eval", "rep": r} for r in range(3)]
    a, b, c = as_trials(scr, "screen"), as_trials(sel, "select"), as_trials(ev, "eval")
    assert {t["phase"] for t in a + b} == {"select"} and {t["phase"] for t in c} == {"eval"}
    assert not {t["rep"] for t in a} & {t["rep"] for t in b}  # distinct Laplace draws


def test_violation_category():
    j = [{"status": "json"}] * 3
    assert violation_category(j, j) == "count"
    assert violation_category(j, j + [{"status": "number"}]) == "number_fallback"
    assert violation_category(j + [{"status": "failed"}], j + [{"status": "number"}]) == "failed"


def test_run_jobs_resume(tmp_path, pm):
    inputs = {"a": degree_input(3, pm.neighbors(3)), "b": degree_input(4, pm.neighbors(4))}
    jobs = [(k, "screen", r) for k in inputs for r in range(3)]
    client = MockProbeClient("exact")
    asyncio.run(run_jobs(client, inputs, jobs[:4], tmp_path, concurrency=2, seed=0, desc="t"))
    with (tmp_path / "samples.jsonl").open("a") as f:
        f.write('{"key": "b", "pha')  # interrupted write
    have = load_jsonl(tmp_path / "samples.jsonl")
    assert len(have) == 4
    todo = missing_jobs(jobs, have)
    assert todo == jobs[4:]
    asyncio.run(run_jobs(client, inputs, todo, tmp_path, concurrency=2, seed=0, desc="t"))
    rows = load_jsonl(tmp_path / "samples.jsonl")
    assert not missing_jobs(jobs, rows)
    assert all(r["correct"] and r["status"] == "json" for r in rows)


def test_failed_parse_keeps_zero(tmp_path, pm):
    class Garbled(MockProbeClient):
        async def complete(self, system, user, ident):
            return probe_client.Reply("I cannot count.", "length", 10, 4096, 0.0, 1)

    inputs = {"a": degree_input(3, pm.neighbors(3))}
    asyncio.run(run_jobs(Garbled(), inputs, [("a", "screen", 0)], tmp_path, concurrency=1, seed=0, desc="t"))
    row = load_jsonl(tmp_path / "samples.jsonl")[0]
    assert row["status"] == "failed" and row["value"] == 0.0 and row["finish_reason"] == "length"
    assert load_jsonl(tmp_path / "replies.jsonl")[0]["reply"] == "I cannot count."


# ---------------------------------------------------------------------------
# end to end (mock negative controls, Bonferroni, transfer)
# ---------------------------------------------------------------------------


def _run(*args):
    r = subprocess.run([sys.executable, str(SCRIPT), *map(str, args)], capture_output=True, text=True, cwd=ROOT)
    assert r.returncode == 0, r.stdout + r.stderr
    return r.stdout


SMALL = ["--hub-flips", "30", "--mid-nodes", "3", "--low-nodes", "2", "--no-constructed"]


@pytest.mark.parametrize("mode,expect", [("exact", 0), ("bias", 0), ("edge", None)])
def test_end_to_end_mock(tmp_path, mode, expect):
    d = tmp_path / mode
    _run("init", "--out", d, "--provider", "mock", "--mock-mode", mode, "--mock-trigger", "7", *SMALL)
    _run("screen", "--out", d)
    cands = load_jsonl(d / "screen" / "candidates.jsonl")
    spec = "top:10" if cands else "random"
    _run("confirm", "--out", d, "--name", "c", "--pairs", spec, "--eval", "200", "--select", "10")
    design = json.loads((d / "confirm_c" / "design.json").read_text())
    rows = load_jsonl(d / "confirm_c" / "pairs.jsonl")
    assert design["alpha_pair"] == pytest.approx(0.05 / design["m"]) and len(rows) == design["m"]
    assert all(r["alpha_pair"] == design["alpha_pair"] for r in rows)
    own = load_jsonl(d / "confirm_c" / "samples.jsonl")
    assert {s["phase"] for s in own} == {"select", "eval"}
    for r in rows:
        assert r["eval_trials"][0] in (200, 500) and r["eval_trials"][1] in (200, 500)
        assert r["select_trials"][0] >= 10 + 3  # screen trials + fresh selection trials, both selection only
    viol = load_jsonl(d / "confirm_c" / "confirmed.jsonl")
    if expect is not None:
        assert len(viol) == expect
    else:
        assert cands and len(viol) == len(rows) > 0
        assert all(7 in (r["flip"]["vertex"],) and r["category"] == "count" for r in viol)
        # transfer: same plan, other model (exact) -> no violation retained; reruns resume
        t = tmp_path / "transfer"
        _run("init", "--out", t, "--plan-from", d, "--provider", "mock", "--mock-mode", "exact")
        _run("confirm", "--out", t, "--name", "tr", "--pairs", f"confirmed:{d / 'confirm_c'}", "--select", "10")
        out = _run("confirm", "--out", t, "--name", "tr", "--pairs", f"confirmed:{d / 'confirm_c'}", "--select", "10")
        assert "0 to run" in out
        assert load_jsonl(t / "confirm_tr" / "confirmed.jsonl") == []
        rep = tmp_path / "rep"
        _run("report", "--runs", d, t, "--report-dir", rep)
        report = json.loads((rep / "report.json").read_text())
        assert report["transfer"][0]["retained"] == 0 and report["transfer"][0]["source_violations"] == len(viol)


def test_confirm_design_is_frozen(tmp_path):
    d = tmp_path / "f"
    _run("init", "--out", d, "--provider", "mock", "--mock-mode", "exact", *SMALL)
    _run("screen", "--out", d)
    _run("confirm", "--out", d, "--name", "r", "--pairs", "random", "--eval", "50", "--select", "5")
    r = subprocess.run([sys.executable, str(SCRIPT), "confirm", "--out", str(d), "--name", "r", "--pairs", "random",
                        "--eval", "60", "--select", "5"], capture_output=True, text=True, cwd=ROOT)
    assert r.returncode != 0 and "design has eval=50" in (r.stdout + r.stderr)


# ---------------------------------------------------------------------------
# per-node cap, node-level design, joint Bonferroni
# ---------------------------------------------------------------------------


def test_top_pairs_per_node():
    from certicount.probe import top_pairs

    cands = [{"pair_id": f"a|add{i}"} for i in range(5)] + [{"pair_id": "b|add1"}, {"pair_id": "c|add2"}]
    assert top_pairs(cands, 3) == ["a|add0", "a|add1", "a|add2"]
    assert top_pairs(cands, 3, per_node=2) == ["a|add0", "a|add1", "b|add1"]
    assert top_pairs(cands, 10, per_node=1) == ["a|add0", "b|add1", "c|add2"]


def test_node_level_pairs_and_table(pm):
    from certicount.probe import node_level_pairs, node_table

    plan = build_plan(pm, "PM", seed=0, mid_nodes=3, low_nodes=2, hub_flips=6, constructed=False)
    rows = []
    for p in plan["pairs"]:
        big = p["node_id"] == plan["nodes"]["hub"][0]
        d = 5.0 if big and p["flip"]["vertex"] % 2 else (2.0 if big else 1.0)
        rows.append({"pair_id": p["pair_id"], "node_id": p["node_id"], "kind": p["kind"], "complete": True,
                     "delta_max": d, "frac_far": 1.0 if d > 1 else 0.0, "candidate": d > 1})
    ids, universe = node_level_pairs(plan, rows)
    n_sel = sum(len(v) for v in plan["nodes"].values())
    assert len(universe) == n_sel and len(ids) == 1
    best = next(r for r in rows if r["pair_id"] == ids[0])
    assert best["delta_max"] == 5.0
    t = node_table(universe, [{"pair_id": ids[0], "violation": True, "eps_lb": 3.0}])
    allrow = t[-1]
    assert allrow["bin"] == "all" and allrow["nodes"] == n_sel and allrow["confirmed"] == 1
    assert allrow["with_candidate"] == 1 and allrow["confirmed_share"] == pytest.approx(1 / n_sel)


def test_family_recompute_only_shrinks():
    from certicount.audit import epsilon_from_counts
    from certicount.probe import family_recompute

    def row(k, k2, n=300):
        e = max(0.0, epsilon_from_counts(k, n, k2, n, 0.05 / 2))
        return {"counts": {"k_num": k, "n_num": n, "k_den": k2, "n_den": n}, "eps": [0, 0, 2.0], "eps_lb": e,
                "violation": e > 2, "kind": "real", "category": "count" if e > 2 else None}

    sets = {"s1": [row(300, 0), row(150, 30)], "s2": [row(290, 1), row(280, 3)] + [row(200, 100)] * 40}
    rs, tot = family_recompute(sets, 0.05)
    assert tot["M"] == 44 and tot["alpha_pair"] == pytest.approx(0.05 / 44)
    for r in rs:
        assert r["violations_family"] <= r["violations_design"]
    assert tot["violations_family"] >= 1  # 300 vs 0 of 300 survives any reasonable M


def test_end_to_end_nodes_and_report(tmp_path):
    d = tmp_path / "edge"
    _run("init", "--out", d, "--provider", "mock", "--mock-mode", "edge", "--mock-trigger", "7", *SMALL)
    _run("screen", "--out", d)
    _run("confirm", "--out", d, "--name", "div", "--pairs", "top:10", "--per-node", "1", "--eval", "200",
         "--select", "10")
    rows = load_jsonl(d / "confirm_div" / "pairs.jsonl")
    xs = [r["x_key"] for r in rows]
    assert len(xs) == len(set(xs))  # at most one pair per input
    _run("confirm", "--out", d, "--name", "nodes", "--pairs", "nodes", "--eval", "200", "--select", "10")
    design = json.loads((d / "confirm_nodes" / "design.json").read_text())
    universe = design["pair_source"]["universe"]
    plan = json.loads((d / "plan.json").read_text())
    assert len(universe) == sum(len(v) for v in plan["nodes"].values())
    nrows = load_jsonl(d / "confirm_nodes" / "pairs.jsonl")
    assert len({r["node_id"] for r in nrows}) == len(nrows) == design["m"]
    assert all(r["flip"]["vertex"] == 7 for r in nrows)  # the edge mock only errs on the trigger vertex
    summ = json.loads((d / "confirm_nodes" / "summary.json").read_text())
    assert summ["nodes"][-1]["bin"] == "all" and summ["nodes"][-1]["confirmed"] == design["m"]
    # rerun with another per-node cap on the same name is refused
    r = subprocess.run([sys.executable, str(SCRIPT), "confirm", "--out", str(d), "--name", "div", "--pairs", "top:10",
                        "--per-node", "2", "--eval", "200", "--select", "10"], capture_output=True, text=True, cwd=ROOT)
    assert r.returncode != 0 and "per_node" in (r.stdout + r.stderr)
    rep = tmp_path / "rep"
    _run("report", "--runs", d, "--report-dir", rep, "--family-alpha", "0.05")
    report = json.loads((rep / "report.json").read_text())
    tot = report["family_totals"][0]
    assert tot["M"] == len(rows) + len(nrows)
    assert tot["violations_family"] <= sum(r["violation"] for r in rows + nrows)
    assert any(n["set"] == "nodes" and n["bin"] == "all" for n in report["nodes"])


def test_nodes_design_exact_mock_has_no_pairs(tmp_path):
    d = tmp_path / "exact"
    _run("init", "--out", d, "--provider", "mock", "--mock-mode", "exact", *SMALL)
    _run("screen", "--out", d)
    r = subprocess.run([sys.executable, str(SCRIPT), "confirm", "--out", str(d), "--name", "nodes", "--pairs", "nodes"],
                       capture_output=True, text=True, cwd=ROOT)
    assert r.returncode != 0 and "no pairs to confirm" in (r.stdout + r.stderr)
    universe = json.loads((d / "confirm_nodes" / "nodes_universe.json").read_text())
    assert universe and not any(u["candidate"] for u in universe)


def test_report_locates_moved_source(tmp_path):
    root = tmp_path / "runs"
    src = root / "m1"
    _run("init", "--out", src, "--provider", "mock", "--mock-mode", "edge", "--mock-trigger", "7", *SMALL)
    _run("screen", "--out", src)
    _run("confirm", "--out", src, "--name", "main", "--pairs", "top:5", "--eval", "100", "--select", "5")
    t = root / "m2"
    _run("init", "--out", t, "--plan-from", src, "--provider", "mock", "--mock-mode", "edge", "--mock-trigger", "7")
    _run("confirm", "--out", t, "--name", "tr", "--pairs", f"confirmed:{src / 'confirm_main'}", "--eval", "100",
         "--select", "5")
    des = json.loads((t / "confirm_tr" / "design.json").read_text())
    des["pair_source"]["path"] = "/elsewhere/results/m1/confirm_main/confirmed.jsonl"
    (t / "confirm_tr" / "design.json").write_text(json.dumps(des))
    s = json.loads((t / "confirm_tr" / "summary.json").read_text())
    s["design"]["pair_source"]["path"] = des["pair_source"]["path"]
    (t / "confirm_tr" / "summary.json").write_text(json.dumps(s))
    _run("report", "--runs", src, t, "--report-dir", tmp_path / "rep")
    report = json.loads((tmp_path / "rep" / "report.json").read_text())
    tr = report["transfer"][0]
    assert tr["source_violations"] > 0 and tr["retained"] == tr["source_violations"]
    (src / "confirm_main" / "confirmed.jsonl").rename(src / "confirm_main" / "moved.jsonl")
    r = subprocess.run([sys.executable, str(SCRIPT), "report", "--runs", str(src), str(t), "--report-dir",
                        str(tmp_path / "rep2")], capture_output=True, text=True, cwd=ROOT)
    assert r.returncode != 0 and "cannot find" in (r.stdout + r.stderr)
