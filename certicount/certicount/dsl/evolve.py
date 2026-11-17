"""Self-evolution of the curator's design instructions from its own failures.

One generation:

1. **evaluate** the parent spec (:class:`certicount.dsl.prompt_spec.PromptSpec`): the curator
   designs every training task ``designs`` times with the full design loop (checks, noise-aware
   gate, feedback-driven rewrites, :func:`certicount.dsl.designer.design_with_restarts`);
2. **reflect**: the rejected drafts are grouped by the stage that rejected them; a sample of each
   group (program + the checker's feedback) goes to a reflection call of the same model, which
   proposes ONE edit (add / replace / delete) of ONE evolvable module: a guidance rule, a worked
   example of another statistic, or a repair hint attached to matching rejections;
3. the edited spec must pass :func:`certicount.dsl.prompt_spec.leak_check`, otherwise the
   reflection is asked once more with the problems;
4. every child is evaluated once; the best one is evaluated a second time and replaces the
   parent only if its mean score beats the parent's (the parent is re-evaluated every
   generation, so neither side profits from one lucky evaluation).

Score of an evaluation (public information only: training tasks, public n, synthetic graphs):

    qualified_rate - lambda_calls * mean model calls per design - mu_chars * module characters / 1000

where a design is *qualified* if it was accepted and its noise-free relative error through the
real release (:func:`certicount.dsl.noisy_gate.noise_free_check`) is at most
``slack_factor * reference + slack_abs`` (reference = the task's reference program).

Privacy never depends on the spec: every accepted program is certified by the deriver and the
falsifier exactly as without evolution. A falsifier refutation during evolution (stage
``refuted``) would be a bug of the deriver and is counted in every evaluation.
"""

from __future__ import annotations

import asyncio
import json
import random
import statistics
from collections import Counter, defaultdict
from dataclasses import dataclass, field, replace

from agentscope.formatter import FormatterBase
from agentscope.model import ChatModelBase

from psc.events import collect_errors
from psc.mechanism import DEFAULT_MECHANISM
from psc.models import chat

from .designer import (DSL_REFERENCE, MATRIX_REFERENCE, answer_part, design_reference_params, design_with_restarts,
                       draft_stage)
from .ground_truth import reference_program
from .library import analyst_prompt
from .noisy_gate import NoisyGate, noise_free_check
from .prompt_spec import Example, PromptSpec, leak_check

MODULES = ("rules", "examples", "repair_hints")


@dataclass(frozen=True)
class EvolveConfig:
    train_tasks: tuple[str, ...] = ("degree", "2-star", "4-star")
    n: int = 400  # public number of nodes of the training setting (not an evaluation graph)
    node_bounds: bool = False
    alpha: float = 0.0
    eps: float = 2.0
    mechanism: str = DEFAULT_MECHANISM
    designs: int = 4  # designs per task and evaluation
    max_iterations: int = 3
    concurrency: int = 8
    generations: int = 5
    children: int = 3
    patience: int = 2  # generations without improvement before stopping
    samples_per_stage: int = 4
    max_samples: int = 12
    slack_factor: float = 1.2
    slack_abs: float = 0.05
    lambda_calls: float = 0.02
    mu_chars: float = 0.01
    seed: int = 0

    def gate(self) -> NoisyGate:
        return NoisyGate(self.n, self.eps, self.node_bounds, self.alpha, self.mechanism)

    def to_dict(self) -> dict:
        return {k: getattr(self, k) for k in self.__dataclass_fields__}


@dataclass
class Evaluation:
    score: float
    qualified_rate: float
    accept_rate: float
    mean_calls: float
    per_task: dict[str, dict]
    stages: dict[str, int]
    failures: list[dict] = field(default_factory=list)
    designs: list[dict] = field(default_factory=list)

    def summary(self) -> dict:
        return {"score": self.score, "qualified_rate": self.qualified_rate, "accept_rate": self.accept_rate,
                "mean_calls": self.mean_calls, "per_task": self.per_task, "stages": self.stages}


# ----------------------------------------------------------------- evaluation
_REF_BIAS: dict[tuple, float] = {}


def reference_bias(task: str, cfg: EvolveConfig) -> float:
    key = (task, cfg.gate())
    if key not in _REF_BIAS:
        rep = noise_free_check(reference_program(task, cfg.node_bounds), task, cfg.gate())
        _REF_BIAS[key] = max(r["bias"] for r in rep.rows)
    return _REF_BIAS[key]


async def evaluate(spec: PromptSpec, model: ChatModelBase, formatter: FormatterBase, cfg: EvolveConfig,
                   label: str = "") -> Evaluation:
    """Design every training task ``cfg.designs`` times with ``spec`` (concurrently)."""
    gate = cfg.gate()
    params = design_reference_params(cfg.n)
    sem = asyncio.Semaphore(max(1, cfg.concurrency))

    async def one(task: str, k: int) -> dict:
        async with sem:
            with collect_errors(phase="evolve_eval", candidate=label, task=task, design=k):
                res = await design_with_restarts(model, formatter, analyst_prompt(task, cfg.n), cfg.n, params,
                                                 task=task, max_iterations=cfg.max_iterations, restarts=1,
                                                 matrix=cfg.node_bounds, noisy=gate, spec=spec)
        bias = None
        if res.program is not None:
            bias = max(r["bias"] for r in noise_free_check(res.program, task, gate).rows)
        limit = cfg.slack_factor * reference_bias(task, cfg) + cfg.slack_abs
        return {
            "task": task, "design": k, "accepted": res.accepted, "calls": res.llm_calls,
            "program": res.program.text() if res.program else None, "noise_free_bias": bias,
            "qualified": bool(res.accepted and bias is not None and bias <= limit),
            "history": [{"program": h.get("program"), "feedback": h.get("feedback"),
                         "stage": draft_stage(h.get("feedback"))} for h in res.history],
        }

    designs = await asyncio.gather(*(one(t, k) for t in cfg.train_tasks for k in range(cfg.designs)))
    per_task: dict[str, dict] = {}
    for t in cfg.train_tasks:
        ds = [d for d in designs if d["task"] == t]
        per_task[t] = {"qualified_rate": statistics.mean(d["qualified"] for d in ds),
                       "accept_rate": statistics.mean(d["accepted"] for d in ds),
                       "mean_calls": statistics.mean(d["calls"] for d in ds)}
    stages = Counter(h["stage"] for d in designs for h in d["history"])
    qualified = statistics.mean(d["qualified"] for d in designs)
    calls = statistics.mean(d["calls"] for d in designs)
    failures = [{"task": d["task"], **h} for d in designs for h in d["history"] if h["stage"] != "accepted"]
    # accepted but not qualified: a failure the checks let through (too noisy / biased vs the reference)
    failures += [{"task": d["task"], "program": d["program"], "stage": "not_qualified",
                  "feedback": f"accepted, but its noise-free relative error {d['noise_free_bias']:.3g} on the public "
                              f"test graphs is well above the best program's for this task"}
                 for d in designs if d["accepted"] and not d["qualified"]]
    score = qualified - cfg.lambda_calls * calls - cfg.mu_chars * spec.module_chars() / 1000
    return Evaluation(score, qualified, statistics.mean(d["accepted"] for d in designs), calls, per_task,
                      dict(stages), failures, list(designs))


# ----------------------------------------------------------------- reflection
REFLECT_SYSTEM = (
    "You maintain the instructions that a program-writing assistant (the curator) receives before it writes "
    "small programs in a restricted language. You cannot change the language or the checks. You improve the "
    "instructions so that the curator's first drafts pass the checks and compute accurate statistics."
)


def sample_failures(failures: list[dict], cfg: EvolveConfig, rnd: random.Random) -> list[dict]:
    by_stage: dict[str, list[dict]] = defaultdict(list)
    for f in failures:
        by_stage[f["stage"]].append(f)
    out: list[dict] = []
    for stage, fs in sorted(by_stage.items(), key=lambda kv: -len(kv[1])):
        seen, picked = set(), []
        for f in rnd.sample(fs, len(fs)):
            key = (f.get("program") or "")[:200]
            if key in seen:
                continue
            seen.add(key)
            picked.append(f)
            if len(picked) >= cfg.samples_per_stage:
                break
        out += picked
    return out[: cfg.max_samples]


def reflect_prompt(spec: PromptSpec, ev: Evaluation, samples: list[dict], cfg: EvolveConfig,
                   problems: list[str] | None = None) -> str:
    reference = DSL_REFERENCE + ("\n" + MATRIX_REFERENCE if cfg.node_bounds else "")
    lines = [
        "The curator receives this language description (READ-ONLY, you cannot change it):",
        '"""', reference, '"""', "",
        "After it, the curator receives these editable instruction modules (JSON):",
        json.dumps(spec.modules(), indent=2, ensure_ascii=False), "",
        "- rules: short guidance sentences (plain text, no code).",
        "- examples: worked programs {title, program, aggregate, note} for statistics that the system is NOT asked "
        "to compute (never a degree, k-star, triangle or degree-moment program).",
        "- repair_hints: [pattern, hint] pairs; when a draft is rejected and the regular expression `pattern` matches "
        "the rejection message, the plain-text hint is added to the feedback the curator sees.", "",
        f"Last evaluation: {ev.qualified_rate:.0%} of the designs were accepted and accurate, "
        f"{ev.accept_rate:.0%} accepted, {ev.mean_calls:.2f} drafts per design on average.",
        "Rejections by stage: " + ", ".join(f"{k}={v}" for k, v in sorted(ev.stages.items()) if k != "accepted"), "",
        "Failed drafts (program and the message of the check):",
    ]
    for i, f in enumerate(samples, 1):
        prog = (f.get("program") or "(no program could be read)").strip()
        lines += [f"[{i}] stage={f['stage']}", prog, f"message: {(f.get('feedback') or '')[:600]}", ""]
    lines += [
        "Propose exactly ONE edit to ONE module that would prevent the most frequent or most harmful failure above. "
        "Prefer general guidance about the language and the randomized release over task-specific advice.",
        "Reply with one JSON object:",
        '{"module": "rules" | "examples" | "repair_hints", "op": "add" | "replace" | "delete", '
        '"index": <0-based position, for replace / delete>, '
        '"value": <a string for rules; {"title": ..., "program": ..., "aggregate": ..., "note": ...} for examples; '
        '{"pattern": ..., "hint": ...} for repair_hints>, "reason": "<one sentence>"}',
    ]
    if problems:
        lines += ["", "Your previous edit was refused: " + "; ".join(problems) + ". Propose a different edit."]
    return "\n".join(lines)


def parse_patch(text: str) -> dict | None:
    """The last JSON object with a ``module`` key in the reply (after any reasoning block)."""
    text = answer_part(text)
    dec = json.JSONDecoder()
    found = None
    for i, ch in enumerate(text):
        if ch != "{":
            continue
        try:
            obj, _ = dec.raw_decode(text[i:])
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict) and "module" in obj:
            found = obj
    return found


def apply_patch(spec: PromptSpec, patch: dict, name: str) -> PromptSpec:
    """The edited spec; raises ``ValueError`` on a malformed patch."""
    module, op = patch.get("module"), patch.get("op")
    if module not in MODULES or op not in ("add", "replace", "delete"):
        raise ValueError(f"unknown module / op: {module!r} / {op!r}")
    items = list(getattr(spec, module))
    if op in ("replace", "delete"):
        idx = patch.get("index")
        if not isinstance(idx, int) or not 0 <= idx < len(items):
            raise ValueError(f"index {idx!r} out of range for {module} ({len(items)} items)")
    if op != "delete":
        v = patch.get("value")
        if module == "rules":
            if not isinstance(v, str) or not v.strip():
                raise ValueError("a rule is a non-empty string")
            item = v.strip()
        elif module == "examples":
            if not isinstance(v, dict) or not v.get("program"):
                raise ValueError("an example needs a program")
            item = Example(str(v.get("title", "example")), str(v["program"]), str(v.get("aggregate", "total")),
                           str(v.get("note", "")))
        else:
            if isinstance(v, (list, tuple)) and len(v) == 2:
                v = {"pattern": v[0], "hint": v[1]}
            if not isinstance(v, dict) or not v.get("pattern") or not v.get("hint"):
                raise ValueError("a repair hint needs a pattern and a hint")
            item = (str(v["pattern"]), str(v["hint"]))
        if op == "add":
            items.append(item)
        else:
            items[patch["index"]] = item
    else:
        del items[patch["index"]]
    return replace(spec, name=name, parent=spec.name, **{module: tuple(items)})


async def propose_child(spec: PromptSpec, ev: Evaluation, model: ChatModelBase, formatter: FormatterBase,
                        cfg: EvolveConfig, name: str, rnd: random.Random, tries: int = 2) -> tuple[PromptSpec | None, dict]:
    """One reflection (plus a retry with the leak / format problems)."""
    samples = sample_failures(ev.failures, cfg, rnd)
    record: dict = {"name": name, "parent": spec.name, "samples": len(samples), "attempts": []}
    problems: list[str] | None = None
    for _ in range(tries):
        with collect_errors(phase="reflect", candidate=name):
            text = await chat(model, formatter, REFLECT_SYSTEM, reflect_prompt(spec, ev, samples, cfg, problems),
                              agent="Reflector")
        patch = parse_patch(text)
        attempt: dict = {"patch": patch}
        try:
            if patch is None:
                raise ValueError("no JSON edit found in the reply")
            child = apply_patch(spec, patch, name)
            problems = leak_check(child)
        except ValueError as exc:
            child, problems = None, [str(exc)]
        attempt["problems"] = problems
        record["attempts"].append(attempt)
        if child is not None and not problems:
            record["patch"] = patch
            return child, record
    return None, record


# ----------------------------------------------------------------- the loop
@dataclass
class Candidate:
    spec: PromptSpec
    evals: list[Evaluation] = field(default_factory=list)

    @property
    def mean(self) -> float:
        return statistics.mean(e.score for e in self.evals) if self.evals else float("-inf")


async def evolve(start: PromptSpec, model: ChatModelBase, formatter: FormatterBase, cfg: EvolveConfig,
                 log=lambda rec: None) -> tuple[PromptSpec, list[dict]]:
    """Run the generations; ``log(record)`` receives one record per evaluated candidate.
    Returns the best spec and the lineage."""
    rnd = random.Random(cfg.seed)
    lineage: list[dict] = []

    def emit(kind: str, cand: Candidate, gen: int, ev: Evaluation, extra: dict | None = None) -> None:
        rec = {"kind": kind, "generation": gen, "name": cand.spec.name, "parent": cand.spec.parent,
               "digest": cand.spec.digest, "evaluation": ev.summary(), "mean_score": cand.mean,
               "evaluations": len(cand.evals), "spec": cand.spec.to_dict(), "designs": ev.designs, **(extra or {})}
        lineage.append(rec)
        log(rec)

    parent = Candidate(start)
    ev = await evaluate(parent.spec, model, formatter, cfg, parent.spec.name)
    parent.evals.append(ev)
    emit("parent", parent, 0, ev)
    stale = 0
    for gen in range(1, cfg.generations + 1):
        if not parent.evals[-1].failures:  # nothing left to learn from
            lineage.append({"kind": "converged", "generation": gen, "parent": parent.spec.name,
                            "parent_mean": parent.mean})
            log(lineage[-1])
            break
        children: list[tuple[Candidate, dict]] = []
        for c in range(cfg.children):
            name = f"g{gen}c{c + 1}"
            child, rec = await propose_child(parent.spec, parent.evals[-1], model, formatter, cfg, name, rnd)
            if child is None:
                lineage.append({"kind": "refused", "generation": gen, **rec})
                log(lineage[-1])
                continue
            cand = Candidate(child)
            cev = await evaluate(child, model, formatter, cfg, name)
            cand.evals.append(cev)
            emit("child", cand, gen, cev, {"reflection": rec})
            children.append((cand, rec))
        pev = await evaluate(parent.spec, model, formatter, cfg, parent.spec.name)
        parent.evals.append(pev)
        emit("parent", parent, gen, pev)
        improved = False
        if children:
            best, _ = max(children, key=lambda cr: cr[0].mean)
            if best.mean > parent.mean:
                bev = await evaluate(best.spec, model, formatter, cfg, best.spec.name)  # confirmation
                best.evals.append(bev)
                emit("confirm", best, gen, bev)
                if best.mean > parent.mean:
                    parent, improved = best, True
        stale = 0 if improved else stale + 1
        lineage.append({"kind": "generation", "generation": gen, "parent": parent.spec.name,
                        "parent_mean": parent.mean, "improved": improved})
        log(lineage[-1])
        if stale >= cfg.patience:
            break
    return parent.spec, lineage
