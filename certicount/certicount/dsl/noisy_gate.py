"""Noise-aware utility gate: run a draft through the real randomized release on public graphs.

The exact utility test (:mod:`certicount.dsl.utility`) runs a program on the true
graph, where the public release equals the private data (``N(self) = P``, ``A`` = the
0/1 adjacency). A program that reads the release as if it were the graph passes it,
is certified (its GS can even be 0), and is useless at run time: with ε1 = 1 every
noisy row of a 453-node graph holds about 120 fake neighbours (A3/CS2/CS3: estimates
30-100 times the truth).

Here the draft runs through :func:`certicount.dsl.ground_truth.dp_execute` -- the same
randomized response, degree bound, projection and (per-node architecture) unbiased
matrix as a real run -- on public synthetic graphs with the public number of nodes,
and the *noise-free* estimate (the final Laplace draws of ε3 left out) is compared with
the exact count. The gate measures the systematic error the release introduces into
the program, not the Laplace noise (that is the sensitivity's job, already certified).

Graphs: Holme-Kim powerlaw-cluster graphs (heavy-tailed degrees and triangles, as in
social graphs). Sparse Erdős-Rényi graphs separate correct and wrong programs poorly
(few triangles, no hubs) and are not used. Everything is public: ``n``, ε, the budget
split and the graph models; no private data and no privacy budget is used.

Criterion: the median (over ``reps`` releases) relative error of the noise-free estimate
is at most ``tau`` on every graph. On the 131 drafts of CS2/CS3 (n = 453, ε = 2) every
correct program stays at or below 0.79 (the PSC triangle reference, whose own estimator
is biased) and every program that reads ``N(self)`` in place of ``P`` is at least 8.7;
``tau = 2`` sits between the two.
"""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass, field
from functools import lru_cache

import numpy as np

from psc.ground_truth import relative_error
from psc.graph import Graph
from psc.mechanism import DEFAULT_MECHANISM

from .ground_truth import dp_execute
from .lang import Interpreter, Program
from .utility import reference_counter

# (m, triad probability) of the Holme-Kim public test graphs
DEFAULT_GRAPHS: tuple[tuple[int, float], ...] = ((4, 0.6), (2, 0.6))


def holme_kim(n: int, m: int, p_triad: float, rng: np.random.Generator) -> Graph:
    """Powerlaw-cluster graph (Holme & Kim, Phys. Rev. E 2002): preferential attachment
    with ``m`` edges per new node, each followed by a triad-formation step with
    probability ``p_triad``."""
    if n <= m:
        return Graph.from_edges(n, [(u, v) for u in range(n) for v in range(u + 1, n)])
    adj: list[set[int]] = [set() for _ in range(n)]
    ends: list[int] = []  # endpoint multiset: preferential attachment by degree

    def add(u: int, v: int) -> bool:
        if u == v or v in adj[u]:
            return False
        adj[u].add(v)
        adj[v].add(u)
        ends.extend((u, v))
        return True

    for v in range(1, m + 1):  # a star on the first m + 1 nodes seeds the process
        add(0, v)
    for v in range(m + 1, n):
        added, last = 0, None
        while added < m:
            choices = sorted(adj[last] - adj[v] - {v}) if last is not None else []
            if choices and rng.random() < p_triad:
                w = int(choices[int(rng.integers(len(choices)))])
            else:
                w = int(ends[int(rng.integers(len(ends)))])
            if add(v, w):
                added += 1
                last = w
    return Graph.from_edges(n, [(u, w) for u in range(n) for w in adj[u] if u < w])


@lru_cache(maxsize=32)
def public_test_graphs(n: int, specs: tuple[tuple[int, float], ...] = DEFAULT_GRAPHS,
                       seed: int = 7) -> tuple[tuple[str, Graph], ...]:
    rng = np.random.default_rng([seed, n])
    return tuple((f"Holme-Kim(n={n}, m={m}, p={p:g})", holme_kim(n, m, p, rng)) for m, p in specs)


@dataclass(frozen=True)
class NoisyGate:
    """Public settings of the release the gate simulates (those of the deployment)."""

    n: int
    eps: float = 2.0
    node_bounds: bool = False
    alpha: float = 0.0
    mechanism: str = DEFAULT_MECHANISM
    r1: float = 0.5
    r2: float = 0.2
    tau: float = 2.0
    reps: int = 8
    graphs: tuple[tuple[int, float], ...] = DEFAULT_GRAPHS
    seed: int = 7

    def to_dict(self) -> dict:
        return {k: getattr(self, k) for k in self.__dataclass_fields__}


@dataclass
class NoisyReport:
    passed: bool
    rows: list[dict] = field(default_factory=list)
    error: str | None = None

    def worst(self) -> dict | None:
        return max(self.rows, key=lambda r: r["bias"], default=None)

    def feedback(self) -> str:
        if self.error:
            return f"noise-free check failed: the program fails on the randomized release of a public graph: {self.error}"
        w = self.worst()
        if self.passed or w is None:
            return "noise-free check passed"
        ratio = w["ratio"]
        how = (f"{ratio:.3g} times the exact answer" if ratio > 0 and math.isfinite(ratio)
               else f"{w['estimate']:.4g} while the exact answer is {w['truth']:.4g}")
        return (f"noise-free check failed: run through the actual randomized release on a public random graph "
                f"({w['graph']}; exact answer {w['truth']:.4g}) with the final Laplace noise left out, the estimate is "
                f"{how} (median over {w['reps']} releases). The published N(...) / A(...) are randomized copies of the "
                "graph with missing and fake edges, not the graph itself.")


def noise_free_check(program: Program, task: str | None, gate: NoisyGate) -> NoisyReport:
    """Median relative error of the noise-free estimate on each public test graph."""
    if task is None:
        return NoisyReport(True)
    count = reference_counter(task)
    interp = Interpreter(program)
    rows: list[dict] = []
    for name, g in public_test_graphs(gate.n, gate.graphs, gate.seed):
        truth = float(count(g))
        ests: list[float] = []
        for i in range(gate.reps):
            rng = np.random.default_rng([gate.seed, 1, i])
            try:
                tr = dp_execute(g, program, gate.eps, rng, task, gate.mechanism, gate.r1, gate.r2,
                                gate.node_bounds, gate.alpha)
                ests.append(interp.aggregate(float(sum(tr.counts)), g.n))
            except (ArithmeticError, ValueError, TypeError, KeyError, OverflowError) as exc:
                return NoisyReport(False, rows, f"{type(exc).__name__}: {exc}")
        est = statistics.median(ests)
        bias = statistics.median(relative_error(e, truth, g.n) for e in ests)
        rows.append({"graph": name, "truth": truth, "estimate": est, "bias": bias, "reps": gate.reps,
                     "ratio": est / truth if truth else math.inf})
    return NoisyReport(all(r["bias"] <= gate.tau for r in rows), rows)
