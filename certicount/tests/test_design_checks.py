"""Step 1a of the design loop: reader, repair hints, noise-aware gate, GS growth check, transcript tags."""

from __future__ import annotations

import asyncio
import random
import sys
from pathlib import Path
from typing import Any

import pytest
from agentscope.model import ChatModelBase, ChatResponse

from psc.models import ModelConfig, create_formatter
from certicount.dsl.designer import (
    TRUNCATED_FEEDBACK, _text, check_draft, design_program, design_reference_params, draft_stage, growth_feedback,
    read_draft, repair_hint,
)
from certicount.dsl.ground_truth import reference_program
from certicount.dsl.lang import DSLError, Env, Interpreter, parse_program
from certicount.dsl.library import analyst_prompt
from certicount.dsl.matrix import table_matrix
from certicount.dsl.noisy_gate import NoisyGate, holme_kim, noise_free_check, public_test_graphs
from certicount.dsl.sensitivity import PublicParams, derive

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from analyze_design_certification import calls_by_design  # noqa: E402

FMT = create_formatter(ModelConfig())
N = 200  # public graph size of the gate tests (the experiments use the real n)
GATE = NoisyGate(N, reps=4)
GATE_NODE = NoisyGate(N, node_bounds=True, alpha=5.0, reps=4)


# ---------------------------------------------------------------- reader: several for clauses
def test_several_for_clauses_are_nested_sums():
    flat = parse_program("Q = project(P, D)\nreturn sum(A(j, k) for j in Q for k in Q)", "total / 6")
    nested = parse_program("Q = project(P, D)\nreturn sum(sum(A(j, k) for k in Q) for j in Q)", "total / 6")
    assert flat.ret == nested.ret
    p = PublicParams(40, D=6, dmax=6, eps1=1.0)
    assert derive(flat, p).gs == pytest.approx(derive(nested, p).gs)
    rnd = random.Random(3)
    vals = {(j, k): rnd.choice((-0.58, 1.58)) for j in range(9) for k in range(j + 1, 9)}
    env = Env(frozenset({1, 2, 4, 5, 7}), 0, {}, 9, D=6, dmax=6, matrix=table_matrix(vals))
    assert Interpreter(flat).local(env) == pytest.approx(Interpreter(nested).local(env))


def test_inner_domain_may_use_the_outer_variable_and_conditions_stay_rejected():
    parse_program("return sum(size(N(v)) for u in P for v in N(u))")
    with pytest.raises(DSLError, match="without conditions"):
        parse_program("return sum(1 for a in P for b in P if a < b)")
    with pytest.raises(DSLError, match="shadows"):
        parse_program("return sum(1 for a in P for a in P)")


# ---------------------------------------------------------------- reader: reasoning and truncation
def test_program_is_read_after_the_reasoning_block():
    reply = ("<think>draft:\n```dsl\nreturn size(N(self))\n```\naggregate: total / n\nno, use P</think>\n"
             "```dsl\nreturn size(P)\n```\naggregate: total / n")
    prog, _ = read_draft(reply)
    assert prog is not None and prog.source.strip() == "return size(P)"
    prog, entry = read_draft("<think>```dsl\nreturn size(P)\n```</think>\nI give up.")
    assert prog is None and draft_stage(entry["feedback"]) == "parse"


def test_truncated_reasoning_is_its_own_stage():
    prog, entry = read_draft("<think>let me add 4.2 + 99.1 = 103.3, then ...")
    assert prog is None and entry["truncated"] and entry["feedback"] == TRUNCATED_FEEDBACK
    assert draft_stage(entry["feedback"]) == "truncated"


# ---------------------------------------------------------------- repair hints
@pytest.mark.parametrize("source, needle", [
    ("name = size(P)\nreturn name * (name - 1) // 2", "'/' instead of '//'"),
    ("return sum(size(N(v) & {w}) for v in P)", "no literals"),
    ("return sum(size(N(v) & N(u)) for v in N(u))", "'u' is not defined"),
    ("degree = project(P, D)\nreturn comb(degree, 2)", "comb(size(S), k)"),
    ("Q = project(N(self), D)\nreturn sum(sum(A(v, w) for w in Q) for v in Q)", "N(self) is only a randomized copy"),
    ("name = size(P)\nname = comb(name, 2)\nreturn name", "assign each name once"),
    ("<program>\nreturn comb(size(N(self)), 3)", "placeholder"),
    ("neighbors = A(self)\nreturn 0", "two nodes"),
])
def test_rejections_carry_a_repair_hint(source, needle):
    prog, entry = read_draft(f"```dsl\n{source}\n```\naggregate: total")
    assert prog is None and draft_stage(entry["feedback"]) == "parse"
    assert "Hint:" in entry["feedback"] and needle in entry["feedback"]


def test_hints_never_contain_a_code_fence_or_a_task_program():
    for msg in ("no code block found", "sum supports 'for <name> in <set>' without conditions",
                "a program reads either the noisy rows N(...) or the unbiased matrix A(...), not both"):
        hint = repair_hint(msg) or ""
        assert "```" not in hint and "A(j, k)" not in hint


# ---------------------------------------------------------------- GS growth check
@pytest.mark.parametrize("source, aggregate", [
    ("stars = size(P) * (size(P) - 1) * (size(P) - 2) / 6\nreturn stars", "total"),
    ("name = sum(A(j, k) for j in P for k in P) / 2\nreturn name", "total / 3"),
])
def test_gs_growing_with_n_is_rejected(source, aggregate):
    params = design_reference_params(453)
    fb = check_draft(parse_program(source, aggregate), None, params, falsifier=False)
    assert fb is not None and "grows with the number of nodes" in fb and draft_stage(fb) == "gs_loose"


@pytest.mark.parametrize("node_bounds", [False, True])
@pytest.mark.parametrize("task", ["degree", "2-star", "3-star", "triangle", "degree-moment2"])
def test_references_have_n_independent_gs(task, node_bounds):
    assert growth_feedback(reference_program(task, node_bounds), design_reference_params(453)) is None


# ---------------------------------------------------------------- noise-aware gate
def test_public_graphs_are_deterministic_heavy_tailed_and_clustered():
    a, b = public_test_graphs(N), public_test_graphs(N)
    assert [g.edges for _, g in a] == [g.edges for _, g in b]
    import numpy as np

    g = holme_kim(N, 4, 0.6, np.random.default_rng(1))
    degs = [len(g.adj[i]) for i in range(N)]
    from certicount.dsl.utility import reference_counter

    assert max(degs) > 5 * (sum(degs) / N) and reference_counter("triangle")(g) > 50


@pytest.mark.parametrize("gate", [GATE, GATE_NODE], ids=["psc", "node"])
@pytest.mark.parametrize("task", ["degree", "2-star", "3-star", "triangle"])
def test_gate_accepts_the_references(task, gate):
    rep = noise_free_check(reference_program(task, gate.node_bounds), task, gate)
    assert rep.passed, rep.rows


@pytest.mark.parametrize("source, aggregate, task", [
    ("return comb(size(N(self)), 3)", "total", "3-star"),
    ("return comb(size(N(self)), 2)", "total", "2-star"),
    ("s = project(N(self), D)\nreturn sum(size(N(v) & s) for v in s) / 2", "total / 3", "triangle"),
])
def test_gate_rejects_the_release_read_as_the_graph(source, aggregate, task):
    rep = noise_free_check(parse_program(source, aggregate), task, GATE)
    assert not rep.passed and "noise-free check failed" in rep.feedback() and "times the exact answer" in rep.feedback()
    assert draft_stage(rep.feedback()) == "noisy"


def test_gate_rejects_degree_from_the_noisy_row_in_the_node_architecture():
    rep = noise_free_check(parse_program("return size(N(self))", "total / n"), "degree", GATE_NODE)
    assert not rep.passed


class _Script(ChatModelBase):
    """Curator that answers a fixed sequence of replies."""

    def __init__(self, replies: list[str]) -> None:
        super().__init__(model_name="script", stream=False)
        self.replies = list(replies)

    async def __call__(self, messages: list[dict], **kwargs: Any) -> ChatResponse:  # type: ignore[override]
        return _text(self.replies.pop(0))


def test_design_loop_rejects_the_shortcut_with_the_gate_and_accepts_the_rewrite():
    bad = "```dsl\nreturn comb(size(N(self)), 3)\n```\naggregate: total"
    good = "```dsl\nreturn comb(size(project(P, D)), 3)\n```\naggregate: total"
    params = design_reference_params(N)
    res = asyncio.run(design_program(_Script([bad]), FMT, analyst_prompt("3-star", N), N, params, "3-star", 1))
    assert res.accepted  # without the gate the shortcut is accepted (GS 0, exact utility test passes)
    res = asyncio.run(design_program(_Script([bad, good]), FMT, analyst_prompt("3-star", N), N, params, "3-star", 2,
                                     noisy=GATE))
    assert res.accepted and res.iterations == 2
    assert [draft_stage(h["feedback"]) for h in res.history] == ["noisy", "accepted"]


# ---------------------------------------------------------------- transcript grouping
def test_calls_are_grouped_by_design_tag_or_by_position():
    designs = [{"dataset": "PM", "task": "t", "design": k, "llm_calls": c} for k, c in ((0, 2), (1, 1))]
    tagged = [{"dataset": "PM", "task": "t", "design": 1, "reply": "b0"},
              {"dataset": "PM", "task": "t", "design": 0, "reply": "a0"},
              {"dataset": "PM", "task": "t", "design": 0, "reply": "a1"}]
    assert [[c["reply"] for c in g] for g in calls_by_design(designs, tagged)] == [["a0", "a1"], ["b0"]]
    serial = [{"reply": r} for r in ("a0", "a1", "b0")]
    assert [[c["reply"] for c in g] for g in calls_by_design(designs, serial)] == [["a0", "a1"], ["b0"]]
