"""Self-evolution of the curator's design instructions from its own failures.

One generation:

1. **evaluate** a spec (:class:`certicount.dsl.prompt_spec.PromptSpec`): the curator designs every
   training task ``designs`` times with the full design loop (checks, noise-aware gate,
   feedback-driven rewrites, :func:`certicount.dsl.designer.design_with_restarts`);
2. **select** the spec to edit: with ``pareto`` (GEPA, Agrawal et al. 2025) a member of the Pareto
   front of all evaluated specs over the per-task scores, drawn with a weight equal to the number
   of tasks on which it is best, so a rule that fixes one task is not lost to the average;
   otherwise the incumbent;
3. **reflect**: the rejected drafts of that spec are grouped by the stage that rejected them; a
   sample of each group (program + the checker's feedback) goes to a reflection call of the same
   model, which proposes ONE edit (add / replace / delete) of ONE evolvable module: a guidance
   rule, a worked example of another statistic, or a repair hint attached to matching rejections;
4. the edited spec must pass :func:`certicount.dsl.prompt_spec.leak_check` and keep at most
   ``max_rules`` rules, otherwise the reflection is asked once more with the problems;
5. every child is evaluated once; the incumbent is re-evaluated every generation; the best child
   is evaluated until it has ``confirm_evals`` evaluations and replaces the incumbent only if its
   mean design score beats the incumbent's by more than ``z`` standard errors (racing,
   Maron & Moore 1993; one lucky evaluation of 12 designs moved the score by 0.1-0.4 in CS5).

Score of a design (public information only: training tasks, public n, synthetic graphs):

    qualified - lambda_calls * model calls - nu_gs * log(max(1, GS / GS of the reference))

where a design is *qualified* if it was accepted and its noise-free relative error through the
real release (:func:`certicount.dsl.noisy_gate.noise_free_check`) is at most
``slack_factor * reference + slack_abs`` (reference = the task's reference program), and the GS
term charges a certified but looser bound (more noise at run time; GS at the design-time public
parameters). The score of an evaluation is the mean design score minus
``mu_chars * module characters / 1000``.

Privacy never depends on the spec: every accepted program is certified by the deriver and the
falsifier exactly as without evolution. A falsifier refutation during evolution (stage
``refuted``) would be a bug of the deriver and is counted in every evaluation.
"""

from __future__ import annotations

import asyncio
import json
import math
import random
import statistics
from collections import Counter, defaultdict
from dataclasses import dataclass, field, replace

from agentscope.formatter import FormatterBase
from agentscope.model import ChatModelBase

from psc.events import collect_errors
from psc.mechanism import DEFAULT_MECHANISM
from psc.models import chat

from .designer import DesignOptions, answer_part, design_reference_params, design_with_restarts, draft_stage, dsl_reference
from .ground_truth import reference_program
from .library import analyst_prompt
from .noisy_gate import NoisyGate, noise_free_check
from .prompt_spec import Example, PromptSpec, leak_check
from .sensitivity import derive

MODULES = ("rules", "examples", "repair_hints")


@dataclass(frozen=True)
class EvolveConfig:
    # open-wedge reads the noisy rows like the held-out triangle (see certicount.dsl.library)
    train_tasks: tuple[str, ...] = ("degree", "2-star", "4-star", "open-wedge")
    n: int = 400  # public number of nodes of the training setting (not an evaluation graph)
    node_bounds: bool = False
    alpha: float = 0.0
    eps: float = 2.0
    mechanism: str = DEFAULT_MECHANISM
    designs: int = 8  # designs per task and evaluation (CS5: 4, too few to rank specs)
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
    nu_gs: float = 0.1
    confirm_evals: int = 2  # evaluations a child needs before it can replace the incumbent
    z: float = 1.0  # required margin in standard errors of the difference of the mean design scores
    max_rules: int = 4
    pareto: bool = True
    normalize: bool = True  # certicount.dsl.designer.DesignOptions.normalize
    seed: int = 0

    def gate(self) -> NoisyGate:
        return NoisyGate(self.n, self.eps, self.node_bounds, self.alpha, self.mechanism)

    def to_dict(self) -> dict:
        return {k: getattr(self, k) for k in self.__dataclass_fields__}


def wilson_interval(successes: float, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score interval of a proportion (Wilson 1927); ``(0, 1)`` without trials."""
    if n <= 0:
        return 0.0, 1.0
    p = successes / n
    den = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return max(0.0, centre - half), min(1.0, centre + half)


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
    penalty: float = 0.0  # mu_chars * module characters / 1000

    def summary(self) -> dict:
        return {"score": self.score, "qualified_rate": self.qualified_rate, "accept_rate": self.accept_rate,
                "mean_calls": self.mean_calls, "per_task": self.per_task, "stages": self.stages,
                "qualified_ci95": list(wilson_interval(sum(d["qualified"] for d in self.designs), len(self.designs)))}


# ----------------------------------------------------------------- evaluation
_REF_BIAS: dict[tuple, float] = {}
_REF_GS: dict[tuple, float] = {}


def reference_bias(task: str, cfg: EvolveConfig) -> float:
    key = (task, cfg.gate())
    if key not in _REF_BIAS:
        rep = noise_free_check(reference_program(task, cfg.node_bounds), task, cfg.gate())
        _REF_BIAS[key] = max(r["bias"] for r in rep.rows)
    return _REF_BIAS[key]


def reference_gs(task: str, cfg: EvolveConfig) -> float:
    """GS of the task's reference program at the design-time public parameters."""
    key = (task, cfg.n, cfg.node_bounds)
    if key not in _REF_GS:
        _REF_GS[key] = derive(reference_program(task, cfg.node_bounds), design_reference_params(cfg.n)).gs
    return _REF_GS[key]


def design_score(d: dict, cfg: EvolveConfig) -> float:
    s = float(d["qualified"]) - cfg.lambda_calls * d["calls"]
    if d["accepted"] and d.get("gs_ratio") is not None and d["gs_ratio"] > 1:
        s -= cfg.nu_gs * math.log(d["gs_ratio"])
    return s


async def evaluate(spec: PromptSpec, model: ChatModelBase, formatter: FormatterBase, cfg: EvolveConfig,
                   label: str = "") -> Evaluation:
    """Design every training task ``cfg.designs`` times with ``spec`` (concurrently)."""
    gate = cfg.gate()
    params = design_reference_params(cfg.n)
    sem = asyncio.Semaphore(max(1, cfg.concurrency))
    options = DesignOptions(normalize=cfg.normalize)

    async def one(task: str, k: int) -> dict:
        async with sem:
            with collect_errors(phase="evolve_eval", candidate=label, task=task, design=k):
                res = await design_with_restarts(model, formatter, analyst_prompt(task, cfg.n), cfg.n, params,
                                                 task=task, max_iterations=cfg.max_iterations, restarts=1,
                                                 matrix=cfg.node_bounds, noisy=gate, spec=spec, options=options)
        bias = None
        if res.program is not None:
            bias = max(r["bias"] for r in noise_free_check(res.program, task, gate).rows)
        limit = cfg.slack_factor * reference_bias(task, cfg) + cfg.slack_abs
        ref_gs = reference_gs(task, cfg)
        gs_ratio = None
        if res.gs_reference is not None:
            gs_ratio = res.gs_reference / ref_gs if ref_gs > 0 else (1.0 if res.gs_reference == 0 else math.inf)
        d = {
            "task": task, "design": k, "accepted": res.accepted, "calls": res.llm_calls,
            "program": res.program.text() if res.program else None, "noise_free_bias": bias,
            "gs": res.gs_reference, "gs_ratio": gs_ratio,
            "qualified": bool(res.accepted and bias is not None and bias <= limit),
            "history": [{"program": h.get("program"), "feedback": h.get("feedback"),
                         "stage": draft_stage(h.get("feedback"))} for h in res.history],
        }
        d["score"] = design_score(d, cfg)
        return d

    designs = await asyncio.gather(*(one(t, k) for t in cfg.train_tasks for k in range(cfg.designs)))
    per_task: dict[str, dict] = {}
    for t in cfg.train_tasks:
        ds = [d for d in designs if d["task"] == t]
        ratios = [d["gs_ratio"] for d in ds if d["gs_ratio"] is not None and math.isfinite(d["gs_ratio"])]
        per_task[t] = {"qualified_rate": statistics.mean(d["qualified"] for d in ds),
                       "qualified_ci95": list(wilson_interval(sum(d["qualified"] for d in ds), len(ds))),
                       "accept_rate": statistics.mean(d["accepted"] for d in ds),
                       "mean_calls": statistics.mean(d["calls"] for d in ds),
                       "score": statistics.mean(d["score"] for d in ds),
                       "mean_gs_ratio": statistics.mean(ratios) if ratios else None}
    stages = Counter(h["stage"] for d in designs for h in d["history"])
    qualified = statistics.mean(d["qualified"] for d in designs)
    calls = statistics.mean(d["calls"] for d in designs)
    failures = [{"task": d["task"], **h} for d in designs for h in d["history"]
                if h["stage"] not in ("accepted", "superseded")]
    # accepted but not qualified: a failure the checks let through (too noisy / biased vs the reference)
    failures += [{"task": d["task"], "program": d["program"], "stage": "not_qualified",
                  "feedback": f"accepted, but its noise-free relative error {d['noise_free_bias']:.3g} on the public "
                              f"test graphs is well above the best program's for this task"}
                 for d in designs if d["accepted"] and not d["qualified"]]
    # accepted with a looser certified bound than needed: more noise at run time
    failures += [{"task": d["task"], "program": d["program"], "stage": "gs_looser",
                  "feedback": f"accepted, but its certified sensitivity is {d['gs_ratio']:.3g} times the smallest one "
                              "known for this statistic, so its reports carry that much more noise"}
                 for d in designs if d["accepted"] and d["gs_ratio"] is not None and d["gs_ratio"] > 1.05]
    penalty = cfg.mu_chars * spec.module_chars() / 1000
    score = statistics.mean(d["score"] for d in designs) - penalty
    return Evaluation(score, qualified, statistics.mean(d["accepted"] for d in designs), calls, per_task,
                      dict(stages), failures, list(designs), penalty)


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
    reference = dsl_reference(spec.core, cfg.node_bounds)
    lines = [
        "The curator receives this language description (READ-ONLY, you cannot change it):",
        '"""', reference, '"""', "",
        "After it, the curator receives these editable instruction modules (JSON):",
        json.dumps(spec.modules(), indent=2, ensure_ascii=False), "",
        f"- rules: short guidance sentences (plain text, no code; at most {cfg.max_rules} rules, short ones work "
        "better than long ones).",
        "- examples: worked programs {title, program, aggregate, note} for statistics that the system is NOT asked "
        "to compute (never a degree, k-star, triangle, wedge or degree-moment program).",
        "- repair_hints: [pattern, hint] pairs; when a draft is rejected and the regular expression `pattern` matches "
        "the rejection message, the plain-text hint is added to the feedback the curator sees.", "",
        f"Last evaluation: {ev.qualified_rate:.0%} of the designs were accepted and accurate, "
        f"{ev.accept_rate:.0%} accepted, {ev.mean_calls:.2f} drafts per design on average.",
        "Per task: " + "; ".join(f"{t}: {v['qualified_rate']:.0%} accurate, {v['mean_calls']:.2f} drafts"
                                 for t, v in ev.per_task.items()),
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
            if len(child.rules) > cfg.max_rules:
                problems.append(f"at most {cfg.max_rules} rules: replace or delete a rule instead of adding one")
        except ValueError as exc:
            child, problems = None, [str(exc)]
        attempt["problems"] = problems
        record["attempts"].append(attempt)
        if child is not None and not problems:
            record["patch"] = patch
            return child, record
    return None, record


# ----------------------------------------------------------------- candidates and statistics
@dataclass
class Candidate:
    spec: PromptSpec
    evals: list[Evaluation] = field(default_factory=list)

    @property
    def scores(self) -> list[float]:
        """Every design score of every evaluation, the module penalty included."""
        return [d["score"] - e.penalty for e in self.evals for d in e.designs]

    @property
    def mean(self) -> float:
        return statistics.mean(self.scores) if self.evals else float("-inf")

    @property
    def se(self) -> float:
        s = self.scores
        return statistics.stdev(s) / math.sqrt(len(s)) if len(s) > 1 else math.inf

    def task_scores(self) -> dict[str, float]:
        by: dict[str, list[float]] = defaultdict(list)
        for e in self.evals:
            for d in e.designs:
                by[d["task"]].append(d["score"] - e.penalty)
        return {t: statistics.mean(v) for t, v in by.items()}


def beats(a: Candidate, b: Candidate, z: float) -> bool:
    """``a``'s mean design score exceeds ``b``'s by more than ``z`` standard errors of the difference."""
    se = math.sqrt(a.se ** 2 + b.se ** 2) if math.isfinite(a.se) and math.isfinite(b.se) else math.inf
    diff = a.mean - b.mean
    return diff > 0 and (diff > z * se if math.isfinite(se) else False)


def pareto_front(pool: list[Candidate], tasks: tuple[str, ...]) -> list[Candidate]:
    """Candidates no other candidate matches on every task and beats on one."""
    vecs = [(c, c.task_scores()) for c in pool if c.evals]

    def dominates(u: dict, v: dict) -> bool:
        return all(u.get(t, -math.inf) >= v.get(t, -math.inf) for t in tasks) and \
            any(u.get(t, -math.inf) > v.get(t, -math.inf) for t in tasks)

    return [c for c, v in vecs if not any(dominates(u, v) for o, u in vecs if o is not c)]


def select_parent(front: list[Candidate], tasks: tuple[str, ...], rnd: random.Random) -> Candidate:
    """GEPA's selection: weight = number of tasks on which the candidate has the best score of the front."""
    weights = []
    for c in front:
        ts = c.task_scores()
        weights.append(sum(1 for t in tasks if ts.get(t, -math.inf) >= max(o.task_scores().get(t, -math.inf)
                                                                              for o in front) - 1e-12))
    if not any(weights):
        weights = [1] * len(front)
    return rnd.choices(front, weights=weights, k=1)[0]


# ----------------------------------------------------------------- the loop
async def evolve(start: PromptSpec, model: ChatModelBase, formatter: FormatterBase, cfg: EvolveConfig,
                 log=lambda rec: None) -> tuple[PromptSpec, list[dict]]:
    """Run the generations; ``log(record)`` receives one record per evaluated candidate.
    Returns the best spec (the incumbent) and the lineage."""
    rnd = random.Random(cfg.seed)
    lineage: list[dict] = []

    def emit(kind: str, cand: Candidate, gen: int, ev: Evaluation, extra: dict | None = None) -> None:
        rec = {"kind": kind, "generation": gen, "name": cand.spec.name, "parent": cand.spec.parent,
               "digest": cand.spec.digest, "evaluation": ev.summary(), "mean_score": cand.mean,
               "se": cand.se if math.isfinite(cand.se) else None,
               "evaluations": len(cand.evals), "spec": cand.spec.to_dict(), "designs": ev.designs, **(extra or {})}
        lineage.append(rec)
        log(rec)

    async def run_eval(cand: Candidate, kind: str, gen: int, extra: dict | None = None) -> Evaluation:
        ev = await evaluate(cand.spec, model, formatter, cfg, cand.spec.name)
        cand.evals.append(ev)
        emit(kind, cand, gen, ev, extra)
        return ev

    incumbent = Candidate(start)
    pool: list[Candidate] = [incumbent]
    await run_eval(incumbent, "parent", 0)
    stale = 0
    for gen in range(1, cfg.generations + 1):
        front = pareto_front(pool, cfg.train_tasks) if cfg.pareto else [incumbent]
        if not any(c.evals[-1].failures for c in front):  # nothing left to learn from
            lineage.append({"kind": "converged", "generation": gen, "parent": incumbent.spec.name,
                            "parent_mean": incumbent.mean})
            log(lineage[-1])
            break
        children: list[Candidate] = []
        for c in range(cfg.children):
            name = f"g{gen}c{c + 1}"
            base = select_parent([f for f in front if f.evals[-1].failures], cfg.train_tasks, rnd) \
                if cfg.pareto else incumbent
            child, rec = await propose_child(base.spec, base.evals[-1], model, formatter, cfg, name, rnd)
            if child is None:
                lineage.append({"kind": "refused", "generation": gen, **rec})
                log(lineage[-1])
                continue
            cand = Candidate(child)
            await run_eval(cand, "child", gen, {"reflection": rec})
            children.append(cand)
            pool.append(cand)
        await run_eval(incumbent, "parent", gen)
        improved = False
        if children:
            best = max(children, key=lambda cand: cand.mean)
            if best.mean > incumbent.mean:
                while len(best.evals) < max(1, cfg.confirm_evals):  # confirmation
                    await run_eval(best, "confirm", gen)
                if beats(best, incumbent, cfg.z):
                    incumbent, improved = best, True
        stale = 0 if improved else stale + 1
        front_names = [c.spec.name for c in pareto_front(pool, cfg.train_tasks)]
        lineage.append({"kind": "generation", "generation": gen, "parent": incumbent.spec.name,
                        "parent_mean": incumbent.mean, "parent_se": incumbent.se if math.isfinite(incumbent.se) else None,
                        "improved": improved, "front": front_names})
        log(lineage[-1])
        if stale >= cfg.patience:
            break
    return incumbent.spec, lineage
