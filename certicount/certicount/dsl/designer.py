"""Curator-side program design loop: the LLM proposes, the system checks.

``design_program`` asks the curator model to translate the analyst prompt into
a DSL program using public information only (the prompt, ``n`` and the DSL
reference; no private data, so design spends no privacy budget and its result
can be cached across runs). Each draft is parsed, its GS derived with the
public parameters of a reference setting, its utility tested on public
synthetic graphs, and the derivation checked by the falsifier on small public
graphs (a refuted GS is never accepted); a failing draft goes back to the model
with the symptoms, up to ``max_iterations`` times. ``design_with_restarts``
repeats the whole loop with a fresh history (independent attempts). The node
later re-derives the GS itself
(:func:`certicount.dsl.sensitivity.verify_certificate`): the curator's design is
never trusted for privacy.

The prompt only documents the language and the mechanism; it never contains
the program of a task.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any

from agentscope.formatter import FormatterBase
from agentscope.message import TextBlock
from agentscope.model import ChatModelBase, ChatResponse

from psc.models import chat
from psc.prompts import extract_structured, structured_block

from .falsifier import check_derivation
from .lang import DSLError, Program, parse_program
from .library import PROGRAMS, infer_program_task, kstar_source
from .sensitivity import PublicParams, SensitivityError, derive
from .utility import utility_test

logger = logging.getLogger(__name__)

DESIGNER_SYSTEM = (
    "You are the curator agent of a multi-agent system that counts substructures of a graph under "
    "edge local differential privacy. You never see the graph. You write the program that every node "
    "runs locally on its own neighbor list; the system derives the program's sensitivity and the "
    "node executes it. Answer with the program only, in the requested format."
)

DSL_REFERENCE = """The program language (a small subset of Python):
- P: the set of this node's true neighbors (private and exact; it never contains the node itself)
- self: this node's id; n: number of nodes
- D: public degree threshold, dmax: public maximum degree of the public noisy graph (equal to D here)
- N(x): public neighbor set of node x in the public noisy graph. It is a randomized-response copy of the
  real graph: it misses some real edges and contains some fake ones. Reading N(...) at all costs privacy
  budget (the noisy graph must be published first).
- size(S); project(S, k): at most k elements of S; comb(x, k); pow(x, k); clip(x, lo, hi); min(a, b); max(a, b)
- sum(<expr> for j in <set>)  -- the only loop; j ranges over node ids
- set operators & (intersection), | (union), - (difference) between two sets;
  number operators + - * and / by public values only
- lines 'name = <expr>' (each name assigned once) followed by one final 'return <expr>'
Not supported (the parser rejects them): set or list literals such as {self} or [j], the 'in' / 'not in'
operators, comparisons (==, <, >), if/else, for-loops outside sum(...), conditions inside sum(...),
lambda, len (use size), math.*, keyword arguments, and any function not listed above.
How the result is computed: every node reports its return value plus Laplace noise scaled to the
program's sensitivity (the most one changed edge can change all reports together), and the aggregate
is an arithmetic expression over total (the sum of all node reports) and n. If one substructure is
counted by several nodes or several times, correct for it with constant factors.
Smaller sensitivity means less noise: bound degrees with project(P, D) before nonlinear functions.
The sensitivity checker bounds comb(size(S), k) tightly; products of expressions get looser bounds.
Reading D or dmax, or calling N, makes the system spend part of the budget on a noisy degree bound."""

_FORMAT = (
    "Reply with exactly two parts:\n```dsl\n<program>\n```\naggregate: <expression over total and n>"
)

_CODE_BLOCK = re.compile(r"```(?:dsl|python)?[ \t]*\n(.*?)```", re.S)


def design_reference_params(n: int) -> PublicParams:
    """Public parameters of the design-time checks: the real ``d̂max`` is not
    known yet, so a reference bound ``min(n - 1, 10)`` stands in for it."""
    d = max(2, min(n - 1, 10))
    return PublicParams(n, D=d, dmax=d)


def _excerpt(text: str, limit: int = 300) -> str:
    flat = " ".join(text.replace("`", "'").split())
    return flat[:limit] + ("..." if len(flat) > limit else "")


def render_attempt(i: int, h: dict) -> str:
    """One previous attempt, without nesting code fences."""
    if h.get("program"):
        head = f"Attempt {i}:\n```dsl\n{h['program'].strip()}\n```\naggregate: {h.get('aggregate') or 'total'}"
        if h.get("budget"):
            head += f"\nbudget: {h['budget']}"
    else:
        head = f"Attempt {i}: no program could be read from your reply (it began: \"{_excerpt(h.get('reply', ''))}\")"
    return f"{head}\nResult: {h['feedback']}"


def design_prompt(input_prompt: str, n: int, history: list[dict]) -> str:
    payload = {"phase": "design_program", "input_prompt": input_prompt, "attempt": len(history) + 1}
    parts = [DSL_REFERENCE, f"The input prompt from the analyst is:\n\"\"\"\n{input_prompt}\n\"\"\"", f"The graph has {n} nodes."]
    if history:
        parts.append("Your previous attempts were rejected:\n\n" + "\n\n".join(render_attempt(i, h) for i, h in enumerate(history, 1)))
        parts.append("Write a corrected program. Do not repeat a rejected program.")
    parts.append(_FORMAT)
    return "\n\n".join(parts) + f"\n\n{structured_block(payload)}"


def parse_design_reply(text: str) -> tuple[str, str, str | None]:
    """``(local program, aggregate, budget line or None)``."""
    m = _CODE_BLOCK.search(text)
    if not m:
        raise DSLError("no code block found (put the program in a dsl code block)")
    rest = text[m.end():]
    agg = re.search(r"aggregate:\s*(.+)", rest) or re.search(r"aggregate:\s*(.+)", text)
    budget = re.search(r"budget:\s*(.+)", rest)
    return (m.group(1).strip(), agg.group(1).strip().strip("`") if agg else "total",
            budget.group(1).strip().strip("`") if budget else None)


def read_draft(text: str) -> tuple[Program | None, dict]:
    """Parse a reply; returns the program (or ``None``) and its history entry."""
    try:
        local, agg, budget = parse_design_reply(text)
    except DSLError as exc:
        return None, {"program": "", "aggregate": "", "reply": text[:2000], "feedback": f"rejected: not a valid program: {exc}"}
    entry = {"program": local, "aggregate": agg, "budget": budget}
    try:
        return parse_program(local, agg, budget=budget), entry
    except DSLError as exc:
        return None, {**entry, "feedback": f"rejected: not a valid program: {exc}"}


@dataclass
class DesignResult:
    program: Program | None
    task: str | None
    iterations: int
    accepted: bool
    gs_reference: float | None = None
    history: list[dict] = field(default_factory=list)
    llm_calls: int = 0
    restarts: int = 1
    attempts: list[dict] = field(default_factory=list)  # one summary per independent loop
    mode: str = "exact"
    score: dict | None = None  # search mode: simulated accuracy of the chosen program

    def to_dict(self) -> dict:
        return {
            "accepted": self.accepted, "iterations": self.iterations, "llm_calls": self.llm_calls,
            "program": self.program.text() if self.program else None, "gs_reference": self.gs_reference,
            "history": self.history, "restarts": self.restarts, "attempts": self.attempts, "mode": self.mode,
            "score": self.score,
        }


def check_draft(program: Program, task: str | None, params: PublicParams, utility_graphs: int = 30,
                public_n: int | None = None, truncate: bool = True, falsifier: bool = True) -> str | None:
    """Feedback for a draft, or ``None`` if it is accepted."""
    try:
        der = derive(program, params)
    except SensitivityError as exc:
        return f"sensitivity check failed: {exc}"
    loose = [w for w in der.warnings if "loose" in w]
    if loose:
        return f"sensitivity GS = {der.gs:g} is too loose: {loose[0]}"
    if task is not None:
        rep = utility_test(program, task, count=utility_graphs, public_n=public_n, truncate=truncate)
        if not rep.passed:
            return rep.feedback()
    if falsifier:
        return falsifier_feedback(program)
    return None


# Falsifier runs of the design-time check: (n, dmax, random symmetric graphs; None = every graph)
FALSIFIER_CHECKS: tuple[tuple[int, int, int | None], ...] = ((5, 3, None), (7, 4, 500))
_FALSIFIER_CACHE: dict[str, str | None] = {}


def falsifier_feedback(program: Program) -> str | None:
    """Rejection reason if the falsifier refutes the derived GS on small public
    graphs, or the program fails on one of them; ``None`` otherwise (also when
    the deriver rejects the program at the small parameters: nothing to refute)."""
    if program.digest not in _FALSIFIER_CACHE:
        _FALSIFIER_CACHE[program.digest] = _falsify_draft(program)
    return _FALSIFIER_CACHE[program.digest]


def _falsify_draft(program: Program) -> str | None:
    for n, dmax, samples in FALSIFIER_CHECKS:
        chk = check_derivation(program, n, dmax, samples)
        if chk.error:
            return f"the program fails on a public test graph with {n} nodes: {chk.error}"
        if chk.refuted:
            # the deriver's bound does not hold: a bug of the checker, never accept the program
            logger.warning("falsifier refutes the derived GS %g at n=%d, dmax=%d (a flip changes the count by %g):\n%s",
                           chk.gs, n, dmax, chk.witness.max_delta, program.text())
            return (f"sensitivity certification failed: on a public test graph with {n} nodes and maximum degree "
                    f"{dmax}, adding or removing one neighbor changes the program's result by "
                    f"{chk.witness.max_delta:g}, more than the derived sensitivity {chk.gs:g}; the system cannot "
                    "certify this program, express the computation differently")
    return None


def _duplicate_of(program: Program, seen: dict[str, int]) -> int | None:
    return seen.get(program.digest)


async def design_program(
    model: ChatModelBase, formatter: FormatterBase, input_prompt: str, n: int,
    params: PublicParams, task: str | None = None, max_iterations: int = 3,
) -> DesignResult:
    """``task`` names the reference counter used by the utility test (``None``
    skips it, e.g. for a task without a brute-force reference)."""
    history: list[dict] = []
    seen: dict[str, int] = {}
    for it in range(1, max_iterations + 1):
        text = await chat(model, formatter, DESIGNER_SYSTEM, design_prompt(input_prompt, n, history), agent="Curator")
        program, entry = read_draft(text)
        if program is None:
            history.append(entry)
            continue
        dup = _duplicate_of(program, seen)
        if dup is not None:
            history.append({**entry, "feedback": f"rejected: identical to attempt {dup}, which was already rejected"})
            continue
        seen[program.digest] = it
        feedback = check_draft(program, task, params, public_n=n)
        if feedback is None:
            gs = derive(program, params).gs
            history.append({**entry, "feedback": "accepted", "gs": gs})
            return DesignResult(program, task, it, True, gs, history, it)
        history.append({**entry, "feedback": f"rejected: {feedback}"})
    return DesignResult(None, task, max_iterations, False, None, history, max_iterations)


async def design_with_restarts(
    model: ChatModelBase, formatter: FormatterBase, input_prompt: str, n: int,
    params: PublicParams, task: str | None = None, max_iterations: int = 3, restarts: int = 1,
) -> DesignResult:
    """Up to ``restarts`` independent design loops (fresh history each); the
    first accepted program is used. All loops are recorded in ``attempts``."""
    attempts: list[dict] = []
    calls = 0
    last: DesignResult | None = None
    for r in range(1, max(1, restarts) + 1):
        res = await design_program(model, formatter, input_prompt, n, params, task, max_iterations)
        calls += res.llm_calls
        attempts.append({"restart": r, "accepted": res.accepted, "iterations": res.iterations,
                         "program": res.program.text() if res.program else None, "history": res.history})
        last = res
        if res.accepted:
            break
    assert last is not None
    return DesignResult(last.program, task, last.iterations, last.accepted, last.gs_reference, last.history,
                        calls, restarts=len(attempts), attempts=attempts)


class MockDesignerModel(ChatModelBase):
    """Offline curator that writes the reference program of the task.

    ``flawed_first`` makes the first draft of a k-star task skip the projection,
    so that the rejection-and-rewrite path of the loop is exercised. In the
    accuracy search (:mod:`certicount.dsl.search`) it proposes the reference
    program with a lower threshold / budget share in later proposals, so the
    search path can be tested offline.
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
        if payload.get("phase") == "search_program":
            return _text(_mock_search_reply(task, src, int(payload.get("proposal", 1))))
        if self.flawed_first and payload.get("attempt") == 1 and m:
            src = kstar_source(int(m.group(1)), projected=False)
        return _text(f"```dsl\n{src.local}\n```\naggregate: {src.aggregate}\n")


def _mock_search_reply(task: str, src, proposal: int) -> str:
    local, budget = src.local, None
    factors = (1.0, 0.8, 0.65, 0.5)
    shares = (0.5, 0.4, 0.3, 0.2)
    i = (proposal - 1) % len(factors)
    if "project(P, D)" in local and i:
        local = local.replace("project(P, D)", f"project(P, D * {factors[i]:g})")
    elif "N(" in local and i:
        budget = f"r1={shares[i]:g}, r2=0.2"
    out = f"```dsl\n{local}\n```\naggregate: {src.aggregate}\n"
    return out + (f"budget: {budget}\n" if budget else "")


def _text(text: str) -> ChatResponse:
    return ChatResponse(content=[TextBlock(type="text", text=text)])


def dump(result: DesignResult) -> str:
    return json.dumps(result.to_dict(), ensure_ascii=False, indent=2)
