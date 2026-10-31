"""Composite queries and privacy budget accounting (research content 6).

The curator splits a compound question into library tasks or DSL programs; the
privacy controller allocates the budget once, with sequential composition only,
and reuses what is already published:

* the RR noisy graph (``eps1``) is built once for every subquery that reads ``N(.)``;
* the noisy degrees (``eps2``) are published once; they give one shared threshold
  ``D`` for every subquery that needs a degree bound, and the average degree is
  their mean (post-processing, no extra Laplace report);
* each remaining subquery gets its own Laplace report, the remaining budget being
  split evenly among them.

:class:`PrivacyAccountant` records every release in a ledger and refuses to
exceed the total ε. Execution is code-only (DSL interpreter on every node), so
the result does not depend on an LLM; the LLM's part is the decomposition.
"""

from __future__ import annotations

import ast
import json
import math
import re
from dataclasses import dataclass, field
from typing import Mapping, Sequence

import numpy as np

from psc.dp import build_noisy_graph, graph_projection, laplace_noise, project_neighbor_list
from psc.graph import Graph
from psc.mechanism import DEFAULT_MECHANISM, get_mechanism
from psc.models import chat
from psc.prompts import extract_json

from .dsl.lang import Env, Interpreter, Program, smallest_projector
from .dsl.library import PROGRAMS
from .dsl.sensitivity import PublicParams, derive
from .dsl.utility import reference_counter


class BudgetExceeded(RuntimeError):
    pass


@dataclass
class PrivacyAccountant:
    budget: float
    ledger: list[dict] = field(default_factory=list)

    @property
    def spent(self) -> float:
        return sum(e["eps"] for e in self.ledger)

    @property
    def remaining(self) -> float:
        return self.budget - self.spent

    def spend(self, release: str, eps: float, note: str = "") -> None:
        if eps < 0 or not math.isfinite(eps):
            raise ValueError("eps must be finite and nonnegative")
        if self.spent + eps > self.budget + 1e-9:
            raise BudgetExceeded(f"{release}: {eps:g} exceeds the remaining budget {self.remaining:g}")
        self.ledger.append({"release": release, "eps": eps, "note": note})

    def reuse(self, release: str, by: str) -> None:
        self.ledger.append({"release": release, "eps": 0.0, "note": f"reused by {by} (post-processing)"})


# ---------------------------------------------------------------------------
# Plans
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CompositePlan:
    name: str
    subqueries: tuple[tuple[str, str], ...]  # (alias, task)
    combine: str  # arithmetic over the aliases
    description: str = ""

    def combine_value(self, values: Mapping[str, float]) -> float:
        return _safe_eval(self.combine, values)


PLANS: dict[str, CompositePlan] = {
    "clustering": CompositePlan(
        "clustering", (("T", "triangle"), ("W", "2-star")), "3 * T / W",
        "global clustering coefficient 3 * #triangles / #2-stars",
    ),
    "degree_and_3star": CompositePlan(
        "degree_and_3star", (("deg", "degree"), ("S3", "3-star")), "S3",
        "average degree and 3-star count sharing the noisy degrees",
    ),
    "star_profile": CompositePlan(
        "star_profile", (("S2", "2-star"), ("S3", "3-star"), ("S4", "4-star")), "S3 / S2",
        "2-, 3- and 4-star counts; ratio of 3-stars to 2-stars",
    ),
}


def _safe_eval(expr: str, values: Mapping[str, float]) -> float:
    def ev(node):
        if isinstance(node, ast.Expression):
            return ev(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return float(node.value)
        if isinstance(node, ast.Name) and node.id in values:
            return float(values[node.id])
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            return -ev(node.operand)
        if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div)):
            a, b = ev(node.left), ev(node.right)
            if isinstance(node.op, ast.Add):
                return a + b
            if isinstance(node.op, ast.Sub):
                return a - b
            if isinstance(node.op, ast.Mult):
                return a * b
            return a / b if b != 0 else math.nan
        raise ValueError(f"combine expression may only use + - * / over {sorted(values)}")

    return ev(ast.parse(expr, mode="eval"))


def truth(graph: Graph, plan: CompositePlan) -> dict:
    vals = {alias: reference_counter(task)(graph) for alias, task in plan.subqueries}
    return {**vals, "combined": plan.combine_value(vals)}


# ---------------------------------------------------------------------------
# Execution
# ---------------------------------------------------------------------------


def allocate(plan: CompositePlan, eps: float, r1: float = 0.5, r2: float = 0.2) -> dict:
    programs = {alias: PROGRAMS[task].parse() for alias, task in plan.subqueries}
    need_graph = any(p.uses_rows for p in programs.values())
    need_bound = any(p.needs_degree_bound for p in programs.values())
    degree_from_reports = need_bound
    eps1 = r1 * eps if need_graph else 0.0
    rest = eps - eps1
    eps2 = r2 * rest if need_bound else 0.0
    reported = [a for a, t in plan.subqueries if not (t == "degree" and degree_from_reports)]
    eps3 = (rest - eps2) / len(reported) if reported else 0.0
    return {"programs": programs, "eps1": eps1, "eps2": eps2, "eps3": eps3, "reported": reported,
            "degree_from_reports": degree_from_reports}


def run_composite(graph: Graph, plan: CompositePlan, eps: float, rng: np.random.Generator,
                  mechanism=DEFAULT_MECHANISM, r1: float = 0.5, r2: float = 0.2) -> dict:
    alloc = allocate(plan, eps, r1, r2)
    acct = PrivacyAccountant(eps)
    n = graph.n
    profile = get_mechanism(mechanism)

    noisy = None
    if alloc["eps1"] > 0:
        acct.spend("rr_graph", alloc["eps1"], "randomized response, lower triangle")
        noisy = build_noisy_graph(graph, alloc["eps1"], rng)
    D = None
    reports_deg: list[float] = []
    if alloc["eps2"] > 0:
        acct.spend("noisy_degrees", alloc["eps2"], "deg + Lap(1/eps2) per node")
        reports_deg = [d + laplace_noise(1.0, alloc["eps2"], rng) for d in graph.degrees()]
        D = profile.degree_bound(reports_deg, "3-star").projection_degree  # one shared bound
        if noisy is not None:
            noisy = graph_projection(noisy, D, rng)
    params = PublicParams(n, D=D, dmax=D)
    rows = dict(enumerate(noisy.adj)) if noisy is not None else {}
    projected = [frozenset(project_neighbor_list(graph.neighbors(i), D, rng)) if D is not None else frozenset(graph.adj[i])
                 for i in range(n)]

    estimates: dict[str, float] = {}
    details: dict[str, dict] = {}
    for alias, task in plan.subqueries:
        prog: Program = alloc["programs"][alias]
        if task == "degree" and alloc["degree_from_reports"]:
            acct.reuse("noisy_degrees", alias)
            estimates[alias] = max(0.0, float(np.mean(reports_deg)))
            details[alias] = {"task": task, "source": "noisy_degrees", "eps": 0.0}
            continue
        gs = derive(prog, params).gs
        acct.spend(f"report:{alias}", alloc["eps3"], f"{task}: Lap(GS/eps3), GS = {gs:g}")
        interp = Interpreter(prog)
        total = 0.0
        for i in range(n):
            real = frozenset(graph.adj[i])
            # one projection per node, shared by every subquery (drawn once above)
            env = Env(real, i, rows, n, D=D or 0, dmax=D or 0,
                      projector=lambda s, k, i=i, real=real: projected[i] if s == real and k == D else smallest_projector(s, k))
            total += interp.local(env) + laplace_noise(gs, alloc["eps3"], rng)
        estimates[alias] = interp.aggregate(total, n)
        details[alias] = {"task": task, "source": "laplace_report", "eps": alloc["eps3"], "gs": gs}
    combined = plan.combine_value(estimates)
    return {
        "plan": plan.name, "estimates": estimates, "combined": combined, "details": details,
        "ledger": acct.ledger, "spent": acct.spent, "budget": eps, "D": D,
    }


# ---------------------------------------------------------------------------
# LLM decomposition (the curator proposes, the system checks)
# ---------------------------------------------------------------------------

PLANNER_SYSTEM = (
    "You are the curator agent. You decompose a graph question into counting subqueries that the "
    "system can answer under edge local differential privacy. Answer with JSON only."
)


def planner_prompt(question: str, tasks: Sequence[str]) -> str:
    return (
        f"Available subqueries: {', '.join(tasks)}.\n"
        f"Question: {question}\n"
        "Return JSON {\"subqueries\": [[alias, task], ...], \"combine\": \"<arithmetic over the aliases>\"}."
    )


def check_plan(payload: Mapping, name: str = "llm_plan") -> CompositePlan:
    subs = payload.get("subqueries")
    if not isinstance(subs, list) or not subs:
        raise ValueError("plan needs a nonempty subqueries list")
    pairs = []
    for item in subs:
        if not (isinstance(item, (list, tuple)) and len(item) == 2):
            raise ValueError("each subquery is [alias, task]")
        alias, task = str(item[0]), str(item[1])
        if not re.fullmatch(r"[A-Za-z_]\w*", alias) or task not in PROGRAMS:
            raise ValueError(f"bad subquery {item!r}; tasks: {sorted(PROGRAMS)}")
        pairs.append((alias, task))
    plan = CompositePlan(name, tuple(pairs), str(payload.get("combine", pairs[0][0])))
    plan.combine_value({a: 1.0 for a, _ in pairs})  # validates the expression
    return plan


async def plan_with_llm(model, formatter, question: str) -> CompositePlan:
    text = await chat(model, formatter, PLANNER_SYSTEM, planner_prompt(question, sorted(PROGRAMS)), agent="Curator")
    payload = extract_json(text)
    if payload is None:
        raise ValueError(f"no JSON plan in reply: {text[:200]!r}")
    return check_plan(payload)


def plan_from_keywords(question: str) -> CompositePlan:
    q = question.lower()
    if "clustering" in q or "transitivity" in q:
        return PLANS["clustering"]
    if "star" in q and "profile" in q:
        return PLANS["star_profile"]
    if "degree" in q and "3-star" in q:
        return PLANS["degree_and_3star"]
    raise ValueError("no known plan; use --plan or an LLM planner")


def dumps(result: dict) -> str:
    return json.dumps(result, ensure_ascii=False, indent=2, default=float)
