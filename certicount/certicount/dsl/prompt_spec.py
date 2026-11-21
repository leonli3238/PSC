"""The curator's design instructions as data: a frozen core plus modules that may evolve.

The design prompt (:func:`certicount.dsl.designer.design_prompt`) is assembled from

    core        DSL_REFERENCE / MATRIX_REFERENCE / output format (frozen: the semantics of
                P, N, A, the budget and the reply format; never edited automatically)
    rules       short guidance lines ("Guidance:" block after the language reference)
    examples    small worked programs for statistics that are NOT tasks of the system
    repair_hints  (regex over a rejection message, hint) pairs added to the feedback of a
                rejected draft, on top of the built-in parser hints

``V0`` has empty modules and the core ``v1``; ``LEGACY_V0`` (``load_spec("legacy")``) has empty
modules and the core ``legacy``: its prompt is byte-identical to the one of the CS2-CS5 runs.
Every spec has a content hash recorded in the run manifests.

:func:`leak_check` guards the evolvable modules: no example may compute a statistic of the
system (any task with a brute-force counter, checked by differential testing, so a renamed
or reshaped copy of a reference program is caught too), and rules / hints may not carry
code (no fence, no ``return``).
"""

from __future__ import annotations

import hashlib
import itertools
import json
import re
from dataclasses import asdict, dataclass, field
from functools import lru_cache
from pathlib import Path

from .lang import DSLError, parse_program
from .utility import utility_test

# tasks whose programs must never appear in a prompt (every task with a brute-force counter)
GUARDED_TASKS: tuple[str, ...] = ("degree", "triangle", "degree-moment2", "open-wedge",
                                  "degree-ge3", "triangle-node", "triangle-edge", "4-cycle",
                                  *(f"{k}-star" for k in range(2, 9)))
MAX_MODULE_CHARS = 3000  # all evolvable text together
_CODE = re.compile(r"```|\breturn\b")


@dataclass(frozen=True)
class Example:
    title: str
    program: str
    aggregate: str = "total"
    note: str = ""


@dataclass(frozen=True)
class PromptSpec:
    name: str = "v0"
    rules: tuple[str, ...] = ()
    examples: tuple[Example, ...] = ()
    repair_hints: tuple[tuple[str, str], ...] = ()
    parent: str | None = None
    # frozen core of the prompt (certicount.dsl.designer.dsl_reference): "v1" (no angle-bracket
    # placeholders, the constructs CS4/CS5 drafts failed on spelled out), "legacy" (CS2-CS5 text),
    # "v1-repeat3" / "v1-alt" (the prompt-core comparison CS6a)
    core: str = "v1"

    # ------------------------------------------------------------- rendering
    def guidance(self) -> str:
        """Text inserted after the language reference ("" for empty modules)."""
        parts = []
        if self.rules:
            parts.append("Guidance:\n" + "\n".join(f"- {r}" for r in self.rules))
        if self.examples:
            blocks = []
            for e in self.examples:
                note = f"\n{e.note}" if e.note else ""
                blocks.append(f"Example ({e.title}):\n```dsl\n{e.program.strip()}\n```\naggregate: {e.aggregate}{note}")
            parts.append("Worked examples of the language (statistics that are not the requested one):\n\n"
                         + "\n\n".join(blocks))
        return "\n\n".join(parts)

    def hints_for(self, feedback: str) -> list[str]:
        out = []
        for pattern, hint in self.repair_hints:
            try:
                if re.search(pattern, feedback):
                    out.append(hint)
            except re.error:
                continue
        return out

    # ------------------------------------------------------------- identity / io
    def modules(self) -> dict:
        return {"rules": list(self.rules), "examples": [asdict(e) for e in self.examples],
                "repair_hints": [list(h) for h in self.repair_hints]}

    def module_chars(self) -> int:
        return len(json.dumps(self.modules(), ensure_ascii=False))

    @property
    def digest(self) -> str:
        """Content hash of the modules (and of the core unless it is ``legacy``, so the digests of
        the CS2-CS5 specs are unchanged)."""
        content = self.modules() if self.core == "legacy" else {**self.modules(), "core": self.core}
        return hashlib.sha256(json.dumps(content, sort_keys=True).encode()).hexdigest()[:16]

    def to_dict(self) -> dict:
        return {"name": self.name, "parent": self.parent, "digest": self.digest, "core": self.core, **self.modules()}

    @classmethod
    def from_dict(cls, d: dict) -> "PromptSpec":
        """A dict without ``core`` was written before cores existed: its prompt used the legacy core."""
        return cls(
            name=d.get("name", "spec"),
            rules=tuple(d.get("rules", ())),
            examples=tuple(Example(**e) for e in d.get("examples", ())),
            repair_hints=tuple((h[0], h[1]) for h in d.get("repair_hints", ())),
            parent=d.get("parent"),
            core=d.get("core", "legacy"),
        )

    def save(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps(self.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")


V0 = PromptSpec()
LEGACY_V0 = PromptSpec(name="legacy", core="legacy")  # the prompt of CS2-CS5, byte for byte
# empty-module specs of the prompt-core comparison (CS6a): B = prohibition stated three times,
# C = positive rewrites + closing checklist + rewrite hints (certicount.dsl.designer.dsl_reference);
# generic = rewrites of single constructs over placeholders, leak-checked (core_leak_check), CS9
CORE_SPECS = {c: PromptSpec(name=c, core=c) for c in ("v1-repeat3", "v1-alt", "generic")}


def load_spec(ref: str | None) -> PromptSpec:
    """``None`` / ``"v0"`` / ``"v1"`` -> :data:`V0` (core v1, empty modules); ``"legacy"`` -> :data:`LEGACY_V0`;
    ``"v1-repeat3"`` / ``"v1-alt"`` / ``"generic"`` -> :data:`CORE_SPECS`; otherwise a JSON file written by
    :meth:`PromptSpec.save`."""
    if ref in (None, "", "v0", "v1"):
        return V0
    if ref == "legacy":
        return LEGACY_V0
    if ref in CORE_SPECS:
        return CORE_SPECS[ref]
    return PromptSpec.from_dict(json.loads(Path(ref).read_text(encoding="utf-8")))


# ----------------------------------------------------------------- leak / validity check
def leak_check(spec: PromptSpec) -> list[str]:
    """Problems that forbid using ``spec`` (empty list: usable)."""
    problems: list[str] = []
    if spec.module_chars() > MAX_MODULE_CHARS:
        problems.append(f"modules too long ({spec.module_chars()} > {MAX_MODULE_CHARS} characters)")
    for i, r in enumerate(spec.rules):
        if _CODE.search(r):
            problems.append(f"rule {i + 1} contains code")
    for i, (pattern, hint) in enumerate(spec.repair_hints):
        if _CODE.search(hint):
            problems.append(f"repair hint {i + 1} contains code")
        try:
            re.compile(pattern)
        except re.error as exc:
            problems.append(f"repair hint {i + 1}: invalid pattern ({exc})")
    for i, e in enumerate(spec.examples):
        try:
            prog = parse_program(e.program, e.aggregate)
        except DSLError as exc:
            problems.append(f"example {i + 1} is not a valid program: {exc}")
            continue
        for task in GUARDED_TASKS:
            try:
                computes = utility_test(prog, task, count=12, named=True).passed
            except (ArithmeticError, ValueError, TypeError, KeyError):
                computes = False
            if computes:
                problems.append(f"example {i + 1} computes the task {task!r}")
    return problems


# ----------------------------------------------------------------- leak check of a frozen core
# Instances of the placeholders of a core's DSL fragments (certicount.dsl.designer.core_templates):
# the private list, bounded or not, and their sizes. Only placeholders are filled in, nothing is
# wrapped around a fragment: a fragment leaks if it alone, read as the whole program, computes a task.
LEAK_INSTANCES: dict[str, tuple[str, ...]] = {
    "S": ("P", "project(P, D)"), "T": ("P", "project(P, D)"),
    "x": ("size(P)", "size(project(P, D))"), "a": ("size(P)", "size(project(P, D))"),
    "b": ("size(P)", "size(project(P, D))"), "k": ("2", "3"), "EXPR": ("1", "size(P)"),
}
LEAK_AGGREGATES: tuple[str, ...] = ("total", "total / 2", "total / 3", "total / 4", "total / 6", "total / n")
# what the language reference gives without any rewrite: size, pow and comb of the private degree
GIVEN_PROGRAMS: tuple[str, ...] = ("size(P)", "pow(size(P), 2)", "pow(size(P), 3)",
                                   *(f"comb(size(P), {k})" for k in range(2, 9)))


def fragment_instances(fragment: str) -> list[str]:
    names = [p for p in LEAK_INSTANCES if re.search(rf"\b{p}\b", fragment)]
    out = []
    for combo in itertools.product(*(LEAK_INSTANCES[p] for p in names)):
        sub = dict(zip(names, combo))
        out.append(re.sub(r"\b(" + "|".join(names) + r")\b", lambda m: sub[m.group(1)], fragment) if names
                   else fragment)
    return out


def _computes(expr: str, aggregate: str, task: str) -> bool:
    try:
        prog = parse_program(f"return {expr}", aggregate)
        # the named graphs first (cheap), then random graphs
        return (utility_test(prog, task, count=0, named=True).passed
                and utility_test(prog, task, count=12, named=False).passed)
    except (DSLError, ArithmeticError, ValueError, TypeError, KeyError):
        return False


def computed_tasks(expr: str, tasks: tuple[str, ...] = GUARDED_TASKS) -> list[tuple[str, str]]:
    """``(aggregate, task)`` pairs for which ``return expr`` computes a task."""
    return [(agg, t) for agg in LEAK_AGGREGATES for t in tasks if _computes(expr, agg, t)]


@lru_cache(maxsize=1)
def given_tasks() -> frozenset[str]:
    """Tasks a single call of the language reference computes (:data:`GIVEN_PROGRAMS`): no rewrite
    can leak them (degree, the k-stars, the second degree moment)."""
    return frozenset(t for e in GIVEN_PROGRAMS for _, t in computed_tasks(e))


@lru_cache(maxsize=None)
def core_leak_check(core: str) -> tuple[dict, ...]:
    """Fragments of a frozen core that compute a guarded task not in :func:`given_tasks` once their
    placeholders are filled in (empty: the core shows no program of a task). ``v1-alt`` leaks the
    rows triangle and the open wedges; ``generic`` must leak nothing (``tests/test_extension.py``)."""
    from .designer import core_templates  # the designer imports this module

    tasks = tuple(t for t in GUARDED_TASKS if t not in given_tasks())
    leaks = []
    for frag in core_templates(core):
        for expr in fragment_instances(frag):
            for agg, task in computed_tasks(expr, tasks):
                leaks.append({"fragment": frag, "program": expr, "aggregate": agg, "task": task})
    return tuple(leaks)
