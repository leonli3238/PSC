"""Run the agent-based experiments of the paper (Naive / PSC / PSC-B).

Experiments
-----------
exp1  Performance on all datasets (Table 2), eps = 2
exp2  Effect of the privacy budget eps in {1.0, 1.5, 2.0, 2.5, 3.0} on CU, Do (Fig. 2)
exp3  Effect of the global sensitivity optimisation: PSC vs PSC-B on CU, Do (Table 3)
exp4  Effect of the privacy budget allocation on CU, ML (Fig. 3)
exp5  Appendix B: RAW / REFINED single LLM vs PSC without DP (Table 4)
exp6  Appendix B: Naive + RAW vs Naive + REFINED on the noisy graph (Table 5)
pilot Initial real-LLM validation: PSC x1 + Naive x3 on CU, Do; node-level LLM-vs-rule accuracy

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
from psc.graph import TASKS, load_dataset  # noqa: E402
from psc.models import PROVIDERS, ModelConfig  # noqa: E402


def _runs(args, default: int) -> int:
    return args.runs if args.runs is not None else default


def _cfg(args) -> ModelConfig:
    return ModelConfig.from_env(
        args.provider,
        config_path=args.config,
        node_model=args.node_model,
        curator_model=args.curator_model,
        max_concurrency=args.concurrency,
        mock_error_rate=args.mock_error_rate,
    )


def exp1(args, cfg):
    datasets = args.datasets.split(",") if args.datasets else list(DATASETS)
    tasks = args.tasks.split(",") if args.tasks else list(TASKS)
    summary, per_run = run_async(
        run_agent_experiment(args.data, cfg, datasets, tasks, [2.0], _runs(args, 10), ("Naive", "PSC"), args.seed, verbose=args.verbose),
    )
    md = table2_markdown(summary, datasets, ("Naive", "PSC"))
    return summary, per_run, md


def exp2(args, cfg):
    datasets = args.datasets.split(",") if args.datasets else ["CU", "Do"]
    tasks = args.tasks.split(",") if args.tasks else list(TASKS)
    eps_values = [1.0, 1.5, 2.0, 2.5, 3.0]
    summary, per_run = run_async(
        run_agent_experiment(args.data, cfg, datasets, tasks, eps_values, _runs(args, 10), ("Naive", "PSC"), args.seed, verbose=args.verbose),
    )
    md = generic_markdown(summary, ["dataset", "task", "eps", "method", "avg_relative_error", "mean_estimate", "truth"])
    return summary, per_run, md


def exp3(args, cfg):
    datasets = args.datasets.split(",") if args.datasets else ["CU", "Do"]
    tasks = args.tasks.split(",") if args.tasks else ["triangle", "2-star", "3-star"]
    summary, per_run = run_async(
        run_agent_experiment(args.data, cfg, datasets, tasks, [2.0], _runs(args, 10), ("PSC", "PSC-B"), args.seed, verbose=args.verbose),
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
            run_agent_experiment(args.data, cfg, datasets, tasks, [2.0], _runs(args, 10), ("PSC",), args.seed, r1=r1, r2=0.2, verbose=args.verbose),
        )
        for row in s:
            row["setting"] = "vary-eps1"
        summary_all += s
        per_run_all += p
    # (c)(d): fix eps1 = 0.5 eps, vary eps2 = r2 (eps - eps1)
    for r2 in [0.1, 0.3, 0.5, 0.7, 0.9]:
        s, p = run_async(
            run_agent_experiment(args.data, cfg, datasets, tasks, [2.0], _runs(args, 10), ("PSC",), args.seed, r1=0.5, r2=r2, verbose=args.verbose),
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
    tasks = args.tasks.split(",") if args.tasks else list(TASKS)
    methods = ("RAW", "REFINED", "PSC-noDP")
    summary, per_run = run_async(
        run_agent_experiment(args.data, cfg, datasets, tasks, [0.0], _runs(args, 10), methods, args.seed, verbose=args.verbose),
    )
    md = table2_markdown(summary, datasets, methods, eps=0.0)
    return summary, per_run, md


def exp6(args, cfg):
    """Appendix B, Table 5: Naive + RAW vs Naive + REFINED on the noisy graph."""
    datasets = args.datasets.split(",") if args.datasets else list(DATASETS)
    tasks = args.tasks.split(",") if args.tasks else list(TASKS)
    methods = ("Naive", "Naive+REFINED")
    summary, per_run = run_async(
        run_agent_experiment(args.data, cfg, datasets, tasks, [2.0], _runs(args, 10), methods, args.seed, verbose=args.verbose),
    )
    md = table2_markdown(summary, datasets, methods)
    return summary, per_run, md


PILOT_COLUMNS = [
    "dataset", "task", "method", "runs", "avg_relative_error", "rule_relative_error", "delta",
    "node_samples", "node_update_acc", "node_e2e_acc", "send_acc", "count_rel_diff",
    "aggregate_acc", "task_acc", "parse_failures", "llm_calls_per_run",
]


def _expected_calls(method: str, task: str, n: int) -> int:
    if method.startswith("Naive"):
        return 2
    return 2 * n + 3 if task == "triangle" else n + 3


def pilot(args, cfg):
    """Initial real-LLM validation: PSC x1 and Naive x3 on CU, Do (all tasks, eps = 2).

    The per-node comparison with the rules is independent of the DP noise, so
    a single PSC run per setting already yields n node-level samples.
    """
    datasets = args.datasets.split(",") if args.datasets else ["CU", "Do"]
    tasks = args.tasks.split(",") if args.tasks else list(TASKS)
    plan = [("PSC", _runs(args, 1), [2.0]), ("Naive", args.naive_runs, [2.0])]
    if args.with_nodp:
        plan.append(("PSC-noDP", 1, [0.0]))

    total = 0
    for ds in datasets:
        recs = load_dataset(args.data, ds)
        for task in tasks:
            for method, runs, _ in plan:
                total += runs * _expected_calls(method, task, recs[task].vertex_num)
    print(f"pilot plan: {[(m, r) for m, r, _ in plan]} on {datasets} x {tasks}; expected LLM calls = {total}")

    summary, per_run = [], []
    for method, runs, eps_values in plan:
        s, p = run_async(
            run_agent_experiment(args.data, cfg, datasets, tasks, eps_values, runs, (method,), args.seed, verbose=args.verbose),
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
    ap.add_argument("--runs", type=int, default=None, help="default 10 (paper); pilot: PSC runs, default 1")
    ap.add_argument("--naive-runs", type=int, default=3, help="pilot only: Naive runs per setting")
    ap.add_argument("--with-nodp", action="store_true", help="pilot only: also run PSC-noDP once per setting")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--config", default=None, help="model config file (default: $PSC_CONFIG or config.toml)")
    ap.add_argument("--provider", default=None, choices=PROVIDERS, help="default: $PSC_PROVIDER, then config file")
    ap.add_argument("--node-model", default=None, help="default: config file")
    ap.add_argument("--curator-model", default=None, help="default: config file")
    ap.add_argument("--concurrency", type=int, default=None, help="max concurrent LLM calls of node agents (default: config file)")
    ap.add_argument("--mock-error-rate", type=float, default=0.0, help="inject +-1 errors into mock node agents")
    ap.add_argument("--tag", default=None, help="sub-directory name; default: mock or <provider>_<model>")
    ap.add_argument("--verbose", action="store_true", help="print every run")
    ap.add_argument("--log-level", default="WARNING")
    args = ap.parse_args()

    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.WARNING))
    cfg = _cfg(args)
    endpoint = f" base_url={cfg.base_url or 'default'} api_key={'set' if cfg.api_key else 'MISSING'}" if cfg.provider in ("openai", "dashscope") else ""
    print(f"provider={cfg.provider} node_model={cfg.node_model} curator_model={cfg.curator_model}{endpoint} "
          f"concurrency={cfg.max_concurrency} stream={cfg.stream} runs={args.runs if args.runs is not None else 'default'} "
          f"structured_input={cfg.use_structured_input}")

    summary, per_run, md = EXPERIMENTS[args.exp](args, cfg)

    out_dir = save_results(Path(args.out) / args.exp / (args.tag or default_tag(cfg)), summary, per_run, md)
    print("\n" + md)
    print(f"\nsaved summary.json, runs.json, table.md in {out_dir}/")


if __name__ == "__main__":
    main()
