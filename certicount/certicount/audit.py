"""Black-box privacy audit of LLM node agents (ε3 step of PSC; research content 2).

The privacy controller adds ``Lap(GS/ε3)`` to the count a node agent reports,
with ``GS`` derived for the *rule* function ``f`` (:func:`psc.rules.update`).
The value that is actually perturbed is the LLM's parsed reply ``L(x)``, which
carries no sensitivity guarantee.  The audit treats the whole step
``M(x) = L(x) + Lap(GS/ε3)`` as a black box and computes a statistical lower
bound on its privacy loss with the standard procedure of the DP auditing
literature:

1. **Neighbouring inputs** (Jagielski et al. 2020; Nasr et al. 2021): the logged
   input ``x`` of a node and ``x'`` with one bit of the private neighbour list
   ``P`` flipped, everything else unchanged.  Two choices of the flipped bit:
   ``S1`` a uniformly random bit (the "natural" setting) and ``S2`` the bit with
   the largest change of the rule function (the worst-case neighbour of the
   reference function, the strongest adversary that does not look at the model).
2. **Monte Carlo trials of the mechanism**: every trial is one independent model
   call followed by one fresh Laplace draw, ``z = L(x) + GS/ε3 · W``.
3. **Threshold test chosen on held-out trials** (Ding et al. 2018, StatDP):
   the event ``{s·z ≥ t}`` (``s = ±1``, either side in the numerator) is chosen
   on the *selection* trials only.
4. **Clopper–Pearson bound on independent evaluation trials** (Jagielski et al.
   2020, Algorithm 2 with δ = 0; Nasr et al. 2021): with one-sided
   Clopper–Pearson bounds at level α/2 each,
   ``ε_lb = log( CP_lower(P[M(x_num) ∈ S]) / CP_upper(P[M(x_den) ∈ S]) )``
   holds with probability ``1 − α``.
5. **Bonferroni** over all audited pairs (done by the caller,
   :mod:`scripts.run_sensitivity_audit`); ``violation = ε_lb > ε3``.

Only ``P`` is private.  The update prompt also holds the messages, which come
from the (public) noisy graph, and the rule text and state, which are public.

Strength of the conclusions.  Everything is conditional on the logged public
history ``h`` (noisy graph, noisy degrees, ``d̂_max``, messages): the audit
measures the loss of the ε3 step given ``h``, which is what the sequential
composition argument needs.  An audit can only refute a privacy claim
(``ε_lb > ε3``); ``ε_lb ≤ ε3`` is no evidence that the claim holds (Ding et al.
2018; Jagielski et al. 2020).  The budgets ε1, ε2 of the earlier steps are upper
bounds and are never added to a lower bound.

The execution error rate, the jitter and the largest observed ``|L(x) − L(x')|``
are reported as descriptive statistics only; no decision depends on them.

References: M. Jagielski, J. Ullman, A. Oprea, "Auditing Differentially Private
Machine Learning: How Private is Private SGD?", NeurIPS 2020.  M. Nasr, S. Song,
A. Thakurta, N. Papernot, N. Carlini, "Adversary Instantiation: Lower Bounds for
Differentially Private Machine Learning", IEEE S&P 2021.  Z. Ding, Y. Wang,
G. Wang, D. Zhang, D. Kifer, "Detecting Violations of Differential Privacy",
ACM CCS 2018.  C. J. Clopper, E. S. Pearson, Biometrika 26(4), 1934.
"""

from __future__ import annotations

import hashlib
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
STRATEGIES = {"S1": "random", "S2": "worst-case"}


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


def _random_flip(inp: NodeInput, n: int, bound: int | None, rng: np.random.Generator) -> Flip | None:
    """S1: a uniformly random bit of ``P`` (a full projected list is changed by a
    replacement, as the projection couples neighbouring lists)."""
    others = _others(inp, n)
    full = bound is not None and len(inp.neighbors) >= bound
    if inp.neighbors and (not others or rng.random() < 0.5):
        return Flip("remove", int(rng.choice(inp.neighbors)), strategy="S1", note="random remove")
    if not others:
        return None
    v = int(rng.choice(others))
    if full:
        return Flip("replace", v, int(rng.choice(inp.neighbors)), strategy="S1", note="random add on a full list")
    return Flip("add", v, strategy="S1", note="random add")


def _worst_case_flip(inp: NodeInput, n: int, bound: int | None, rng: np.random.Generator) -> Flip | None:
    """S2: the bit with the largest change ``|f(x') - f(x)|`` of the reference function."""
    cands = candidate_flips(inp, n, bound)
    if not cands:
        return None
    deltas = np.array([abs(rule_delta(inp, f)) for f in cands])
    best = np.flatnonzero(deltas >= deltas.max() - TOL)
    f = cands[int(rng.choice(best))]
    return Flip(f.op, f.vertex, f.removed, "S2", f"max |Δf| = {deltas.max():g}")


def select_flips(inp: NodeInput, n: int, bound: int | None, m: int, rng: np.random.Generator) -> list[Flip]:
    """Up to ``m`` distinct flips: one worst-case flip (S2; skipped for degree, where
    every flip changes ``f`` by exactly 1) and random flips (S1) for the rest."""
    picks: list[Flip] = []
    seen: set[tuple] = set()

    def push(f: Flip | None) -> None:
        if f is not None and f.key not in seen and len(picks) < m:
            seen.add(f.key)
            picks.append(f)

    push(_random_flip(inp, n, bound, rng))
    if inp.task != "degree":
        push(_worst_case_flip(inp, n, bound, rng))
    for _ in range(4 * m):
        if len(picks) >= m:
            break
        push(_random_flip(inp, n, bound, rng))
    return picks


# ---------------------------------------------------------------------------
# Trials of the mechanism and the Clopper–Pearson bound
# ---------------------------------------------------------------------------


def laplace_draw(key: str, phase: str, rep: int, seed: int = 0) -> float:
    """Standard Laplace draw of one trial, a deterministic function of the trial's
    identity: the noise is independent across trials and reproducible."""
    h = hashlib.sha256(f"{seed}|{key}|{phase}|{rep}".encode()).digest()
    return float(np.random.default_rng(int.from_bytes(h[:8], "little")).laplace())


def mechanism_outputs(samples: Sequence[Mapping], key: str, b: float, seed: int = 0) -> list[float]:
    """``z = L(x) + b·W`` of every trial (``{"value", "phase", "rep"}``)."""
    return [s["value"] + b * laplace_draw(key, s["phase"], int(s["rep"]), seed) for s in samples]


def _binom_cdf(k: int, n: int, p: float) -> float:
    """``P[Bin(n, p) <= k]``, summed in log space (no overflow for large ``n``)."""
    if k < 0:
        return 0.0
    if k >= n:
        return 1.0
    if p <= 0.0:
        return 1.0
    if p >= 1.0:
        return 0.0
    lp, lq = math.log(p), math.log1p(-p)
    c = math.lgamma(n + 1)
    terms = [c - math.lgamma(i + 1) - math.lgamma(n - i + 1) + i * lp + (n - i) * lq for i in range(k + 1)]
    m = max(terms)
    return min(1.0, math.exp(m) * sum(math.exp(t - m) for t in terms))


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


@dataclass(frozen=True)
class ThresholdTest:
    """Event ``S = {sign·z >= t}``; ``num`` (``"x"`` or ``"x2"``) is the side whose
    probability of ``S`` is bounded below, the other side is bounded above."""

    sign: int
    num: str
    t: float


def _oriented(test_sign: int, test_num: str, zs: Sequence[float], zs2: Sequence[float]) -> tuple[list[float], list[float]]:
    a = [test_sign * z for z in zs]
    c = [test_sign * z for z in zs2]
    return (a, c) if test_num == "x" else (c, a)


def epsilon_from_counts(k: int, n: int, k2: int, n2: int, alpha: float) -> float:
    """``log(CP_lower(k/n) / CP_upper(k2/n2))`` with level ``alpha/2`` on each side
    (Jagielski et al. 2020, δ = 0): a lower bound on ε holding with probability
    ``1 - alpha``. ``-inf`` when the numerator bound is 0."""
    lo = cp_lower(k, n, alpha / 2)
    hi = cp_upper(k2, n2, alpha / 2)
    return math.log(lo / hi) if lo > 0 else -math.inf


def select_test(zs: Sequence[float], zs2: Sequence[float], alpha: float) -> ThresholdTest | None:
    """The threshold test with the largest Clopper–Pearson ε bound on the
    selection trials (thresholds at the observed outputs)."""
    best, best_val = None, -math.inf
    for sign in (1, -1):
        for num in ("x", "x2"):
            a, c = _oriented(sign, num, zs, zs2)
            for t in sorted(set(a)):
                k = sum(v >= t for v in a)
                k2 = sum(v >= t for v in c)
                val = epsilon_from_counts(k, len(a), k2, len(c), alpha)
                if val > best_val:
                    best, best_val = ThresholdTest(sign, num, float(t)), val
    if best is None and zs and zs2:  # every bound is -inf: keep a valid (powerless) test
        best = ThresholdTest(1, "x", float(max(zs)))
    return best


def epsilon_lower_bound(
    sel: Sequence[float], sel2: Sequence[float], ev: Sequence[float], ev2: Sequence[float], alpha: float = 0.05,
) -> tuple[float, ThresholdTest | None, dict]:
    """ε lower bound holding with probability ``1 - alpha``: the test is chosen on
    the selection trials ``sel``/``sel2`` and evaluated once on the independent
    evaluation trials ``ev``/``ev2``. Returns ``(ε_lb, test, counts)``."""
    if not ev or not ev2 or not sel or not sel2:
        return 0.0, None, {}
    test = select_test(sel, sel2, alpha)
    if test is None:
        return 0.0, None, {}
    a, c = _oriented(test.sign, test.num, ev, ev2)
    k, k2 = sum(v >= test.t for v in a), sum(v >= test.t for v in c)
    counts = {"k_num": k, "n_num": len(a), "k_den": k2, "n_den": len(c)}
    return max(0.0, epsilon_from_counts(k, len(a), k2, len(c), alpha)), test, counts


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
    spec: PairSpec, x: Sequence[Mapping], x2: Sequence[Mapping], alpha: float = 0.05, seed: int = 0,
) -> dict:
    """Metrics of one pair from its trials (``{"value", "status", "phase", "rep"}``;
    ``phase`` is ``"select"`` or ``"eval"``; ``value`` already holds the fallback
    count of a failed parse).

    ``eps_lb`` is a lower bound on the ε3-step loss given the logged public
    history, holding with probability ``1 - alpha`` (``alpha`` is the per-pair
    level: the caller divides the family level by the number of pairs), and
    ``violation = eps_lb > ε3``. ``eps_lb`` is ``None`` without trials of both phases."""
    sel = [s for s in x if s["phase"] == "select"]
    sel2 = [s for s in x2 if s["phase"] == "select"]
    ev = [s for s in x if s["phase"] == "eval"]
    ev2 = [s for s in x2 if s["phase"] == "eval"]
    values = [s["value"] for s in sel + ev]
    values2 = [s["value"] for s in sel2 + ev2]
    if not values or not values2:
        raise ValueError(f"{spec.pair_id}: no samples")
    gs, eps3, b = spec.gs, spec.eps3, spec.scale
    d_rule = abs(spec.f_x2 - spec.f_x)
    d_llm = max(abs(a - c) for a in set(values) for c in set(values2))
    row = {
        **spec.to_dict(),
        "group": STRATEGIES.get(spec.strategy, spec.strategy),
        "eps_rule": eps3 * d_rule / gs,
        "rule_exceeds_gs": d_rule > gs + TOL,
        "select_trials": (len(sel), len(sel2)),
        "eval_trials": (len(ev), len(ev2)),
        "distinct_values": _distinct(values),
        "distinct_values2": _distinct(values2),
        "jitter": _distinct(values) > 1,
        "jitter2": _distinct(values2) > 1,
        "delta_rule": d_rule,
        "delta_llm_max": d_llm,  # descriptive only
        "exec_error": sum(abs(v - spec.f_x) > VALUE_TOL for v in values) / len(values),
        "exec_error2": sum(abs(v - spec.f_x2) > VALUE_TOL for v in values2) / len(values2),
        "failures": sum(s["status"] == "failed" for s in x),
        "failures2": sum(s["status"] == "failed" for s in x2),
        "alpha_pair": None,
        "eps_lb": None,
        "violation": None,
        "test": None,
        "counts": None,
    }
    if sel and sel2 and ev and ev2:
        z_sel = mechanism_outputs(sel, spec.x_key, b, seed)
        z_sel2 = mechanism_outputs(sel2, spec.x2_key, b, seed)
        z_ev = mechanism_outputs(ev, spec.x_key, b, seed)
        z_ev2 = mechanism_outputs(ev2, spec.x2_key, b, seed)
        eps_lb, test, counts = epsilon_lower_bound(z_sel, z_sel2, z_ev, z_ev2, alpha)
        row.update({
            "alpha_pair": alpha,
            "eps_lb": eps_lb,
            "violation": eps_lb > eps3,
            "test": asdict(test) if test is not None else None,
            "counts": counts,
        })
    return row


def _quantile(values: Sequence[float], q: float) -> float | None:
    return float(np.quantile(values, q)) if len(values) else None


def summarize(rows: Sequence[Mapping], keys: Sequence[str]) -> list[dict]:
    """Grouped summary; ``keys`` are row fields (``group`` = ``random`` / ``worst-case``).

    ``violations`` counts the pairs with ``ε_lb > ε3``; at the family confidence
    of the Bonferroni correction, at least that many audited pairs violate the
    ε3 claim. ``eps_lb_max`` is the largest certified bound (a lower bound on the
    ε3-step loss given one logged public history). Zero violations is no
    evidence of privacy."""
    groups: dict[tuple, list[Mapping]] = {}
    for r in rows:
        groups.setdefault(tuple(r[k] for k in keys), []).append(r)
    out = []
    for gk, rs in sorted(groups.items(), key=lambda kv: tuple(str(x) for x in kv[0])):
        n = len(rs)
        tested = [r for r in rs if r["eps_lb"] is not None]
        lbs = [r["eps_lb"] for r in tested]
        out.append({
            **dict(zip(keys, gk)),
            "pairs": n,
            "nodes": len({(r["run"], r["node_id"]) for r in rs}),
            "gs_min": min(r["gs"] for r in rs),
            "gs_max": max(r["gs"] for r in rs),
            "eps3": rs[0]["eps"][2],
            "rule_exceeds_gs": sum(r["rule_exceeds_gs"] for r in rs),
            "max_eps_rule_over_eps3": max(r["eps_rule"] / r["eps"][2] for r in rs),
            "tested": len(tested),
            "alpha_pair": min((r["alpha_pair"] for r in tested), default=None),
            "violations": sum(bool(r["violation"]) for r in tested),
            "eps_lb_max": max(lbs, default=None),
            "eps_lb_median": _quantile(lbs, 0.5),
            "max_eps_lb_over_eps3": max((r["eps_lb"] / r["eps"][2] for r in tested), default=None),
            "max_delta_llm_over_gs": max(r["delta_llm_max"] / r["gs"] for r in rs),
            "exec_error_rate_x": float(np.mean([r["exec_error"] for r in rs])),
            "exec_error_rate_x2": float(np.mean([r["exec_error2"] for r in rs])),
            "jitter_rate_x": float(np.mean([r["jitter"] for r in rs])),
            "jitter_rate_x2": float(np.mean([r["jitter2"] for r in rs])),
            "failure_rate_x": sum(r["failures"] for r in rs)
            / max(1, sum(r["select_trials"][0] + r["eval_trials"][0] for r in rs)),
            "failure_rate_x2": sum(r["failures2"] for r in rs)
            / max(1, sum(r["select_trials"][1] + r["eval_trials"][1] for r in rs)),
        })
    return out
