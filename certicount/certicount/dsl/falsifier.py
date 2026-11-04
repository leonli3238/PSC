"""Falsifier (verification layer L2): search small graphs for sensitivity counterexamples.

Exhaustive mode enumerates, for node ``0`` on ``n`` vertices, every public
graph with maximum degree ``<= dmax`` (symmetric, or arbitrary rows for the
asymmetric ablation), every private set ``P`` (``0 not in P``) and every flip of
one vertex, and reports the largest ``|f(P) - f(P xor {v})|`` with a witness.
Random mode samples the graphs (with every ``P`` and flip on each) on larger
graphs. A falsifier can only refute a claimed GS; the bound used for the noise
comes from the deriver.

:func:`check_derivation` derives the GS at the falsifier's own public
parameters and searches for a flip that exceeds it. The design loop rejects a
program it refutes (:func:`certicount.dsl.designer.check_draft`), and the fuzz
test runs it on random programs (:mod:`certicount.dsl.fuzz`).
"""

from __future__ import annotations

import functools
import itertools
import random
from dataclasses import asdict, dataclass
from typing import Iterator

from .lang import Env, Interpreter, Program
from .sensitivity import Facts, PublicParams, SensitivityError, derive


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


@functools.lru_cache(maxsize=None)
def _all_symmetric_graphs(n: int, dmax: int) -> tuple[tuple[frozenset, ...], ...]:
    return tuple(tuple(g) for g in symmetric_graphs(n, dmax))


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
    every_set = [frozenset(c) for r in range(n) for c in itertools.combinations(others, r)] if privates is None else []
    rnd = random.Random(seed)
    best = Counterexample(0.0)
    checked = 0
    for rows in graphs:
        table = dict(enumerate(rows))

        def f(p: frozenset) -> float:
            return interp.local(Env(p, 0, table, n, D=D, dmax=dmax))

        if privates is None:
            values = {p: f(p) for p in every_set}  # each P once; its flips are other P
            sets = every_set
        else:
            values = None
            sets = [frozenset(v for v in others if rnd.random() < rnd.random()) for _ in range(privates)]
        for p in sets:
            y = values[p] if values is not None else f(p)
            for v in others:
                d = abs((values[p ^ {v}] if values is not None else f(p ^ {v})) - y)
                checked += 1
                if d > best.max_delta + 1e-12:
                    best = Counterexample(d, tuple(sorted(p)), v, tuple(tuple(sorted(r)) for r in rows))
    best.checked = checked
    return best


def falsify(program: Program, claimed_gs: float, n: int = 5, dmax: int = 3, D: int | None = None,
            symmetric: bool = True, samples: int = 2000, seed: int = 0,
            exhaustive: bool = True) -> tuple[bool, Counterexample]:
    """``(refuted, witness)``: on every symmetric graph (``exhaustive``), on
    ``samples`` random symmetric graphs, or on ``samples`` asymmetric rows."""
    if not program.uses_rows:
        graphs = [[frozenset() for _ in range(n)]]
    elif not symmetric:
        graphs = asymmetric_rows(n, dmax, samples, seed)
    elif exhaustive:
        graphs = _all_symmetric_graphs(n, dmax)
    else:
        graphs = random_symmetric_graphs(n, dmax, samples, seed)
    ce = max_delta(program, n, dmax, graphs, D=D)
    return ce.max_delta > claimed_gs + 1e-9, ce


@dataclass
class DerivationCheck:
    """The GS derived at ``PublicParams(n, dmax, dmax)`` against the falsifier."""

    n: int
    dmax: int
    samples: int | None  # random symmetric graphs; None: every symmetric graph
    gs: float | None = None
    witness: Counterexample | None = None
    skipped: str | None = None  # the deriver rejects the program at these parameters
    error: str | None = None  # the interpreter failed on a test graph

    @property
    def refuted(self) -> bool:
        return self.gs is not None and self.witness is not None and self.witness.max_delta > self.gs + 1e-9

    @property
    def tight(self) -> bool:
        return self.gs is not None and self.witness is not None and abs(self.witness.max_delta - self.gs) <= 1e-9

    def to_dict(self) -> dict:
        out = asdict(self)
        out.update(refuted=self.refuted, tight=self.tight)
        return out


def check_derivation(program: Program, n: int = 5, dmax: int = 3, samples: int | None = None, seed: int = 0,
                     facts: Facts | None = None) -> DerivationCheck:
    """Derive the GS at small public parameters (``D = dmax``) and search for a
    flip that exceeds it on every symmetric graph (``samples=None``) or on
    ``samples`` random ones (every ``P`` and flip of node 0 on each)."""
    out = DerivationCheck(n, dmax, samples)
    try:
        out.gs = derive(program, PublicParams(n, D=dmax, dmax=dmax), facts).gs
    except SensitivityError as exc:
        out.skipped = str(exc)
        return out
    try:
        _, out.witness = falsify(program, out.gs, n=n, dmax=dmax, samples=samples or 0, seed=seed,
                                 exhaustive=samples is None)
    except (ArithmeticError, ValueError) as exc:
        out.error = f"{type(exc).__name__}: {exc}"
    return out
