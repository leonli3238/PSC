"""Appendix B baselines: single-LLM prompting without DP (RAW / REFINED).

* RAW      -- zero-shot: definition + task with node and edge string.
* REFINED  -- FS + Least-to-Most + 1-hop (Nguyen and Yan, 2024): definition,
              COT instruction, a worked example on a 10-node graph, the task
              and the 1-hop neighbor set of every node.

Both are answered by a single LLM (the curator model) that sees the *true*
edges, i.e. the standard (non-private) substructure counting setting used in
Exp5.  ``NaiveFramework(prompt_style="refined")`` reuses the REFINED template
on the noisy graph for Exp6.
"""

from __future__ import annotations

import math
import time

import numpy as np

from .graph import Graph, TaskRecord, kstar_k
from .progress import note_phase
from .prompts import raw_prompt, refined_prompt

# ---------------------------------------------------------------------------
# Worked example on a fixed 10-node graph (nodes 1..10 as in the paper)
# ---------------------------------------------------------------------------


def _example_graph() -> Graph:
    """A fixed random 10-node graph (deterministic) used for the few-shot
    example; the paper's example has 10 nodes and 38 edges."""
    rng = np.random.default_rng(2024)
    edges = [(u, v) for u in range(10) for v in range(u + 1, 10)]
    idx = rng.choice(len(edges), size=38, replace=False)
    return Graph.from_edges(10, [edges[i] for i in sorted(idx)])


def build_example(task: str) -> str:
    g = _example_graph()
    ids = lambda xs: ", ".join(str(x + 1) for x in xs)  # noqa: E731 - 1-based ids
    edge_txt = ", ".join(f"({u + 1},{v + 1})" for u, v in g.edges)
    lines = [
        f"This is an example of how you can count {task}.",
        f"Given a graph has {g.n} nodes and {g.m} edges.",
        f"The edge list is: ({edge_txt})",
        "Step 1: List neighbors for each node.",
    ]
    lines += [f"- Node {i + 1}: neighbors = [{ids(g.neighbors(i))}]" for i in range(g.n)]
    lines.append("Step 2: Calculate the degree for each node.")
    lines += [f"- Node {i + 1}: degree = {g.degree(i)}" for i in range(g.n)]

    if task == "degree":
        total = sum(g.degrees())
        lines.append("Step 3: Sum all degrees and divide by the number of nodes.")
        lines.append(f"Average degree = ({' + '.join(str(d) for d in g.degrees())}) / {g.n} = {total} / {g.n} = {total / g.n:.4f}.")
    elif task == "triangle":
        lines.append("Step 3: For each edge (u, v), find the common neighbors of u and v.")
        per_edge = []
        for u, v in g.edges:
            common = sorted(g.adj[u] & g.adj[v])
            per_edge.append(len(common))
            lines.append(f"- Edge ({u + 1},{v + 1}): common neighbors = [{ids(common)}], count = {len(common)}")
        s = sum(per_edge)
        lines.append("Step 4: Sum the counts and divide by 3.")
        lines.append(f"Total triangles = {s} / 3 = {s // 3}.")
    else:
        k = kstar_k(task)
        lines.append(f"Step 3: Calculate C(degree, {k}) for nodes with degree >= {k}.")
        vals = []
        for i in range(g.n):
            d = g.degree(i)
            if d >= k:
                c = math.comb(d, k)
                vals.append(c)
                lines.append(f"- Node {i + 1}: C({d}, {k}) = {c}")
        lines.append(f"Step 4: Sum all {task}s.")
        lines.append(f"Total {task}s = {' + '.join(map(str, vals))} = {sum(vals)}.")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


def build_single_llm_prompt(style: str, task: str, graph: Graph) -> str:
    if style == "raw":
        return raw_prompt(task, graph.n, graph.edges)
    if style == "refined":
        return refined_prompt(task, graph.n, graph.edges, [graph.neighbors(i) for i in range(graph.n)], build_example(task))
    raise ValueError(f"unknown prompt style {style!r}")


class SingleLLMBaseline:
    """RAW / REFINED single-LLM baseline on the original graph (no DP)."""

    def __init__(self, model_cfg, style: str = "raw", seed: int = 0) -> None:
        from .framework import _AgentFactory  # local import to avoid a cycle

        self.style = style
        self.factory = _AgentFactory(model_cfg, seed)

    @property
    def name(self) -> str:
        return self.style.upper()

    async def run(self, record: TaskRecord, eps: float | None = None):
        from .framework import RunResult

        t0 = time.perf_counter()
        graph = record.graph()
        curator = self.factory.curator()
        note_phase("answer")
        estimate = await curator.answer_prompt(build_single_llm_prompt(self.style, record.task, graph))
        return RunResult(
            method=self.name,
            dataset=record.dataset,
            task=record.task,
            eps=0.0,
            estimate=estimate,
            truth=record.answer,
            split=(0.0, 0.0, 0.0),
            sensitivity=None,
            d_hat_max=None,
            noisy_edges=None,
            llm_calls=curator.llm_calls,
            parse_failures=curator.parse_failures,
            elapsed=time.perf_counter() - t0,
        )
