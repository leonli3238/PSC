"""An offline ``ChatModelBase`` that emulates a perfect LLM agent.

The mock reads the ``<structured_input>`` block of the last user message and
executes the corresponding rule from :mod:`psc.rules` exactly.  It lets the
complete AgentScope pipeline (curator agent, privacy controller, node agents,
message passing, aggregation) run end-to-end without any API access, and it
makes the agent-based PSC/Naive results reproducible against GT-PSC/GT-Naive.

Optionally a small ``error_rate`` can be injected to emulate the arithmetic
slips of small LLMs that the paper observes for node agents.
"""

from __future__ import annotations

import json
from typing import Any

import numpy as np
from agentscope.message import TextBlock
from agentscope.model import ChatModelBase, ChatResponse

from . import rules
from .graph import infer_task_from_prompt
from .prompts import extract_structured


class MockChatModel(ChatModelBase):
    """Deterministic rule-following stand-in for an LLM."""

    def __init__(
        self,
        model_name: str = "mock-perfect-reasoner",
        error_rate: float = 0.0,
        seed: int = 0,
    ) -> None:
        super().__init__(model_name=model_name, stream=False)
        self.error_rate = error_rate
        self._rng = np.random.default_rng(seed)
        self.calls = 0

    # ChatModelBase API -------------------------------------------------------
    async def __call__(self, messages: list[dict], **kwargs: Any) -> ChatResponse:  # type: ignore[override]
        self.calls += 1
        text = _last_user_text(messages)
        payload = extract_structured(text)
        if payload is None:
            raise ValueError("MockChatModel requires a <structured_input> block in the prompt")
        answer = self._dispatch(payload, text)
        reply = f"Following the given rules.\n```json\n{json.dumps(answer)}\n```"
        return ChatResponse(content=[TextBlock(type="text", text=reply)])

    # Rule execution ------------------------------------------------------------
    def _dispatch(self, p: dict[str, Any], text: str) -> dict[str, Any]:
        phase = p.get("phase")
        if phase == "select_task":
            return {"task": infer_task_from_prompt(p["input_prompt"])}
        if phase == "node_send":
            return rules.send_message(p["node_id"], p["neighbors"])
        if phase == "node_update":
            count = rules.update(p["task"], p["neighbors"], p.get("messages"))
            return {p["state_var"]: self._maybe_perturb(count)}
        if phase == "curator_aggregate":
            return {"result": rules.aggregate(p["task"], p["counts"], p["n"])}
        if phase in ("naive_answer", "single_llm"):
            edges = [tuple(e) for e in p["edges"]]
            return {"result": rules.naive_answer(p["task"], p["n"], edges)}
        raise ValueError(f"unknown phase {phase!r} in structured input")

    def _maybe_perturb(self, value: float) -> float:
        """Emulate occasional off-by-one style mistakes of small LLMs."""
        if self.error_rate > 0 and self._rng.random() < self.error_rate:
            return max(0.0, value + float(self._rng.choice([-1, 1])))
        return value


def _last_user_text(messages: list[dict]) -> str:
    for msg in reversed(messages):
        if msg.get("role") != "user":
            continue
        content = msg.get("content")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            return "\n".join(b.get("text", "") for b in content if isinstance(b, dict))
    raise ValueError("no user message found")
