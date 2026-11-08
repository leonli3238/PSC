"""P4: compare methods and execution modes on identical DP noise (research contents 3–5).

LLM / agent modes:
  ``naive``     the paper's Naive (RR graph with the whole budget, curator LLM answers)
  ``baseline``  the paper's PSC (curator rules, node LLMs)
  ``bind``      LLM + binding + message validation
  ``program``   Improvement 2: the curator designs a DSL program, nodes run it (no node LLM)
  ``nodebound`` ``program`` with per-node degree bounds by edge clipping (Imola et al. USENIX
                Security 2022; :mod:`certicount.dsl.clipping`, ``--clip-alpha``)
  ``codeagg``   the paper's PSC with the final aggregation done by code (node LLMs still count)
  ``codecost``  bind + code send + code aggregation
Code-only references (no model call):
  ``gt-naive``  GT-Naive          ``gt-psc``  GT-PSC (same mechanism profile as the agents)
  ``gt-dsl``    GT-DSL: the reference DSL program of the task executed in code
  ``gt-dsl-node`` GT-DSL with per-node edge clipping (the code reference of ``nodebound``)
  ``gt-tuned``  the reference program with threshold factor / budget split grid-tuned on public
                synthetic graphs (the "equally tuned PSC" baseline of the DSL search)

Run i of every mode uses the noise of ``[seed, i]``. Each LLM mode also records
the paired code value on its own noise (``rule_relative_error``: GT-Naive for
Naive, GT-PSC for PSC, the program itself for ``program``), so
``llm_error = relative_error - rule_relative_error`` is the error the LLM adds
at execution time (0 for ``program``). For ``program`` every run is also paired
with GT-DSL on the same noise: ``design_error = relative_error - gt_dsl_relative_error``
is the error the LLM designer adds (negative: the design beats the library algorithm).

Design (``program``): ``--design-mode exact`` accepts the first exact program
(``--design-iterations`` drafts per loop, ``--design-restarts`` independent
loops); ``--design-mode search`` runs the accuracy-driven self-improving search
(:mod:`certicount.dsl.search`, ``--search-*``). ``--design-temperature`` > 0
samples different designs. The design is made once per cell and reused by all
runs (it only uses public information).

``--eps`` takes a comma separated list (ε sweep). ``--program-runs`` gives the
DSL more runs than the LLM modes (it makes no model call after the design).
Every model call is written to ``transcripts.jsonl`` (prompt, reply, usage) and
every failure to ``errors.jsonl``, tagged with dataset / task / mode / eps / run.

Out-of-library tasks (4-star, 5-star, degree-moment2) only run in ``program``,
``gt-dsl`` and ``gt-tuned``. Offline by default (mock models). A real provider
calls paid / remote models: check ``--dry-run`` first.

    ../.venv/bin/python scripts/run_execution_compare.py --datasets CU,EE --runs 10 --mock-error-rate 0.05 --tag p4_mock
    ../.venv/bin/python scripts/run_execution_compare.py --datasets CU --tasks 3-star \\
        --modes gt-naive,naive,gt-psc,baseline,gt-dsl,program --runs 10 --tag cu_3star_methods
"""

from __future__ import annotations

import argparse
import asyncio
import dataclasses
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import certicount  # noqa: E402,F401
from psc.dp import naive_budget  # noqa: E402
from psc.events import collect_errors, set_error_sink, set_transcript_sink  # noqa: E402
from psc.experiments import run_rng  # noqa: E402
from psc.framework import NaiveFramework, RunResult  # noqa: E402
from psc.graph import TASKS, TaskRecord, load_dataset  # noqa: E402
from psc.ground_truth import gt_naive, gt_psc  # noqa: E402
from psc.library import get_algorithm  # noqa: E402
from psc.mechanism import DEFAULT_MECHANISM  # noqa: E402
from psc.models import PROVIDERS, ModelConfig, create_model  # noqa: E402
from psc.progress import llm_progress  # noqa: E402
from certicount import DATA_DIR  # noqa: E402
from certicount.artifacts import append_jsonl, out_dir, write_json, write_manifest  # noqa: E402
from certicount.cost import calls_per_run  # noqa: E402
from certicount.dsl.ground_truth import dp_execute, gs_ratio, gt_dsl, noise_ratio  # noqa: E402
from certicount.dsl.library import OUT_OF_LIBRARY, PROGRAMS  # noqa: E402
from certicount.dsl.quality import task_record  # noqa: E402
from certicount.dsl.search import SearchOptions, tune_reference  # noqa: E402
from certicount.execution_report import markdown, summarize  # noqa: E402
from certicount.framework import TrustedPSCFramework, TrustOptions, baseline_options  # noqa: E402

MODES = {
    "baseline": baseline_options,
    "bind": lambda: TrustOptions(execution="llm"),
    "program": lambda: TrustOptions(execution="program"),
    "nodebound": lambda: TrustOptions(execution="program", node_bounds=True),
    "codeagg": lambda: TrustOptions(execution="llm", binding=False, validate=False, aggregate_by_code=True),
    "codecost": lambda: TrustOptions(execution="llm", send_by_code=True, aggregate_by_code=True),
}
AGENT_MODES = (*MODES, "naive")
CODE_MODES = {"gt-naive": "GT-Naive", "gt-psc": "GT-PSC", "gt-dsl": "GT-DSL", "gt-dsl-node": "GT-DSL-node",
              "gt-tuned": "GT-Tuned"}
PROGRAM_MODES = ("program", "nodebound")
ALL_MODES = (*AGENT_MODES, *CODE_MODES)
DEFAULT_MODES = "baseline,bind,program,codecost"

# backwards compatible name
record_for = task_record


def supported(mode: str, task: str) -> bool:
    if mode in ("program", "nodebound", "gt-dsl", "gt-dsl-node", "gt-tuned"):
        return task in PROGRAMS
    return task in TASKS


def search_options(args, eps: float) -> SearchOptions:
    return SearchOptions(rounds=args.search_rounds, proposals=args.search_proposals, sims=args.search_sims,
                         patience=args.search_patience, eps=eps, r1=args.r1, r2=args.r2,
                         allow_budget=not args.search_fixed_budget)


def program_options(args, eps: float, node_bounds: bool = False) -> TrustOptions:
    search = dataclasses.asdict(search_options(args, eps)) if args.design_mode == "search" else None
    return TrustOptions(execution="program", max_design_iterations=args.design_iterations,
                        design_restarts=args.design_restarts, design_mode=args.design_mode, search=search,
                        node_bounds=node_bounds, clip_alpha=args.clip_alpha)


def make_framework(mode: str, cfg: ModelConfig, args=None, eps: float = 2.0, designer_model=None):
    if mode == "naive":
        return NaiveFramework(cfg)
    if mode in PROGRAM_MODES and args is not None:
        opts = program_options(args, eps, node_bounds=mode == "nodebound")
    else:
        opts = MODES[mode]()
    r1, r2 = (args.r1, args.r2) if args is not None else (0.5, 0.2)
    return TrustedPSCFramework(cfg, opts, r1=r1, r2=r2, designer_model=designer_model)


def run_code(mode: str, rec: TaskRecord, eps: float, rng: np.random.Generator, r1: float = 0.5, r2: float = 0.2,
             search: SearchOptions | None = None, keep_grid: bool = False, clip_alpha: float = 0.0) -> RunResult:
    """One run of a code-only reference, as a :class:`RunResult`."""
    t0 = time.perf_counter()
    g = rec.graph()
    if mode == "gt-naive":
        est, split, gs, d_hat, extra = gt_naive(g, rec.task, eps, rng), naive_budget(eps).as_tuple(), None, None, {}
    elif mode == "gt-psc":
        tr = gt_psc(g, rec.task, eps, rng, r1=r1, r2=r2, return_trace=True, mechanism=DEFAULT_MECHANISM)
        est, split, gs, d_hat, extra = tr.result, tr.split.as_tuple(), tr.sensitivity, tr.d_hat_max, {}
    elif mode == "gt-tuned":
        tuned = tune_reference(rec.task, rec.vertex_num, search or SearchOptions(eps=eps, r1=r1, r2=r2))
        tr = dp_execute(g, tuned.program, eps, rng, rec.task, DEFAULT_MECHANISM, r1, r2)
        est, split, gs, d_hat = tr.estimate, tr.split, tr.gs, tr.d_hat_max
        extra = {"program": tuned.program.text(), "tuning_score": tuned.score["score"],
                 "tuning_reference_score": tuned.reference_score["score"],
                 **({"tuning_grid": tuned.grid} if keep_grid else {})}
    else:
        node = mode == "gt-dsl-node"
        tr = gt_dsl(g, rec.task, eps, rng, mechanism=DEFAULT_MECHANISM, r1=r1, r2=r2, node_bounds=node, alpha=clip_alpha)
        est, split, gs, d_hat = tr.estimate, tr.split, tr.gs, tr.d_hat_max
        extra = {"program": PROGRAMS[rec.task].parse().text(),
                 **({"clip_alpha": clip_alpha, **tr.to_dict()} if node else {})}
    return RunResult(
        method=CODE_MODES[mode], dataset=rec.dataset, task=rec.task, eps=eps, estimate=float(est), truth=rec.answer,
        split=tuple(split), sensitivity=gs, d_hat_max=d_hat, noisy_edges=None, llm_calls=0, parse_failures=0,
        elapsed=time.perf_counter() - t0, extra={"code": True, **extra},
    )


def design_calls(args) -> int:
    if args.design_mode == "search":
        return args.search_rounds * args.search_proposals
    return args.design_iterations * args.design_restarts


def planned_calls(mode: str, task: str, n: int, runs: int, args=None) -> int:
    if mode in CODE_MODES:
        return 0
    if mode == "naive":
        return 2 * runs  # task selection + answer
    o = MODES[mode]()
    msgs = get_algorithm(task).needs_messages if task in TASKS else False
    per = calls_per_run(msgs, n, o.execution, o.send_by_code, o.aggregate_by_code, design_calls=0)
    design = (design_calls(args) if args is not None else o.max_design_iterations) if o.execution == "program" else 0
    return per["total"] * runs + design


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--datasets", default="CU")
    ap.add_argument("--tasks", default="degree,3-star,triangle,4-star")
    ap.add_argument("--modes", default=DEFAULT_MODES, help=f"comma separated subset of {','.join(ALL_MODES)}")
    ap.add_argument("--runs", type=int, default=10)
    ap.add_argument("--gt-runs", type=int, default=None,
                    help="runs of the code-only modes (gt-*), default --runs; e.g. 1000 as in the paper")
    ap.add_argument("--program-runs", type=int, default=None,
                    help="runs of the program mode (no model call after the design), default --runs")
    ap.add_argument("--eps", default="2.0", help="privacy budget, or a comma separated list for an ε sweep")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--r1", type=float, default=0.5, help="default budget share of the RR noisy graph")
    ap.add_argument("--r2", type=float, default=0.2, help="default budget share of the noisy degree bound")
    ap.add_argument("--data", default=str(DATA_DIR))
    ap.add_argument("--provider", default="mock", choices=PROVIDERS)
    ap.add_argument("--profile", default=None)
    ap.add_argument("--config", default=None)
    ap.add_argument("--node-model", default=None)
    ap.add_argument("--curator-model", default=None)
    ap.add_argument("--mock-error-rate", type=float, default=0.0)
    g = ap.add_argument_group("DSL design (program mode)")
    g.add_argument("--design-mode", default="exact", choices=("exact", "search"))
    g.add_argument("--design-iterations", type=int, default=3, help="exact mode: drafts per design loop")
    g.add_argument("--design-restarts", type=int, default=1, help="exact mode: independent loops until one is accepted")
    g.add_argument("--design-temperature", type=float, default=None,
                   help="sampling temperature of the designer only (default: the config's temperature)")
    g.add_argument("--search-rounds", type=int, default=4)
    g.add_argument("--search-proposals", type=int, default=3, help="model calls per search round")
    g.add_argument("--search-patience", type=int, default=2)
    g.add_argument("--search-sims", type=int, default=50, help="DP simulations per synthetic graph")
    g.add_argument("--search-fixed-budget", action="store_true", help="do not let the designer choose r1 / r2")
    g.add_argument("--clip-alpha", type=float, default=0.0,
                   help="nodebound / gt-dsl-node: public margin α of the edge-clipping bound floor(max(y_i, 0) + α)")
    ap.add_argument("--dry-run", action="store_true", help="print the planned model calls and exit")
    ap.add_argument("--tag", default=None)
    args = ap.parse_args()

    if args.provider == "mock":
        cfg = ModelConfig(mock_error_rate=args.mock_error_rate)
    else:
        cfg = ModelConfig.from_env(provider=args.provider, config_path=args.config, profile=args.profile,
                                   node_model=args.node_model, curator_model=args.curator_model)
    datasets, tasks, modes = args.datasets.split(","), args.tasks.split(","), args.modes.split(",")
    eps_list = [float(x) for x in args.eps.split(",")]
    unknown = [m for m in modes if m not in ALL_MODES]
    if unknown:
        ap.error(f"unknown mode(s) {unknown}; choose from {', '.join(ALL_MODES)}")
    gt_runs = args.gt_runs if args.gt_runs is not None else args.runs
    program_runs = args.program_runs if args.program_runs is not None else args.runs
    loaded = {ds: load_dataset(args.data, ds) for ds in datasets}
    cells = [(ds, t, m, e) for e in eps_list for ds in datasets for t in tasks for m in modes if supported(m, t)]

    def runs_of(mode: str) -> int:
        return gt_runs if mode in CODE_MODES else program_runs if mode in PROGRAM_MODES else args.runs

    planned = sum(planned_calls(m, t, loaded[ds]["degree"].vertex_num, runs_of(m), args) for ds, t, m, _ in cells)
    print(f"{len(cells)} cells (ε = {', '.join(f'{e:g}' for e in eps_list)}), at most {planned} model calls ({args.provider})")
    if args.dry_run:
        return

    out = out_dir("execution", args.tag, "execution")
    write_manifest(out, {**vars(args), "planned_calls": planned})
    set_error_sink(out / "errors.jsonl")
    set_transcript_sink(out / "transcripts.jsonl")
    designer = None
    if args.provider != "mock" and args.design_temperature is not None:
        dcfg = dataclasses.replace(cfg, temperature=args.design_temperature) if args.design_temperature is not None else cfg
        designer = create_model(dcfg, "curator")

    async def run_all() -> list[dict]:
        rows = []
        with llm_progress(planned) as bar:
            for c, (ds, task, mode, eps) in enumerate(cells, 1):
                rec = task_record(loaded[ds], ds, task)
                fw = None if mode in CODE_MODES else make_framework(mode, cfg, args, eps, designer)
                method = CODE_MODES.get(mode) or {"program": "DSL", "nodebound": "DSL-node"}.get(mode) or fw.name
                search = search_options(args, eps)
                results: list[RunResult] = []
                dicts: list[dict] = []
                n_runs = runs_of(mode)
                t0 = time.perf_counter()
                for i in range(n_runs):
                    bar.set_description(f"cell {c}/{len(cells)} {ds} {task} ε={eps:g} {method} run {i + 1}/{n_runs}", refresh=False)
                    if fw is None:
                        res = run_code(mode, rec, eps, run_rng(args.seed, i), args.r1, args.r2, search,
                                       keep_grid=i == 0, clip_alpha=args.clip_alpha)
                    else:
                        with collect_errors(dataset=ds, task=task, mode=mode, method=method, eps=eps, run=i) as errors:
                            res = await fw.run(rec, eps, rng=run_rng(args.seed, i))
                        res.extra["errors"] = errors
                    d = res.to_dict()
                    d["mode"], d["run"] = mode, i
                    if mode in PROGRAM_MODES:
                        gt = gt_dsl(rec.graph(), task, eps, run_rng(args.seed, i), mechanism=DEFAULT_MECHANISM,
                                    r1=args.r1, r2=args.r2, node_bounds=mode == "nodebound", alpha=args.clip_alpha)
                        d["paired_gt_dsl"] = gt.to_dict()
                        if not res.extra.get("rejected"):
                            d["design_gs_ratio"] = gs_ratio(res.sensitivity, gt.gs)
                            d["design_noise_ratio"] = noise_ratio(
                                res.extra["mechanism_trace"].get("final_noise_scale"), gt.final_noise_scale)
                    results.append(res)
                    dicts.append(d)
                    append_jsonl(d, out / "runs.jsonl")
                row = summarize(ds, task, mode, method, rec.vertex_num, eps, results, dicts, fw is None)
                rows.append(row)
                extra = f", design_error {row['design_error']:.4f}" if row.get("design_error") is not None else ""
                bar.write(f"[{c}/{len(cells)}] {ds} {task} ε={eps:g} {method}: RE {row['relative_error']:.4f} over "
                          f"{row['runs']} runs ({row['rejected']} rejected){extra}, {time.perf_counter() - t0:.1f}s", file=bar.fp)
        return rows

    rows = asyncio.run(run_all())
    write_json({"settings": vars(args), "rows": rows}, out / "summary.json")
    header = (
        f"provider = {cfg.provider}, node = {cfg.node_model}, curator = {cfg.curator_model}, mock error rate = "
        f"{args.mock_error_rate}, ε = {args.eps}, runs: LLM {args.runs} / DSL {program_runs} / code {gt_runs} "
        f"(noise of run i: seed [{args.seed}, i]), r1 = {args.r1}, r2 = {args.r2}. Design: {args.design_mode}"
        + (f" ({args.design_iterations} draft(s) x {args.design_restarts} restart(s))" if args.design_mode == "exact" else
           f" ({args.search_rounds} round(s) x {args.search_proposals} proposal(s), {args.search_sims} sims/graph)")
        + f", designer temperature = {args.design_temperature if args.design_temperature is not None else cfg.temperature}."
        f" Edge-clipping α = {args.clip_alpha:g}. Out-of-library tasks: {', '.join(OUT_OF_LIBRARY)}."
    )
    md = markdown(rows, header, gt_runs)
    (out / "table.md").write_text(md, encoding="utf-8")
    print(md)
    print(f"results in {out}")


if __name__ == "__main__":
    main()
