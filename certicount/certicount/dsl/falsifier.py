"""Falsifier (verification layer L2): search small graphs for sensitivity counterexamples.

Exhaustive mode enumerates, for node ``0`` on ``n`` vertices, every public
graph with maximum degree ``<= dmax`` (symmetric, or arbitrary rows for the
asymmetric ablation), every private set ``P`` (``0 not in P``) and every flip of
one vertex, and reports the largest ``|f(P) - f(P xor {v})|`` with a witness.
Random mode samples the same space on larger graphs. A falsifier can only
refute a claimed GS; the bound used for the noise comes from the deriver.
"""

from __future__ import annotations

import itertools
import random
from dataclasses import dataclass
from typing import Iterator

from .lang import Env, Interpreter, Program


@dataclass
class Counterexample:
    max_delta: float
    private: tuple[int, ...] = ()
    vertex: int | None = None
    rows: tuple[tuple[int, ...], ...] = ()
    checked: int = 0

    def to_dict(self) -> dict:
        return {
            "max_delta": self.max_delta, "private": list(self.private), "vertex": self.vertex,
            "rows": [list(r) for r in self.rows], "checked": self.checked,
        }


def symmetric_graphs(n: int, dmax: int) -> Iterator[list[frozenset]]:
    pairs = list(itertools.combinations(range(n), 2))
    for mask in range(1 << len(pairs)):
        adj = [set() for _ in range(n)]
        for b, (u, v) in enumerate(pairs):
            if mask >> b & 1:
                adj[u].add(v)
                adj[v].add(u)
        if all(len(a) <= dmax for a in adj):
            yield [frozenset(a) for a in adj]


def asymmetric_rows(n: int, dmax: int, samples: int, seed: int = 0) -> Iterator[list[frozenset]]:
    """Rows of arbitrary subsets (size <= dmax, no self loops): ``G'`` need not be symmetric."""
    rnd = random.Random(seed)
    for _ in range(samples):
        yield [frozenset(rnd.sample([u for u in range(n) if u != j], rnd.randint(0, min(dmax, n - 1)))) for j in range(n)]


def random_symmetric_graphs(n: int, dmax: int, samples: int, seed: int = 0) -> Iterator[list[frozenset]]:
    rnd = random.Random(seed)
    for _ in range(samples):
        adj = [set() for _ in range(n)]
        pairs = list(itertools.combinations(range(n), 2))
        rnd.shuffle(pairs)
        p = rnd.random()
        for u, v in pairs:
            if rnd.random() < p and len(adj[u]) < dmax and len(adj[v]) < dmax:
                adj[u].add(v)
                adj[v].add(u)
        yield [frozenset(a) for a in adj]


def max_delta(
    program: Program, n: int, dmax: int, graphs, D: int | None = None,
    privates: int | None = None, seed: int = 0,
) -> Counterexample:
    """Largest change of the local count of node 0 over ``graphs``.

    ``privates=None`` enumerates every ``P``; otherwise ``privates`` random
    sets are drawn per graph.
    """
    interp = Interpreter(program)
    D = dmax if D is None else D
    others = list(range(1, n))
    rnd = random.Random(seed)
    best = Counterexample(0.0)
    checked = 0
    for rows in graphs:
        def f(p: frozenset) -> float:
            return interp.local(Env(p, 0, dict(enumerate(rows)), n, D=D, dmax=dmax))

        if privates is None:
            sets = (frozenset(c) for r in range(n) for c in itertools.combinations(others, r))
        else:
            sets = (frozenset(v for v in others if rnd.random() < rnd.random()) for _ in range(privates))
        for p in sets:
            y = f(p)
            for v in others:
                d = abs(f(p ^ {v}) - y)
                checked += 1
                if d > best.max_delta + 1e-12:
                    best = Counterexample(d, tuple(sorted(p)), v, tuple(tuple(sorted(r)) for r in rows))
    best.checked = checked
    return best


def falsify(program: Program, claimed_gs: float, n: int = 5, dmax: int = 3, D: int | None = None,
            symmetric: bool = True, samples: int = 2000, seed: int = 0) -> tuple[bool, Counterexample]:
    """``(refuted, witness)``: exhaustive on symmetric graphs, sampled otherwise."""
    if program.uses_rows:
        graphs = symmetric_graphs(n, dmax) if symmetric else asymmetric_rows(n, dmax, samples, seed)
    else:
        graphs = [[frozenset() for _ in range(n)]]
    ce = max_delta(program, n, dmax, graphs, D=D)
    return ce.max_delta > claimed_gs + 1e-9, ce
