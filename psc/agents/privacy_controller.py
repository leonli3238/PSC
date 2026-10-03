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

from typing import Sequence

import numpy as np
from agentscope.agent import AgentBase
from agentscope.formatter import FormatterBase
from agentscope.memory import InMemoryMemory
from agentscope.message import Msg
from agentscope.model import ChatModelBase

from ..dp import BudgetSplit, graph_projection, naive_budget, split_budget
from ..events import record_error
from ..graph import TASKS, Graph, infer_task_from_prompt
from ..library import DPFrameworkSpec, dp_library_summary, get_dp_framework
from ..models import chat
from ..mechanism import DEFAULT_MECHANISM, MechanismProfile, get_mechanism
from ..prompts import PRIVACY_CONTROLLER_SYSTEM, extract_json, task_selection_prompt
from .node_agent import NodeAgent


class PrivacyController(AgentBase):
    def __init__(
        self,
        model: ChatModelBase,
        formatter: FormatterBase,
        rng: np.random.Generator,
        r1: float = 0.5,
        r2: float = 0.2,
        name: str = "PrivacyController",
        mechanism: str | MechanismProfile = DEFAULT_MECHANISM,
    ) -> None:
        super().__init__()
        self.name = name
        self.model = model
        self.formatter = formatter
        self.memory = InMemoryMemory()
        self.rng = rng
        self.r1, self.r2 = r1, r2
        self.mechanism = get_mechanism(mechanism)
        self.degree_trace: dict = {}
        self.node_sensitivities: list[float] | None = None
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
            task = infer_task_from_prompt(input_prompt)
            record_error(
                "parse_failure", f"PrivacyController: invalid task, using rule-based inference ({task})",
                reply=text, agent=self.name, phase="select",
            )
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
        bound = self.mechanism.degree_bound(noisy_degrees, spec.task)
        d_hat_max = bound.projection_degree
        self.degree_trace = {
            "noisy_degree_reports": noisy_degrees,
            "noisy_max_degree": bound.raw_max,
            "sensitivity_degree": bound.sensitivity_degree,
        }
        if noisy_graph is not None:
            noisy_graph = graph_projection(noisy_graph, d_hat_max, self.rng)
            for node in nodes:
                node.set_noisy_neighbors(noisy_graph.adj[node.node_id])
        else:
            # No noisy graph: bound the neighbor list each node uses locally
            per_node = self.mechanism.node_projection_degrees(noisy_degrees, d_hat_max, spec.task, eps2)
            limits = [d_hat_max] * len(nodes) if per_node is None else [int(x) for x in per_node]
            for node, limit in zip(nodes, limits):
                node.bound_degree(limit, self.rng)
            if per_node is not None:
                self.node_sensitivities = [spec.sensitivity(len(nodes), D, self.mechanism) for D in limits]
                self.degree_trace.update(node_projection_degrees=limits, node_sensitivities=self.node_sensitivities)
        return spec.sensitivity(len(nodes), d_hat_max, self.mechanism, bound.sensitivity_degree), d_hat_max, noisy_graph

    # ------------------------------------------------------------------
    # Algorithm 3, line 13: protected reports
    # ------------------------------------------------------------------
    def collect_reports(self, nodes: Sequence[NodeAgent], sensitivity: float, eps3: float) -> list[float]:
        scales = self.node_sensitivities or [sensitivity] * len(nodes)
        return [node.protected_count(s, eps3, self.rng) for node, s in zip(nodes, scales)]

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
