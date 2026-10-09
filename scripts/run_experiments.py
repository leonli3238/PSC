"""Run the agent-based experiments of the paper (Naive / PSC / PSC-B).

Experiments
-----------
exp1  Performance on all datasets (Table 2), eps = 2
exp2  Effect of the privacy budget eps in {1.0, 1.5, 2.0, 2.5, 3.0} on CU, Do (Fig. 2)
exp3  Effect of the global sensitivity optimisation: PSC vs PSC-B on CU, Do (Table 3)
exp4  Effect of the privacy budget allocation on CU, ML (Fig. 3)
exp5  Appendix B: RAW / REFINED single LLM vs PSC without DP (Table 4)
exp6  Appendix B: Naive + RAW vs Naive + REFINED on the noisy graph (Table 5)
pilot Real-LLM validation: PSC x10 + Naive x10 on CU, Do; node-level LLM-vs-rule accuracy

Model providers
---------------
mock       offline, rule-following reasoner (default; no API key needed)
openai     OPENAI_API_KEY [, OPENAI_BASE_URL]; paper: node=gpt-4.1-mini curator=gpt-4.1
dashscope  DASHSCOPE_API_KEY; e.g. node=qwen3-8b curator=qwen-plus
ollama     local models via OLLAMA_HOST / OLLAMA_MODEL

Examples::

    python scripts/run_experiments.py --exp exp1 --runs 10
    python scripts/run_experiments.py --exp exp1 --provider openai --datasets CU,Do --runs 3
    python scripts/run_experiments.py --exp exp3 --runs 10
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from psc.experiments import (  # noqa: E402
    DATASETS,
    PAPER_TABLE3,
    default_tag,
    generic_markdown,
    run_agent_experiment,
    run_async,
    save_results,
    table2_markdown,
)
from psc.events import set_error_sink  # noqa: E402
from psc.graph import DEFAULT_TASKS, TASKS, load_dataset  # noqa: E402
from psc.models import PROVIDERS, ModelConfig  # noqa: E402
from psc.mechanism import DEFAULT_MECHANISM, MECHANISMS  # noqa: E402
from psc.artifacts import append_run, new_run_directory, write_manifest  # noqa: E402


def _runs(args, default: int) -> int:
    return args.runs if args.runs is not None else default


def _run_experiment(args, *pos, **kwargs):
    return run_agent_experiment(
        *pos, **kwargs, mechanism=args.mechanism,
        on_result=getattr(args, "on_result", None),
    )


def pilot_runs(args) -> dict[str, int]:
    count = _runs(args, 10)
    return {"PSC": count, "Naive": args.naive_runs if args.naive_runs is not None else count}


def _cfg(args) -> ModelConfig:
    return ModelConfig.from_env(
        args.provider,
        config_path=args.config,
        node_model=args.node_model,
        curator_model=args.curator_model,
        max_concurrency=args.concurrency,
        parallel_runs=args.parallel_runs,
        mock_error_rate=args.mock_error_rate,
    )


def exp1(args, cfg):
    datasets = args.datasets.split(",") if args.datasets else list(DATASETS)
    tasks = args.tasks.split(",") if args.tasks else list(DEFAULT_TASKS)
    summary, per_run = run_async(
        _run_experiment(args, args.data, cfg, datasets, tasks, [2.0], _runs(args, 10), ("Naive", "PSC"), args.seed, verbose=args.verbose),
    )
    md = table2_markdown(summary, datasets, ("Naive", "PSC"))
    return summary, per_run, md


def exp2(args, cfg):
    datasets = args.datasets.split(",") if args.datasets else ["CU", "Do"]
    tasks = args.tasks.split(",") if args.tasks else list(DEFAULT_TASKS)
    eps_values = [1.0, 1.5, 2.0, 2.5, 3.0]
    summary, per_run = run_async(
        _run_experiment(args, args.data, cfg, datasets, tasks, eps_values, _runs(args, 10), ("Naive", "PSC"), args.seed, verbose=args.verbose),
    )
    md = generic_markdown(summary, ["dataset", "task", "eps", "method", "avg_relative_error", "mean_estimate", "truth"])
    return summary, per_run, md


def exp3(args, cfg):
    datasets = args.datasets.split(",") if args.datasets else ["CU", "Do"]
    tasks = args.tasks.split(",") if args.tasks else ["triangle", "3-star"]
    summary, per_run = run_async(
        _run_experiment(args, args.data, cfg, datasets, tasks, [2.0], _runs(args, 10), ("PSC", "PSC-B"), args.seed, verbose=args.verbose),
    )
    idx = {(r["method"], r["dataset"], r["task"]): r["avg_relative_error"] for r in summary}
    rows = []
    for task in tasks:
        for ds in datasets:
            paper = PAPER_TABLE3.get((task, ds))
            rows.append(
                {
                    "task": task,
                    "dataset": ds,
                    "PSC": idx.get(("PSC", ds, task)),
                    "PSC-B": idx.get(("PSC-B", ds, task)),
                    "paper PSC": paper[1] if paper else None,
                    "paper PSC-B": paper[3] if paper else None,
                    "paper GT-PSC": paper[0] if paper else None,
                    "paper GT-PSC-B": paper[2] if paper else None,
                },
            )
    md = generic_markdown(rows, ["task", "dataset", "PSC", "PSC-B", "paper PSC", "paper PSC-B", "paper GT-PSC", "paper GT-PSC-B"])
    return summary, per_run, md


def exp4(args, cfg):
    datasets = args.datasets.split(",") if args.datasets else ["CU", "ML"]
    tasks = args.tasks.split(",") if args.tasks else ["triangle"]
    summary_all, per_run_all = [], []
    # (a)(b): vary eps1 = r1 * eps with eps2 = 0.2 (eps - eps1)
    for r1 in [0.1, 0.3, 0.5, 0.7, 0.9]:
        s, p = run_async(
            _run_experiment(args, args.data, cfg, datasets, tasks, [2.0], _runs(args, 10), ("PSC",), args.seed, r1=r1, r2=0.2, verbose=args.verbose),
        )
        for row in s:
            row["setting"] = "vary-eps1"
        summary_all += s
        per_run_all += p
    # (c)(d): fix eps1 = 0.5 eps, vary eps2 = r2 (eps - eps1)
    for r2 in [0.1, 0.3, 0.5, 0.7, 0.9]:
        s, p = run_async(
            _run_experiment(args, args.data, cfg, datasets, tasks, [2.0], _runs(args, 10), ("PSC",), args.seed, r1=0.5, r2=r2, verbose=args.verbose),
        )
        for row in s:
            row["setting"] = "vary-eps2"
        summary_all += s
        per_run_all += p
    md = generic_markdown(summary_all, ["setting", "dataset", "task", "r1", "r2", "avg_relative_error", "mean_estimate", "truth"])
    return summary_all, per_run_all, md


def exp5(args, cfg):
    """Appendix B, Table 4: RAW / REFINED single LLM vs PSC without DP."""
    datasets = args.datasets.split(",") if args.datasets else list(DATASETS)
    tasks = args.tasks.split(",") if args.tasks else list(DEFAULT_TASKS)
    methods = ("RAW", "REFINED", "PSC-noDP")
    summary, per_run = run_async(
        _run_experiment(args, args.data, cfg, datasets, tasks, [0.0], _runs(args, 10), methods, args.seed, verbose=args.verbose),
    )
    md = table2_markdown(summary, datasets, methods, eps=0.0)
    return summary, per_run, md


def exp6(args, cfg):
    """Appendix B, Table 5: Naive + RAW vs Naive + REFINED on the noisy graph."""
    datasets = args.datasets.split(",") if args.datasets else list(DATASETS)
    tasks = args.tasks.split(",") if args.tasks else list(DEFAULT_TASKS)
    methods = ("Naive", "Naive+REFINED")
    summary, per_run = run_async(
        _run_experiment(args, args.data, cfg, datasets, tasks, [2.0], _runs(args, 10), methods, args.seed, verbose=args.verbose),
    )
    md = table2_markdown(summary, datasets, methods)
    return summary, per_run, md


PILOT_COLUMNS = [
    "dataset", "task", "method", "mechanism", "runs", "avg_relative_error", "se_relative_error", "rule_relative_error", "delta",
    "node_samples", "node_update_acc", "node_e2e_acc", "send_acc", "count_rel_diff",
    "aggregate_acc", "task_acc", "parse_failures", "api_retries", "failed_calls", "llm_calls_per_run",
]


def _expected_calls(method: str, task: str, n: int) -> int:
    if method.startswith("Naive"):
        return 2
    return 2 * n + 3 if task == "triangle" else n + 3


def pilot(args, cfg):
    """Real-LLM validation: PSC and Naive both default to 10 runs (eps = 2).

    Each PSC run also yields n node-level LLM-vs-rule samples; the relative
    error is averaged over the runs like Naive's.
    """
    datasets = args.datasets.split(",") if args.datasets else ["CU", "Do"]
    tasks = args.tasks.split(",") if args.tasks else list(DEFAULT_TASKS)
    runs = pilot_runs(args)
    plan = [(m, r) for m, r in runs.items()] + ([("PSC-noDP", 1)] if args.with_nodp else [])

    total = 0
    for ds in datasets:
        recs = load_dataset(args.data, ds)
        for task in tasks:
            for method, n in plan:
                total += n * _expected_calls(method, task, recs[task].vertex_num)
    print(f"pilot plan: {plan} on {datasets} x {tasks}; expected LLM calls = {total}")

    # one schedule for PSC and Naive so that their runs overlap
    summary, per_run = run_async(
        _run_experiment(args, args.data, cfg, datasets, tasks, [2.0], runs, tuple(runs), args.seed, verbose=args.verbose),
    )
    summary.sort(key=lambda r: list(runs).index(r["method"]))
    if args.with_nodp:
        s, p = run_async(
            _run_experiment(args, args.data, cfg, datasets, tasks, [0.0], 1, ("PSC-noDP",), args.seed, verbose=args.verbose),
        )
        summary += s
        per_run += p
    return summary, per_run, generic_markdown(summary, PILOT_COLUMNS)


EXPERIMENTS = {"exp1": exp1, "exp2": exp2, "exp3": exp3, "exp4": exp4, "exp5": exp5, "exp6": exp6, "pilot": pilot}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--exp", default="exp1", choices=EXPERIMENTS)
    ap.add_argument("--data", default="data")
    ap.add_argument("--out", default="results", help="results go to <out>/<exp>/<tag>/")
    ap.add_argument("--datasets", default=None, help="comma separated; default depends on the experiment")
    ap.add_argument("--tasks", default=None, help="comma separated; default depends on the experiment")
    ap.add_argument("--runs", type=int, default=None, help="runs per method and setting; default 10, including pilot")
    ap.add_argument("--naive-runs", type=int, default=None, help="pilot only: override Naive runs (default follows --runs)")
    ap.add_argument("--mechanism", choices=MECHANISMS, default=DEFAULT_MECHANISM, help="shared GT/agent mechanism; legacy reproduces the old implementation")
    ap.add_argument("--dry-run", action="store_true", help="preview pilot/exp1 calls and settings without calling a model")
    ap.add_argument("--with-nodp", action="store_true", help="pilot only: also run PSC-noDP once per setting")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--config", default=None, help="model config file (default: $PSC_CONFIG or config.toml)")
    ap.add_argument("--provider", default=None, choices=PROVIDERS, help="default: $PSC_PROVIDER, then config file")
    ap.add_argument("--node-model", default=None, help="default: config file")
    ap.add_argument("--curator-model", default=None, help="default: config file")
    ap.add_argument("--concurrency", type=int, default=None, help="max concurrent LLM calls of node agents (default: config file)")
    ap.add_argument("--parallel-runs", type=int, default=None, help="runs executed concurrently across all settings (default: config file)")
    ap.add_argument("--mock-error-rate", type=float, default=0.0, help="inject +-1 errors into mock node agents")
    ap.add_argument("--tag", default=None, help="new result directory; default includes model, mechanism and timestamp")
    ap.add_argument("--verbose", action="store_true", help="print one line per finished run; a model-call progress bar is always shown")
    ap.add_argument("--log-level", default="WARNING")
    args = ap.parse_args()

    if (args.runs is not None and args.runs < 1) or (args.naive_runs is not None and args.naive_runs < 1):
        ap.error("run counts must be positive")
    datasets = args.datasets.split(",") if args.datasets else (["CU", "Do"] if args.exp in ("pilot", "exp2", "exp3") else ["CU", "ML"] if args.exp == "exp4" else list(DATASETS))
    tasks = args.tasks.split(",") if args.tasks else (["triangle", "3-star"] if args.exp == "exp3" else ["triangle"] if args.exp == "exp4" else list(DEFAULT_TASKS))
    if set(datasets) - set(DATASETS) or set(tasks) - set(TASKS):
        ap.error("unknown dataset or task")

    cfg = _cfg(args)
    if args.dry_run:
        if args.exp not in ("pilot", "exp1"):
            ap.error("--dry-run currently supports pilot and exp1")
        counts = pilot_runs(args) if args.exp == "pilot" else {"Naive": _runs(args, 10), "PSC": _runs(args, 10)}
        if args.exp == "pilot" and args.with_nodp:
            counts["PSC-noDP"] = 1
        total = sum(
            count * _expected_calls(method, task, load_dataset(args.data, ds)[task].vertex_num)
            for ds in datasets for task in tasks for method, count in counts.items()
        )
        print(f"provider={cfg.provider} node={cfg.node_model} curator={cfg.curator_model} mechanism={args.mechanism}")
        print(f"datasets={datasets} tasks={tasks} runs={counts}; total runs={len(datasets)*len(tasks)*sum(counts.values())}; expected LLM calls={total}")
        return
    try:
        out_dir = new_run_directory(Path(args.out) / args.exp, args.tag, f"{default_tag(cfg)}_{args.mechanism}")
    except (FileExistsError, ValueError) as exc:
        ap.error(f"{exc}; choose a new --tag to preserve previous runs")
    args.on_result = lambda row: append_run(out_dir / "runs.jsonl", row)
    write_manifest(out_dir, args.mechanism, args.data, datasets, {
        "experiment": args.exp, "datasets": datasets, "tasks": tasks,
        "runs": pilot_runs(args) if args.exp == "pilot" else _runs(args, 10), "seed": args.seed,
        "provider": cfg.provider, "node_model": cfg.node_model, "curator_model": cfg.curator_model,
        "temperature": cfg.temperature, "stream": cfg.stream, "parallel_runs": cfg.parallel_runs,
        "max_concurrency": cfg.max_concurrency, "max_retries": cfg.max_retries,
        "retry_backoff": cfg.retry_backoff, "structured_input": cfg.use_structured_input,
        "node_base_url": cfg.endpoint("node"), "curator_base_url": cfg.endpoint("curator"), "extra": cfg.extra, "node_extra": cfg.node_extra, "curator_extra": cfg.curator_extra,
        "with_nodp": args.with_nodp,
        "rng_recipe": "default_rng([seed, run-1]); DP draws consumed sequentially within each run",
    })
    level = getattr(logging, args.log_level.upper(), logging.WARNING)
    logging.basicConfig(level=level)
    file_log = logging.FileHandler(out_dir / "run.log", mode="w", encoding="utf-8")
    file_log.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    logging.getLogger().addHandler(file_log)
    set_error_sink(out_dir / "errors.jsonl")

    if cfg.endpoint("node") == cfg.endpoint("curator"):
        urls = f" base_url={cfg.base_url or 'default'}"
    else:
        urls = f" node_base_url={cfg.endpoint('node') or 'default'} curator_base_url={cfg.endpoint('curator') or 'default'}"
    endpoint = f"{urls} api_key={'set' if cfg.api_key else 'MISSING'}" if cfg.provider in ("openai", "vllm", "dashscope") else ""
    print(f"provider={cfg.provider} node_model={cfg.node_model} curator_model={cfg.curator_model}{endpoint} "
          f"concurrency={cfg.max_concurrency} parallel_runs={cfg.parallel_runs} stream={cfg.stream} runs={args.runs if args.runs is not None else 'default'} "
          f"structured_input={cfg.use_structured_input} max_retries={cfg.max_retries} retry_backoff={cfg.retry_backoff}s mechanism={args.mechanism}")
    print(f"errors are logged to {out_dir}/errors.jsonl and {out_dir}/run.log while running")

    summary, per_run, md = EXPERIMENTS[args.exp](args, cfg)

    save_results(out_dir, summary, per_run, md)
    print("\n" + md)
    print(f"\nsaved summary.json, runs.json, runs.jsonl, manifest.json, table.md, errors.jsonl, run.log in {out_dir}/")


if __name__ == "__main__":
    main()
