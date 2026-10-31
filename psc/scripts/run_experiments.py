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

--with-tritr adds the agent-based TriTR (NAM-DPRD's DP framework, same curator and
node rules as PSC) to exp1 / exp2 / exp3; --gt-runs N appends pure-Python GT-PSC
(and GT-PSC-B for exp3, GT-TriTR with --with-tritr) over N runs to the same table.

Every run writes transcripts.jsonl (full prompt and reply of each model call) by
default; pass --no-save-transcripts to skip it.

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
    python scripts/run_experiments.py --exp exp1 --datasets CU,Do --with-tritr --gt-runs 1000
    python scripts/run_experiments.py --exp exp1 --methods Naive --naive-prompt cot --datasets CU,Do
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
    run_ground_truth,
    save_results,
    table2_markdown,
    with_llm_error_table,
)
from psc.events import set_error_sink, set_transcript_sink  # noqa: E402
from psc.graph import DEFAULT_TASKS, TASKS, load_dataset  # noqa: E402
from psc.models import PROVIDERS, ModelConfig  # noqa: E402
from psc.mechanism import DEFAULT_MECHANISM, MECHANISMS  # noqa: E402
from psc.artifacts import append_run, new_run_directory, write_manifest  # noqa: E402
from psc.prompts import DEFAULT_NAIVE_PROMPT, NAIVE_PROMPTS  # noqa: E402


def _runs(args, default: int) -> int:
    return args.runs if args.runs is not None else default


TRITR_EXPERIMENTS = ("exp1", "exp2", "exp3")
# agent methods that --methods may select per experiment
METHOD_CHOICES = {"exp1": ("Naive", "PSC", "TriTR"), "exp2": ("Naive", "PSC", "TriTR"), "exp3": ("PSC", "PSC-B", "TriTR")}


def _run_experiment(args, *pos, **kwargs):
    return run_agent_experiment(
        *pos, **kwargs, mechanism=args.mechanism,
        on_result=getattr(args, "on_result", None),
        tritr_alpha=args.tritr_alpha,
        naive_prompt=args.naive_prompt,
    )


def _with_tritr(args, methods: tuple[str, ...]) -> tuple[str, ...]:
    return methods + ("TriTR",) if args.with_tritr and "TriTR" not in methods else methods


def _methods(args, default: tuple[str, ...]) -> tuple[str, ...]:
    """Agent methods of exp1-3: ``--methods`` if given, else the default (plus TriTR)."""
    return _with_tritr(args, tuple(args.methods.split(",")) if args.methods else default)


def _gt_reference(args, datasets, tasks, eps_values, base: tuple[str, ...], agent_methods: tuple[str, ...]) -> list[dict]:
    """Pure-Python GT rows over ``--gt-runs`` runs (none when 0): GT of ``base``,
    plus GT-TriTR when TriTR is among the agent methods."""
    if not args.gt_runs:
        return []
    methods = base + (("TriTR",) if "TriTR" in agent_methods else ())
    return run_ground_truth(
        args.data, datasets, tasks, eps_values, args.gt_runs, args.seed, ["GT-" + m for m in methods],
        mechanism=args.mechanism, tritr_alpha=args.tritr_alpha,
    )


def pilot_runs(args) -> dict[str, int]:
    count = _runs(args, 10)
    return {"PSC": count, "Naive": args.naive_runs if args.naive_runs is not None else count}


def _cfg(args) -> ModelConfig:
    return ModelConfig.from_env(
        args.provider,
        config_path=args.config,
        profile=args.profile,
        node_model=args.node_model,
        curator_model=args.curator_model,
        max_concurrency=args.concurrency,
        parallel_runs=args.parallel_runs,
        mock_error_rate=args.mock_error_rate,
    )


def exp1(args, cfg):
    datasets = args.datasets.split(",") if args.datasets else list(DATASETS)
    tasks = args.tasks.split(",") if args.tasks else list(DEFAULT_TASKS)
    methods = _methods(args, ("Naive", "PSC"))
    summary, per_run = run_async(
        _run_experiment(args, args.data, cfg, datasets, tasks, [2.0], _runs(args, 10), methods, args.seed, verbose=args.verbose),
    )
    gt = _gt_reference(args, datasets, tasks, [2.0], ("Naive", "PSC"), methods)
    md = table2_markdown(summary + gt, datasets, methods + tuple(dict.fromkeys(r["method"] for r in gt)))
    return summary + gt, per_run, md


def exp2(args, cfg):
    datasets = args.datasets.split(",") if args.datasets else ["CU", "Do"]
    tasks = args.tasks.split(",") if args.tasks else list(DEFAULT_TASKS)
    eps_values = [1.0, 1.5, 2.0, 2.5, 3.0]
    methods = _methods(args, ("Naive", "PSC"))
    summary, per_run = run_async(
        _run_experiment(args, args.data, cfg, datasets, tasks, eps_values, _runs(args, 10), methods, args.seed, verbose=args.verbose),
    )
    summary += _gt_reference(args, datasets, tasks, eps_values, ("Naive", "PSC"), methods)
    md = generic_markdown(summary, ["dataset", "task", "eps", "method", "avg_relative_error", "mean_estimate", "truth"])
    return summary, per_run, md


def exp3(args, cfg):
    datasets = args.datasets.split(",") if args.datasets else ["CU", "Do"]
    tasks = args.tasks.split(",") if args.tasks else ["triangle", "3-star"]
    methods = _methods(args, ("PSC", "PSC-B"))
    summary, per_run = run_async(
        _run_experiment(args, args.data, cfg, datasets, tasks, [2.0], _runs(args, 10), methods, args.seed, verbose=args.verbose),
    )
    summary += _gt_reference(args, datasets, tasks, [2.0], ("PSC", "PSC-B"), methods)
    measured = list(dict.fromkeys(r["method"] for r in summary))
    idx = {(r["method"], r["dataset"], r["task"]): r["avg_relative_error"] for r in summary}
    rows = []
    for task in tasks:
        for ds in datasets:
            paper = PAPER_TABLE3.get((task, ds))
            rows.append(
                {
                    "task": task,
                    "dataset": ds,
                    **{m: idx.get((m, ds, task)) for m in measured},
                    "paper PSC": paper[1] if paper else None,
                    "paper PSC-B": paper[3] if paper else None,
                    "paper GT-PSC": paper[0] if paper else None,
                    "paper GT-PSC-B": paper[2] if paper else None,
                },
            )
    md = generic_markdown(rows, ["task", "dataset", *measured, "paper PSC", "paper PSC-B", "paper GT-PSC", "paper GT-PSC-B"])
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
    "delta_signed", "exec_exact", "lucky_gain", "llm_harm", "node_samples", "node_update_acc", "node_e2e_acc", "send_acc", "count_rel_diff",
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
    ap.add_argument("--with-tritr", action="store_true", help=f"{'/'.join(TRITR_EXPERIMENTS)}: also run the agent-based TriTR")
    ap.add_argument("--tritr-alpha", type=float, default=0.0, help="TriTR: margin added to every noisy degree (NAM-DPRD uses 150)")
    ap.add_argument("--methods", default=None, help="exp1/exp2: subset of Naive,PSC,TriTR; exp3: of PSC,PSC-B,TriTR (default: the experiment's methods)")
    ap.add_argument("--naive-prompt", choices=NAIVE_PROMPTS, default=DEFAULT_NAIVE_PROMPT,
                    help="Naive (+RAW): 'paper' (default) sends only the paper's (V(G), Q) + edge list prompt; "
                         "'paper-direct' adds an instruction to answer with the final number only; 'cot' adds the "
                         "curator system prompt and the step-by-step/JSON answer instruction (default before 2026-10-13)")
    ap.add_argument("--gt-runs", type=int, default=0, help=f"{'/'.join(TRITR_EXPERIMENTS)}: append pure-Python GT rows over this many runs (0: none)")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--config", default=None, help="model config file (default: $PSC_CONFIG or config.toml)")
    ap.add_argument("--profile", default=None, help="[profiles.<name>] of the config file: gateway key file, stream, concurrency, retries")
    ap.add_argument("--provider", default=None, choices=PROVIDERS, help="default: $PSC_PROVIDER, then config file")
    ap.add_argument("--node-model", default=None, help="default: config file")
    ap.add_argument("--curator-model", default=None, help="default: config file")
    ap.add_argument("--concurrency", type=int, default=None, help="max concurrent LLM calls of node agents (default: config file)")
    ap.add_argument("--parallel-runs", type=int, default=None, help="runs executed concurrently across all settings (default: config file)")
    ap.add_argument("--mock-error-rate", type=float, default=0.0, help="inject +-1 errors into mock node agents")
    ap.add_argument("--tag", default=None, help="new result directory; default includes model, mechanism and timestamp")
    ap.add_argument("--save-transcripts", dest="save_transcripts", action="store_true", default=True,
                    help="write every model call (agent, phase, system/user prompt, full reply, tokens) to transcripts.jsonl (default: on)")
    ap.add_argument("--no-save-transcripts", dest="save_transcripts", action="store_false",
                    help="do not write transcripts.jsonl (saves disk space on large prompts)")
    ap.add_argument("--verbose", action="store_true", help="print one line per finished run; a model-call progress bar is always shown")
    ap.add_argument("--log-level", default="WARNING")
    args = ap.parse_args()

    if (args.runs is not None and args.runs < 1) or (args.naive_runs is not None and args.naive_runs < 1):
        ap.error("run counts must be positive")
    if (args.with_tritr or args.gt_runs) and args.exp not in TRITR_EXPERIMENTS:
        ap.error(f"--with-tritr / --gt-runs apply to {', '.join(TRITR_EXPERIMENTS)}")
    if args.tritr_alpha < 0 or args.gt_runs < 0:
        ap.error("--tritr-alpha and --gt-runs must be nonnegative")
    if args.methods is not None:
        chosen = args.methods.split(",")
        allowed = METHOD_CHOICES.get(args.exp)
        if allowed is None:
            ap.error(f"--methods applies to {', '.join(METHOD_CHOICES)}")
        if not args.methods or set(chosen) - set(allowed) or len(set(chosen)) != len(chosen):
            ap.error(f"--methods for {args.exp}: distinct names from {','.join(allowed)}")
    datasets = args.datasets.split(",") if args.datasets else (["CU", "Do"] if args.exp in ("pilot", "exp2", "exp3") else ["CU", "ML"] if args.exp == "exp4" else list(DATASETS))
    tasks = args.tasks.split(",") if args.tasks else (["triangle", "3-star"] if args.exp == "exp3" else ["triangle"] if args.exp == "exp4" else list(DEFAULT_TASKS))
    if set(datasets) - set(DATASETS) or set(tasks) - set(TASKS):
        ap.error("unknown dataset or task")

    cfg = _cfg(args)
    if args.dry_run:
        if args.exp not in ("pilot", "exp1"):
            ap.error("--dry-run currently supports pilot and exp1")
        counts = pilot_runs(args) if args.exp == "pilot" else {m: _runs(args, 10) for m in _methods(args, ("Naive", "PSC"))}
        if args.exp == "pilot" and args.with_nodp:
            counts["PSC-noDP"] = 1
        total = sum(
            count * _expected_calls(method, task, load_dataset(args.data, ds)[task].vertex_num)
            for ds in datasets for task in tasks for method, count in counts.items()
        )
        print(f"provider={cfg.provider} profile={cfg.profile or 'none'} node={cfg.node_model} curator={cfg.curator_model} "
              f"stream={cfg.stream} concurrency={cfg.max_concurrency} parallel_runs={cfg.parallel_runs} mechanism={args.mechanism}")
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
        "provider": cfg.provider, "profile": cfg.profile, "node_model": cfg.node_model, "curator_model": cfg.curator_model,
        "temperature": cfg.temperature, "stream": cfg.stream, "parallel_runs": cfg.parallel_runs,
        "max_concurrency": cfg.max_concurrency, "max_retries": cfg.max_retries,
        "retry_backoff": cfg.retry_backoff, "structured_input": cfg.use_structured_input,
        "node_base_url": cfg.endpoint("node"), "curator_base_url": cfg.endpoint("curator"), "extra": cfg.extra, "node_extra": cfg.node_extra, "curator_extra": cfg.curator_extra,
        "with_nodp": args.with_nodp,
        **({"methods": list(_methods(args, ()))} if args.methods else {}),
        **({"with_tritr": True} if args.with_tritr else {}),
        **({"tritr_alpha": args.tritr_alpha} if "TriTR" in _methods(args, ()) else {}),
        **({"gt_runs": args.gt_runs} if args.gt_runs else {}),
        "naive_prompt": args.naive_prompt,
        "save_transcripts": args.save_transcripts,
        "rng_recipe": "default_rng([seed, run-1]); DP draws consumed sequentially within each run",
    })
    level = getattr(logging, args.log_level.upper(), logging.WARNING)
    logging.basicConfig(level=level)
    file_log = logging.FileHandler(out_dir / "run.log", mode="w", encoding="utf-8")
    file_log.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    logging.getLogger().addHandler(file_log)
    set_error_sink(out_dir / "errors.jsonl")
    if args.save_transcripts:
        set_transcript_sink(out_dir / "transcripts.jsonl")

    if cfg.endpoint("node") == cfg.endpoint("curator"):
        urls = f" base_url={cfg.base_url or 'default'}"
    else:
        urls = f" node_base_url={cfg.endpoint('node') or 'default'} curator_base_url={cfg.endpoint('curator') or 'default'}"
    endpoint = f"{urls} api_key={'set' if cfg.api_key else 'MISSING'}" if cfg.provider in ("openai", "vllm", "dashscope") else ""
    print(f"provider={cfg.provider} profile={cfg.profile or 'none'} node_model={cfg.node_model} curator_model={cfg.curator_model}{endpoint} "
          f"concurrency={cfg.max_concurrency} parallel_runs={cfg.parallel_runs} stream={cfg.stream} runs={args.runs if args.runs is not None else 'default'} "
          f"structured_input={cfg.use_structured_input} max_retries={cfg.max_retries} retry_backoff={cfg.retry_backoff}s mechanism={args.mechanism}"
          + (f" methods={args.methods}" if args.methods else "")
          + (f" tritr_alpha={args.tritr_alpha:g}" if "TriTR" in _methods(args, ()) else "")
          + (f" gt_runs={args.gt_runs}" if args.gt_runs else "")
          + f" naive_prompt={args.naive_prompt}")
    print(f"errors are logged to {out_dir}/errors.jsonl and {out_dir}/run.log while running"
          + (f"; every model call to {out_dir}/transcripts.jsonl" if args.save_transcripts else ""))

    summary, per_run, md = EXPERIMENTS[args.exp](args, cfg)
    if args.exp != "pilot":
        md = with_llm_error_table(md, summary)

    save_results(out_dir, summary, per_run, md)
    print("\n" + md)
    print(f"\nsaved summary.json, runs.json, runs.jsonl, manifest.json, table.md, errors.jsonl, run.log"
          + (", transcripts.jsonl" if args.save_transcripts else "") + f" in {out_dir}/")


if __name__ == "__main__":
    main()
