"""Privacy controller: enforces ``eps``-edge LDP for the whole pipeline.

It (1) selects the DP framework from the library and determines the
parameters (privacy budget split, global sensitivity) and (2) executes the
noise mechanisms **in code** so that the guarantee never depends on an LLM
following instructions (Challenge 1 in the paper):

* ``BuildNoisyGraph`` (Algorithm 1) -- collects the RR-perturbed edges that
  each node agent releases and assembles ``G'``.
* ``GSOptimize`` (Algorithm 2) -- noisy max degree + graph projection.
* Laplace mechanism on each node's local count (Algorithm 3, line 13).
"""

from __future__ import annotations

import logging
from typing import Sequence

import numpy as np
from agentscope.agent import AgentBase
from agentscope.formatter import FormatterBase
from agentscope.memory import InMemoryMemory
from agentscope.message import Msg
from agentscope.model import ChatModelBase

from ..dp import BudgetSplit, graph_projection, naive_budget, split_budget
from ..graph import TASKS, Graph, infer_task_from_prompt
from ..library import DPFrameworkSpec, dp_library_summary, get_dp_framework
from ..models import chat
from ..prompts import PRIVACY_CONTROLLER_SYSTEM, extract_json, task_selection_prompt
from .node_agent import NodeAgent

logger = logging.getLogger(__name__)


class PrivacyController(AgentBase):
    def __init__(
        self,
        model: ChatModelBase,
        formatter: FormatterBase,
        rng: np.random.Generator,
        r1: float = 0.5,
        r2: float = 0.2,
        name: str = "PrivacyController",
    ) -> None:
        super().__init__()
        self.name = name
        self.model = model
        self.formatter = formatter
        self.memory = InMemoryMemory()
        self.rng = rng
        self.r1, self.r2 = r1, r2
        self.llm_calls = 0
        self.parse_failures = 0

    # ------------------------------------------------------------------
    # DP framework selection & parameter determination (Alg. 3, line 4)
    # ------------------------------------------------------------------
    async def select_framework(self, input_prompt: str) -> DPFrameworkSpec:
        self.llm_calls += 1
        text = await chat(
            self.model,
            self.formatter,
            PRIVACY_CONTROLLER_SYSTEM,
            task_selection_prompt("privacy controller", input_prompt, dp_library_summary(), list(TASKS)),
        )
        payload = extract_json(text) or {}
        task = str(payload.get("task", "")).strip().lower()
        if task not in TASKS:
            self.parse_failures += 1
            logger.warning("PrivacyController: invalid task %r, using rule-based inference", task)
            task = infer_task_from_prompt(input_prompt)
        return get_dp_framework(task)

    def determine_budget(self, eps: float, spec: DPFrameworkSpec, gs_optimization: bool = True, naive: bool = False) -> BudgetSplit:
        if naive:
            return naive_budget(eps)
        return split_budget(eps, spec.noisy_graph, spec.gs_optimization and gs_optimization, self.r1, self.r2)

    # ------------------------------------------------------------------
    # Algorithm 1: BuildNoisyGraph
    # ------------------------------------------------------------------
    def build_noisy_graph(self, nodes: Sequence[NodeAgent], eps1: float) -> Graph:
        released: list[tuple[int, int]] = []
        for node in nodes:
            released.extend(node.release_noisy_edges(eps1, self.rng))
        noisy = Graph.from_edges(len(nodes), released)
        for node in nodes:
            node.set_noisy_neighbors(noisy.adj[node.node_id])
        return noisy

    # ------------------------------------------------------------------
    # Algorithm 2: GSOptimize
    # ------------------------------------------------------------------
    def gs_optimize(
        self,
        nodes: Sequence[NodeAgent],
        noisy_graph: Graph | None,
        eps2: float,
        spec: DPFrameworkSpec,
    ) -> tuple[float, int, Graph | None]:
        """Return ``(GS_f, d_hat_max, projected noisy graph)``."""
        noisy_degrees = [node.report_noisy_degree(eps2, self.rng) for node in nodes]
        d_hat_max = max(1, int(np.ceil(max(noisy_degrees))))
        if noisy_graph is not None:
            noisy_graph = graph_projection(noisy_graph, d_hat_max, self.rng)
            for node in nodes:
                node.set_noisy_neighbors(noisy_graph.adj[node.node_id])
        else:
            # No noisy graph: bound the neighbor list each node uses locally
            for node in nodes:
                node.bound_degree(d_hat_max, self.rng)
        return spec.sensitivity(len(nodes), d_hat_max), d_hat_max, noisy_graph

    # ------------------------------------------------------------------
    # Algorithm 3, line 13: protected reports
    # ------------------------------------------------------------------
    def collect_reports(self, nodes: Sequence[NodeAgent], sensitivity: float, eps3: float) -> list[float]:
        return [node.protected_count(sensitivity, eps3, self.rng) for node in nodes]

    # ------------------------------------------------------------------
    # AgentScope API
    # ------------------------------------------------------------------
    async def observe(self, msg: Msg | list[Msg] | None) -> None:
        if msg is not None:
            await self.memory.add(msg)

    async def reply(self, msg: Msg | None = None, **kwargs) -> Msg:  # type: ignore[override]
        if msg is None:
            raise ValueError("PrivacyController.reply expects the input prompt message")
        spec = await self.select_framework(msg.get_text_content() or "")
        return Msg(name=self.name, content=spec.describe(), role="assistant", metadata={"task": spec.task})
