"""The PSC framework (Algorithm 3) and the Naive baseline (Section 2.4)
orchestrated with AgentScope 1.0 agents.
"""

from __future__ import annotations

import logging
import math
import time
from dataclasses import asdict, dataclass, field

import numpy as np
from agentscope.message import Msg
from agentscope.pipeline import fanout_pipeline

from . import rules
from .agents import CuratorAgent, NodeAgent, PrivacyController
from .dp import BudgetSplit
from .graph import Graph, TaskRecord, task_prompt
from .library import AlgorithmSpec
from .models import ModelConfig, create_formatter, create_model

logger = logging.getLogger(__name__)


@dataclass
class RunResult:
    method: str
    dataset: str
    task: str
    eps: float
    estimate: float
    truth: float
    split: tuple[float, float, float]
    sensitivity: float | None
    d_hat_max: int | None
    noisy_edges: int | None
    llm_calls: int
    parse_failures: int
    elapsed: float
    extra: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


class _AgentFactory:
    """Builds the agents for one run (shared model instances)."""

    def __init__(self, cfg: ModelConfig, seed: int) -> None:
        self.cfg = cfg
        self.rng = np.random.default_rng(seed)
        self.node_model = create_model(cfg, "node")
        self.curator_model = create_model(cfg, "curator")
        self.formatter = create_formatter(cfg)
        NodeAgent.set_max_concurrency(cfg.max_concurrency)

    def nodes(self, graph: Graph) -> list[NodeAgent]:
        return [NodeAgent(i, graph.adj[i], self.node_model, self.formatter) for i in range(graph.n)]

    def curator(self) -> CuratorAgent:
        return CuratorAgent(self.curator_model, self.formatter)

    def controller(self, r1: float, r2: float) -> PrivacyController:
        return PrivacyController(self.curator_model, self.formatter, self.rng, r1=r1, r2=r2)


class PSCFramework:
    """Algorithm 3."""

    def __init__(
        self,
        model_cfg: ModelConfig | None = None,
        seed: int = 0,
        gs_optimization: bool = True,
        r1: float = 0.5,
        r2: float = 0.2,
        dp: bool = True,
    ) -> None:
        """
        Args:
            gs_optimization: run ``GSOptimize`` (``False`` gives PSC-B, Exp3).
            r1, r2: budget allocation ratios (``eps1 = r1 eps``,
                ``eps2 = r2 (eps - eps1)``).
            dp: ``False`` gives the non-DP version of Appendix B (Exp5): no
                randomized response, no projection and no Laplace noise; the
                node agents work on the true neighbor lists and the curator
                receives the standard (non-LDP) prompt.
        """
        self.cfg = model_cfg or ModelConfig()
        self.factory = _AgentFactory(self.cfg, seed)
        self.gs_optimization = gs_optimization
        self.r1, self.r2 = r1, r2
        self.dp = dp

    @property
    def name(self) -> str:
        if not self.dp:
            return "PSC-noDP"
        return "PSC" if self.gs_optimization else "PSC-B"

    async def run(self, record: TaskRecord, eps: float) -> RunResult:
        t0 = time.perf_counter()
        graph = record.graph()
        n = graph.n
        input_prompt = record.input_prompt if self.dp else task_prompt(record.task, n, ldp=False)

        # Lines 1-3: initialise node agents with N_G(v_i) and count 0
        nodes = self.factory.nodes(graph)
        curator = self.factory.curator()
        controller = self.factory.controller(self.r1, self.r2)

        # Line 4: DP framework selection, budget split and sensitivity
        spec = await controller.select_framework(input_prompt)
        if self.dp:
            split: BudgetSplit = controller.determine_budget(eps, spec, self.gs_optimization)
        else:
            split = BudgetSplit(0.0, 0.0, 0.0)

        # Lines 5-6: noisy graph
        noisy_graph: Graph | None = None
        if split.eps1 > 0:
            noisy_graph = controller.build_noisy_graph(nodes, split.eps1)
        elif not self.dp:
            # Non-DP version: the "noisy" edge memory is the true graph
            for node in nodes:
                node.set_noisy_neighbors(graph.adj[node.node_id])

        # Lines 7-8: global sensitivity optimisation
        d_hat_max: int | None = None
        if split.eps2 > 0:
            sensitivity, d_hat_max, noisy_graph = controller.gs_optimize(nodes, noisy_graph, split.eps2, spec)
        else:
            sensitivity = spec.sensitivity(n, None)

        # Line 9: curator designs the distributed algorithm
        algo = await curator.design_algorithm(input_prompt)
        if algo.task != spec.task:
            logger.warning("Curator (%s) and privacy controller (%s) disagree on the task", algo.task, spec.task)

        # Line 10: send messages to noisy neighbors
        if algo.needs_messages:
            send_instr = Msg(curator.name, algo.send, "assistant", metadata={"phase": "send", "task": algo.task})
            outgoing = await fanout_pipeline(nodes, send_instr, enable_gather=True)
            for msg in outgoing:
                for j in msg.metadata["recipients"]:
                    await nodes[j].observe(msg)

        # Lines 11-12: update local counts
        update_instr = Msg(curator.name, algo.update, "assistant", metadata={"phase": "update", "task": algo.task})
        await fanout_pipeline(nodes, update_instr, enable_gather=True)

        # Line 13: Laplace-protected reports (skipped in the non-DP version)
        if self.dp:
            reports = controller.collect_reports(nodes, sensitivity, split.eps3)
        else:
            reports = [node.count for node in nodes]
        for node, value in zip(nodes, reports):
            await curator.observe(Msg(node.name, f"{value}", "assistant", metadata={"kind": "report"}))

        # Line 14: aggregation
        estimate = await curator.aggregate(algo, input_prompt, reports, n)

        validation = _validate_psc(nodes, algo, reports, estimate, n)
        validation.update(
            controller_task=spec.task,
            curator_task=algo.task,
            task_correct=spec.task == algo.task == record.task,
        )

        return RunResult(
            method=self.name,
            dataset=record.dataset,
            task=record.task,
            eps=eps if self.dp else 0.0,
            estimate=estimate,
            truth=record.answer,
            split=split.as_tuple(),
            sensitivity=sensitivity if self.dp else None,
            d_hat_max=d_hat_max,
            noisy_edges=noisy_graph.m if noisy_graph is not None else None,
            llm_calls=sum(x.llm_calls for x in nodes) + curator.llm_calls + controller.llm_calls,
            parse_failures=sum(x.parse_failures for x in nodes) + curator.parse_failures + controller.parse_failures,
            elapsed=time.perf_counter() - t0,
            extra={"raw_count_sum": sum(x.count for x in nodes), "validation": validation},
        )


class NaiveFramework:
    """Section 2.4: RR noisy graph appended to the curator's prompt.

    ``prompt_style="raw"`` is the default Naive (+RAW) of Table 2;
    ``prompt_style="refined"`` gives Naive + REFINED of Exp6 / Table 5.
    """

    def __init__(self, model_cfg: ModelConfig | None = None, seed: int = 0, prompt_style: str = "raw") -> None:
        self.cfg = model_cfg or ModelConfig()
        self.factory = _AgentFactory(self.cfg, seed)
        if prompt_style not in ("raw", "refined"):
            raise ValueError(prompt_style)
        self.prompt_style = prompt_style

    @property
    def name(self) -> str:
        return "Naive" if self.prompt_style == "raw" else "Naive+REFINED"

    async def run(self, record: TaskRecord, eps: float) -> RunResult:
        t0 = time.perf_counter()
        graph = record.graph()
        input_prompt = record.input_prompt

        nodes = self.factory.nodes(graph)
        curator = self.factory.curator()
        controller = self.factory.controller(0.5, 0.2)

        spec = await controller.select_framework(input_prompt)
        split = controller.determine_budget(eps, spec, naive=True)
        noisy_graph = controller.build_noisy_graph(nodes, split.eps1)  # Algorithm 1

        if self.prompt_style == "raw":
            estimate = await curator.answer_with_noisy_graph(spec.task, input_prompt, graph.n, noisy_graph.edges)
        else:
            from .baselines import build_single_llm_prompt

            estimate = await curator.answer_prompt(build_single_llm_prompt("refined", spec.task, noisy_graph))
        validation = {
            "controller_task": spec.task,
            "task_correct": spec.task == record.task,
            # exact count on the same noisy graph: what a perfect curator would answer
            "rule_estimate": rules.naive_answer(spec.task, graph.n, noisy_graph.edges),
        }
        return RunResult(
            method=self.name,
            dataset=record.dataset,
            task=record.task,
            eps=eps,
            estimate=estimate,
            truth=record.answer,
            split=split.as_tuple(),
            sensitivity=None,
            d_hat_max=None,
            noisy_edges=noisy_graph.m,
            llm_calls=curator.llm_calls + controller.llm_calls,
            parse_failures=curator.parse_failures + controller.parse_failures,
            elapsed=time.perf_counter() - t0,
            extra={"validation": validation},
        )


_MAX_LOGGED_MISMATCHES = 30


def _validate_psc(nodes: list[NodeAgent], algo: AlgorithmSpec, reports: list[float], estimate: float, n: int) -> dict:
    """Compare every LLM step of one PSC run with the rule executed in code.

    * ``send_exact``   -- the LLM's message equals ``rules.send_message``.
    * ``update_exact`` -- the LLM's count equals the update rule applied to the
      messages the node actually received (isolates update errors).
    * ``e2e_exact``    -- the LLM's count equals the count a perfect pipeline
      would give (send and update errors combined).
    * ``rule_estimate`` -- the aggregate a perfect pipeline would return with
      the *same* Laplace noise, i.e. a paired GT-PSC value for this run.
    """
    task = algo.task
    expected_send = {}
    send_exact = 0
    if algo.needs_messages:
        expected_send = {node.node_id: rules.send_message(node.node_id, node.noisy_neighbors) for node in nodes}
        send_exact = sum(node.sent_payload == expected_send[node.node_id] for node in nodes)

    update_exact = e2e_exact = 0
    rule_counts: list[float] = []
    mismatches: list[dict] = []
    for node in nodes:
        given_inbox = node.reference_count(task, node.inbox)
        expected_inbox = [expected_send[j] for j in node.noisy_neighbors] if algo.needs_messages else []
        perfect = node.reference_count(task, expected_inbox)
        rule_counts.append(perfect)
        update_exact += math.isclose(node.count, given_inbox, abs_tol=1e-6)
        ok = math.isclose(node.count, perfect, abs_tol=1e-6)
        e2e_exact += ok
        if not ok and len(mismatches) < _MAX_LOGGED_MISMATCHES:
            mismatches.append(
                {"node": node.node_id, "llm": node.count, "rule": perfect, "messages": len(node.inbox)},
            )

    noise = [r - node.count for r, node in zip(reports, nodes)]
    rule_estimate = rules.aggregate(task, [c + z for c, z in zip(rule_counts, noise)], n)
    rule_aggregate = rules.aggregate(task, reports, n)
    llm_sum, rule_sum = sum(node.count for node in nodes), sum(rule_counts)
    return {
        "nodes": len(nodes),
        "send_checked": len(nodes) if algo.needs_messages else 0,
        "send_exact": int(send_exact),
        "update_exact": int(update_exact),
        "e2e_exact": int(e2e_exact),
        "llm_count_sum": llm_sum,
        "rule_count_sum": rule_sum,
        "count_rel_diff": abs(llm_sum - rule_sum) / max(abs(rule_sum), 1e-9),
        "aggregate_exact": math.isclose(estimate, rule_aggregate, rel_tol=1e-3, abs_tol=1e-3),
        "rule_estimate": rule_estimate,
        "mismatches": mismatches,
    }
