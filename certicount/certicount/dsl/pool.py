"""LLM-designed program pools for the degree-first adaptive execution.

The curator LLM proposes local counting programs for a task, the system certifies them, and the
run-time selector of :mod:`certicount.dsl.adaptive` chooses among the certified programs:

1. **Certification**, the gates of the design loop (:func:`certicount.dsl.designer.check_draft`): the
   program parses, its GS is derived and not loose, it gives the exact answer without noise and without
   truncation on public test graphs, and the falsifier does not refute the derived GS. The aggregate
   must be affine in ``total`` (the selector simulates it).
2. **Deduplication**: a program whose estimator equals one already certified on fixed public inputs
   (local count times the aggregate's slope) is rejected unless its certified noise is smaller.
3. **Public score**: a certified program is simulated through the whole private pipeline on public
   synthetic graphs (sizes x degree profiles x clustering) over the settings the selector can choose
   (a fraction of the noisy maximum degree as the bound, and the RR budget of programs that read ``N``);
   its score on a graph is that of its best setting there. All programs see the same noise.
4. **Pool**: the hand-written library program plus, greedily, the certified programs that lower the
   pool's score (geometric mean over the graphs of the best pool program on each) by ``min_gain`` or more.
   The model sees the pool, the scores per graph and the rejections, and proposes again.

Only public information reaches the model (the task, the language, scores on synthetic graphs), so the
designer may be a remote API: no edge ever enters a prompt. A pool is designed once per task and reused
by every run and dataset. Every request to the model, retries included, is counted
(:class:`BudgetedModel`), so a design never exceeds its call budget.

:func:`random_design` is the non-LLM baseline: random programs of the same language
(:mod:`certicount.dsl.fuzz`) through the same gates.
"""

from __future__ import annotations

import random
import re
import time
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Sequence

import numpy as np
from agentscope.message import TextBlock
from agentscope.model import ChatModelBase, ChatResponse

from psc.dp import split_budget
from psc.graph import Graph
from psc.ground_truth import relative_error
from psc.models import chat
from psc.prompts import extract_structured, structured_block

from .adaptive import FAMILIES, Candidate, Streams, _affine, execute, factor_space, release_degrees, row_space, synthetic_graph
from .designer import _CODE_BLOCK, DSL_REFERENCE, check_draft, design_reference_params, read_draft
from .falsifier import random_symmetric_graphs
from .fuzz import sources as random_sources
from .ground_truth import degree_class
from .lang import Env, Interpreter, Program, parse_program
from .library import PROGRAMS, analyst_prompt, infer_program_task
from .sensitivity import PublicParams, SensitivityError, derive
from .utility import reference_counter, utility_test

# ---------------------------------------------------------------------------
# Call budget
# ---------------------------------------------------------------------------


class CallBudgetExceeded(RuntimeError):
    """The design used up its model-call budget (not retryable: :func:`psc.models.chat` raises it)."""


class BudgetedModel(ChatModelBase):
    """Counts every request to ``inner`` (each retry of :func:`psc.models.chat` is one) and refuses
    every request after ``limit``."""

    def __init__(self, inner: ChatModelBase, limit: int) -> None:
        super().__init__(model_name=getattr(inner, "model_name", type(inner).__name__),
                         stream=getattr(inner, "stream", False))
        self.inner, self.limit, self.requests = inner, int(limit), 0
        for k in ("psc_structured_input", "psc_max_retries", "psc_retry_backoff"):
            if hasattr(inner, k):
                setattr(self, k, getattr(inner, k))

    @property
    def remaining(self) -> int:
        return self.limit - self.requests

    async def __call__(self, *args: Any, **kwargs: Any):  # type: ignore[override]
        if self.requests >= self.limit:
            raise CallBudgetExceeded(f"the model-call budget of {self.limit} request(s) is used up")
        self.requests += 1
        return await self.inner(*args, **kwargs)


# ---------------------------------------------------------------------------
# Public settings and synthetic graphs
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TaskSetting:
    """Fixed before the release: ``eps2`` and the rounding (``degree_class``) of the noisy degrees, and
    the RR budget of the PSC setting (``eps1_default``)."""

    eps2: float
    eps1_default: float
    degree_class: str


def task_setting(task: str, eps: float, r1: float = 0.5, r2: float = 0.2) -> TaskSetting:
    ref = PROGRAMS[task].parse()
    if not ref.needs_degree_bound:
        raise ValueError(f"task {task!r} uses no degree bound: nothing to select")
    split = split_budget(eps, ref.uses_rows, True, r1, r2)
    return TaskSetting(split.eps2, split.eps1, degree_class(task, ref))


PROFILES = ("sparse", "dense", "hubs")
SHORT_FAMILY = {"chung-lu": "CL", "geometric": "GEO", "threshold": "TH"}


def profile_weights(profile: str, n: int) -> np.ndarray:
    """Expected degrees of a synthetic graph."""
    if profile == "sparse":
        return np.full(n, 3.0)
    if profile == "dense":
        return np.full(n, 8.0)
    if profile == "hubs":
        w = np.arange(1, n + 1, dtype=float) ** -0.8
        return np.minimum(w / w.mean() * 5.0, 0.4 * (n - 1))
    raise ValueError(f"unknown degree profile {profile!r}; choose from {PROFILES}")


@dataclass(frozen=True)
class Scenario:
    name: str
    graph: Graph
    truth: float


def scenarios(task: str, sizes: Sequence[int], profiles: Sequence[str], families: Sequence[str],
              seed: int) -> list[Scenario]:
    """Public synthetic graphs with a nonzero answer (one per size x profile x family)."""
    count = reference_counter(task)
    out = []
    for n in sizes:
        for prof in profiles:
            for fam in families:
                for attempt in range(20):
                    rng = np.random.default_rng([seed, n, PROFILES.index(prof), FAMILIES.index(fam), attempt])
                    g = synthetic_graph(profile_weights(prof, n), fam, rng)
                    truth = float(count(g))
                    if truth >= 1:
                        break
                name = f"n{n}-{prof}" + (f"-{SHORT_FAMILY[fam]}" if len(families) > 1 else "")
                out.append(Scenario(name, g, truth))
    return out


# ---------------------------------------------------------------------------
# Scoring on the public graphs
# ---------------------------------------------------------------------------

DESIGN_ROW_FACTORS = (1.0, 0.75, 0.5)
DESIGN_EPS1 = (0.6, 1.0, 1.4)


@dataclass
class PoolOptions:
    rounds: int = 3
    per_call: int = 4  # programs requested per model call
    max_pool: int = 4  # deployed programs, the library program included
    min_gain: float = 0.03  # relative drop of the pool score a program must bring to be deployed
    sizes: tuple[int, ...] = (60, 150)
    profiles: tuple[str, ...] = PROFILES
    families: tuple[str, ...] = ("chung-lu", "threshold")  # tasks whose library program reads N
    sims_rows: int = 10
    sims_degrees: int = 300
    eps: float = 2.0
    seed: int = 2026
    reference_n: int = 100  # public parameters of the certification: D = dmax = 10
    max_seconds: float = 0.05  # one execution on the largest graph (the library triangle program: about 2 ms)
    keep: int = 6  # certified programs outside the pool shown to the model

    @classmethod
    def from_dict(cls, d: dict | None) -> "PoolOptions":
        d = dict(d or {})
        for k in ("sizes", "profiles", "families"):
            if k in d and isinstance(d[k], str):
                d[k] = tuple(int(x) if k == "sizes" else x for x in d[k].split(","))
            elif k in d:
                d[k] = tuple(d[k])
        return cls(**d)


def design_settings(program: Program, D: int, eps: float, eps2: float) -> list[Candidate]:
    """The settings a program is scored with (a coarser grid than the run-time selector's)."""
    if program.uses_rows:
        return row_space(program, D, eps, eps2, DESIGN_ROW_FACTORS, DESIGN_EPS1)
    return factor_space(program, D)


def setting_label(c: Candidate) -> str:
    if len(c.key) >= 4 and c.key[2] == "eps1":
        return f"B = {c.key[1]:g} D, eps1 = {c.key[3]:g}"
    return f"B = {c.key[1]:g} D"


@dataclass
class ProgramScore:
    errors: list[float]  # per graph: mean relative error of the best setting
    settings: list[str]  # that setting
    seconds: float

    @property
    def score(self) -> float:
        return geomean(self.errors)

    def to_dict(self) -> dict:
        return {"score": self.score, "errors": self.errors, "settings": self.settings, "seconds": self.seconds}


def geomean(xs: Sequence[float]) -> float:
    return float(np.exp(np.mean(np.log(np.maximum(np.asarray(xs, dtype=float), 1e-12)))))


class Scorer:
    """Scores programs of a task on its public graphs, with common random numbers: run ``s`` of graph
    ``k`` uses the same streams, release and RR graphs for every program."""

    def __init__(self, task: str, opts: PoolOptions) -> None:
        self.task, self.opts = task, opts
        self.setting = task_setting(task, opts.eps)
        rows = PROGRAMS[task].parse().uses_rows
        self.scenarios = scenarios(task, opts.sizes, opts.profiles, opts.families if rows else opts.families[:1],
                                   opts.seed)
        self._runs: dict[tuple, tuple] = {}

    @property
    def names(self) -> list[str]:
        return [s.name for s in self.scenarios]

    def _run(self, k: int, s: int, rows: bool) -> tuple:
        key = (k, s, rows)
        if key not in self._runs:
            g = self.scenarios[k].graph
            st = Streams.draw(g.n, np.random.default_rng([self.opts.seed, 7, k, s]), rows=rows)
            self._runs[key] = (st, release_degrees(g, self.setting.eps2, st, self.setting.degree_class), {})
        return self._runs[key]

    def _errors(self, program: Program, k: int, s: int) -> tuple[np.ndarray, list[str]]:
        sc = self.scenarios[k]
        st, rel, cache = self._run(k, s, program.uses_rows)
        cands = design_settings(program, rel.D, self.opts.eps, self.setting.eps2)
        errs = [relative_error(execute(sc.graph, c, self.opts.eps, rel, st, cache), sc.truth, sc.graph.n) for c in cands]
        return np.array(errs), [setting_label(c) for c in cands]

    def timing(self, program: Program) -> float:
        """Seconds of one execution on the largest graph (raises what the program raises)."""
        k = max(range(len(self.scenarios)), key=lambda i: (self.scenarios[i].graph.n, self.scenarios[i].graph.max_degree()))
        sc = self.scenarios[k]
        st, rel, cache = self._run(k, 0, program.uses_rows)
        cand = design_settings(program, rel.D, self.opts.eps, self.setting.eps2)[0]
        t0 = time.perf_counter()
        execute(sc.graph, cand, self.opts.eps, rel, st, dict(cache))
        return time.perf_counter() - t0

    def score(self, program: Program) -> ProgramScore:
        sims = self.opts.sims_rows if program.uses_rows else self.opts.sims_degrees
        t0 = time.perf_counter()
        errors, settings = [], []
        for k in range(len(self.scenarios)):
            acc, labels = None, []
            for s in range(sims):
                e, labels = self._errors(program, k, s)
                acc = e if acc is None else acc + e
            mean = acc / sims
            j = int(np.argmin(mean))
            errors.append(float(mean[j]))
            settings.append(labels[j])
        return ProgramScore(errors, settings, time.perf_counter() - t0)


# ---------------------------------------------------------------------------
# Certification and deduplication
# ---------------------------------------------------------------------------

_FINGERPRINT_INPUTS: list[tuple[int, dict, list[frozenset], int]] = []


def _fingerprint_inputs() -> list[tuple[int, dict, list[frozenset], int]]:
    if not _FINGERPRINT_INPUTS:
        for n, dmax, seed in ((9, 4, 0), (12, 5, 1), (12, 3, 2)):
            rnd = random.Random(seed)
            for rows in random_symmetric_graphs(n, dmax, 2, seed):
                privates = [frozenset(v for v in range(n) if v != i and rnd.random() < 0.45) for i in range(n)]
                _FINGERPRINT_INPUTS.append((n, dict(enumerate(rows)), privates, dmax))
    return _FINGERPRINT_INPUTS


def fingerprint(program: Program) -> tuple[float, ...]:
    """The estimator on fixed public inputs: every node's local count times the aggregate's slope, and
    the aggregate's offset (rewritings of one estimator give the same fingerprint)."""
    interp = Interpreter(program)
    out: list[float] = []
    for n, rows, privates, D in _fingerprint_inputs():
        a, b = _affine(program, n)
        out += [round(a * interp.local(Env(P, i, rows, n, D=D, dmax=D)), 9) for i, P in enumerate(privates)]
        out.append(round(b, 9))
    return tuple(out)


NOISE_BOUNDS = (5, 10, 40)


def scaled_noise(program: Program, n: int) -> tuple[float, ...]:
    """``|aggregate slope| x GS`` at ``D = dmax`` in :data:`NOISE_BOUNDS`: the Laplace scale (times ε3)
    one report adds to the estimate."""
    a, _ = _affine(program, n)
    return tuple(abs(a) * derive(program, PublicParams(n, D=b, dmax=b)).gs for b in NOISE_BOUNDS)


@dataclass
class Draft:
    """One proposal and what the system made of it."""

    source: str  # "hand" | "llm" | "random"
    round: int
    program: Program | None
    text: str  # as written (program and aggregate)
    idea: str = ""
    status: str = "rejected"  # "certified" | "rejected"
    reason: str | None = None
    category: str | None = None  # rejection class (statistics)
    fingerprint: tuple | None = field(default=None, repr=False)
    noise: tuple | None = None
    score: ProgramScore | None = None
    deployed: bool = False

    def to_dict(self) -> dict:
        return {
            "source": self.source, "round": self.round, "status": self.status, "deployed": self.deployed,
            "program": self.program.text() if self.program is not None else None, "text": self.text,
            "idea": self.idea, "reason": self.reason, "category": self.category,
            "noise": list(self.noise) if self.noise else None, "score": self.score.to_dict() if self.score else None,
        }


def rejection_category(reason: str) -> str:
    for key, cat in (("not a valid program", "parse"), ("linear in total", "aggregate"),
                     ("sensitivity check failed", "sensitivity"), ("too loose", "loose"),
                     ("utility test failed", "inexact"), ("certification failed", "falsifier"),
                     ("fails on a public test graph", "runtime"), ("fails on a public synthetic graph", "runtime"),
                     ("same estimator", "duplicate"), ("identical to", "duplicate"), ("too slow", "slow")):
        if key in reason:
            return cat
    return "other"


def certify(program: Program, task: str, opts: PoolOptions) -> str | None:
    """Rejection reason, or ``None``: the gates of the design loop with the projection as the identity
    in the exactness test (a lower bound is the selector's choice, not an error)."""
    try:
        _affine(program, opts.reference_n)
    except ValueError as exc:
        return f"rejected: the aggregate must be linear in total ({exc})"
    fb = check_draft(program, task, design_reference_params(opts.reference_n), public_n=max(opts.sizes), truncate=False)
    return None if fb is None else f"rejected: {fb}"


def admit(draft: Draft, task: str, opts: PoolOptions, scorer: Scorer, drafts: Sequence[Draft]) -> Draft:
    """Run the gates on ``draft.program``; certified drafts get their fingerprint, noise and score."""
    program = draft.program
    if program is None:
        draft.category = rejection_category(draft.reason or "")
        return draft
    if program.budget is not None:  # the selector chooses the split
        program = draft.program = parse_program(program.source, program.aggregate_source)
    try:
        reason = _gates(program, task, opts, scorer, drafts, draft)
    except (ArithmeticError, ValueError, RecursionError) as exc:  # overflow, a zero divisor at some bound, ...
        reason = f"rejected: the program fails on a public test graph: {type(exc).__name__}: {exc}"
    if reason is not None:
        draft.reason, draft.category = reason, rejection_category(reason)
        return draft
    draft.score = scorer.score(program)
    draft.status, draft.reason = "certified", "certified"
    return draft


def _gates(program: Program, task: str, opts: PoolOptions, scorer: Scorer, drafts: Sequence[Draft],
           draft: Draft) -> str | None:
    same = next((k for k, d in enumerate(drafts, 1) if d.program is not None and d.program.digest == program.digest), None)
    if same:
        return f"rejected: identical to an earlier program (#{same})"
    reason = certify(program, task, opts)
    if reason is not None:
        return reason
    fp, noise = fingerprint(program), scaled_noise(program, opts.reference_n)
    draft.fingerprint, draft.noise = fp, noise
    for k, d in enumerate(drafts, 1):
        if d.status == "certified" and d.fingerprint == fp and all(x >= y - 1e-9 for x, y in zip(noise, d.noise)):
            return (f"rejected: computes the same estimator as program #{k} and its certified noise is not smaller "
                    "(a rewritten formula is the same estimator)")
    seconds = scorer.timing(program)
    if seconds > opts.max_seconds:
        return (f"rejected: too slow ({seconds:.1f} s for one run on a graph with {max(opts.sizes)} nodes; "
                f"limit {opts.max_seconds:g} s)")
    return None


def deploy(drafts: Sequence[Draft], opts: PoolOptions) -> list[int]:
    """Greedy pool: the library program (index 0), then the certified program that lowers the pool score
    most, while the drop is at least ``min_gain`` and the pool has fewer than ``max_pool`` programs."""
    pool = [0]
    best = np.array(drafts[0].score.errors)
    left = [i for i, d in enumerate(drafts) if i and d.status == "certified"]
    while len(pool) < opts.max_pool and left:
        gains = [(geomean(best) / geomean(np.minimum(best, drafts[i].score.errors)) - 1.0, -i) for i in left]
        gain, neg = max(gains)
        if gain < opts.min_gain:
            break
        pool.append(-neg)
        left.remove(-neg)
        best = np.minimum(best, drafts[-neg].score.errors)
    for i, d in enumerate(drafts):
        d.deployed = i in pool
    return pool


# ---------------------------------------------------------------------------
# The model's side: prompt and replies
# ---------------------------------------------------------------------------

POOL_SYSTEM = (
    "You are the curator agent of a multi-agent system that counts substructures of a graph under edge "
    "local differential privacy. You never see the graph. You design the programs that every node runs "
    "locally on its own neighbor list; the system certifies the privacy of every program and, for every "
    "run, picks the program and the parameters that suit the graph. Answer in the requested format."
)

POOL_GUIDE = """How the programs are used. Every node first publishes its degree plus Laplace noise. From these
public values alone the system picks, for every run, one program of the pool and its settings: the degree
bound D (used by project(..., D), by the projection of the noisy graph to maximum degree D, and in the
sensitivity) is a fraction of the noisy maximum degree, trading truncation bias for noise; a program that
calls N also gets a share of the budget for the noisy graph. So write programs in terms of D and do not pick
numbers for D or a budget split. A new program is kept only if it beats the pool on some kinds of graphs.
The system checks: (1) without noise and without truncation (the noisy graph equals the real graph and
project returns its whole set) the local program summed over all nodes and passed through the aggregate
gives the exact answer on every graph; (2) the sensitivity is derivable and not loose; (3) the program is not
the same estimator as a program already certified (rewriting a formula does not change the estimator).
Score: mean relative error |estimate - truth| / truth of the whole private pipeline (noisy degrees, noisy
graph, projection, Laplace noise of the reports, aggregate), simulated with eps = {eps:g} on public synthetic
graphs (no real data): {graphs}. A program's score on a graph is that of its best settings; lower is better."""


def graphs_text(opts: PoolOptions, rows: bool) -> str:
    fams = (", and structure " + " / ".join(f"{SHORT_FAMILY[f]} ({t})" for f, t in
                                           zip(opts.families, ("little clustering", "strong clustering")))
            if rows and len(opts.families) > 1 else "")
    return (f"n = {' or '.join(str(n) for n in opts.sizes)} nodes; degrees sparse (average about 3), dense (about 8) "
            f"or hubs (heavy-tailed, average about 5, a few nodes up to 0.4 n){fams}")


def _flat(text: str, limit: int = 400) -> str:
    flat = " ".join(text.replace("`", "'").split())
    return flat[:limit] + ("..." if len(flat) > limit else "")


def _render(k: int, d: Draft, best: np.ndarray, names: Sequence[str]) -> str:
    origin = "library" if d.source == "hand" else f"round {d.round}"
    head = (f"Program #{k} ({origin}{', in the pool' if d.deployed else ''}); noise multiplier |aggregate slope| x GS "
            f"at D = 10: {d.noise[1]:.3g}")
    code = f"```dsl\n{d.program.source.strip()}\n```\naggregate: {d.program.aggregate_source}"
    errs = "  ".join(f"{name} {e:.3g}{'*' if d.deployed and e <= b + 1e-12 else ''}"
                     for name, e, b in zip(names, d.score.errors, best))
    return f"{head}\n{code}\nrelative error per graph: {errs}"


def pool_prompt(task: str, drafts: Sequence[Draft], pool: Sequence[int], scorer: Scorer, opts: PoolOptions,
                rnd: int) -> str:
    rows = PROGRAMS[task].parse().uses_rows
    best = np.min([drafts[i].score.errors for i in pool], axis=0)
    parts = [DSL_REFERENCE, POOL_GUIDE.format(eps=opts.eps, graphs=graphs_text(opts, rows)),
             f"The input prompt from the analyst is:\n\"\"\"\n{analyst_prompt(task, 100)}\n\"\"\"",
             "The pool now (* marks the best program of the pool on that graph):\n\n"
             + "\n\n".join(_render(i + 1, drafts[i], best, scorer.names) for i in pool)
             + f"\n\nPool score (geometric mean over the graphs of the best pool program): {geomean(best):.4g}"]
    others = sorted((i for i, d in enumerate(drafts) if d.status == "certified" and i not in pool),
                    key=lambda i: drafts[i].score.score)[: opts.keep]
    if others:
        parts.append(f"Certified programs not in the pool (they lower the pool score by less than "
                     f"{100 * opts.min_gain:g}%):\n\n" + "\n\n".join(_render(i + 1, drafts[i], best, scorer.names) for i in others))
    last = [d for d in drafts if d.source == "llm" and d.round == rnd - 1 and d.status != "certified"]
    if last:
        parts.append("Rejected in the previous round:\n" + "\n".join(
            f"- {_flat(d.text, 300)} -- {_flat(d.reason or '', 400)}" for d in last))
    parts.append(
        f"Propose {opts.per_call} new programs, different from each other and from every program above, each aimed "
        "at the graphs where the pool is weakest. For each, first write one sentence on the idea, then the program "
        "as\n```dsl\n<program>\n```\naggregate: <expression over total and n>"
    )
    payload = {"phase": "design_pool", "task": task, "input_prompt": analyst_prompt(task, 100), "round": rnd}
    return "\n\n".join(parts) + f"\n\n{structured_block(payload)}"


def split_drafts(text: str) -> list[tuple[str, str]]:
    """``(idea, segment)`` per code block: the segment runs from the block to the next block (its
    aggregate line follows the block), the idea is the last line of text before the block."""
    blocks = list(_CODE_BLOCK.finditer(text))
    out = []
    for k, m in enumerate(blocks):
        before = text[blocks[k - 1].end() if k else 0: m.start()]
        lines = [ln.strip(" *#-") for ln in before.splitlines() if ln.strip() and not ln.strip().startswith("aggregate:")]
        end = blocks[k + 1].start() if k + 1 < len(blocks) else len(text)
        out.append((lines[-1][:240] if lines else "", text[m.start(): end]))
    return out


def read_drafts(text: str, source: str, rnd: int, limit: int) -> list[Draft]:
    segments = split_drafts(text)
    if not segments:
        return [Draft(source, rnd, None, _flat(text, 300), reason="rejected: no program could be read from the reply "
                      "(put every program in its own dsl code block)", category="parse")]
    out = []
    for idea, seg in segments[:limit]:
        program, entry = read_draft(seg)
        written = f"{entry.get('program', '')}\naggregate: {entry.get('aggregate') or 'total'}".strip()
        out.append(Draft(source, rnd, program, written, idea, reason=entry.get("feedback")))
    return out


# ---------------------------------------------------------------------------
# Design loops
# ---------------------------------------------------------------------------


@dataclass
class PoolDesign:
    task: str
    drafts: list[Draft]
    pool: list[int]  # indices into drafts; 0 is the library program
    scenarios: list[str]
    calls: int = 0  # logical model calls
    requests: int | None = None  # requests counted by a BudgetedModel (retries included)
    stopped: str | None = None
    stats: dict = field(default_factory=dict)
    seconds: float = 0.0

    @property
    def programs(self) -> list[Program]:
        return [self.drafts[i].program for i in self.pool]

    @property
    def pool_errors(self) -> list[float]:
        return np.min([self.drafts[i].score.errors for i in self.pool], axis=0).tolist()

    def to_dict(self) -> dict:
        llm = [d for d in self.drafts if d.source != "hand"]
        return {
            "task": self.task, "calls": self.calls, "requests": self.requests, "stopped": self.stopped,
            "seconds": self.seconds, "scenarios": self.scenarios,
            "pool": self.pool, "pool_programs": [p.text() for p in self.programs],
            "hand_score": self.drafts[0].score.score, "pool_score": geomean(self.pool_errors),
            "hand_errors": self.drafts[0].score.errors, "pool_errors": self.pool_errors,
            "proposed": len(llm), "certified": sum(d.status == "certified" for d in llm),
            "deployed": len(self.pool) - 1,
            "rejections": dict(Counter(d.category for d in llm if d.status != "certified")),
            "stats": self.stats, "drafts": [d.to_dict() for d in self.drafts],
        }


def hand_draft(task: str, opts: PoolOptions, scorer: Scorer) -> Draft:
    prog = PROGRAMS[task].parse()
    d = Draft("hand", 0, prog, prog.text(), "the library program", status="certified", reason="certified")
    d.fingerprint, d.noise, d.score = fingerprint(prog), scaled_noise(prog, opts.reference_n), scorer.score(prog)
    return d


async def design_pool(model: ChatModelBase, formatter, task: str, opts: PoolOptions | None = None,
                      scorer: Scorer | None = None) -> PoolDesign:
    """``opts.rounds`` model calls at most, each asking for ``opts.per_call`` programs."""
    opts = opts or PoolOptions()
    t0 = time.perf_counter()
    scorer = scorer or Scorer(task, opts)
    drafts = [hand_draft(task, opts, scorer)]
    pool, calls, stopped = deploy(drafts, opts), 0, None
    before = getattr(model, "requests", None)
    for rnd in range(1, opts.rounds + 1):
        if isinstance(model, BudgetedModel) and model.remaining < 1:
            stopped = "call budget"
            break
        try:
            text = await chat(model, formatter, POOL_SYSTEM, pool_prompt(task, drafts, pool, scorer, opts, rnd),
                              agent="Curator")
        except CallBudgetExceeded:
            stopped = "call budget"
            break
        calls += 1
        for d in read_drafts(text, "llm", rnd, opts.per_call):
            drafts.append(admit(d, task, opts, scorer, drafts))
        pool = deploy(drafts, opts)
    requests = None if before is None else model.requests - before  # this design's requests (a model may be shared)
    return PoolDesign(task, drafts, pool, scorer.names, calls, requests, stopped, seconds=time.perf_counter() - t0)


RANDOM_AGGREGATES = ("total", "total / 2", "total / 3", "total / 6", "total / n")


def random_design(task: str, count: int, seed: int = 0, opts: PoolOptions | None = None,
                  scorer: Scorer | None = None) -> PoolDesign:
    """Non-LLM baseline: ``count`` random programs of the language (:func:`certicount.dsl.fuzz.sources`)
    with a random constant aggregate through the same gates. Cheap gates run first; only certified
    programs are kept as drafts, the rest is counted in ``stats``."""
    opts = opts or PoolOptions()
    t0 = time.perf_counter()
    scorer = scorer or Scorer(task, opts)
    drafts = [hand_draft(task, opts, scorer)]
    rnd = random.Random(seed)
    stats: Counter = Counter()
    for src in random_sources(count, seed):
        program = parse_program(src, rnd.choice(RANDOM_AGGREGATES))
        try:  # cheap pre-checks before the full gates
            der = derive(program, design_reference_params(opts.reference_n))
        except SensitivityError:
            stats["sensitivity"] += 1
            continue
        if any("loose" in w for w in der.warnings):
            stats["loose"] += 1
            continue
        if not utility_test(program, task, count=5, truncate=False).passed:
            stats["inexact"] += 1
            continue
        d = admit(Draft("random", 1, program, program.text()), task, opts, scorer, drafts)
        stats[d.category or "certified"] += 1
        if d.status == "certified":
            drafts.append(d)
    pool = deploy(drafts, opts)
    return PoolDesign(task, drafts, pool, scorer.names, stats={"proposed": count, **stats},
                      seconds=time.perf_counter() - t0)


# ---------------------------------------------------------------------------
# Offline proposer
# ---------------------------------------------------------------------------


def _mock_batches(task: str) -> list[list[tuple[str, str, str]]]:
    """(idea, program, aggregate) per round; every batch mixes good, duplicate and wrong programs."""
    if task == "triangle":
        return [
            [("Count the noisy edges among my real neighbours, without asking the noisy graph to keep my own edges.",
              "return 0.5 * sum(size(P & N(j)) for j in P)", "total / 3"),
             ("The library program written differently.", "S = N(self) & P\nreturn sum(size(N(j) & P) for j in S) / 2",
              "total / 3"),
             ("Count every wedge once.", "S = P & N(self)\nreturn sum(size(P & N(j)) for j in S)", "total / 3"),
             ("Exclude myself explicitly.", "return size(P - {self})", "total")],
            [("Bound my own list first.", "Q = project(P, D)\nreturn 0.5 * sum(size(Q & N(j)) for j in Q)", "total / 3"),
             ("Use only public rows inside the sum.", "return 0.5 * sum(size(N(j) & N(self)) for j in P)", "total / 3")],
        ]
    m = re.fullmatch(r"(\d+)-star", task)
    if m:
        k = int(m.group(1))
        return [
            [("Scale the count and undo it in the aggregate.", f"deg = size(project(P, D))\nreturn 2 * comb(deg, {k})",
              "total / 2"),
             ("Add a linear correction for the neighbours cut by the projection.",
              f"Q = project(P, D)\nreturn comb(size(Q), {k}) + (size(P) - size(Q)) * comb(D - 1, {k - 1})", "total"),
             ("Count one fewer neighbour.", f"return comb(size(project(P, D)), {k - 1})", "total")],
            [("A slightly lower threshold.", f"return comb(size(project(P, D - 1)), {k})", "total")],
        ]
    if task == "degree-moment2":
        return [[("Square written as a product.", "deg = size(project(P, D))\nreturn deg * deg", "total"),
                 ("Square from pairs.", "deg = size(project(P, D))\nreturn 2 * comb(deg, 2) + deg", "total")]]
    return [[]]


class MockPoolModel(ChatModelBase):
    """Offline proposer: fixed batches per task and round (see :func:`_mock_batches`)."""

    def __init__(self) -> None:
        super().__init__(model_name="mock-pool", stream=False)
        self.calls = 0

    async def __call__(self, messages: list[dict], **kwargs: Any) -> ChatResponse:  # type: ignore[override]
        self.calls += 1
        user = next(m for m in reversed(messages) if m.get("role") == "user")["content"]
        if isinstance(user, list):
            user = "\n".join(b.get("text", "") for b in user if isinstance(b, dict))
        payload = extract_structured(user) or {}
        task = payload.get("task") or infer_program_task(payload.get("input_prompt", ""))
        batches = _mock_batches(task)
        batch = batches[(int(payload.get("round", 1)) - 1) % len(batches)]
        text = "\n\n".join(f"{idea}\n```dsl\n{local}\n```\naggregate: {agg}" for idea, local, agg in batch)
        return ChatResponse(content=[TextBlock(type="text", text=text or "I have no new program.")])
