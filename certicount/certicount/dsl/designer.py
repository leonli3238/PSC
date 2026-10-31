"""Curator-side program design loop: the LLM proposes, the system checks.

``design_program`` asks the curator model to translate the analyst prompt into
a DSL program using public information only (the prompt, ``n`` and the DSL
reference; no private data, so design spends no privacy budget and its result
can be cached across runs). Each draft is parsed, its GS derived with the
public parameters of a reference setting, and its utility tested on synthetic
graphs; a failing draft goes back to the model with the reason, up to
``max_iterations`` times. The node later re-derives the GS itself
(:func:`certicount.dsl.sensitivity.verify_certificate`): the curator's design
is never trusted for privacy.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

from agentscope.formatter import FormatterBase
from agentscope.message import TextBlock
from agentscope.model import ChatModelBase, ChatResponse

from psc.models import chat
from psc.prompts import extract_structured, structured_block

from .lang import DSLError, Program, parse_program
from .library import PROGRAMS, infer_program_task, kstar_source
from .sensitivity import PublicParams, SensitivityError, derive
from .utility import utility_test

DESIGNER_SYSTEM = (
    "You are the curator agent of a multi-agent system that counts substructures of a graph under "
    "edge local differential privacy. You never see the graph. You write the program that every node "
    "runs locally on its own neighbor list; the system derives the program's sensitivity and the "
    "node executes it. Answer with the program only, in the requested format."
)

DSL_REFERENCE = """The program language (a small subset of Python):
- P: the set of this node's true neighbors (private; it never contains the node itself)
- self: this node's id; n: number of nodes
- D: public degree threshold, dmax: public maximum degree of the public noisy graph (equal to D here)
- N(x): public neighbor set of node x in the public noisy graph
- size(S); project(S, k): at most k elements of S; comb(x, k); pow(x, k); clip(x, lo, hi); min(a, b); max(a, b)
- sum(<expr> for j in <set>)
- set operators & (intersection), | (union), - (difference); number operators + - * and / by public values only
- lines 'name = <expr>' followed by one final 'return <expr>'
The node reports return_value + Laplace noise scaled to the program's sensitivity, so smaller sensitivity
means more accurate results: bound degrees with project(P, D) before nonlinear functions.
The aggregation is an arithmetic expression over total (the sum of all node reports) and n."""

_FORMAT = (
    "Reply with exactly two parts:\n```dsl\n<program>\n```\naggregate: <expression over total and n>"
)


def design_reference_params(n: int) -> PublicParams:
    """Public parameters of the design-time checks: the real ``d̂max`` is not
    known yet, so a reference bound ``min(n - 1, 10)`` stands in for it."""
    d = max(2, min(n - 1, 10))
    return PublicParams(n, D=d, dmax=d)


def design_prompt(input_prompt: str, n: int, history: list[dict]) -> str:
    payload = {"phase": "design_program", "input_prompt": input_prompt, "attempt": len(history) + 1}
    parts = [DSL_REFERENCE, f"The input prompt from the analyst is:\n\"\"\"\n{input_prompt}\n\"\"\"", f"The graph has {n} nodes."]
    for h in history:
        parts.append(f"Your previous program:\n```dsl\n{h['program']}\n```\naggregate: {h['aggregate']}\nIt was rejected: {h['feedback']}")
    parts.append(_FORMAT)
    return "\n\n".join(parts) + f"\n\n{structured_block(payload)}"


def parse_design_reply(text: str) -> tuple[str, str]:
    m = re.search(r"```(?:dsl|python)?\s*\n(.*?)```", text, re.S)
    if not m:
        raise DSLError("no ```dsl code block found")
    agg = re.search(r"aggregate:\s*(.+)", text[m.end():]) or re.search(r"aggregate:\s*(.+)", text)
    return m.group(1).strip(), (agg.group(1).strip().strip("`") if agg else "total")


@dataclass
class DesignResult:
    program: Program | None
    task: str | None
    iterations: int
    accepted: bool
    gs_reference: float | None = None
    history: list[dict] = field(default_factory=list)
    llm_calls: int = 0

    def to_dict(self) -> dict:
        return {
            "accepted": self.accepted, "iterations": self.iterations, "llm_calls": self.llm_calls,
            "program": self.program.text() if self.program else None, "gs_reference": self.gs_reference,
            "history": self.history,
        }


def check_draft(program: Program, task: str | None, params: PublicParams, utility_graphs: int = 30) -> str | None:
    """Feedback for a draft, or ``None`` if it is accepted."""
    try:
        der = derive(program, params)
    except SensitivityError as exc:
        return f"sensitivity check failed: {exc}"
    loose = [w for w in der.warnings if "loose" in w]
    if loose:
        return f"sensitivity GS = {der.gs:g} is too loose: {loose[0]}"
    if task is not None:
        rep = utility_test(program, task, count=utility_graphs)
        if not rep.passed:
            return rep.feedback()
    return None


async def design_program(
    model: ChatModelBase, formatter: FormatterBase, input_prompt: str, n: int,
    params: PublicParams, task: str | None = None, max_iterations: int = 3,
) -> DesignResult:
    """``task`` names the reference counter used by the utility test (``None``
    skips it, e.g. for a task without a brute-force reference)."""
    history: list[dict] = []
    for it in range(1, max_iterations + 1):
        text = await chat(model, formatter, DESIGNER_SYSTEM, design_prompt(input_prompt, n, history), agent="Curator")
        try:
            local, agg = parse_design_reply(text)
            program = parse_program(local, agg)
        except DSLError as exc:
            history.append({"program": text[-2000:], "aggregate": "", "feedback": f"not a valid program: {exc}"})
            continue
        feedback = check_draft(program, task, params)
        if feedback is None:
            gs = derive(program, params).gs
            history.append({"program": local, "aggregate": agg, "feedback": "accepted", "gs": gs})
            return DesignResult(program, task, it, True, gs, history, it)
        history.append({"program": local, "aggregate": agg, "feedback": feedback})
    return DesignResult(None, task, max_iterations, False, None, history, max_iterations)


class MockDesignerModel(ChatModelBase):
    """Offline curator that writes the reference program of the task.

    ``flawed_first`` makes the first draft of a k-star task skip the projection,
    so that the rejection-and-rewrite path of the loop is exercised.
    """

    def __init__(self, flawed_first: bool = False) -> None:
        super().__init__(model_name="mock-designer", stream=False)
        self.flawed_first = flawed_first
        self.calls = 0

    async def __call__(self, messages: list[dict], **kwargs: Any) -> ChatResponse:  # type: ignore[override]
        self.calls += 1
        user = next(m for m in reversed(messages) if m.get("role") == "user")["content"]
        if isinstance(user, list):
            user = "\n".join(b.get("text", "") for b in user if isinstance(b, dict))
        payload = extract_structured(user) or {}
        task = infer_program_task(payload.get("input_prompt", ""))
        if task is None:
            return _text("I cannot express this task.")
        src = PROGRAMS.get(task)
        m = re.fullmatch(r"(\d+)-star", task)
        if src is None and m:
            src = kstar_source(int(m.group(1)))
        if src is None:
            return _text("I cannot express this task.")
        if self.flawed_first and payload.get("attempt") == 1 and m:
            src = kstar_source(int(m.group(1)), projected=False)
        return _text(f"```dsl\n{src.local}\n```\naggregate: {src.aggregate}\n")


def _text(text: str) -> ChatResponse:
    return ChatResponse(content=[TextBlock(type="text", text=text)])


def dump(result: DesignResult) -> str:
    return json.dumps(result.to_dict(), ensure_ascii=False, indent=2)
