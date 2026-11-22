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

import asyncio
import json
import logging
import re
from dataclasses import asdict, dataclass, field, replace
from typing import Any

from agentscope.formatter import FormatterBase
from agentscope.message import TextBlock
from agentscope.model import ChatModelBase, ChatResponse

from psc.models import chat
from psc.prompts import extract_structured, structured_block

from .falsifier import check_derivation
from .ground_truth import estimate_gs
from .lang import BinOp, Call, DSLError, Name, Neg, Program, Sum, parse_program
from .library import NODE_PROGRAMS, PROGRAMS, ProgramSource, infer_program_task, kstar_source
from .matrix import REFERENCE_EPS1
from .noisy_gate import NoisyGate, noise_free_check
from .prompt_spec import V0, PromptSpec
from .selection import Selection, SimOptions, select_program
from .sensitivity import PublicParams, SensitivityError, derive
from .utility import named_graphs, random_graphs, run_exact, utility_test

logger = logging.getLogger(__name__)

DESIGNER_SYSTEM = (
    "You are the curator agent of a multi-agent system that counts substructures of a graph under "
    "edge local differential privacy. You never see the graph. You write the program that every node "
    "runs locally on its own neighbor list; the system derives the program's sensitivity and the "
    "node executes it. Answer with the program only, in the requested format."
)

DSL_REFERENCE_LEGACY = """The program language (a small subset of Python):
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

# Core "v1": the language facts of the legacy core, without angle-bracket placeholders (drafts of
# CS4/CS5 copied '<program>' from the format) and with the constructs the parse failures of CS4/CS5
# asked for spelled out (one 'for' clause, nested sums, no '//', a set is not a number, no name 'u').
# Facts only; no program of a task.
DSL_REFERENCE = """The program language (a small subset of Python):
- P: the set of this node's true neighbors (private and exact; it never contains the node itself)
- self: this node's id (the only name for this node); n: number of nodes
- D: public degree threshold, dmax: public maximum degree of the public noisy graph (equal to D here)
- N(x): public neighbor set of node x in the public noisy graph. It is a randomized-response copy of the
  real graph: it misses some real edges and contains some fake ones. Reading N(...) at all costs privacy
  budget (the noisy graph must be published first). No node is in its own row: x is never in N(x).
- size(S); project(S, k): at most k elements of S; comb(x, k); pow(x, k); clip(x, lo, hi); min(a, b); max(a, b)
- sum(EXPR for j in SET) is the only loop: exactly one 'for' clause, j ranges over the node ids in SET.
  Pairs are nested sums: sum(sum(EXPR for k in SET2) for j in SET1).
- set operators & (intersection), | (union), - (difference) between two sets. A set is not a number:
  take size(S) before arithmetic, comb or pow.
- number operators + - * and / by public values only (no //, % or **)
- straight-line code: lines NAME = EXPR (each name assigned once), then one final line return EXPR
Not supported (the parser rejects them): set or list literals such as {self} or [j], the 'in' / 'not in'
operators, comparisons (==, <, >), if/else, for-loops outside sum(...), conditions inside sum(...),
lambda, len (use size), math.*, keyword arguments, and any function not listed above.
How the result is computed: every node reports its return value plus Laplace noise scaled to the
program's sensitivity (the most one changed edge can change all reports together), and the aggregate
is an arithmetic expression over total (the sum of all node reports) and n. If one substructure is
counted by several nodes or several times, correct for it with constant factors.
Smaller sensitivity means less noise: bound degrees with project(P, D) before nonlinear functions.
Reading D or dmax, or calling N, makes the system spend part of the budget on a noisy degree bound."""

# Added to DSL_REFERENCE in the per-node architecture (TrustOptions.node_bounds) only, so the
# prompt of the PSC architecture is unchanged.
MATRIX_REFERENCE = """Per-node architecture (this run):
- D is this node's own public degree bound (each node has its own); project(P, D) keeps at most D neighbors.
- A(x, y): public unbiased estimate of the edge between nodes x and y, computed from randomized-response
  bits of the projected neighbor lists: E[A(x, y)] = 1 if the edge is kept, 0 otherwise; A(x, x) = 0.
  Each value is noisy (between -1/(e^eps1 - 1) and e^eps1/(e^eps1 - 1)) but sums of A are unbiased counts.
  A program reads either N(...) or A(...), not both; reading A costs the same budget as N."""

# Release of one design round of design_candidates (per-node architecture): the curator writes one
# program per release and the system keeps the more accurate one (certicount.dsl.selection).
RELEASE_NOTES = {
    "rows": ("This design round: do not use A(...). If the statistic needs edges between other nodes, read the "
             "noisy rows N(...); if it does not, use P only."),
    "matrix": ("This design round: do not use N(...). If the statistic needs edges between other nodes, read the "
               "unbiased matrix A(...); if it does not, use P only."),
}
RELEASES = tuple(RELEASE_NOTES)

_FORMAT_LEGACY = (
    "Reply with exactly two parts:\n```dsl\n<program>\n```\naggregate: <expression over total and n>"
)
_FORMAT = (
    "Reply with exactly two parts after your reasoning:\n"
    "1. one code block that opens with the line ```dsl and closes with the line ```, holding only the "
    "program lines (no tags, no aggregate line inside the block);\n"
    "2. after the block, one line that starts with 'aggregate:' followed by an arithmetic expression over "
    "total and n."
)

# The prohibition paragraph of DSL_REFERENCE, verbatim (core "v1-repeat3" states it three times).
NOT_SUPPORTED = """Not supported (the parser rejects them): set or list literals such as {self} or [j], the 'in' / 'not in'
operators, comparisons (==, <, >), if/else, for-loops outside sum(...), conditions inside sum(...),
lambda, len (use size), math.*, keyword arguments, and any function not listed above."""

# Core "v1-alt": positive rewrites of the Python constructs the CS2-CS5 parse failures used, over a
# generic set S (language facts: no task statistic, no aggregate, no program of a task).
ALTERNATIVES = """How to write common Python constructs in this language (S is any set expression, x any number):
- unordered pairs of distinct elements of S, instead of sum(1 for v in S for w in S if v < w):
  0.5 * sum(size(S) - 1 for v in S)
- unordered pairs of elements of S that are neighbors in the noisy graph, instead of a condition
  'if v < w and w in N(v)': 0.5 * sum(size(S & N(v)) for v in S)
- unordered pairs of elements of S that are not neighbors in the noisy graph, instead of 'w not in N(v)':
  0.5 * sum(size(S - N(v)) - 1 for v in S)   (v itself is in S - N(v), hence the - 1)
- in general, never test membership or order: count the matching elements with size(...) of a set
  expression and correct repeated counting with a constant factor (0.5 for pairs counted in both orders)
- x ** 2 is pow(x, 2); comb(x, k) and pow(x, k) need k written as a number
- a running total in a for loop is sum(EXPR for v in S); a name is assigned once (use a new name per step)
- this node is self; other nodes exist only as loop variables of sum(...)"""

CHECKLIST = """Before you answer, check the program line by line:
1. no if, in, not in, <, >, == and no {...} or [...] anywhere;
2. no **, // or %;
3. every argument of comb, pow, + - * / is a number: size(S), never a set S;
4. the only node names are self and the loop variables of sum(...);
5. every name is assigned once and the last line is the return line."""

# Core "generic": rewrites of single Python constructs, each over placeholders (S, T sets; x, a, b
# numbers; EXPR a number expression; k a constant). Unlike ALTERNATIVES (whose pair rewrites over
# S & N(v) / S - N(v) are the rows triangle and open-wedge programs once S = project(P, D)), no line
# fills in a statistic: prompt_spec.core_leak_check substitutes the placeholders by P / project(P, D)
# and their sizes and checks that no instance computes a guarded task beyond the ones the language
# reference gives by itself (degree, k-stars, degree moments). The prompt text is rendered from these
# tuples, so the checked fragments are exactly the shown ones.
GENERIC_REWRITES: tuple[tuple[str, str, str], ...] = (  # (Python, DSL, note)
    ("len(S)", "size(S)", ""),
    ("sum(1 for v in S if v in T)", "size(S & T)", ""),
    ("sum(1 for v in S if v not in T)", "size(S - T)", ""),
    ("1 if x >= 1 else 0", "clip(x, 0, 1)", "x a whole number, x >= 0"),
    ("a if a < b else b", "min(a, b)", ""),
    ("a if a > b else b", "max(a, b)", ""),
    ("x ** k", "pow(x, k)", ""),
    ("math.comb(x, k)", "comb(x, k)", ""),
    ("total = 0, then total += EXPR in a for loop over v in S", "sum(EXPR for v in S)", ""),
)
GENERIC_RULES: tuple[str, ...] = (
    "never test membership, order or a condition: count the matching elements with size(...) of a set "
    "expression, and turn a condition on a number into clip, min or max",
    "correct repeated counting with a constant factor: a sum over both orders of a pair counts each unordered "
    "pair twice, and a structure that each of its k nodes counts is counted k times",
    "k in comb(x, k) and pow(x, k) is written as a number; a name is assigned once (use a new name per step)",
    "this node is self; other nodes exist only as loop variables of sum(...)",
)


def _generic_text() -> str:
    lines = ["How to write common Python constructs in this language (Python on the left, this language on the "
             "right; S and T are any set expressions, x, a and b any numbers, EXPR any number expression, k a whole "
             "number):"]
    lines += [f"- {py}  ->  {dsl}" + (f"   ({note})" if note else "") for py, dsl, note in GENERIC_REWRITES]
    lines += [f"- {r}" for r in GENERIC_RULES]
    return "\n".join(lines)


GENERIC = _generic_text()

# DSL fragments of each core that prompt_spec.core_leak_check instantiates (rewrites and hints)
V1ALT_TEMPLATES: tuple[str, ...] = (
    "0.5 * sum(size(S) - 1 for v in S)", "0.5 * sum(size(S & N(v)) for v in S)",
    "0.5 * sum(size(S - N(v)) - 1 for v in S)", "pow(x, 2)", "sum(EXPR for v in S)",
)
GENERIC_TEMPLATES: tuple[str, ...] = tuple(dsl for _, dsl, _ in GENERIC_REWRITES)

CORES = ("v1", "legacy", "v1-repeat3", "v1-alt", "generic")


def _check_core(core: str) -> None:
    if core not in CORES:
        raise ValueError(f"unknown prompt core {core!r}; known: {', '.join(CORES)}")


def core_templates(core: str) -> tuple[str, ...]:
    """DSL fragments a core shows the curator, with placeholders (``()``: none beyond the language)."""
    _check_core(core)
    return {"v1-alt": V1ALT_TEMPLATES, "generic": GENERIC_TEMPLATES}.get(core, ())


def dsl_reference(core: str = "v1", matrix: bool = False) -> str:
    """Language reference of a prompt core: ``legacy`` (the CS2-CS5 text), ``v1``, ``v1-repeat3``
    (v1 with :data:`NOT_SUPPORTED` also stated first; :func:`prompt_tail` states it a third time),
    ``v1-alt`` (v1 plus :data:`ALTERNATIVES`) or ``generic`` (v1 plus :data:`GENERIC`)."""
    _check_core(core)
    if core == "legacy":
        base = DSL_REFERENCE_LEGACY
    elif core == "v1-repeat3":
        base = NOT_SUPPORTED + "\n\n" + DSL_REFERENCE
    elif core == "v1-alt":
        base = DSL_REFERENCE + "\n" + ALTERNATIVES
    elif core == "generic":
        base = DSL_REFERENCE + "\n" + GENERIC
    else:
        base = DSL_REFERENCE
    return base + ("\n" + MATRIX_REFERENCE if matrix else "")


def prompt_tail(core: str = "v1") -> str:
    """Text placed right before the reply format ("" for ``v1`` / ``legacy``)."""
    _check_core(core)
    return {"v1-repeat3": NOT_SUPPORTED, "v1-alt": CHECKLIST, "generic": CHECKLIST}.get(core, "")


def reply_format(core: str = "v1") -> str:
    _check_core(core)
    return _FORMAT_LEGACY if core == "legacy" else _FORMAT

_CODE_BLOCK = re.compile(r"```(?:dsl|python)?[ \t]*\n(.*?)```", re.S)


def design_reference_params(n: int) -> PublicParams:
    """Public parameters of the design-time checks: the real ``d̂max`` is not
    known yet, so a reference bound ``min(n - 1, 10)`` stands in for it."""
    d = max(2, min(n - 1, 10))
    return PublicParams(n, D=d, dmax=d, eps1=REFERENCE_EPS1)


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
    if h.get("normalized"):
        head += "\nNote: the system rewrote your reply before checking it: " + "; ".join(h["normalized"])
    if h.get("tighten_request") and h.get("feedback") == "accepted":
        return f"{head}\nResult: accepted, but {h['tighten_request']}"
    return f"{head}\nResult: {h['feedback']}"


def design_prompt(input_prompt: str, n: int, history: list[dict], matrix: bool = False,
                  spec: PromptSpec | None = None, release: str | None = None) -> str:
    """``spec``: evolvable modules and prompt core (:mod:`certicount.dsl.prompt_spec`); a spec with
    ``core="legacy"`` and empty modules gives the CS2-CS5 prompt byte for byte. ``release``: the
    release of this design round (:data:`RELEASE_NOTES`; per-node architecture)."""
    payload = {"phase": "design_program", "input_prompt": input_prompt, "attempt": len(history) + 1}
    if release is not None:
        payload["release"] = release
    core = spec.core if spec is not None else V0.core
    reference = dsl_reference(core, matrix)
    guidance = spec.guidance() if spec is not None else ""
    parts = [reference] + ([RELEASE_NOTES[release]] if release is not None else []) + ([guidance] if guidance else [])
    parts += [f"The input prompt from the analyst is:\n\"\"\"\n{input_prompt}\n\"\"\"", f"The graph has {n} nodes."]
    if history:
        attempts = "\n\n".join(render_attempt(i, h) for i, h in enumerate(history, 1))
        if any(h.get("tighten_request") for h in history):
            parts.append("Your previous attempts:\n\n" + attempts)
            parts.append("Write an equivalent program (the same statistic) whose sensitivity the checker bounds more "
                         "tightly. If you see none, repeat the accepted program unchanged.")
        else:
            parts.append("Your previous attempts were rejected:\n\n" + attempts)
            parts.append("Write a corrected program. Do not repeat a rejected program.")
    tail = prompt_tail(core)
    if tail:
        parts.append(tail)
    parts.append(reply_format(core))
    return "\n\n".join(parts) + f"\n\n{structured_block(payload)}"


TRUNCATED_FEEDBACK = ("rejected: the reply was cut off during the reasoning, before any program; "
                      "reason more briefly and give the program")


def is_truncated(text: str) -> bool:
    """A reasoning reply that never closed its ``<think>`` block (output token limit)."""
    return "<think>" in text and "</think>" not in text


def answer_part(text: str) -> str:
    """The reply after the reasoning block (the whole reply without one)."""
    return text.rsplit("</think>", 1)[1] if "</think>" in text else text


def parse_design_reply(text: str) -> tuple[str, str, str | None]:
    """``(local program, aggregate, budget line or None)``, read after the reasoning
    block: a program drafted inside the reasoning is not the answer."""
    text = answer_part(text)
    m = _CODE_BLOCK.search(text)
    if not m:
        raise DSLError("no code block found (put the program in a dsl code block)")
    rest = text[m.end():]
    agg = re.search(r"aggregate:\s*(.+)", rest) or re.search(r"aggregate:\s*(.+)", text)
    budget = re.search(r"budget:\s*(.+)", rest)
    return (m.group(1).strip(), agg.group(1).strip().strip("`") if agg else "total",
            budget.group(1).strip().strip("`") if budget else None)


# (pattern of the parser's message, hint); the first match is used. Hints say how to write a
# construct in the language; they never contain the program of a task.
_REPAIR_HINTS: tuple[tuple[str, str], ...] = (
    (r"no code block found",
     "put the program in a code block marked dsl, followed by a line 'aggregate: <expression over total and n>'"),
    (r"without conditions",
     "remove the 'if' condition: sum over all elements and correct repeated counting with a constant factor"),
    (r"comb expects \(num, num\), got \(set",
     "comb takes a number: write comb(size(S), k)"),
    (r"project expects \(set, num\), got \(num",
     "project takes a set: write project(S, k) and take size(...) afterwards"),
    (r"size expects \(set\)",
     "size takes a set (P, N(x), project(...) or a set expression)"),
    (r"expects .*got",
     "check the argument types: N(node), A(node, node), size(set), project(set, number), comb(number, k)"),
    (r"A takes \d+ argument",
     "A(x, y) takes two nodes: the noisy indicator of the edge between x and y"),
    (r"reads either the noisy rows N\(\.\.\.\) or the unbiased matrix A",
     "N(...) and A(...) are two different releases and a program uses one of them; this node's own "
     "neighbors are P (bounded: project(P, D)), N(self) is only a randomized copy of them"),
    (r"is already defined",
     "assign each name once: use a new name for every step"),
    (r"only 'name = <expr>' lines",
     "write straight-line code: no for / if statements, loops only as sum(<expr> for j in <set>), "
     "and end with 'return <expr>'"),
    (r"must end with 'return",
     "end the program with 'return <expr>'"),
    (r"unknown function",
     "only N, A, size, project, comb, pow, clip, min, max and sum are available"),
)


# Core "v1-alt" only: hints that give the rewrite (over a generic set S) instead of the prohibition.
_ALT_HINTS: tuple[tuple[str, str], ...] = (
    (r"without conditions",
     "drop the condition and count with size(...) of a set expression: unordered pairs of elements of S that are "
     "neighbors in the noisy graph are 0.5 * sum(size(S & N(v)) for v in S), unordered pairs of distinct elements "
     "of S are 0.5 * sum(size(S) - 1 for v in S)"),
    (r"only 'name = <expr>' lines",
     "write a running total as sum(EXPR for v in S), assign every name once and end with the return line; "
     "there are no for / if statements"),
)

# Core "generic" only: the same rewrites over the placeholders of GENERIC (no pair formula).
_GENERIC_HINTS: tuple[tuple[str, str], ...] = (
    (r"without conditions",
     "drop the condition: count the elements of S that are in T with size(S & T) (not in T: size(S - T)) and "
     "write a condition on a number with clip, min or max"),
    (r"only 'name = <expr>' lines",
     "write a running total as sum(EXPR for v in S), assign every name once and end with the return line; "
     "there are no for / if statements"),
)


def repair_hint(message: str, source: str = "", core: str = "v1") -> str | None:
    """How to express what the parser rejected (``None``: no specific hint). ``core="v1-alt"``
    uses the rewrite hints :data:`_ALT_HINTS` first, ``core="generic"`` :data:`_GENERIC_HINTS`."""
    if core in ("v1-alt", "generic"):
        if "**" in source and re.search(r"unsupported syntax BinOp|syntax", message):
            return ("write pow(x, 2) instead of x ** 2 (pow takes a constant exponent)" if core == "v1-alt" else
                    "write pow(x, k) instead of x ** k (k written as a number)")
        for pattern, hint in (_ALT_HINTS if core == "v1-alt" else _GENERIC_HINTS):
            if re.search(pattern, message):
                return hint
    if re.search(r"<[a-z][a-z _-]*>", source):
        return ("replace the placeholder in angle brackets with your actual program; "
                "do not copy '<...>' from the format description")
    if "//" in source and re.search(r"unsupported syntax BinOp|syntax", message):
        return "use '/' instead of '//' (results are real numbers)"
    if re.search(r"unsupported syntax (Set|List|Tuple|Dict|Subscript)", message):
        return "there are no literals, tuples or indexing: build sets from P, N(x), project, &, |, -"
    m = re.search(r"unknown name '([^']+)'", message)
    if m:
        return (f"'{m.group(1)}' is not defined: this node is 'self', its neighbors are P, other nodes are the "
                "loop variables of sum(...); public numbers are n, D, dmax")
    for pattern, hint in _REPAIR_HINTS:
        if re.search(pattern, message):
            return hint
    return None


def _rejected(exc: Exception, source: str, core: str = "v1") -> str:
    hint = repair_hint(str(exc), source, core)
    return f"rejected: not a valid program: {exc}" + (f". Hint: {hint}" if hint else "")


_TAG_LINE = re.compile(r"^\s*</?\s*[A-Za-z][A-Za-z _-]*>\s*$")
_FLOOR_DIV = re.compile(r"//")


def normalize_source(local: str) -> tuple[str, str | None, list[str]]:
    """Format-only repairs of a drafted program: ``(program, aggregate found inside the block or
    None, notes)``. Lines that are a single tag (``<program>``, ``</program>``) are dropped, an
    ``aggregate:`` / ``budget:`` line written inside the code block is taken out of it, and ``//``
    becomes ``/`` (the language has real division only). The rewritten program is the one that is
    checked, certified and executed, so the repair does not touch privacy; the utility test still
    decides whether it computes the requested statistic."""
    notes: list[str] = []
    lines = local.splitlines()
    kept = [ln for ln in lines if not _TAG_LINE.match(ln)]
    if len(kept) != len(lines):
        notes.append("removed the tag line(s) " + ", ".join(sorted({ln.strip() for ln in lines if _TAG_LINE.match(ln)})))
    agg = None
    body = []
    for ln in kept:
        m = re.match(r"\s*(aggregate|budget):\s*(.*)$", ln)
        if m:
            if m.group(1) == "aggregate":
                agg = m.group(2).strip().strip("`")
            notes.append(f"moved the line '{ln.strip()}' out of the code block")
            continue
        body.append(ln)
    out = "\n".join(body).strip()
    if _FLOOR_DIV.search(out):
        out = _FLOOR_DIV.sub("/", out)
        notes.append("replaced '//' by '/'")
    return out, agg, notes


def read_draft(text: str, normalize: bool = False, core: str = "v1") -> tuple[Program | None, dict]:
    """Parse a reply; returns the program (or ``None``) and its history entry.
    ``normalize``: apply :func:`normalize_source` first (recorded in ``entry["normalized"]``).
    ``core``: prompt core of the run (selects the repair hints, :func:`repair_hint`)."""
    if is_truncated(text):
        return None, {"program": "", "aggregate": "", "reply": text[-2000:], "truncated": True,
                      "feedback": TRUNCATED_FEEDBACK}
    try:
        local, agg, budget = parse_design_reply(text)
    except DSLError as exc:
        return None, {"program": "", "aggregate": "", "reply": answer_part(text)[:2000],
                      "feedback": _rejected(exc, answer_part(text), core)}
    notes: list[str] = []
    if normalize:
        local, inner_agg, notes = normalize_source(local)
        m = _CODE_BLOCK.search(answer_part(text))
        after = answer_part(text)[m.end():] if m else ""
        if inner_agg and not re.search(r"aggregate:", after):
            agg = inner_agg
    entry = {"program": local, "aggregate": agg, "budget": budget}
    if notes:
        entry["normalized"] = notes
    try:
        return parse_program(local, agg, budget=budget), entry
    except DSLError as exc:
        return None, {**entry, "feedback": _rejected(exc, local, core)}


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
    selection: dict | None = None  # design_with_restarts(select="min_gs"): the candidates and the choice

    def to_dict(self) -> dict:
        return {
            "accepted": self.accepted, "iterations": self.iterations, "llm_calls": self.llm_calls,
            "program": self.program.text() if self.program else None, "gs_reference": self.gs_reference,
            "history": self.history, "restarts": self.restarts, "attempts": self.attempts, "mode": self.mode,
            "score": self.score, "selection": self.selection,
        }


def check_draft(program: Program, task: str | None, params: PublicParams, utility_graphs: int = 30,
                public_n: int | None = None, truncate: bool = True, falsifier: bool = True,
                noisy: NoisyGate | None = None) -> str | None:
    """Feedback for a draft, or ``None`` if it is accepted. ``noisy``: also run the
    noise-free check through the real release (:mod:`certicount.dsl.noisy_gate`)."""
    try:
        der = derive(program, params)
    except SensitivityError as exc:
        return f"sensitivity check failed: {exc}"
    except RecursionError:  # a draft the deriver cannot analyse is rejected, not a crash of the run
        return "sensitivity check failed: the program is too deeply nested to analyse; write it with fewer nested sums"
    loose = [w for w in der.warnings if "loose" in w]
    if loose:
        return f"sensitivity GS = {der.gs:g} is too loose: {loose[0]}"
    grows = growth_feedback(program, params, der.gs)
    if grows:
        return grows
    if task is not None:
        rep = utility_test(program, task, count=utility_graphs, public_n=public_n, truncate=truncate)
        if not rep.passed:
            return rep.feedback()
        if noisy is not None:
            nrep = noise_free_check(program, task, noisy)
            if not nrep.passed:
                return nrep.feedback()
    if falsifier:
        return falsifier_feedback(program)
    return None


def _own_row_calls(e) -> list[str]:
    """``N(self)`` / ``A(self, .)`` / ``A(., self)`` calls in an expression."""
    out: list[str] = []
    if isinstance(e, Call):
        if e.func in ("N", "A") and any(isinstance(a, Name) and a.id == "self" for a in e.args):
            out.append(f"{e.func}(...self...)")
        for a in e.args:
            out += _own_row_calls(a)
    elif isinstance(e, BinOp):
        out += _own_row_calls(e.left) + _own_row_calls(e.right)
    elif isinstance(e, Neg):
        out += _own_row_calls(e.operand)
    elif isinstance(e, Sum):
        out += _own_row_calls(e.body) + _own_row_calls(e.domain)
    return out


def reads_own_row(program: Program) -> bool:
    return any(_own_row_calls(e) for _, e in program.assigns) or bool(_own_row_calls(program.ret))


OWN_ROW_FEEDBACK = (
    "the program reads this node's own entries of the release (N(self), A(self, ...) or A(..., self)). In this "
    "architecture they are only randomized copies of this node's own edges, which it knows exactly as P: they add "
    "noise and no information. Use P (bounded: project(P, D)) for this node's own neighbors and read the release "
    "only for edges between other nodes")


def release_feedback(program: Program, release: str | None) -> str | None:
    """Rejection if the draft reads the release the design round excludes (:data:`RELEASE_NOTES`)."""
    if release == "rows" and program.uses_matrix:
        return "this design round must not read A(...): read the noisy rows N(...) or P only"
    if release == "matrix" and program.uses_rows:
        return "this design round must not read N(...): read the unbiased matrix A(...) or P only"
    return None


def growth_feedback(program: Program, params: PublicParams, gs: float | None = None) -> str | None:
    """Rejection if the derived GS grows with the number of nodes at fixed public degree bounds:
    some set reaching the count is bounded only by ``n - 1`` (e.g. ``P`` without ``project``), so the
    noise grows with the graph although a degree bound is available. Generalises the ``comb`` loose
    warning of the deriver to every expression (products, sums over pairs, ...)."""
    try:
        g1 = derive(program, params).gs if gs is None else gs
        g2 = derive(program, PublicParams(4 * params.n, params.D, params.dmax, params.eps1)).gs
    except SensitivityError:
        return None
    if g2 > g1 * 1.01 + 1e-9:
        return (f"sensitivity GS = {g1:g} is too loose: it grows with the number of nodes (GS = {g2:g} on a graph "
                f"with {4 * params.n} nodes and the same degree bound), so a set in the program is bounded only by n; "
                "bound the neighbor sets with project(..., D) before counting")
    return None


def draft_stage(feedback: str | None) -> str:
    """Stage of the design loop a draft stopped at, from its feedback."""
    if feedback is None or feedback == "accepted":
        return "accepted"
    f = feedback.removeprefix("rejected: ")
    for prefix, stage in (("the reply was cut off", "truncated"), ("not a valid program", "parse"),
                          ("identical to attempt", "duplicate"), ("sensitivity check failed", "gs_failed"),
                          ("sensitivity GS", "gs_loose"), ("utility test failed", "semantic"),
                          ("noise-free check failed", "noisy"), ("sensitivity certification failed", "refuted"),
                          ("this design round must not", "release"),
                          ("the program reads this node's own entries", "own_row"),
                          ("the program fails on a public test graph", "refuted"), ("superseded", "superseded"),
                          ("not tighter", "not_tighter")):
        if f.startswith(prefix):
            return stage
    return "other"


# Falsifier runs of the design-time check: (n, dmax, random symmetric graphs; None = every graph)
FALSIFIER_CHECKS: tuple[tuple[int, int, int | None], ...] = ((5, 3, None), (7, 4, 500))
_FALSIFIER_CACHE: dict[str, str | None] = {}
_FALSIFIER_RUNS: dict[str, list] = {}  # digest -> the DerivationChecks behind the cached feedback


def falsifier_feedback(program: Program) -> str | None:
    """Rejection reason if the falsifier refutes the derived GS on small public
    graphs, or the program fails on one of them; ``None`` otherwise (also when
    the deriver rejects the program at the small parameters: nothing to refute)."""
    if program.digest not in _FALSIFIER_CACHE:
        _FALSIFIER_CACHE[program.digest] = _falsify_draft(program)
    return _FALSIFIER_CACHE[program.digest]


def _falsify_draft(program: Program) -> str | None:
    runs = _FALSIFIER_RUNS[program.digest] = []
    for n, dmax, samples in FALSIFIER_CHECKS:
        chk = check_derivation(program, n, dmax, samples)
        runs.append(chk)
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


@dataclass(frozen=True)
class BoundSlack:
    """Derived GS against the largest change the falsifier found, on its small public graphs."""

    ratio: float  # max over the falsifier runs of derived GS / largest observed change
    n: int
    dmax: int
    gs: float
    observed: float


def bound_slack(program: Program) -> BoundSlack | None:
    """How loose the derived bound of ``program`` is on the falsifier's graphs (public; ``None``
    if nothing could be compared). The derived GS is an upper bound of the true sensitivity and
    the observed change a lower bound, so ``ratio`` bounds the slack the deriver adds; a ratio
    near 1 means the noise is already scaled to what the program needs."""
    if program.digest not in _FALSIFIER_RUNS or program.digest not in _FALSIFIER_CACHE:
        _FALSIFIER_CACHE[program.digest] = _falsify_draft(program)
    best = None
    for chk in _FALSIFIER_RUNS[program.digest]:
        if chk.gs is None or chk.witness is None or chk.witness.max_delta <= 0:
            continue
        r = chk.gs / chk.witness.max_delta
        if best is None or r > best.ratio:
            best = BoundSlack(r, chk.n, chk.dmax, chk.gs, chk.witness.max_delta)
    return best


def tighten_request(slack: BoundSlack) -> str:
    """Feedback for an accepted program whose bound is loose (no program, no task knowledge)."""
    return (f"the system's sensitivity bound for this program is loose: on a public test graph with {slack.n} nodes "
            f"and maximum degree {slack.dmax} it derives GS = {slack.gs:g}, but one changed neighbor never changes the "
            f"result by more than {slack.observed:g}. The noise is scaled to the derived bound. The checker bounds "
            "exactly any expression that reads the private data through a single size(...); it bounds products of "
            "different counts, and sets that are counted before being intersected, more loosely. A difference of two "
            "counts over the same sets is bounded by the sum of both bounds, although one changed neighbor moves "
            "both: count the difference inside one sum instead")


def static_feedback(program: Program, opts: "DesignOptions") -> str | None:
    """Checks of the draft's text before any derivation: the release of the round, own rows."""
    fb = release_feedback(program, opts.release)
    if fb is None and opts.own_row and reads_own_row(program):
        fb = OWN_ROW_FEEDBACK
    return fb


def _duplicate_of(program: Program, seen: dict[str, int]) -> int | None:
    return seen.get(program.digest)


@dataclass(frozen=True)
class DesignOptions:
    """Behaviour of the design loop beyond the prompt.

    ``normalize``: format-only repairs of a reply (:func:`normalize_source`).
    ``tighten``: extra calls after an acceptance whose bound is loose on the falsifier's graphs
    (:func:`bound_slack` above ``slack_tol``); a rewrite replaces the accepted program only if it
    passes every check and its derived GS is smaller.
    ``early_stop``: stages (:func:`draft_stage`) after which two rejections in a row end the loop
    (e.g. ``("noisy", "gs_loose")``: the feedback did not help, more calls rarely do).
    ``select`` / ``min_accepted`` (:func:`design_with_restarts`): ``"first"`` keeps the first accepted
    program; ``"min_gs"`` runs restarts until ``min_accepted`` behaviourally different programs
    are accepted (or the restarts run out) and keeps the one with the smallest derived GS, then the
    smallest noise-free error on the public graphs. Everything compared is public.
    GS comparisons (``tighten``, ``min_gs``) use the GS in units of the estimate, ``|c| · GS``
    (:func:`certicount.dsl.ground_truth.estimate_gs`): moving a constant factor between the
    local program and the aggregate is not a tighter program.
    ``release`` (per-node architecture, :func:`design_candidates`): ``"rows"`` rejects drafts that
    read ``A``, ``"matrix"`` drafts that read ``N``; ``None``: no restriction.
    ``own_row``: reject drafts that read this node's own entries of the release (``N(self)``,
    ``A(self, .)``, :data:`OWN_ROW_FEEDBACK`); for the per-node architecture only."""

    normalize: bool = True
    tighten: int = 0
    slack_tol: float = 1.2
    early_stop: tuple[str, ...] = ()
    select: str = "first"
    min_accepted: int = 1
    release: str | None = None
    own_row: bool = False

    def to_dict(self) -> dict:
        return {k: (list(v) if isinstance(v, tuple) else v) for k, v in asdict(self).items()}


LEGACY_OPTIONS = DesignOptions(normalize=False)


async def design_program(
    model: ChatModelBase, formatter: FormatterBase, input_prompt: str, n: int,
    params: PublicParams, task: str | None = None, max_iterations: int = 3, matrix: bool = False,
    noisy: NoisyGate | None = None, spec: PromptSpec | None = None, options: DesignOptions | None = None,
) -> DesignResult:
    """``task`` names the reference counter used by the utility test (``None``
    skips it, e.g. for a task without a brute-force reference). ``matrix``: the
    per-node architecture, whose prompt documents ``A`` (:data:`MATRIX_REFERENCE`).
    ``noisy``: the noise-aware utility gate (:mod:`certicount.dsl.noisy_gate`).
    ``spec``: evolvable prompt modules (guidance and extra repair hints).
    ``options``: :class:`DesignOptions` (default: normalisation on, no tightening, no early stop)."""
    opts = options or DesignOptions()
    history: list[dict] = []
    seen: dict[str, int] = {}
    calls = 0

    def reject(entry: dict, feedback: str) -> None:
        extra = spec.hints_for(feedback) if spec is not None else []
        history.append({**entry, "feedback": feedback + "".join(f" Hint: {h}" for h in extra)})

    def stop_early() -> bool:
        if not opts.early_stop or len(history) < 2:
            return False
        a, b = draft_stage(history[-1]["feedback"]), draft_stage(history[-2]["feedback"])
        return a == b and a in opts.early_stop

    async def draft() -> tuple[Program | None, dict]:
        nonlocal calls
        calls += 1
        text = await chat(model, formatter, DESIGNER_SYSTEM,
                          design_prompt(input_prompt, n, history, matrix, spec, opts.release), agent="Curator")
        return read_draft(text, normalize=opts.normalize, core=(spec or V0).core)

    for it in range(1, max_iterations + 1):
        program, entry = await draft()
        if program is None:
            reject(entry, entry["feedback"])
        elif (dup := _duplicate_of(program, seen)) is not None:
            reject(entry, f"rejected: identical to attempt {dup}, which was already rejected")
        else:
            seen[program.digest] = it
            feedback = static_feedback(program, opts) or check_draft(program, task, params, public_n=n, noisy=noisy)
            if feedback is None:
                gs = derive(program, params).gs
                history.append({**entry, "feedback": "accepted", "gs": gs})
                program, gs = await _tighten(program, gs, entry, history, seen, draft, task, params, n, noisy, opts)
                return DesignResult(program, task, it, True, gs, history, calls)
            reject(entry, f"rejected: {feedback}")
        if stop_early():
            history[-1]["early_stop"] = True
            return DesignResult(None, task, it, False, None, history, calls)
    return DesignResult(None, task, max_iterations, False, None, history, calls)


async def _tighten(program: Program, gs: float, entry: dict, history: list[dict], seen: dict[str, int], draft,
                   task: str | None, params: PublicParams, n: int, noisy: NoisyGate | None,
                   opts: DesignOptions) -> tuple[Program, float]:
    """Ask for an equivalent program with a tighter bound while the accepted one is loose."""
    for _ in range(max(0, opts.tighten)):
        slack = bound_slack(program)
        if slack is None or slack.ratio <= opts.slack_tol:
            break
        accepted = next(h for h in reversed(history) if h.get("feedback") == "accepted")
        accepted["tighten_request"] = tighten_request(slack)
        cand, centry = await draft()
        centry = {**centry, "round": "tighten"}
        if cand is None:
            history.append(centry)
            continue
        if cand.digest in seen:
            history.append({**centry, "feedback": "not tighter: the same program as an earlier attempt"})
            break
        seen[cand.digest] = len(history) + 1
        feedback = static_feedback(cand, opts) or check_draft(cand, task, params, public_n=n, noisy=noisy)
        if feedback is not None:
            history.append({**centry, "feedback": f"rejected: {feedback}"})
            continue
        cgs = derive(cand, params).gs
        ce, pe = estimate_gs(cand, cgs, n), estimate_gs(program, gs, n)
        if ce < pe * (1 - 1e-9):
            accepted["feedback"] = (f"superseded: a later attempt has the smaller GS {cgs:g} (this one {gs:g}; "
                                    f"in units of the estimate {ce:g} against {pe:g})")
            history.append({**centry, "feedback": "accepted", "gs": cgs})
            program, gs = cand, cgs
        else:
            history.append({**centry, "feedback": f"not tighter: GS {cgs:g} ({ce:g} in units of the estimate, the "
                                                  f"aggregate's factor included) is not below {pe:g}"})
    return program, gs


def behavior_key(program: Program, params: PublicParams) -> str:
    """Programs with the same answers on public test graphs and the same derived GS are one
    candidate for :func:`design_with_restarts` (AlphaCode-style clustering by behaviour)."""
    graphs = [g for _, g in named_graphs()] + random_graphs(6, seed=7)
    try:
        values = [round(run_exact(program, g), 6) for g in graphs]
        gs = round(derive(program, params).gs, 6)
    except (ArithmeticError, ValueError, SensitivityError):
        return program.digest
    return json.dumps([values, gs])


async def design_with_restarts(
    model: ChatModelBase, formatter: FormatterBase, input_prompt: str, n: int,
    params: PublicParams, task: str | None = None, max_iterations: int = 3, restarts: int = 1,
    matrix: bool = False, noisy: NoisyGate | None = None, spec: PromptSpec | None = None,
    options: DesignOptions | None = None,
) -> DesignResult:
    """Up to ``restarts`` independent design loops (fresh history each). ``options.select``:
    ``"first"`` uses the first accepted program; ``"min_gs"`` collects up to
    ``options.min_accepted`` behaviourally different accepted programs and keeps the one with the
    smallest derived GS, then the smallest noise-free error on the public graphs (both public, so
    the choice spends no budget). All loops are recorded in ``attempts``; ``selection`` lists the
    candidates of ``min_gs``."""
    opts = options or DesignOptions()
    if opts.select not in ("first", "min_gs"):
        raise ValueError(f"unknown selection rule {opts.select!r}")
    attempts: list[dict] = []
    calls = 0
    last: DesignResult | None = None
    pool: dict[str, tuple[DesignResult, int]] = {}  # behaviour -> first accepted loop with it
    for r in range(1, max(1, restarts) + 1):
        res = await design_program(model, formatter, input_prompt, n, params, task, max_iterations, matrix, noisy,
                                   spec, opts)
        calls += res.llm_calls
        attempts.append({"restart": r, "accepted": res.accepted, "iterations": res.iterations,
                         "program": res.program.text() if res.program else None, "history": res.history})
        last = res
        if res.accepted:
            if opts.select == "first":
                break
            pool.setdefault(behavior_key(res.program, params), (res, r))
            if len(pool) >= max(1, opts.min_accepted):
                break
    assert last is not None
    if opts.select == "first" or not pool:
        return DesignResult(last.program, task, last.iterations, last.accepted, last.gs_reference, last.history,
                            calls, restarts=len(attempts), attempts=attempts)
    cands = []
    for res, r in pool.values():
        bias = None
        if noisy is not None and task is not None:
            bias = max(row["bias"] for row in noise_free_check(res.program, task, noisy).rows)
        cands.append({"restart": r, "gs": res.gs_reference, "noise_free_bias": bias, "program": res.program.text(),
                      "estimate_gs": estimate_gs(res.program, res.gs_reference, n), "result": res})
    best = min(cands, key=lambda c: (c["estimate_gs"],
                                     c["noise_free_bias"] if c["noise_free_bias"] is not None else 0.0, c["restart"]))
    chosen: DesignResult = best["result"]
    out = DesignResult(chosen.program, task, chosen.iterations, True, chosen.gs_reference, chosen.history, calls,
                       restarts=len(attempts), attempts=attempts)
    out.selection = {"rule": "min_gs", "chosen_restart": best["restart"],
                     "candidates": [{k: v for k, v in c.items() if k != "result"} for c in cands]}
    return out


async def design_candidates(
    model: ChatModelBase, formatter: FormatterBase, input_prompt: str, n: int,
    params: PublicParams, task: str, sim: SimOptions, max_iterations: int = 3, restarts: int = 1,
    spec: PromptSpec | None = None, options: DesignOptions | None = None,
    releases: tuple[str, ...] = RELEASES,
) -> tuple[DesignResult, list[Program], Selection | None]:
    """Per-node architecture: the curator designs one program per release (``releases``, one
    independent design loop each, :data:`RELEASE_NOTES`), the system certifies each with the
    usual checks and chooses by simulating the whole release on public graphs
    (:func:`certicount.dsl.selection.select_program`; ``sim``: its
    :class:`~certicount.dsl.selection.SimOptions`). Behaviourally identical programs (the same
    ``P``-only program from both rounds) are one candidate.

    Returns ``(result, candidates, selection)``: ``result.program`` is the design-time choice
    (``None`` if no candidate is usable), ``result.selection`` records every candidate, its
    simulated score and the alternatives left to the run-time choice
    (:func:`certicount.dsl.selection.execute_selected`)."""
    base = options or DesignOptions()
    loops = await asyncio.gather(*(
        design_with_restarts(model, formatter, input_prompt, n, params, task, max_iterations, restarts, True, None,
                             spec, replace(base, release=r, select="first"))
        for r in releases))
    attempts, cands, origin, keys = [], [], [], {}
    for r, res in zip(releases, loops):
        for a in res.attempts:
            attempts.append({**a, "release": r})
        if res.accepted and res.program is not None:
            key = behavior_key(res.program, params)
            if key in keys:
                origin[keys[key]].append(r)
                continue
            keys[key] = len(cands)
            cands.append((res, r))
            origin.append([r])
    programs = [res.program for res, _ in cands]
    sel = select_program(programs, task, sim) if programs else None
    calls = sum(res.llm_calls for res in loops)
    rows = []
    for i, (res, r) in enumerate(cands):
        rows.append({**sel.rows[i], "releases": origin[i], "program": res.program.text(), "gs": res.gs_reference,
                     "estimate_gs": estimate_gs(res.program, res.gs_reference, n)})
    selection = {"rule": "simulated", "releases": list(releases), "sim": sim.to_dict(),
                 "chosen": sel.chosen if sel else None, "runtime": sel.runtime if sel else [], "candidates": rows,
                 "accepted_by_release": {r: res.accepted for r, res in zip(releases, loops)}}
    if sel is None or sel.chosen is None:
        last = loops[-1]
        out = DesignResult(None, task, max(res.iterations for res in loops), False, None, last.history, calls,
                           restarts=max(res.restarts for res in loops), attempts=attempts)
    else:
        chosen = cands[sel.chosen][0]
        out = DesignResult(chosen.program, task, chosen.iterations, True, chosen.gs_reference, chosen.history, calls,
                           restarts=chosen.restarts, attempts=attempts)
    out.selection = selection
    return out, programs, sel


# Row programs of the mock curator in a "rows" design round: the PSC references, except the triangle
# count, whose PSC reference reads N(self) (rejected by the own-row check of the per-node architecture).
MOCK_ROW_PROGRAMS = {
    "triangle": ProgramSource("Q = project(P, D)\nreturn 0.5 * sum(size(N(v) & Q) for v in Q)", "total / 3"),
}


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
        # the per-node architecture documents A: answer with that architecture's reference; a design
        # round restricted to the rows (design_candidates) gets the row program of MOCK_ROW_PROGRAMS
        release = payload.get("release")
        if release == "rows":
            src = MOCK_ROW_PROGRAMS.get(task) or PROGRAMS.get(task)
        else:
            src = (NODE_PROGRAMS if "A(x, y)" in user else PROGRAMS).get(task)
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
