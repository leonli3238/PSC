"""PSC with the trusted execution layer (research contents 3 and 4).

:class:`TrustedPSCFramework` runs Algorithm 3 of the paper with the
reproduction's DP code (``PrivacyController``: RR graph, noisy max degree,
projection, Laplace) and adds, as options:

* ``binding``  -- task, rules and GS bound on the node side (:mod:`certicount.binding`);
* ``validate`` -- strict message validation (:mod:`certicount.messages`);
* ``execution`` -- ``llm`` (paper) or ``program`` (curator designs a DSL program,
  nodes verify the certificate and execute it, no node LLM call);
* ``node_bounds`` -- program mode with per-node degree bounds by edge clipping
  (Imola et al. USENIX Security 2022, :mod:`certicount.dsl.clipping`) instead of
  the global noisy maximum degree;
* ``send_by_code`` / ``aggregate_by_code`` -- cost options; both steps only
  post-process published data;
* ``adversary`` -- attack hooks (:mod:`certicount.attacks`).

With ``binding=False, validate=False, execution="llm"`` and no adversary the run
is the reproduction's PSC (same model calls, same noise). For a given
``rng`` every execution mode consumes the DP randomness in the same order, so
modes are compared on identical noise.
"""

from __future__ import annotations

import dataclasses
import logging
import math
import time
from dataclasses import dataclass

import numpy as np
from agentscope.message import Msg
from agentscope.pipeline import fanout_pipeline

from psc import rules
from psc.agents import CuratorAgent, PrivacyController
from psc.dp import BudgetSplit, graph_projection, split_budget
from psc.framework import RunResult, _validate_psc
from psc.graph import TASKS, Graph, TaskRecord
from psc.library import get_algorithm, get_dp_framework
from psc.mechanism import DEFAULT_MECHANISM, MechanismProfile, get_mechanism
from psc.models import ModelConfig, create_formatter, create_model
from psc.progress import note_phase

from .agents import EXECUTIONS, TrustedNodeAgent
from .binding import BindingViolation, check_algorithm, check_gs, check_program, get_binding, node_gs
from .dsl.clipping import edge_clipping_bounds
from .dsl.designer import DesignResult, MockDesignerModel, design_reference_params, design_with_restarts
from .dsl.ground_truth import final_noise_scale
from .dsl.lang import Interpreter, Program
from .dsl.library import PROGRAMS
from .dsl.search import SearchOptions, search_program
from .dsl.sensitivity import PublicParams, certify

logger = logging.getLogger(__name__)

_DESIGN_CACHE: dict[tuple, DesignResult] = {}


@dataclass
class TrustOptions:
    execution: str = "llm"
    binding: bool = True
    validate: bool = True
    strict: bool = True
    send_by_code: bool = False
    aggregate_by_code: bool = False
    on_violation: str = "fallback"  # "fallback" to the bound algorithm, or "reject" the run
    program_source: str = "design"  # program mode: "design" (curator LLM) or "library"
    max_design_iterations: int = 3
    # independent design loops (fresh history each) until one is accepted
    design_restarts: int = 1
    # "exact": accept the first draft that passes the exactness test (paper-style);
    # "search": accuracy-driven self-improving search (certicount.dsl.search)
    design_mode: str = "exact"
    search: dict | None = None  # keyword arguments of certicount.dsl.search.SearchOptions
    # program mode with per-node degree bounds (edge clipping, Imola et al. USENIX Security 2022;
    # certicount.dsl.clipping): node i clips P to floor(max(d_i + Lap(1/eps2), 0) + clip_alpha)
    node_bounds: bool = False
    clip_alpha: float = 0.0  # public, data-independent

    @property
    def label(self) -> str:
        if (self.execution == "llm" and not self.binding and not self.validate
                and not self.send_by_code and not self.aggregate_by_code):
            return "PSC"
        parts = [self.execution] + (["nodebound"] if self.execution == "program" and self.node_bounds else [])
        if self.execution != "program":
            parts += (["bind"] if self.binding else []) + (["validate"] if self.validate else [])
        if self.send_by_code and self.execution != "program":
            parts.append("codesend")
        if self.aggregate_by_code and self.execution != "program":
            parts.append("codeagg")
        return "PSC[" + "+".join(parts) + "]"


def baseline_options() -> TrustOptions:
    return TrustOptions(execution="llm", binding=False, validate=False)


class TrustedPSCFramework:
    def __init__(
        self,
        model_cfg: ModelConfig | None = None,
        options: TrustOptions | None = None,
        mechanism: str | MechanismProfile = DEFAULT_MECHANISM,
        r1: float = 0.5,
        r2: float = 0.2,
        adversary=None,
        designer_model=None,
    ) -> None:
        self.cfg = model_cfg or ModelConfig()
        self.opts = options or TrustOptions()
        if self.opts.execution not in EXECUTIONS:
            raise ValueError(f"unknown execution {self.opts.execution!r}")
        self.mechanism = get_mechanism(mechanism)
        self.r1, self.r2 = r1, r2
        self.adversary = adversary
        self.node_model = create_model(self.cfg, "node")
        self.curator_model = create_model(self.cfg, "curator")
        self.formatter = create_formatter(self.cfg)
        if designer_model is None and self.cfg.provider == "mock":
            designer_model = MockDesignerModel()
        self.designer_model = designer_model or self.curator_model
        TrustedNodeAgent.set_max_concurrency(self.cfg.max_concurrency)

    @property
    def name(self) -> str:
        return self.opts.label

    def _nodes(self, graph: Graph) -> list[TrustedNodeAgent]:
        o = self.opts
        return [
            TrustedNodeAgent(i, graph.adj[i], self.node_model, self.formatter, execution=o.execution,
                             validate=o.validate, strict=o.strict, send_by_code=o.send_by_code, n_nodes=graph.n)
            for i in range(graph.n)
        ]

    # ------------------------------------------------------------------
    async def run(self, record: TaskRecord, eps: float, rng: np.random.Generator | None = None) -> RunResult:
        rng = rng if rng is not None else np.random.default_rng(0)
        if self.opts.execution == "program":
            return await self._run_program(record, eps, rng)
        return await self._run_rules(record, eps, rng)

    async def _run_rules(self, record: TaskRecord, eps: float, rng: np.random.Generator) -> RunResult:
        t0 = time.perf_counter()
        graph = record.graph()
        n = graph.n
        nodes = self._nodes(graph)
        curator = CuratorAgent(self.curator_model, self.formatter)
        controller = PrivacyController(self.curator_model, self.formatter, rng, self.r1, self.r2, mechanism=self.mechanism)
        trust: dict = {"violations": []}

        note_phase("select")
        spec = await controller.select_framework(record.input_prompt)
        split: BudgetSplit = controller.determine_budget(eps, spec, True)
        noisy_graph = controller.build_noisy_graph(nodes, split.eps1) if split.eps1 > 0 else None
        d_hat_max = None
        if split.eps2 > 0:
            sensitivity, d_hat_max, noisy_graph = controller.gs_optimize(nodes, noisy_graph, split.eps2, spec)
        else:
            sensitivity = spec.sensitivity(n, None, self.mechanism)

        note_phase("design")
        algo = await curator.design_algorithm(record.input_prompt)
        if self.adversary is not None:
            algo = self.adversary.tamper_algorithm(algo, spec.task)
        binding = None
        if self.opts.binding:
            try:
                binding = check_algorithm(spec.task, algo)
            except BindingViolation as v:
                trust["violations"].append({"kind": v.kind, "message": str(v)})
                if self.opts.on_violation == "reject":
                    return self._rejected(record, eps, split, t0, nodes, curator, controller, trust)
                binding = get_binding(spec.task)
                algo = binding.algorithm
        elif algo.task != spec.task:
            logger.warning("Curator (%s) and privacy controller (%s) disagree on the task", algo.task, spec.task)

        rows = noisy_graph.adj if noisy_graph is not None else None
        for node in nodes:
            node.configure(n, dict(enumerate(rows)) if rows is not None else None, d_hat_max, binding)

        if algo.needs_messages:
            note_phase("send")
            send_instr = Msg(curator.name, algo.send, "assistant", metadata={"phase": "send", "task": algo.task})
            outgoing = await fanout_pipeline(nodes, send_instr, enable_gather=True)
            for node, msg in zip(nodes, outgoing):
                msg.metadata["channel_sender"] = node.node_id  # the transport knows who sent it
            if self.adversary is not None:
                outgoing = self.adversary.inject_messages(nodes, outgoing)
            for msg in outgoing:
                for j in msg.metadata["recipients"]:
                    await nodes[j].observe(msg)
        for node in nodes:
            node.prepare_update()

        note_phase("update")
        update_instr = Msg(curator.name, algo.update, "assistant", metadata={"phase": "update", "task": algo.task})
        await fanout_pipeline(nodes, update_instr, enable_gather=True)

        if self.opts.binding:
            own = node_gs(spec.task, n, d_hat_max, self.mechanism, controller.degree_trace.get("sensitivity_degree"))
            try:
                check_gs(sensitivity, own)
            except BindingViolation as v:
                trust["violations"].append({"kind": v.kind, "message": str(v)})
            sensitivity = own
        reports = controller.collect_reports(nodes, sensitivity, split.eps3)

        note_phase("aggregate")
        if self.opts.aggregate_by_code:
            estimate = rules.aggregate(algo.task, reports, n)
        else:
            for node, value in zip(nodes, reports):
                await curator.observe(Msg(node.name, f"{value}", "assistant", metadata={"kind": "report"}))
            estimate = await curator.aggregate(algo, record.input_prompt, reports, n)

        validation = _validate_psc(nodes, algo, reports, estimate, n)
        validation.update(controller_task=spec.task, curator_task=algo.task, task_correct=spec.task == algo.task == record.task)
        return self._result(record, eps, split, sensitivity, d_hat_max, noisy_graph, nodes, curator, controller,
                            reports, estimate, validation, trust, t0)

    async def _run_program(self, record: TaskRecord, eps: float, rng: np.random.Generator) -> RunResult:
        t0 = time.perf_counter()
        graph = record.graph()
        n = graph.n
        nodes = self._nodes(graph)
        controller = PrivacyController(self.curator_model, self.formatter, rng, self.r1, self.r2, mechanism=self.mechanism)
        trust: dict = {"violations": []}

        note_phase("design")
        program, design = await self._program(record)
        if program is None:
            trust["violations"].append({"kind": "design_failed", "message": "no accepted program"})
            return self._rejected(record, eps, BudgetSplit(0, 0, 0), t0, nodes, None, controller, trust, design)

        # DP framework from the program's requirements (degree class decides the rounding)
        degree_class = record.task if record.task in TASKS else ("triangle" if program.uses_rows else "3-star")
        spec = get_dp_framework(degree_class)
        r1, r2 = program.budget_fractions(self.r1, self.r2)
        split = split_budget(eps, program.uses_rows, program.needs_degree_bound, r1, r2)
        noisy_graph = controller.build_noisy_graph(nodes, split.eps1) if split.eps1 > 0 else None
        d_hat_max = None
        limits: list[int] | None = None
        if split.eps2 > 0:
            if self.opts.node_bounds:
                d_hat_max, noisy_graph, limits = self._edge_clipping(nodes, noisy_graph, split.eps2, spec, controller, rng)
            else:
                _, d_hat_max, noisy_graph = controller.gs_optimize(nodes, noisy_graph, split.eps2, spec)
        # bound of project(P, D) per node: the global d̂max, or the node's own clipping bound
        node_D = limits if limits is not None else [d_hat_max] * n

        certs, node_gs_list = {}, []
        for D in node_D:
            if D not in certs:
                params = PublicParams(n, D=D, dmax=d_hat_max)
                cert = certify(program, params)
                if self.adversary is not None:
                    cert = self.adversary.tamper_certificate(cert)
                try:
                    certs[D] = (cert, check_program(program, cert, params))  # the node's own public check
                except BindingViolation as v:
                    trust["violations"].append({"kind": v.kind, "message": str(v)})
                    return self._rejected(record, eps, split, t0, nodes, None, controller, trust, design)
            node_gs_list.append(certs[D][1])
        cert, gs = certs[node_D[0]][0], max(node_gs_list)
        trust["certified_bounds"] = len(certs)

        rows = dict(enumerate(noisy_graph.adj)) if noisy_graph is not None else None
        for node, D in zip(nodes, node_D):
            node.configure(n, rows, D, None, program, dmax=d_hat_max)
        note_phase("update")
        for node in nodes:
            node.count = node.run_program()
        reports = [node.protected_count(g, split.eps3, rng) for node, g in zip(nodes, node_gs_list)]
        if limits is not None:
            controller.degree_trace.update(node_projection_degrees=limits, node_sensitivities=node_gs_list,
                                           clip_alpha=self.opts.clip_alpha)
        interp = Interpreter(program)
        estimate = interp.aggregate(float(sum(reports)), n)

        # No LLM executes anything here: the paired "rule" value is the program itself,
        # so the execution error is 0 by construction (a different but correct design
        # is not an execution error; its effect is measured against GT-DSL instead).
        count_sum = sum(x.count for x in nodes)
        validation = {
            "nodes": n, "send_checked": 0, "send_exact": 0, "update_exact": n, "e2e_exact": n,
            "llm_count_sum": count_sum, "rule_count_sum": count_sum, "count_rel_diff": 0.0,
            "aggregate_exact": True, "rule_estimate": estimate, "mismatches": [], "checked_against": "program",
        }
        if record.task in TASKS:  # for the record: how far the design is from the library algorithm
            algo = get_algorithm(record.task)
            for node in nodes:  # the node reads the public rows directly; record them as its messages
                if algo.needs_messages:
                    node.sent_payload = rules.send_message(node.node_id, node.noisy_neighbors)
                    node.inbox = [rules.send_message(j, node.public_rows.get(j, ())) for j in node.noisy_neighbors]
            lib = _validate_psc(nodes, algo, reports, estimate, n)
            validation["library"] = {k: lib[k] for k in ("e2e_exact", "rule_count_sum", "count_rel_diff", "rule_estimate")}
        validation.update(controller_task=record.task, curator_task=record.task, task_correct=True)
        trust["certificate"] = cert.to_dict()
        trust["design"] = design.to_dict() if design is not None else None
        coef = interp.aggregate_coefficient(n)
        res = self._result(record, eps, split, gs, d_hat_max, noisy_graph, nodes, None, controller,
                           reports, estimate, validation, trust, t0, design_calls=design.llm_calls if design else 0)
        res.extra["mechanism_trace"].update(
            aggregate_coefficient=coef, final_noise_scale=final_noise_scale(coef, gs, split.eps3),
            budget_fractions=[r1, r2],
        )
        return res

    def _edge_clipping(self, nodes, noisy_graph, eps2: float, spec, controller, rng):
        """Edge clipping (Imola et al. USENIX Security 2022; :mod:`certicount.dsl.clipping`): every node
        publishes ``y_i = d_i + Lap(1/eps2)`` and clips its list to ``floor(max(y_i, 0) + alpha)``. The
        public rows keep PSC's global bound ``d̂max`` computed from the same reports (post-processing).
        Consumes the random numbers in the order of :func:`certicount.dsl.ground_truth.dp_execute`."""
        reports = [node.report_noisy_degree(eps2, rng) for node in nodes]
        bound = self.mechanism.degree_bound(reports, spec.task)
        d_hat_max = bound.projection_degree
        controller.degree_trace = {"noisy_degree_reports": reports, "noisy_max_degree": bound.raw_max,
                                   "sensitivity_degree": bound.sensitivity_degree}
        if noisy_graph is not None:
            noisy_graph = graph_projection(noisy_graph, d_hat_max, rng)
            for node in nodes:
                node.set_noisy_neighbors(noisy_graph.adj[node.node_id])
        limits = edge_clipping_bounds(reports, self.opts.clip_alpha)
        for node, limit in zip(nodes, limits):
            node.bound_degree(limit, rng)
        return d_hat_max, noisy_graph, limits

    async def _program(self, record: TaskRecord) -> tuple[Program | None, DesignResult | None]:
        if self.opts.program_source == "library":
            return PROGRAMS[record.task].parse(), None
        o = self.opts
        search = SearchOptions.from_dict(o.search) if o.design_mode == "search" else None
        key = (id(self.designer_model), record.input_prompt, o.max_design_iterations, o.design_restarts,
               o.design_mode, repr(search))
        cached = key in _DESIGN_CACHE
        if not cached:
            n = record.vertex_num
            if o.design_mode == "search":
                if record.task is None or record.task not in PROGRAMS:
                    raise ValueError("design_mode='search' needs a task with a brute-force reference counter")
                _DESIGN_CACHE[key] = await search_program(self.designer_model, self.formatter, record.input_prompt,
                                                          n, record.task, search)
            elif o.design_mode == "exact":
                _DESIGN_CACHE[key] = await design_with_restarts(
                    self.designer_model, self.formatter, record.input_prompt, n, design_reference_params(n),
                    task=record.task, max_iterations=o.max_design_iterations, restarts=o.design_restarts,
                )
            else:
                raise ValueError(f"unknown design_mode {o.design_mode!r} (exact, search)")
        res = _DESIGN_CACHE[key]
        if cached:  # design is public and reused: no new model call in this run
            res = dataclasses.replace(res, llm_calls=0)
        return res.program, res

    # ------------------------------------------------------------------
    def _trust_stats(self, nodes: list[TrustedNodeAgent], trust: dict) -> dict:
        rejected: dict[str, int] = {}
        for node in nodes:
            for r in node.rejected:
                rejected[r["reason"]] = rejected.get(r["reason"], 0) + 1
        received = sum(len(node.raw_inbox) for node in nodes)
        return {
            **trust,
            "messages_received": received,
            "messages_rejected": sum(rejected.values()),
            "rejected_by_reason": rejected,
            "options": {k: v for k, v in vars(self.opts).items()},
        }

    def _result(self, record, eps, split, sensitivity, d_hat_max, noisy_graph, nodes, curator, controller,
                reports, estimate, validation, trust, t0, design_calls: int = 0) -> RunResult:
        node_calls = sum(x.llm_calls for x in nodes)
        calls = node_calls + (curator.llm_calls if curator else 0) + controller.llm_calls + design_calls
        return RunResult(
            method=self.name, dataset=record.dataset, task=record.task, eps=eps, estimate=estimate, truth=record.answer,
            split=split.as_tuple(), sensitivity=sensitivity, d_hat_max=d_hat_max,
            noisy_edges=noisy_graph.m if noisy_graph is not None else None, llm_calls=calls,
            parse_failures=sum(x.parse_failures for x in nodes) + (curator.parse_failures if curator else 0) + controller.parse_failures,
            elapsed=time.perf_counter() - t0,
            extra={
                "validation": validation, "mechanism": self.mechanism.name, "node_llm_calls": node_calls,
                "trust": self._trust_stats(nodes, trust),
                "mechanism_trace": {
                    **controller.degree_trace, "d_hat_max": d_hat_max, "sensitivity": sensitivity,
                    "laplace_scale": sensitivity / split.eps3 if split.eps3 else 0.0,
                    "raw_counts": [node.count for node in nodes], "noisy_counts": reports,
                    "report_sum_before_clamp": float(sum(reports)),
                },
            },
        )

    def _rejected(self, record, eps, split, t0, nodes, curator, controller, trust, design=None) -> RunResult:
        trust["design"] = design.to_dict() if design is not None else None
        return RunResult(
            method=self.name, dataset=record.dataset, task=record.task, eps=eps, estimate=math.nan, truth=record.answer,
            split=split.as_tuple(), sensitivity=None, d_hat_max=None, noisy_edges=None,
            llm_calls=(curator.llm_calls if curator else 0) + controller.llm_calls + (design.llm_calls if design else 0),
            parse_failures=0, elapsed=time.perf_counter() - t0,
            extra={"rejected": True, "trust": self._trust_stats(nodes, trust)},
        )
