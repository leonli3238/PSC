"""Empirical sensitivity audit of LLM node agents (ε3 step of PSC; research content 2).

The privacy controller adds ``Lap(GS/ε3)`` to the count a node agent reports,
with ``GS`` derived for the *rule* function ``f`` (:func:`psc.rules.update`).
The value that is actually perturbed is the LLM's parsed reply ``L(x)``, which
carries no sensitivity guarantee.  This module provides the pure functions of
the audit:

* parsing logged update prompts back into node inputs, with a round-trip check
  against :func:`psc.prompts.node_update_prompt`;
* neighbouring inputs: one bit of the private neighbour list ``P`` flipped,
  messages and public parameters unchanged (k-star: ``|P| <= D`` is kept, a
  full list is changed by replacing one element, as a projection coupling
  would);
* pair selection strategies S1 (random), S2 (largest rule change), S3 (error
  inducing) and S4 (boundary cases);
* the privacy loss of ``L(x) + Lap(b)`` against ``L(x') + Lap(b)``: the exact
  sup of the log density ratio of the empirical Laplace mixtures, and a
  Clopper–Pearson lower bound on ε from held-out samples;
* per-pair analysis and grouped summaries.

Only ``P`` is private.  The update prompt also holds the messages, which come
from the (public) noisy graph, and the rule text and state, which are public.
"""

from __future__ import annotations

import math
import re
from dataclasses import asdict, dataclass, field
from typing import Iterable, Mapping, Sequence

import numpy as np

from psc import rules
from psc.graph import kstar_k
from psc.prompts import node_update_prompt, strip_structured

TOL = 1e-9
# Values closer than this are the same LLM output (parsed floats such as 0.5)
VALUE_TOL = 1e-6


# ---------------------------------------------------------------------------
# Node inputs and logged prompts
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class NodeInput:
    """Everything the update prompt of one node contains."""

    task: str
    node_id: int
    neighbors: tuple[int, ...]
    messages: tuple[tuple[int, tuple[int, ...]], ...]
    rule: str
    state_var: str
    state: float

    @property
    def message_dicts(self) -> list[dict]:
        return [{"Sender_ID": s, "Sender_Neighbors": list(nb)} for s, nb in self.messages]

    def with_neighbors(self, neighbors: Iterable[int]) -> "NodeInput":
        return NodeInput(
            self.task, self.node_id, tuple(sorted(int(x) for x in neighbors)), self.messages,
            self.rule, self.state_var, self.state,
        )

    def prompt(self) -> str:
        """The update prompt with the ``<structured_input>`` block (stripped by
        :func:`psc.models.chat` for real models, read by the mock)."""
        return node_update_prompt(
            self.task, self.node_id, list(self.neighbors), self.message_dicts, self.rule, self.state, self.state_var,
        )

    def rule_value(self) -> float:
        return rules.update(self.task, self.neighbors, self.message_dicts)

    @property
    def valid_messages(self) -> int:
        nbrs = set(self.neighbors)
        return sum(s in nbrs for s, _ in self.messages)


_UPDATE_PROMPT = re.compile(
    r"Update rule:\n(?P<rule>.*?)\n\nNode ID: (?P<node>\d+)\nState: 1\. `(?P<var>[^`]+)`: (?P<state>\S+)\n"
    r"Neighbor Information:\nConnected to:\n(?P<nb>[^\n]*)\nReceived Messages:\n(?P<msgs>.*?)\n\n"
    r"Apply the update rule and report the updated `(?P=var)` of this node\. ",
    re.S,
)
_MESSAGE = re.compile(r"Message: 1\. `Sender_ID`: (-?\d+); 2\. `Sender_Neighbors`: \[([^\]]*)\]")


def _ints(text: str) -> tuple[int, ...]:
    text = text.strip()
    return tuple(int(x) for x in text.split(",")) if text else ()


def parse_update_prompt(task: str, user: str) -> NodeInput:
    """Rebuild the node input from a logged update prompt (``transcripts.jsonl``
    stores the prompt without the structured block).  Raises ``ValueError``
    when the prompt does not have the :func:`node_update_prompt` layout or
    does not round-trip exactly."""
    m = _UPDATE_PROMPT.match(user)
    if m is None:
        raise ValueError("not a node update prompt")
    nb = m.group("nb")
    neighbors = () if nb == "(none)" else _ints(nb)
    msgs_text = m.group("msgs")
    messages: list[tuple[int, tuple[int, ...]]] = []
    if msgs_text != "(no messages received)":
        lines = msgs_text.split("\n")
        for line in lines:
            mm = _MESSAGE.fullmatch(line)
            if mm is None:
                raise ValueError(f"unparseable message line {line!r}")
            messages.append((int(mm.group(1)), _ints(mm.group(2))))
    inp = NodeInput(
        task=task,
        node_id=int(m.group("node")),
        neighbors=neighbors,
        messages=tuple(messages),
        rule=m.group("rule"),
        state_var=m.group("var"),
        state=float(m.group("state")),
    )
    if strip_structured(inp.prompt()) != user:
        raise ValueError(f"node {inp.node_id}: rebuilt prompt differs from the logged prompt")
    return inp


# ---------------------------------------------------------------------------
# Neighbouring inputs
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Flip:
    """One-bit change of the private list: add ``vertex``, remove ``vertex``, or
    (full k-star list) replace ``removed`` by ``vertex``."""

    op: str
    vertex: int
    removed: int | None = None
    strategy: str = "S1"
    note: str = ""

    @property
    def key(self) -> tuple:
        return (self.op, self.vertex, self.removed)

    def apply(self, neighbors: Sequence[int]) -> tuple[int, ...]:
        s = set(neighbors)
        if self.op == "add":
            if self.vertex in s:
                raise ValueError(f"add {self.vertex}: already a neighbor")
            s.add(self.vertex)
        elif self.op == "remove":
            if self.vertex not in s:
                raise ValueError(f"remove {self.vertex}: not a neighbor")
            s.discard(self.vertex)
        elif self.op == "replace":
            if self.vertex in s or self.removed not in s:
                raise ValueError(f"replace {self.removed} by {self.vertex}: invalid")
            s.discard(self.removed)
            s.add(self.vertex)
        else:
            raise ValueError(f"unknown op {self.op!r}")
        return tuple(sorted(s))


def projection_bound(task: str, d_max: int | None) -> int | None:
    """``|P| <= D`` holds for k-star tasks (the projected list); degree and
    triangle use the unprojected real list."""
    if task in ("degree", "triangle"):
        return None
    kstar_k(task)  # validates the task name
    return d_max


def rule_delta(inp: NodeInput, flip: Flip) -> float:
    return inp.with_neighbors(flip.apply(inp.neighbors)).rule_value() - inp.rule_value()


def _others(inp: NodeInput, n: int) -> list[int]:
    s = set(inp.neighbors)
    return [v for v in range(n) if v != inp.node_id and v not in s]


def candidate_flips(inp: NodeInput, n: int, bound: int | None) -> list[Flip]:
    """Every add / remove that keeps ``|P| <= bound`` (replacements excluded)."""
    out = [Flip("remove", v) for v in inp.neighbors]
    if bound is None or len(inp.neighbors) < bound:
        out += [Flip("add", v) for v in _others(inp, n)]
    return out


def _random_flip(inp: NodeInput, n: int, bound: int | None, rng: np.random.Generator, strategy: str) -> Flip | None:
    others = _others(inp, n)
    full = bound is not None and len(inp.neighbors) >= bound
    if inp.neighbors and (not others or rng.random() < 0.5):
        return Flip("remove", int(rng.choice(inp.neighbors)), strategy=strategy, note="random remove")
    if not others:
        return None
    v = int(rng.choice(others))
    if full:
        return Flip("replace", v, int(rng.choice(inp.neighbors)), strategy=strategy, note="random add on a full list")
    return Flip("add", v, strategy=strategy, note="random add")


def _max_delta_flip(inp: NodeInput, n: int, bound: int | None, rng: np.random.Generator) -> Flip | None:
    cands = candidate_flips(inp, n, bound)
    if not cands:
        return None
    deltas = np.array([abs(rule_delta(inp, f)) for f in cands])
    best = np.flatnonzero(deltas >= deltas.max() - TOL)
    f = cands[int(rng.choice(best))]
    return Flip(f.op, f.vertex, f.removed, "S2", f"max |Δf| = {deltas.max():g}")


def _middle_flip(inp: NodeInput, n: int, bound: int | None) -> Flip | None:
    """S3 for list-length tasks: remove the middle element of a long list, or
    add the non-neighbour that sorts into its middle."""
    nb = inp.neighbors
    if len(nb) >= 3:
        return Flip("remove", nb[len(nb) // 2], strategy="S3", note="remove the middle element")
    others = _others(inp, n)
    if nb and others and (bound is None or len(nb) < bound):
        mid = nb[len(nb) // 2]
        v = min(others, key=lambda x: abs(x - mid))
        return Flip("add", v, strategy="S3", note="add next to the middle element")
    return None


def _triangle_targeted(inp: NodeInput, n: int) -> Flip | None:
    """S3 for triangles: drop the valid sender whose list overlaps ``P`` most
    (its message must now be discarded although it still overlaps), else make
    the most overlapping non-neighbour sender valid."""
    nbrs = set(inp.neighbors)
    overlap = {s: len(nbrs.intersection(lst)) for s, lst in inp.messages}
    valid = [s for s in overlap if s in nbrs]
    if valid:
        s = max(valid, key=lambda x: (overlap[x], -x))
        return Flip("remove", s, strategy="S3", note=f"remove valid sender with overlap {overlap[s]}")
    invalid = [s for s in overlap if s not in nbrs and s != inp.node_id]
    if invalid:
        s = max(invalid, key=lambda x: (overlap[x], -x))
        return Flip("add", s, strategy="S3", note=f"add sender with overlap {overlap[s]}")
    return None


def _boundary_flip(inp: NodeInput, n: int, bound: int | None, rng: np.random.Generator) -> Flip | None:
    """S4: the k-1/k edge of C(d, k), the full list ``|P| = D`` and the empty
    list (degree and k-star only)."""
    if inp.task == "triangle":
        return None
    d = len(inp.neighbors)
    others = _others(inp, n)
    k = 1 if inp.task == "degree" else kstar_k(inp.task)
    if bound is not None and d >= bound and others:
        return Flip("replace", int(rng.choice(others)), int(rng.choice(inp.neighbors)), "S4", "full list |P| = D")
    if d == k - 1 and others:
        return Flip("add", int(rng.choice(others)), strategy="S4", note=f"{k - 1} -> {k} neighbours")
    if d == k:
        return Flip("remove", int(rng.choice(inp.neighbors)), strategy="S4", note=f"{k} -> {k - 1} neighbours")
    if d == 0 and others:
        return Flip("add", int(rng.choice(others)), strategy="S4", note="empty list")
    return None


def select_flips(inp: NodeInput, n: int, bound: int | None, m: int, rng: np.random.Generator) -> list[Flip]:
    """Up to ``m`` distinct flips in the order S1, S1, S2, S3/S4, then S1."""
    picks: list[Flip] = []
    seen: set[tuple] = set()

    def push(f: Flip | None) -> None:
        if f is not None and f.key not in seen and len(picks) < m:
            seen.add(f.key)
            picks.append(f)

    push(_random_flip(inp, n, bound, rng, "S1"))
    push(_random_flip(inp, n, bound, rng, "S1"))
    if inp.task != "degree":  # every degree flip changes f by exactly 1
        push(_max_delta_flip(inp, n, bound, rng))
    targeted = _boundary_flip(inp, n, bound, rng)
    if targeted is None:
        targeted = _triangle_targeted(inp, n) if inp.task == "triangle" else _middle_flip(inp, n, bound)
    push(targeted)
    for _ in range(4 * m):
        if len(picks) >= m:
            break
        push(_random_flip(inp, n, bound, rng, "S1"))
    return picks


# ---------------------------------------------------------------------------
# Privacy loss of L(x) + Lap(b)
# ---------------------------------------------------------------------------


def _logmeanexp(a: Sequence[float]) -> float:
    m = max(a)
    return m + math.log(sum(math.exp(x - m) for x in a) / len(a))


def mixture_logpdf(z: float, ys: Sequence[float], b: float) -> float:
    """Log density at ``z`` of ``Y + Lap(b)`` with ``Y`` uniform on ``ys``."""
    return _logmeanexp([-abs(z - y) / b for y in ys]) - math.log(2 * b)


def privacy_loss(ys: Sequence[float], ys2: Sequence[float], b: float) -> float:
    """``sup_z |log p(z) / p'(z)|`` for the empirical mixtures of ``ys`` and ``ys2``.

    Between consecutive support points ``p(z) = A e^{z/b} + B e^{-z/b}``, so the
    ratio is a Möbius function of ``e^{2z/b}`` and monotone: the sup is reached
    at a support point or in one of the two tails, which are evaluated exactly.
    Equals ``|y - y'| / b`` for single values.
    """
    pts = sorted(set(ys) | set(ys2))
    best = max(abs(mixture_logpdf(z, ys, b) - mixture_logpdf(z, ys2, b)) for z in pts)
    up = _logmeanexp([y / b for y in ys]) - _logmeanexp([y / b for y in ys2])
    down = _logmeanexp([-y / b for y in ys]) - _logmeanexp([-y / b for y in ys2])
    return max(best, abs(up), abs(down))


def _binom_cdf(k: int, n: int, p: float) -> float:
    if k < 0:
        return 0.0
    if k >= n:
        return 1.0
    return sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(k + 1))


def _bisect(fn, lo: float = 0.0, hi: float = 1.0, iters: int = 80) -> float:
    """Root of a decreasing ``fn`` on ``[lo, hi]``."""
    for _ in range(iters):
        mid = (lo + hi) / 2
        if fn(mid) > 0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def cp_lower(k: int, n: int, alpha: float) -> float:
    """One-sided Clopper–Pearson lower bound: ``P[Bin(n, p) >= k] = alpha``."""
    if k <= 0:
        return 0.0
    return _bisect(lambda p: alpha - (1 - _binom_cdf(k - 1, n, p)))


def cp_upper(k: int, n: int, alpha: float) -> float:
    """One-sided Clopper–Pearson upper bound: ``P[Bin(n, p) <= k] = alpha``."""
    if k >= n:
        return 1.0
    return _bisect(lambda p: _binom_cdf(k, n, p) - alpha)


def wilson(k: int, n: int, z: float = 1.959964) -> tuple[float, float]:
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0.0, center - half), min(1.0, center + half))


def _tail(y: float, t: float, b: float) -> float:
    """``P[y + Lap(b) >= t]``."""
    return 0.5 * math.exp(-(t - y) / b) if t >= y else 1 - 0.5 * math.exp((t - y) / b)


@dataclass(frozen=True)
class EventTest:
    """Event ``S = {s·z >= t}``; ``num`` names the side whose probability is bounded below."""

    sign: int
    num: str
    v: float
    u: float
    t: float


def _log_ratio_from_counts(
    k: float, n: int, k2: float, n2: int, ev: EventTest, b: float, alpha: float | None,
) -> float:
    """Lower bound on ``log P[M(num) ∈ S] / P[M(den) ∈ S]`` from ``k`` of ``n``
    numerator samples ``>= v`` and ``k2`` of ``n2`` denominator samples ``> u``.

    ``P[M(num) ∈ S] >= P[L >= v]·g(v)`` and ``P[M(den) ∈ S] <= ρ + (1-ρ)·g(u)``
    with ``ρ >= P[L' > u]`` and ``g(y) = P[y + Lap(b) >= t]``.  The two
    probabilities get one-sided Clopper–Pearson bounds at ``alpha/2`` each;
    ``alpha=None`` uses the plain fractions.
    """
    if alpha is None:
        q, rho = k / n, k2 / n2
    else:
        q, rho = cp_lower(round(k), n, alpha / 2), cp_upper(round(k2), n2, alpha / 2)
    lo = q * _tail(ev.v, ev.t, b)
    hi = rho + (1 - rho) * _tail(ev.u, ev.t, b)
    return math.log(lo / hi) if lo > 0 and hi > 0 else -math.inf


def _counts(num: Sequence[float], den: Sequence[float], ev: EventTest) -> tuple[int, int]:
    return sum(y >= ev.v - VALUE_TOL for y in num), sum(y > ev.u + VALUE_TOL for y in den)


def _oriented(ev_sign: int, ev_num: str, xs: Sequence[float], xs2: Sequence[float]) -> tuple[list[float], list[float]]:
    """Values multiplied by ``sign`` (``S = {sign·z >= t}``), numerator side first."""
    a = [ev_sign * y for y in xs]
    c = [ev_sign * y for y in xs2]
    return (a, c) if ev_num == "x" else (c, a)


def select_event(
    xs: Sequence[float], xs2: Sequence[float], b: float, n_eval: int, n_eval2: int, alpha: float,
) -> tuple[EventTest | None, float]:
    """The event whose bound would be largest if ``n_eval`` / ``n_eval2``
    evaluation samples showed the selection samples' fractions."""
    best, best_val = None, -math.inf
    for sign in (1, -1):
        for num in ("x", "x2"):
            a, c = _oriented(sign, num, xs, xs2)
            for v in sorted(set(a)):
                for u in sorted(set(c)):
                    if u >= v:
                        continue
                    for step in np.linspace(-2.0, 4.0, 61):
                        ev = EventTest(sign, num, v, u, float(v + step * b))
                        k, k2 = _counts(a, c, ev)
                        val = _log_ratio_from_counts(
                            k / len(a) * n_eval, n_eval, k2 / len(c) * n_eval2, n_eval2, ev, b, alpha,
                        )
                        if val > best_val:
                            best, best_val = ev, val
    return best, best_val


def epsilon_lower_bound(
    sel_x: Sequence[float], sel_x2: Sequence[float], eval_x: Sequence[float], eval_x2: Sequence[float],
    b: float, alpha: float = 0.05,
) -> tuple[float, EventTest | None]:
    """ε lower bound holding with probability ``1 - alpha``: the event is chosen
    on the selection samples and evaluated once on the independent evaluation
    samples (Jagielski et al. 2020 style, with the Laplace part integrated)."""
    if not eval_x or not eval_x2:
        return 0.0, None
    ev, _ = select_event(sel_x, sel_x2, b, len(eval_x), len(eval_x2), alpha)
    if ev is None:
        return 0.0, None
    a, c = _oriented(ev.sign, ev.num, eval_x, eval_x2)
    k, k2 = _counts(a, c, ev)
    return max(0.0, _log_ratio_from_counts(k, len(a), k2, len(c), ev, b, alpha)), ev


# ---------------------------------------------------------------------------
# Pair analysis and summaries
# ---------------------------------------------------------------------------


@dataclass
class PairSpec:
    """One neighbouring pair as planned (before any model call)."""

    pair_id: str
    source: str
    dataset: str
    task: str
    run: int
    node_id: int
    x_key: str
    x2_key: str
    flip: dict
    strategy: str
    gs: float
    eps: tuple[float, float, float]
    bound: int | None
    degree: int
    degree2: int
    messages: int
    valid_messages: int
    valid_messages2: int
    f_x: float
    f_x2: float
    prompt_chars: int
    extra: dict = field(default_factory=dict)

    @property
    def eps3(self) -> float:
        return self.eps[2]

    @property
    def scale(self) -> float:
        return self.gs / self.eps3

    def to_dict(self) -> dict:
        d = asdict(self)
        d["eps"] = list(self.eps)
        return d

    @classmethod
    def from_dict(cls, d: Mapping) -> "PairSpec":
        d = dict(d)
        d["eps"] = tuple(d["eps"])
        return cls(**d)


def _distinct(values: Sequence[float]) -> int:
    out: list[float] = []
    for v in sorted(values):
        if not out or v - out[-1] > VALUE_TOL:
            out.append(v)
    return len(out)


def analyze_pair(
    spec: PairSpec, x: Sequence[Mapping], x2: Sequence[Mapping], alpha: float = 0.05,
) -> dict:
    """Metrics of one pair from its samples (``{"value", "status", "phase"}``;
    ``value`` already holds the fallback count of a failed parse)."""
    sel = [s["value"] for s in x if s.get("phase", "main") == "main"]
    sel2 = [s["value"] for s in x2 if s.get("phase", "main") == "main"]
    fol = [s["value"] for s in x if s.get("phase") == "followup"]
    fol2 = [s["value"] for s in x2 if s.get("phase") == "followup"]
    if not sel or not sel2:
        raise ValueError(f"{spec.pair_id}: no samples")
    gs, eps3, b = spec.gs, spec.eps3, spec.scale
    d_rule = abs(spec.f_x2 - spec.f_x)
    deterministic = _distinct(sel) == 1 and _distinct(sel2) == 1
    d_llm = abs(sel[0] - sel2[0]) if deterministic else max(abs(a - c) for a in sel for c in sel2)
    eps_point = privacy_loss(sel, sel2, b)
    robust = deterministic and d_llm > gs + VALUE_TOL
    row = {
        **spec.to_dict(),
        "eps_rule": eps3 * d_rule / gs,
        "rule_exceeds_gs": d_rule > gs + TOL,
        "samples": len(sel),
        "samples2": len(sel2),
        "values": sel,
        "values2": sel2,
        "deterministic": deterministic,
        "jitter": _distinct(sel) > 1,
        "jitter2": _distinct(sel2) > 1,
        "delta_rule": d_rule,
        "delta_llm": d_llm,
        "excess": d_llm - d_rule,
        "exec_error": sum(abs(v - spec.f_x) > VALUE_TOL for v in sel) / len(sel),
        "exec_error2": sum(abs(v - spec.f_x2) > VALUE_TOL for v in sel2) / len(sel2),
        "failures": sum(s["status"] == "failed" for s in x if s.get("phase", "main") == "main"),
        "failures2": sum(s["status"] == "failed" for s in x2 if s.get("phase", "main") == "main"),
        "eps_point": eps_point,
        "robust_violation": robust,
        "suspect": (not deterministic) and eps_point > eps3 + VALUE_TOL,
        "eps_emp": eps3 * d_llm / gs if deterministic else eps_point,
        "followup": len(fol),
        "followup2": len(fol2),
        "eps_lb": None,
        "confirmed": None,
    }
    if fol and fol2:
        eps_lb, ev = epsilon_lower_bound(sel, sel2, fol, fol2, b, alpha)
        row["eps_lb"] = eps_lb
        row["confirmed"] = eps_lb > eps3
        row["event"] = asdict(ev) if ev is not None else None
    return row


def _quantile(values: Sequence[float], q: float) -> float | None:
    return float(np.quantile(values, q)) if len(values) else None


def summarize(rows: Sequence[Mapping], keys: Sequence[str]) -> list[dict]:
    """Grouped summary; ``keys`` are row fields (``group`` = ``random`` / ``targeted``)."""
    groups: dict[tuple, list[Mapping]] = {}
    for r in rows:
        groups.setdefault(tuple(r[k] for k in keys), []).append(r)
    out = []
    for gk, rs in sorted(groups.items(), key=lambda kv: tuple(str(x) for x in kv[0])):
        n = len(rs)
        robust = sum(r["robust_violation"] for r in rs)
        eps3 = rs[0]["eps"][2]
        e = [r["eps_emp"] for r in rs]
        ratio = [r["eps_emp"] / r["eps"][2] for r in rs]
        det = [r for r in rs if r["deterministic"]]
        followed = [r for r in rs if r["eps_lb"] is not None]
        lo, hi = wilson(robust, n)
        max_robust = max((r["eps_emp"] for r in rs if r["robust_violation"]), default=None)
        out.append({
            **dict(zip(keys, gk)),
            "pairs": n,
            "nodes": len({(r["run"], r["node_id"]) for r in rs}),
            "gs_min": min(r["gs"] for r in rs),
            "gs_max": max(r["gs"] for r in rs),
            "eps3": eps3,
            "rule_exceeds_gs": sum(r["rule_exceeds_gs"] for r in rs),
            "max_eps_rule_over_eps3": max(r["eps_rule"] / r["eps"][2] for r in rs),
            "robust_violations": robust,
            "violation_rate": robust / n,
            "violation_ci": [lo, hi],
            "suspect": sum(r["suspect"] for r in rs),
            "followed_up": len(followed),
            "confirmed": sum(bool(r["confirmed"]) for r in followed),
            "max_eps_lb": max((r["eps_lb"] for r in followed), default=None),
            "eps_emp_max": max(e),
            "eps_emp_p95": _quantile(e, 0.95),
            "eps_emp_median": _quantile(e, 0.5),
            "frac_over_eps3": sum(x > 1 + VALUE_TOL for x in ratio) / n,
            "frac_over_2eps3": sum(x > 2 + VALUE_TOL for x in ratio) / n,
            "max_robust_eps_emp": max_robust,
            "total_eps_lower_bound": (rs[0]["eps"][0] + rs[0]["eps"][1] + max_robust) if max_robust is not None else None,
            "deterministic_pairs": len(det),
            "excess_max": max((r["excess"] for r in det), default=None),
            "exec_error_rate_x": float(np.mean([r["exec_error"] for r in rs])),
            "exec_error_rate_x2": float(np.mean([r["exec_error2"] for r in rs])),
            "jitter_rate_x": float(np.mean([r["jitter"] for r in rs])),
            "jitter_rate_x2": float(np.mean([r["jitter2"] for r in rs])),
            "failure_rate_x": sum(r["failures"] for r in rs) / max(1, sum(r["samples"] for r in rs)),
            "failure_rate_x2": sum(r["failures2"] for r in rs) / max(1, sum(r["samples2"] for r in rs)),
        })
    return out
