"""Accuracy-driven self-improving program search, and equal tuning of the reference.

The exactness loop of :mod:`certicount.dsl.designer` accepts the first program
that computes the statistic exactly without truncation, so it can at best find
the library algorithm. Here the designer improves its own program from
feedback on *accuracy*:

1. **Correctness** (gate): parse, derive the GS (not loose), and run without
   noise *and without truncation* (``project`` is the identity) on public test
   graphs; it must give the exact answer. A lower threshold is a bias / noise
   trade-off, not an error, so it passes.
2. **Score**: the whole private pipeline (:func:`certicount.dsl.ground_truth.dp_execute`:
   RR graph, noisy degree bound, projection, Laplace, aggregate) is simulated on
   public synthetic graphs with the real ``n`` and several densities; the score
   is the mean relative error (lower is better), with its bias / noise parts.
3. **Self-improvement**: each round the model sees its own leaderboard
   (programs, scores, bias, noise, GS, split) and recent failures, and proposes
   new candidates, each with a generic exploration instruction (refine the
   best, change the threshold, change the budget split, try another formula).
   The best correct candidate over all rounds is returned.

Only public information is used (the prompt, ``n``, the language and synthetic
graphs): no private data, no budget, and never the error on the real graph.
The node still re-derives the GS of the chosen program at run time.

:func:`tune_reference` gives the library algorithm the same chance: it grid
searches the threshold factor and the budget split of the reference program
with the same scorer (the "equally tuned PSC" baseline, executed in code).
"""

from __future__ import annotations

import asyncio
import math
import statistics as st
from dataclasses import asdict, dataclass, field

import networkx as nx

from psc.experiments import run_rng
from psc.graph import Graph
from psc.ground_truth import relative_error
from psc.mechanism import DEFAULT_MECHANISM
from psc.models import chat
from psc.prompts import structured_block

from .designer import DESIGNER_SYSTEM, DSL_REFERENCE, DesignResult, check_draft, design_reference_params, read_draft
from .ground_truth import dp_execute, reference_program
from .lang import Interpreter, Program, parse_program
from .library import PROGRAMS
from .sensitivity import derive
from .utility import reference_counter


@dataclass
class SearchOptions:
    rounds: int = 4
    proposals: int = 3  # model calls per round
    patience: int = 2  # stop after this many rounds without improvement
    keep: int = 5  # leaderboard entries shown to the model
    sims: int = 50  # DP simulations per synthetic graph
    avg_degrees: tuple[float, ...] = (3.0, 6.0, 12.0)
    families: tuple[str, ...] = ("er", "ba")
    eps: float = 2.0
    seed: int = 2026
    mechanism: str = DEFAULT_MECHANISM
    r1: float = 0.5
    r2: float = 0.2
    allow_budget: bool = True

    @classmethod
    def from_dict(cls, d: dict | None) -> "SearchOptions":
        d = dict(d or {})
        for k in ("avg_degrees", "families"):
            if k in d and isinstance(d[k], str):
                d[k] = tuple(float(x) if k == "avg_degrees" else x for x in d[k].split(","))
            elif k in d:
                d[k] = tuple(d[k])
        return cls(**d)


# ---------------------------------------------------------------------------
# Scoring on public synthetic graphs
# ---------------------------------------------------------------------------


def synthetic_graphs(n: int, opts: SearchOptions) -> list[tuple[str, Graph]]:
    """Public test graphs: only ``n`` is taken from the dataset."""
    out = []
    for k, d in enumerate(opts.avg_degrees):
        d = min(float(d), n - 1.0)
        for fam in opts.families:
            seed = opts.seed + 101 * k + (0 if fam == "er" else 7)
            if fam == "er":
                g = nx.gnp_random_graph(n, d / max(1, n - 1), seed=seed)
            elif fam == "ba":
                g = nx.barabasi_albert_graph(n, max(1, min(n - 1, round(d / 2))), seed=seed)
            else:
                raise ValueError(f"unknown graph family {fam!r} (er, ba)")
            out.append((f"{fam}(avg degree {d:g})", Graph.from_edges(n, [(int(u), int(v)) for u, v in g.edges()])))
    return out


_GRAPH_CACHE: dict[tuple, list[tuple[str, Graph, float]]] = {}


def scoring_graphs(n: int, task: str, opts: SearchOptions) -> list[tuple[str, Graph, float]]:
    key = (n, task, opts.avg_degrees, opts.families, opts.seed)
    if key not in _GRAPH_CACHE:
        ref = reference_counter(task)
        _GRAPH_CACHE[key] = [(name, g, float(ref(g))) for name, g in synthetic_graphs(n, opts)]
    return _GRAPH_CACHE[key]


def score_program(program: Program, task: str, n: int, opts: SearchOptions) -> dict:
    """Simulated accuracy of ``program`` (lower ``score`` is better)."""
    interp = Interpreter(program)
    per_graph, biases, noises, gss, splits = [], [], [], [], []
    for name, g, truth in scoring_graphs(n, task, opts):
        res, pre = [], []
        for s in range(opts.sims):
            tr = dp_execute(g, program, opts.eps, run_rng(opts.seed, s), task, opts.mechanism, opts.r1, opts.r2)
            res.append(relative_error(tr.estimate, truth, n))
            pre.append(interp.aggregate_raw(float(sum(tr.counts)), n))
            gss.append(tr.gs)
            noises.append(tr.final_noise_scale * math.sqrt(2 * n) / max(abs(truth), 1e-3 * n))
            splits.append(tr.split)
        bias = (st.mean(pre) - truth) / max(abs(truth), 1e-3 * n)
        biases.append(bias)
        per_graph.append({"graph": name, "truth": truth, "relative_error": st.mean(res), "bias": bias})
    return {
        # geometric mean over graphs: each density counts the same, sparse graphs
        # with a tiny answer do not dominate
        "score": math.exp(st.mean(math.log(max(p["relative_error"], 1e-12)) for p in per_graph)),
        "mean_relative_error": st.mean(p["relative_error"] for p in per_graph),
        "bias": st.mean(biases), "noise": st.mean(noises), "gs_median": st.median(gss),
        "split": [round(x, 4) for x in splits[0]], "per_graph": per_graph,
    }


# ---------------------------------------------------------------------------
# Self-improving search
# ---------------------------------------------------------------------------

SEARCH_GUIDE = """Goal: the program whose final private estimate has the lowest expected error.
1. Correctness gate: without noise and without truncation (project returns its whole set) the program must
   give the exact answer on public test graphs.
2. Score: the whole private pipeline (noisy graph, noisy degree bound, projection, Laplace noise, aggregate)
   is simulated on public synthetic graphs with the same number of nodes and several densities;
   score = geometric mean over the graphs of the mean relative error (lower is better).
The error has two parts. Noise grows with the sensitivity and shrinks with the budget share of the last
step. Bias comes from truncating degrees with project (and from the noisy graph). You may trade them:
the threshold given to project may be any expression of D, dmax, n and constants, and{budget}"""

_BUDGET_TEXT = (
    " you may add a line 'budget: r1=<x>, r2=<y>' to choose the budget split (r1: share of ε for the noisy graph,"
    " used only if the program calls N; r2: share of the rest for the noisy degree bound, used only if the program"
    " reads D or dmax or calls N; defaults r1=0.5, r2=0.2; each in [0.05, 0.95])."
)

OPERATORS = (
    "Improve the best program so far with a small change.",
    "Keep the formula of the best program and change how strongly degrees are bounded (the threshold).",
    "Keep the formula of the best program and change the budget split.",
    "Try a structurally different correct formula.",
)

_SEARCH_FORMAT = (
    "Reply with:\n```dsl\n<program>\n```\naggregate: <expression over total and n>\n"
    "and optionally a last line\nbudget: r1=<x>, r2=<y>"
)


def _entry_text(i: int, h: dict) -> str:
    head = f"#{i}:\n```dsl\n{h['program'].strip()}\n```\naggregate: {h.get('aggregate') or 'total'}"
    if h.get("budget"):
        head += f"\nbudget: {h['budget']}"
    s = h.get("score")
    if s is None:
        return f"{head}\nResult: {h['feedback']}"
    return (f"{head}\nscore {s['score']:.4f} (bias {s['bias']:+.3f}, noise sd {s['noise']:.3f}, both relative to the "
            f"answer; median GS {s['gs_median']:g}; budget split ε1/ε2/ε3 = {'/'.join(f'{x:g}' for x in s['split'])})")


def search_prompt(input_prompt: str, n: int, history: list[dict], opts: SearchOptions, proposal: int,
                  operator: str | None) -> str:
    payload = {"phase": "search_program", "input_prompt": input_prompt, "proposal": proposal}
    guide = SEARCH_GUIDE.format(budget=_BUDGET_TEXT if opts.allow_budget else " the budget split is fixed.")
    parts = [DSL_REFERENCE, guide, f"The input prompt from the analyst is:\n\"\"\"\n{input_prompt}\n\"\"\"",
             f"The graph has {n} nodes."]
    scored = sorted((h for h in history if h.get("score")), key=lambda h: h["score"]["score"])[: opts.keep]
    failed = [h for h in history if not h.get("score") and h.get("program")][-3:]
    if scored:
        parts.append("Your correct programs so far, best first:\n\n" + "\n\n".join(_entry_text(i, h) for i, h in enumerate(scored, 1)))
    if failed:
        parts.append("Recent rejected programs:\n\n" + "\n\n".join(_entry_text(i, h) for i, h in enumerate(failed, 1)))
    if operator and scored:
        parts.append(f"Task for this proposal: {operator} Propose a program different from all programs above.")
    elif history:
        parts.append("Propose a correct program different from all programs above.")
    parts.append(_SEARCH_FORMAT if opts.allow_budget else _SEARCH_FORMAT.split("\nand optionally")[0])
    return "\n\n".join(parts) + f"\n\n{structured_block(payload)}"


async def search_program(model, formatter, input_prompt: str, n: int, task: str,
                         opts: SearchOptions | None = None) -> DesignResult:
    opts = opts or SearchOptions()
    params = design_reference_params(n)
    history: list[dict] = []
    seen: dict[str, int] = {}
    best: tuple[float, Program, dict] | None = None
    calls, proposal, stale = 0, 0, 0
    for rnd in range(1, opts.rounds + 1):
        prompts = []
        for k in range(opts.proposals):
            proposal += 1
            op = OPERATORS[k % len(OPERATORS)] if rnd > 1 else (None if k == 0 else OPERATORS[3])
            prompts.append((proposal, search_prompt(input_prompt, n, history, opts, proposal, op), op))
        replies = await asyncio.gather(*(chat(model, formatter, DESIGNER_SYSTEM, p, agent="Curator") for _, p, _ in prompts))
        calls += len(replies)
        improved = False
        for (pid, _, op), text in zip(prompts, replies):
            program, entry = read_draft(text)
            entry.update(round=rnd, proposal=pid, operator=op)
            if program is None:
                history.append(entry)
                continue
            if not opts.allow_budget and program.budget is not None:
                program = parse_program(program.source, program.aggregate_source)
                entry["budget"] = None
            if program.digest in seen:
                history.append({**entry, "feedback": f"rejected: identical to proposal {seen[program.digest]}"})
                continue
            seen[program.digest] = pid
            fb = check_draft(program, task, params, public_n=n, truncate=False)
            if fb is not None:
                history.append({**entry, "feedback": f"rejected: {fb}"})
                continue
            sc = score_program(program, task, n, opts)
            history.append({**entry, "feedback": "correct", "score": sc, "gs": derive(program, params).gs})
            if best is None or sc["score"] < best[0] - 1e-12:
                best, improved = (sc["score"], program, sc), True
        stale = 0 if improved else stale + 1
        if best is not None and stale >= opts.patience:
            break
    if best is None:
        return DesignResult(None, task, len(history), False, None, history, calls, mode="search")
    _, program, sc = best
    return DesignResult(program, task, len(history), True, derive(program, params).gs, history, calls,
                        mode="search", score=sc)


# ---------------------------------------------------------------------------
# Equal tuning of the reference (library) algorithm
# ---------------------------------------------------------------------------

THRESHOLD_FACTORS = (1.0, 0.85, 0.7, 0.55, 0.4)
R1_GRID = (0.2, 0.3, 0.4, 0.5, 0.6)
R2_GRID = (0.1, 0.2, 0.3)


@dataclass
class Tuned:
    program: Program
    score: dict
    reference_score: dict
    grid: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"program": self.program.text(), "score": self.score["score"],
                "reference_score": self.reference_score["score"], "grid": self.grid}


_TUNE_CACHE: dict[tuple, Tuned] = {}


def tuning_candidates(task: str) -> list[tuple[str, Program]]:
    src = PROGRAMS[task]
    ref = src.parse()
    out: list[tuple[str, Program]] = []
    factors = THRESHOLD_FACTORS if "project(P, D)" in src.local else (1.0,)
    r1s = R1_GRID if ref.uses_rows else (0.5,)
    r2s = R2_GRID if ref.needs_degree_bound else (0.2,)
    for c in factors:
        local = src.local if c == 1.0 else src.local.replace("project(P, D)", f"project(P, D * {c:g})")
        for r1 in r1s:
            for r2 in r2s:
                budget = None if (r1, r2) == (0.5, 0.2) else (r1, r2)
                out.append((f"threshold D*{c:g}, r1={r1:g}, r2={r2:g}", parse_program(local, src.aggregate, budget=budget)))
    return out


def tune_reference(task: str, n: int, opts: SearchOptions | None = None) -> Tuned:
    """Best threshold factor / budget split of the library algorithm by the search score."""
    opts = opts or SearchOptions()
    key = (task, n, tuple(sorted(asdict(opts).items())))
    if key in _TUNE_CACHE:
        return _TUNE_CACHE[key]
    grid, best = [], None
    ref_score = score_program(reference_program(task), task, n, opts)
    for label, prog in tuning_candidates(task):
        sc = ref_score if prog.digest == reference_program(task).digest else score_program(prog, task, n, opts)
        grid.append({"setting": label, "score": sc["score"], "bias": sc["bias"], "noise": sc["noise"]})
        if best is None or sc["score"] < best[1]["score"] - 1e-12:
            best = (prog, sc)
    assert best is not None
    _TUNE_CACHE[key] = Tuned(best[0], best[1], ref_score, grid)
    return _TUNE_CACHE[key]
