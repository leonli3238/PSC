"""Degree violation probe (route B): screen and confirm ε3 violations of the PSC
degree step with a local node model.

Setting.  For ``degree`` PSC perturbs the node's reported count with
``Lap(GS/ε3)``, ``GS = 1``, ``ε3 = ε = 2`` (no noisy graph, no GS optimisation,
see :func:`psc.dp.split_budget`); the node input is only the private neighbour
list (no messages, no ``d̂_max``), the state starts at ``0.0`` and a failed
parse keeps it.  The node input is therefore rebuilt from the graph exactly as
:class:`psc.agents.node_agent.NodeAgent` builds it (same rule text, state and
prompt), and the result does not depend on any public history.

Margin.  The rule function changes by exactly 1 = GS under every flip.  If the
reported values of ``x`` and ``x'`` are always within 1 of each other, the
density ratio of the two Laplace mixtures is at most ``e^{ε3}``: a violation
needs outputs more than 1 apart.  The screen therefore ranks pairs by the
largest observed ``|L(x) − L(x')|`` (descriptive only).

Two stages (see :mod:`certicount.audit` for the statistics):

* **screen** – few calls per input on many pairs (all 452 flips of every hub);
  the observed outputs pick the candidates and, later, the threshold event
  (they are the *selection* trials of the confirmation);
* **confirm** – fresh *evaluation* trials of the chosen pairs only, one
  Clopper–Pearson bound per pair at level ``α/m`` (Bonferroni over the ``m``
  pairs fixed before any evaluation trial), ``violation = ε_lb > ε3``.

Pairs of the same node share the trials of ``x``; Bonferroni holds under any
dependence.  Screen trials are never used as evaluation trials.

Flip families (targeted pairs; exhaustive hub pairs get the same labels as
``tags``): ``R`` random, ``P`` head / middle / tail of the sorted list, ``C``
consecutive ids, ``S`` digit-similar ids (``12 → 112, 121, 21, 13`` …) or ids
similar to the node's own id.  Constructed inputs (``kind = constructed``):
``L`` crosses a length boundary (9→10, 19→20, 49→50, 99→100, 199→200) and
``X`` uses lists of 150–450 ids.  DP must hold for every input, so they are
valid neighbouring pairs, but they are reported apart from the real PM nodes.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence

import numpy as np

from psc.graph import Graph, load_dataset
from psc.library import get_algorithm

from . import DATA_DIR
from .audit import VALUE_TOL, Flip, NodeInput, PairSpec, analyze_pair, summarize

TASK = "degree"
GS = 1.0
EPS = (0.0, 0.0, 2.0)  # degree: ε3 = ε (no RR, no degree release)
DEGREE_BINS = ((1, 10), (11, 30), (31, 60), (61, 120), (121, None))
TIERS = {"hub": (31, None), "mid": (11, 30), "low": (1, 10)}
FAMILIES = ("R", "P", "C", "S", "L", "X", "E")
FAMILY_QUOTA = {"R": 10, "P": 6, "C": 8, "S": 16}
L_BOUNDARIES = (10, 20, 50, 100, 200)
X_LENGTHS = (150, 250, 350, 450)
CATEGORIES = ("count", "number_fallback", "failed")


def degree_bin(d: int) -> str:
    for lo, hi in DEGREE_BINS:
        if d >= lo and (hi is None or d <= hi):
            return f"{lo}-{hi}" if hi is not None else f">{lo - 1}"
    return "0"


def load_graph(dataset: str, data_dir=DATA_DIR) -> Graph:
    return load_dataset(data_dir, dataset)[TASK].graph()


def degree_input(node_id: int, neighbors: Iterable[int]) -> NodeInput:
    """The update input of a PSC degree node (initial ``count = 0.0``, no messages)."""
    algo = get_algorithm(TASK)
    return NodeInput(
        task=TASK, node_id=int(node_id), neighbors=tuple(sorted(int(x) for x in neighbors)), messages=(),
        rule=algo.update, state_var=algo.state_var, state=0.0,
    )


def input_key(node_id: int, neighbors: Sequence[int]) -> str:
    h = hashlib.sha1(",".join(map(str, sorted(neighbors))).encode()).hexdigest()[:12]
    return f"n{node_id}-d{len(neighbors)}-{h}"


# ---------------------------------------------------------------------------
# Flips and their tags
# ---------------------------------------------------------------------------


def digit_similar(a: int, b: int) -> bool:
    """``a`` and ``b`` share their digits in a way a tokenizer is likely to confuse:
    one is the other with a digit added (12 / 112 / 121), the same digits in another
    order (12 / 21), or one digit changed (12 / 13)."""
    if a == b:
        return False
    sa, sb = str(a), str(b)
    if abs(len(sa) - len(sb)) == 1:
        short, long_ = (sa, sb) if len(sa) < len(sb) else (sb, sa)
        return any(long_[:i] + long_[i + 1:] == short for i in range(len(long_)))
    if len(sa) == len(sb):
        if sorted(sa) == sorted(sb):
            return True
        return sum(x != y for x, y in zip(sa, sb)) == 1
    return False


def digit_variants(u: int, n: int) -> list[int]:
    """Ids digit-similar to ``u`` inside ``[0, n)`` (a digit inserted, changed,
    deleted, or two digits swapped)."""
    s = str(u)
    out: set[int] = set()
    for i in range(len(s) + 1):
        for d in "0123456789":
            t = s[:i] + d + s[i:]
            if t[0] != "0":
                out.add(int(t))
    for i in range(len(s)):
        for d in "0123456789":
            t = s[:i] + d + s[i + 1:]
            if t[0] != "0" or len(t) == 1:
                out.add(int(t))
    if len(s) > 1:
        for i in range(len(s)):
            t = s[:i] + s[i + 1:]
            if t[0] != "0" or len(t) == 1:
                out.add(int(t))
        for i in range(len(s)):
            for j in range(i + 1, len(s)):
                t = list(s)
                t[i], t[j] = t[j], t[i]
                if t[0] != "0":
                    out.add(int("".join(t)))
    out.discard(u)
    return sorted(v for v in out if 0 <= v < n)


def flip_tags(neighbors: Sequence[int], node_id: int, flip: Flip) -> list[str]:
    """Descriptive labels of a flip of ``neighbors``."""
    s = sorted(set(neighbors))
    v = flip.vertex
    union = sorted(set(s) | {v})
    pos = union.index(v) / max(1, len(union) - 1)
    tags = ["head" if pos <= 0.1 else "tail" if pos >= 0.9 else "middle"]
    others = set(s) - {v}
    if v - 1 in others or v + 1 in others:
        tags.append("consecutive")
    if any(digit_similar(v, u) for u in others):
        tags.append("digit_sim")
    if abs(v - node_id) <= 1 or digit_similar(v, node_id):
        tags.append("near_self")
    d, d2 = len(s), len(s) + (1 if flip.op == "add" else -1)
    if max(d, d2) % 10 == 0:
        tags.append("len_boundary")
    return tags


def all_flips(neighbors: Sequence[int], node_id: int, n: int) -> list[Flip]:
    s = set(neighbors)
    return [Flip("remove" if v in s else "add", v, strategy="E") for v in range(n) if v != node_id]


def _flip_of(v: int, s: set[int], family: str, note: str = "") -> Flip:
    return Flip("remove" if v in s else "add", v, strategy=family, note=note)


def targeted_flips(
    neighbors: Sequence[int], node_id: int, n: int, rng: np.random.Generator,
    quota: Mapping[str, int] = FAMILY_QUOTA,
) -> list[Flip]:
    """About ``sum(quota)`` flips of the R/P/C/S families (deduplicated; R fills up)."""
    lst = sorted(set(neighbors))
    s = set(lst)
    non = [v for v in range(n) if v != node_id and v not in s]
    out: dict[int, Flip] = {}

    def push(v: int | None, family: str, note: str = "") -> None:
        if v is None or v == node_id or not 0 <= v < n or v in out:
            return
        out[v] = _flip_of(v, s, family, note)

    def take(family: str, cands: Sequence[tuple[int, str]]) -> None:
        cands = list(cands)
        rng.shuffle(cands)
        before = len(out)
        for v, note in cands:
            if len(out) - before >= quota.get(family, 0):
                break
            push(v, family, note)

    # P: head / middle / tail removals and additions
    p: list[tuple[int, str]] = []
    if lst:
        p += [(lst[0], "remove-head"), (lst[len(lst) // 2], "remove-middle"), (lst[-1], "remove-tail")]
        below = [v for v in non if v < lst[0]]
        above = [v for v in non if v > lst[-1]]
        inside = [v for v in non if lst[0] < v < lst[-1]]
        if below:
            p.append((int(rng.choice(below)), "add-head"))
        if inside:
            mid = lst[len(lst) // 2]
            p.append((min(inside, key=lambda v: abs(v - mid)), "add-middle"))
        if above:
            p.append((int(rng.choice(above)), "add-tail"))
    take("P", p)
    # C: extend or split a run of consecutive ids
    c: list[tuple[int, str]] = []
    for u in lst:
        for v in (u - 1, u + 1):
            if v in s or v == node_id or not 0 <= v < n:
                continue
            c.append((v, "add-next-to"))
        if u - 1 in s and u + 1 in s:
            c.append((u, "remove-inside-run"))
    take("C", c)
    # S: digit-similar to a neighbour or to the node id
    sc: list[tuple[int, str]] = []
    for u in lst + [node_id]:
        for v in digit_variants(u, n):
            sc.append((v, f"similar-{u}"))
    for u in lst:
        if any(digit_similar(u, w) for w in lst if w != u):
            sc.append((u, "remove-similar"))
    take("S", sc)
    # R: uniform over all flips, fills the rest
    target = sum(quota.values())
    tries = 0
    while len(out) < min(target, n - 1) and tries < 50 * target:
        tries += 1
        push(int(rng.integers(0, n)), "R")
    return list(out.values())


# ---------------------------------------------------------------------------
# Plan
# ---------------------------------------------------------------------------


@dataclass
class _Builder:
    dataset: str
    inputs: dict
    pairs: list

    def add_input(self, node_id: int, neighbors: Sequence[int], kind: str) -> str:
        key = input_key(node_id, neighbors)
        self.inputs.setdefault(key, {"node_id": int(node_id), "neighbors": sorted(int(x) for x in neighbors), "kind": kind})
        return key

    def add_pair(self, node_id: int, neighbors: Sequence[int], flip: Flip, *, kind: str, tier: str,
                 family: str, random_ref: bool = False) -> None:
        x_key = self.add_input(node_id, neighbors, kind)
        nb2 = flip.apply(neighbors)
        x2_key = self.add_input(node_id, nb2, kind)
        pid = f"{x_key}|{flip.op}{flip.vertex}"
        self.pairs.append({
            "pair_id": pid, "node_id": int(node_id), "kind": kind, "tier": tier, "family": family,
            "x_key": x_key, "x2_key": x2_key, "flip": {"op": flip.op, "vertex": flip.vertex, "note": flip.note},
            "tags": flip_tags(neighbors, node_id, flip), "degree": len(neighbors), "degree2": len(nb2),
            "bin": degree_bin(len(neighbors)), "random_ref": random_ref,
        })


def _tier_nodes(degrees: Sequence[int], lo: int, hi: int | None) -> list[int]:
    return [i for i, d in enumerate(degrees) if d >= lo and (hi is None or d <= hi)]


def build_plan(
    graph: Graph, dataset: str, *, seed: int = 0, mid_nodes: int = 30, low_nodes: int = 12,
    hub_flips: int | None = None, quota: Mapping[str, int] = FAMILY_QUOTA, constructed: bool = True,
    random_per_node: int = 1,
) -> dict:
    """All screened pairs.  ``hub_flips = None``: every flip of every hub
    (degree > 30); else ``hub_flips`` targeted flips per hub (half R, half P/C/S).
    ``random_per_node`` uniform flips per selected real node are marked
    ``random_ref`` (the fixed set compared across models)."""
    rng = np.random.default_rng(seed)
    degrees = graph.degrees()
    n = graph.n
    b = _Builder(dataset, {}, [])
    hubs = _tier_nodes(degrees, *TIERS["hub"])
    mids = _tier_nodes(degrees, *TIERS["mid"])
    lows = _tier_nodes(degrees, *TIERS["low"])
    mids = sorted(rng.choice(mids, size=min(mid_nodes, len(mids)), replace=False).tolist())
    lows = sorted(rng.choice(lows, size=min(low_nodes, len(lows)), replace=False).tolist())
    for i in hubs:
        nb = graph.neighbors(i)
        if hub_flips is None:
            for f in all_flips(nb, i, n):
                b.add_pair(i, nb, f, kind="real", tier="hub", family="E")
        else:
            half = max(1, hub_flips // 2)
            scale = (hub_flips - half) / max(1, sum(v for k, v in quota.items() if k != "R"))
            q = {k: (half if k == "R" else max(1, round(v * scale))) for k, v in quota.items()}
            for f in targeted_flips(nb, i, n, rng, q):
                b.add_pair(i, nb, f, kind="real", tier="hub", family=f.strategy)
    for tier, nodes in (("mid", mids), ("low", lows)):
        for i in nodes:
            nb = graph.neighbors(i)
            for f in targeted_flips(nb, i, n, rng, quota):
                b.add_pair(i, nb, f, kind="real", tier=tier, family=f.strategy)
    # fixed random reference pairs (one uniform flip per selected real node)
    have = {p["pair_id"]: p for p in b.pairs}
    for i in hubs + mids + lows:
        nb = graph.neighbors(i)
        flips = all_flips(nb, i, n)
        for j in rng.choice(len(flips), size=min(random_per_node, len(flips)), replace=False).tolist():
            f = flips[j]
            pid = f"{input_key(i, nb)}|{f.op}{f.vertex}"
            if pid in have:
                have[pid]["random_ref"] = True
            else:
                tier = "hub" if i in hubs else "mid" if i in mids else "low"
                b.add_pair(i, nb, Flip(f.op, f.vertex, strategy="R"), kind="real", tier=tier, family="R", random_ref=True)
                have[b.pairs[-1]["pair_id"]] = b.pairs[-1]
    if constructed:
        anchors = sorted(range(n), key=lambda i: -degrees[i])[:2]
        for i in anchors:
            pool = [v for v in range(n) if v != i]
            for size in L_BOUNDARIES:
                if size > len(pool):
                    continue
                for variant in range(2):
                    base = sorted(rng.choice(pool, size=size - 1, replace=False).tolist())
                    rest = [v for v in pool if v not in set(base)]
                    sim = [v for v in rest if any(digit_similar(v, u) for u in base)]
                    v = int(rng.choice(sim if variant and sim else rest))
                    b.add_pair(i, base, Flip("add", v, strategy="L", note=f"{size - 1}->{size}"),
                               kind="constructed", tier="constructed", family="L")
            for size in X_LENGTHS:
                if size > len(pool):
                    continue
                base = sorted(rng.choice(pool, size=size, replace=False).tolist())
                q = {"R": 2, "P": 2, "S": 2}
                for f in targeted_flips(base, i, n, rng, q):
                    b.add_pair(i, base, f, kind="constructed", tier="constructed", family="X")
    for p in b.pairs:
        p["f_x"] = float(p["degree"])
        p["f_x2"] = float(p["degree2"])
    plan = {
        "dataset": dataset, "task": TASK, "gs": GS, "eps": list(EPS), "n": n, "seed": seed,
        "params": {"mid_nodes": mid_nodes, "low_nodes": low_nodes, "hub_flips": hub_flips, "quota": dict(quota),
                   "constructed": constructed, "random_per_node": random_per_node},
        "nodes": {"hub": hubs, "mid": mids, "low": lows},
        "inputs": b.inputs, "pairs": b.pairs,
    }
    plan["plan_hash"] = plan_hash(plan)
    return plan


def plan_hash(plan: Mapping) -> str:
    body = json.dumps({"inputs": plan["inputs"], "pairs": [p["pair_id"] for p in plan["pairs"]]}, sort_keys=True)
    return hashlib.sha256(body.encode()).hexdigest()[:16]


def plan_inputs(plan: Mapping) -> dict[str, NodeInput]:
    return {k: degree_input(v["node_id"], v["neighbors"]) for k, v in plan["inputs"].items()}


def check_plan(plan: Mapping) -> None:
    """Every pair is one flipped bit of the private list, never the node itself."""
    inputs = plan["inputs"]
    for p in plan["pairs"]:
        a, c = set(inputs[p["x_key"]]["neighbors"]), set(inputs[p["x2_key"]]["neighbors"])
        diff = a ^ c
        if len(diff) != 1:
            raise ValueError(f"{p['pair_id']}: lists differ in {len(diff)} ids")
        v = next(iter(diff))
        if v != p["flip"]["vertex"] or v == p["node_id"] or not 0 <= v < plan["n"]:
            raise ValueError(f"{p['pair_id']}: invalid flipped id {v}")
        if p["node_id"] in a or p["node_id"] in c:
            raise ValueError(f"{p['pair_id']}: node in its own list")
        if abs(p["f_x2"] - p["f_x"]) != GS:
            raise ValueError(f"{p['pair_id']}: rule change {p['f_x2'] - p['f_x']}")


# ---------------------------------------------------------------------------
# Screen ranking
# ---------------------------------------------------------------------------


def _values(samples: Iterable[Mapping]) -> list[float]:
    return [float(s["value"]) for s in samples]


def screen_pair(pair: Mapping, xs: Sequence[Mapping], x2s: Sequence[Mapping]) -> dict:
    """Descriptive screen statistics of one pair (no statistical claim)."""
    v, v2 = _values(xs), _values(x2s)
    row = {k: pair[k] for k in ("pair_id", "node_id", "kind", "tier", "family", "bin", "degree", "degree2",
                                "tags", "flip", "random_ref")}
    if not v or not v2:
        return {**row, "complete": False}
    delta_max = max(abs(a - c) for a in v for c in v2)
    far = sum(abs(a - c) > GS + VALUE_TOL for a in v for c in v2) / (len(v) * len(v2))
    statuses = Counter(s["status"] for s in list(xs) + list(x2s))
    row.update({
        "complete": True, "values": v, "values2": v2, "delta_max": delta_max, "frac_far": far,
        "candidate": delta_max > GS + VALUE_TOL,
        "exec_error": sum(abs(a - pair["f_x"]) > VALUE_TOL for a in v) / len(v),
        "exec_error2": sum(abs(a - pair["f_x2"]) > VALUE_TOL for a in v2) / len(v2),
        "jitter": len({round(a, 6) for a in v}) > 1 or len({round(a, 6) for a in v2}) > 1,
        "statuses": dict(statuses),
    })
    return row


def _rank_key(r: Mapping) -> tuple:
    return (-r["delta_max"], -r["frac_far"], r["pair_id"])


def rank_candidates(rows: Sequence[Mapping]) -> list[dict]:
    cands = [dict(r) for r in rows if r.get("candidate")]
    cands.sort(key=_rank_key)
    return cands


def top_pairs(cands: Sequence[Mapping], m: int, per_node: int | None = None) -> list[str]:
    """The first ``m`` ranked candidates, at most ``per_node`` per input ``x``
    (one real node = one input; a constructed list is its own input)."""
    taken: Counter = Counter()
    out: list[str] = []
    for c in cands:
        if len(out) >= m:
            break
        x = c["pair_id"].split("|", 1)[0]
        if per_node is not None and taken[x] >= per_node:
            continue
        taken[x] += 1
        out.append(c["pair_id"])
    return out


def node_level_pairs(plan: Mapping, screen_rows: Sequence[Mapping]) -> tuple[list[str], list[dict]]:
    """Node-level design: for every selected real node of the plan, its most
    suspicious screened pair (largest observed |Δ|) if that pair is a candidate
    (|Δ| > GS).  Returns the pair ids and the node universe (every selected
    node, with or without a candidate: the denominator of the node shares)."""
    real_x: dict[int, str] = {}
    for p in plan["pairs"]:
        if p["kind"] == "real":
            real_x.setdefault(p["node_id"], p["x_key"])
    by_node: dict[int, list[Mapping]] = {}
    for r in screen_rows:
        if r.get("kind") == "real" and r.get("complete"):
            by_node.setdefault(r["node_id"], []).append(r)
    ids, universe = [], []
    for tier in ("hub", "mid", "low"):
        for node in plan["nodes"][tier]:
            x = real_x.get(node)
            deg = len(plan["inputs"][x]["neighbors"]) if x else None
            rows = sorted(by_node.get(node, []), key=_rank_key)
            best = rows[0] if rows else None
            cand = bool(best and best.get("candidate"))
            universe.append({
                "node_id": node, "tier": tier, "degree": deg, "bin": degree_bin(deg or 0),
                "screened_pairs": len(rows), "candidate": cand,
                "pair_id": best["pair_id"] if cand else None,
                "delta_max": best["delta_max"] if best else None,
            })
            if cand:
                ids.append(best["pair_id"])
    return ids, universe


def node_table(universe: Sequence[Mapping], rows: Sequence[Mapping]) -> list[dict]:
    """Per degree bin: selected nodes, nodes with a candidate, nodes with a
    confirmed violation.  ``confirmed_share`` is a lower bound on the share of
    violating nodes among the selected ones (a node that is not confirmed may
    still violate)."""
    viol = {r["pair_id"] for r in rows if r.get("violation")}
    tested = {r["pair_id"] for r in rows if r.get("eps_lb") is not None}
    order = [degree_bin(lo) for lo, _ in DEGREE_BINS]
    groups: dict[str, list[Mapping]] = {}
    for u in universe:
        groups.setdefault(u["bin"], []).append(u)
    out = []
    for b in sorted(groups, key=lambda x: order.index(x) if x in order else 99) + ["all"]:
        us = list(universe) if b == "all" else groups[b]
        n = len(us)
        out.append({
            "bin": b, "nodes": n, "with_candidate": sum(u["candidate"] for u in us),
            "tested": sum(u["pair_id"] in tested for u in us),
            "confirmed": sum(u["pair_id"] in viol for u in us),
            "confirmed_share": sum(u["pair_id"] in viol for u in us) / n if n else None,
        })
    return out


def family_recompute(sets: Mapping[str, Sequence[Mapping]], family_alpha: float) -> tuple[list[dict], dict]:
    """Bonferroni over every tested pair of all ``sets`` together: each pair's
    bound is recomputed at ``family_alpha / M`` from its stored evaluation counts.
    The threshold test was chosen on selection trials only, so recomputing the
    bound at another level stays valid; the bounds only shrink."""
    from .audit import epsilon_from_counts

    tested = [(name, r) for name, rs in sets.items() for r in rs if r.get("counts")]
    m = len(tested)
    alpha = family_alpha / m if m else None
    out: dict[str, dict] = {}
    for name, r in tested:
        c = r["counts"]
        e = max(0.0, epsilon_from_counts(c["k_num"], c["n_num"], c["k_den"], c["n_den"], alpha))
        o = out.setdefault(name, {"set": name, "tested": 0, "violations_design": 0, "violations_family": 0,
                                  "violations_family_real_count": 0, "eps_lb_family_max": 0.0})
        o["tested"] += 1
        o["violations_design"] += bool(r.get("violation"))
        v = e > r["eps"][2]
        o["violations_family"] += v
        o["violations_family_real_count"] += v and r.get("kind") == "real" and r.get("category") == "count"
        o["eps_lb_family_max"] = max(o["eps_lb_family_max"], e)
    rows = list(out.values())
    total = {"family_alpha": family_alpha, "M": m, "alpha_pair": alpha,
             "violations_family": sum(o["violations_family"] for o in rows),
             "violations_family_real_count": sum(o["violations_family_real_count"] for o in rows)}
    return rows, total


# ---------------------------------------------------------------------------
# Confirmation analysis
# ---------------------------------------------------------------------------


def pair_spec(plan: Mapping, pair: Mapping, prompt_chars: int = 0) -> PairSpec:
    return PairSpec(
        pair_id=pair["pair_id"], source=pair["kind"], dataset=plan["dataset"], task=TASK, run=0,
        node_id=pair["node_id"], x_key=pair["x_key"], x2_key=pair["x2_key"], flip=dict(pair["flip"]),
        strategy=pair["family"], gs=GS, eps=tuple(plan["eps"]), bound=None, degree=pair["degree"],
        degree2=pair["degree2"], messages=0, valid_messages=0, valid_messages2=0, f_x=pair["f_x"],
        f_x2=pair["f_x2"], prompt_chars=prompt_chars,
        extra={"tier": pair["tier"], "bin": pair["bin"], "tags": pair["tags"], "kind": pair["kind"],
               "random_ref": pair.get("random_ref", False)},
    )


def as_trials(samples: Iterable[Mapping], phase: str) -> list[dict]:
    """Samples of a stage as :func:`certicount.audit.analyze_pair` trials.  Screen
    and extra selection trials both become ``select`` (with disjoint ``rep``s, so
    their Laplace draws are distinct); evaluation trials stay ``eval``."""
    offset = {"screen": 0, "select": 100_000, "eval": 0}[phase]
    target = "eval" if phase == "eval" else "select"
    return [{"value": s["value"], "status": s["status"], "phase": target, "rep": int(s["rep"]) + offset}
            for s in samples]


def violation_category(ev: Sequence[Mapping], ev2: Sequence[Mapping]) -> str:
    """Strict class of a pair from its evaluation trials: ``count`` only when every
    trial of both sides was parsed from the JSON key."""
    st = {s["status"] for s in list(ev) + list(ev2)}
    if "failed" in st:
        return "failed"
    if "number" in st:
        return "number_fallback"
    return "count"


def analyze(plan: Mapping, pair: Mapping, sel: Sequence[Mapping], sel2: Sequence[Mapping],
            ev: Sequence[Mapping], ev2: Sequence[Mapping], alpha_pair: float, seed: int | str) -> dict:
    """``sel``/``ev`` are trials already passed through :func:`as_trials`."""
    row = analyze_pair(pair_spec(plan, pair), list(sel) + list(ev), list(sel2) + list(ev2), alpha_pair, seed)
    row.update({
        "kind": pair["kind"], "tier": pair["tier"], "bin": pair["bin"], "family": pair["family"],
        "tags": pair["tags"], "random_ref": pair.get("random_ref", False),
        "category": violation_category(ev, ev2) if row["violation"] else None,
        "eval_status": dict(Counter(s["status"] for s in list(ev) + list(ev2))),
    })
    return row


def summary_tables(rows: Sequence[Mapping]) -> dict:
    out = {}
    if rows:
        out["by_kind_bin_family"] = summarize(rows, ["kind", "bin", "family"])
        out["by_kind_tier"] = summarize(rows, ["kind", "tier"])
    viol = [r for r in rows if r.get("violation")]
    out["violations_by_category"] = [
        {"kind": k, "bin": b, "category": c, "violations": n}
        for (k, b, c), n in sorted(Counter((r["kind"], r["bin"], r["category"]) for r in viol).items())
    ]
    lbs = [r["eps_lb"] for r in rows if r.get("eps_lb") is not None]
    out["overall"] = {
        "pairs": len(rows), "tested": len(lbs), "violations": len(viol),
        "violations_real_count": sum(r["kind"] == "real" and r["category"] == "count" for r in viol),
        "eps_lb_max": max(lbs, default=None),
        "eps_lb_median": float(np.median(lbs)) if lbs else None,
        "max_delta_llm": max((r["delta_llm_max"] for r in rows), default=None),
    }
    return out


def violation_rate_upper(violations: int, tested: int, alpha: float = 0.05) -> float | None:
    """One-sided Clopper–Pearson upper bound on the share of violating pairs among
    pairs drawn like the tested ones (descriptive, for "no violation" reports)."""
    from .audit import cp_upper

    return cp_upper(violations, tested, alpha) if tested else None


__all__ = [
    "CATEGORIES", "DEGREE_BINS", "EPS", "FAMILIES", "GS", "TASK", "TIERS", "all_flips", "analyze", "as_trials",
    "build_plan", "check_plan", "degree_bin", "degree_input", "digit_similar", "digit_variants", "family_recompute",
    "flip_tags", "input_key", "load_graph", "node_level_pairs", "node_table", "pair_spec", "plan_hash", "plan_inputs",
    "rank_candidates", "screen_pair", "summary_tables", "targeted_flips", "top_pairs", "violation_category",
    "violation_rate_upper",
]
