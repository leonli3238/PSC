"""Prompt specs and the self-evolution loop (offline, scripted models)."""

from __future__ import annotations

import asyncio
import json
import re
from typing import Any

import pytest
from agentscope.model import ChatModelBase, ChatResponse

from psc.models import ModelConfig, create_formatter
from certicount.dsl.designer import _text, design_program, design_prompt, design_reference_params, draft_stage
from certicount.dsl.evolve import EvolveConfig, apply_patch, evolve, parse_patch
from certicount.dsl.library import analyst_prompt
from certicount.dsl.noisy_gate import NoisyGate
from certicount.dsl.prompt_spec import V0, Example, PromptSpec, leak_check, load_spec

FMT = create_formatter(ModelConfig())
RULE = "Count with this node's own neighbors P: N(self) is a randomized copy, not the neighbor set."


def _user(messages: list[dict]) -> str:
    user = next(m for m in reversed(messages) if m.get("role") == "user")["content"]
    if isinstance(user, list):
        user = "\n".join(b.get("text", "") for b in user if isinstance(b, dict))
    return user


# ---------------------------------------------------------------- specs
@pytest.mark.parametrize("matrix", [False, True])
def test_v0_reproduces_the_original_prompt(matrix):
    hist = [{"program": "return 1", "aggregate": "total", "feedback": "rejected: x"}]
    for h in ([], hist):
        assert design_prompt(analyst_prompt("3-star", 49), 49, h, matrix, V0) == \
            design_prompt(analyst_prompt("3-star", 49), 49, h, matrix)
    assert load_spec("v0") is V0 and V0.guidance() == ""


def test_guidance_is_inserted_after_the_language_reference(tmp_path):
    spec = PromptSpec("s", rules=(RULE,), examples=(Example("degree plus one", "return size(project(P, D)) + 1"),))
    p = design_prompt(analyst_prompt("3-star", 49), 49, [], False, spec)
    assert p.index("Guidance:") < p.index("The input prompt from the analyst")
    assert RULE in p and "Example (degree plus one)" in p
    spec.save(tmp_path / "s.json")
    assert load_spec(str(tmp_path / "s.json")) == spec


@pytest.mark.parametrize("program, aggregate", [
    ("d = size(project(P, D))\nreturn d * (d - 1) * (d - 2) / 6", "total"),  # 3-star, reshaped
    ("x = size(P)\nreturn x", "total / n"),  # degree, renamed
    ("Q = project(P, D)\nreturn sum(A(j, k) for j in Q for k in Q)", "total / 6"),  # triangle via A
])
def test_leak_check_refuses_examples_of_system_tasks(program, aggregate):
    spec = PromptSpec("s", examples=(Example("x", program, aggregate),))
    assert any("computes the task" in p for p in leak_check(spec))


def test_leak_check_accepts_other_statistics_and_refuses_code_in_text():
    ok = PromptSpec("s", rules=(RULE,), examples=(Example("degree plus one", "return size(project(P, D)) + 1"),),
                    repair_hints=((r"noise-free check failed", "use P for this node's neighbors"),))
    assert leak_check(ok) == []
    assert leak_check(PromptSpec("s", rules=("write return comb(size(P), 3)",)))
    assert leak_check(PromptSpec("s", repair_hints=(("(", "x"),)))
    assert leak_check(PromptSpec("s", rules=("x" * 4000,)))


# ---------------------------------------------------------------- patches
def test_patches_add_replace_delete_and_reject_malformed():
    s = apply_patch(V0, {"module": "rules", "op": "add", "value": "a"}, "c1")
    s = apply_patch(s, {"module": "rules", "op": "add", "value": "b"}, "c2")
    s = apply_patch(s, {"module": "rules", "op": "replace", "index": 0, "value": "c"}, "c3")
    assert s.rules == ("c", "b") and s.parent == "c2" and s.name == "c3"
    s = apply_patch(s, {"module": "rules", "op": "delete", "index": 1}, "c4")
    assert s.rules == ("c",)
    s = apply_patch(s, {"module": "repair_hints", "op": "add", "value": ["noisy", "use P"]}, "c5")
    assert s.repair_hints == (("noisy", "use P"),)
    for bad in ({"module": "core", "op": "add", "value": "x"}, {"module": "rules", "op": "delete", "index": 5},
                {"module": "examples", "op": "add", "value": {"title": "t"}}):
        with pytest.raises(ValueError):
            apply_patch(s, bad, "x")


def test_patch_is_read_after_the_reasoning_with_nested_values():
    reply = ('<think>maybe {"module": "rules"}</think>\nHere:\n```json\n{"module": "examples", "op": "add", '
             '"value": {"title": "t", "program": "return 1", "aggregate": "total"}, "reason": "r"}\n```')
    assert parse_patch(reply)["value"]["title"] == "t"
    assert parse_patch("<think>{\"module\": \"rules\"}</think> nothing") is None


# ---------------------------------------------------------------- hints in the design loop
class _Script(ChatModelBase):
    def __init__(self, replies: list[str]) -> None:
        super().__init__(model_name="script", stream=False)
        self.replies, self.prompts = list(replies), []

    async def __call__(self, messages: list[dict], **kwargs: Any) -> ChatResponse:  # type: ignore[override]
        self.prompts.append(_user(messages))
        return _text(self.replies.pop(0))


def test_spec_repair_hints_reach_the_next_draft():
    spec = PromptSpec("s", repair_hints=((r"noise-free check failed", "use P for this node's neighbors"),))
    bad = "```dsl\nreturn comb(size(N(self)), 2)\n```\naggregate: total"
    good = "```dsl\nreturn comb(size(project(P, D)), 2)\n```\naggregate: total"
    model = _Script([bad, good])
    res = asyncio.run(design_program(model, FMT, analyst_prompt("2-star", 100), 100, design_reference_params(100),
                                     "2-star", 2, noisy=NoisyGate(100, reps=4), spec=spec))
    assert res.accepted and draft_stage(res.history[0]["feedback"]) == "noisy"
    assert "Hint: use P for this node's neighbors" in model.prompts[1]


# ---------------------------------------------------------------- the loop
class _Learner(ChatModelBase):
    """Curator that reads the noisy row as its neighbor set unless the guidance tells it not to;
    reflector that proposes that guidance."""

    def __init__(self) -> None:
        super().__init__(model_name="learner", stream=False)
        self.reflections = 0

    async def __call__(self, messages: list[dict], **kwargs: Any) -> ChatResponse:  # type: ignore[override]
        user = _user(messages)
        if "editable instruction modules" in user:
            self.reflections += 1
            assert "stage=noisy" in user  # the failures reach the reflection
            return _text(json.dumps({"module": "rules", "op": "add", "value": RULE, "reason": "noisy row"}))
        task = re.search(r"\"input_prompt\": \"([^\"]*)", user)
        knows = RULE in user
        if "average degree" in user:
            src = "return size(P)" if knows else "return size(N(self))"
            return _text(f"```dsl\n{src}\n```\naggregate: total / n")
        arg = "size(project(P, D))" if knows else "size(N(self))"
        assert task is not None
        return _text(f"```dsl\nreturn comb({arg}, 2)\n```\naggregate: total")


def test_evolution_learns_the_rule_from_the_gate_failures_and_keeps_privacy():
    cfg = EvolveConfig(train_tasks=("degree", "2-star"), n=100, designs=2, max_iterations=1, generations=2,
                       children=1, patience=1, concurrency=4)
    model = _Learner()
    log: list[dict] = []
    best, lineage = asyncio.run(evolve(V0, model, FMT, cfg, log.append))
    first = lineage[0]["evaluation"]
    assert first["qualified_rate"] == 0 and first["stages"].get("noisy", 0) == 4
    assert best.name == "g1c1" and best.rules == (RULE,) and best.parent == "v0"
    child = next(r for r in lineage if r["kind"] == "child")
    assert child["evaluation"]["qualified_rate"] == 1.0
    assert all(r["evaluation"]["stages"].get("refuted", 0) == 0 for r in lineage if "evaluation" in r)
    assert model.reflections >= 1 and lineage == log
