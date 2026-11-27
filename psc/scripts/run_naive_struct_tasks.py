"""Naive 基线（Qwen3-8B）在四个判定类图任务上的实验。

任务
----
open-wedge     open wedge（共享一个端点、另两端点不相连的边对）的数量
degree-ge3     指定节点的度数是否 >= 3
triangle-edge  指定边是否属于某个三角形
triangle-node  指定节点是否属于某个三角形

方法沿用论文 Naive（Section 2.4）：``eps`` 全部用于 Algorithm 1 的随机响应
噪声图 ``G'``，curator 模型只收到 ``(V(G), Q)`` 与 ``G'`` 的边表并直接作答。
同一个实例跑 ``--runs`` 次（每次 DP 噪声不同），因此题目固定、噪声独立。

每次运行同时用代码在同一张噪声图上算出"完美 curator"的答案（GT-Naive），
布尔任务比较准确率，open-wedge 另报相对误差。

Example::

    # 项目数据集 CU、Do，qwen3-8b 直答，每个 (数据集, 任务) 3 次
    ../.venv/bin/python scripts/run_naive_struct_tasks.py \
        --provider dashscope --node-model qwen3-8b --curator-model qwen3-8b \
        --datasets CU,Do --runs 3

    # 无 API 的离线自测（mock 完美执行规则，准确率应为 1）
    ../.venv/bin/python scripts/run_naive_struct_tasks.py --provider mock --runs 1 --datasets CU

    # 10–20 节点的小随机图
    ../.venv/bin/python scripts/run_naive_struct_tasks.py --synthetic --nodes 12 --edges 20 --runs 2
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from psc.artifacts import append_run, new_run_directory, write_manifest  # noqa: E402
from psc.dp import build_noisy_graph, naive_budget  # noqa: E402
from psc.events import collect_errors, count_errors, set_error_sink, set_transcript_sink  # noqa: E402
from psc.experiments import DATASETS, default_tag, run_rng  # noqa: E402
from psc.graph import Graph, load_dataset  # noqa: E402
from psc.ground_truth import relative_error  # noqa: E402
from psc.mechanism import DEFAULT_MECHANISM  # noqa: E402
from psc.models import PROVIDERS, ModelConfig, chat, create_formatter, create_model  # noqa: E402
from psc.prompts import CURATOR_SYSTEM, DEFAULT_NAIVE_PROMPT, NAIVE_PROMPTS, PAPER_NAIVE_PROMPTS  # noqa: E402
from psc.struct_tasks import (  # noqa: E402
    STRUCT_TASKS,
    StructRecord,
    answer_kind,
    build_record,
    is_correct,
    naive_answer_on_edges,
    parse_answer,
    struct_naive_prompt,
)

RETRY_KINDS = ("api_error", "empty_reply")
COUNT_TASKS = tuple(t for t in STRUCT_TASKS if answer_kind(t) == "count")


# ---------------------------------------------------------------------------
# Inputs
# ---------------------------------------------------------------------------


def dataset_graph(data_dir: str, dataset: str) -> Graph:
    """The graph of a prepared dataset (every task record shares it)."""
    return load_dataset(data_dir, dataset)["degree"].graph()


def synthetic_graph(n: int, m: int, rng: np.random.Generator) -> Graph:
    candidates = [(u, v) for u in range(n) for v in range(u + 1, n)]
    if n < 3 or not (1 <= m <= len(candidates)):
        raise SystemExit(f"invalid synthetic graph: n={n}, m={m} (need n>=3 and 1<=m<={len(candidates)})")
    picked = rng.choice(len(candidates), size=m, replace=False)
    return Graph.from_edges(n, [candidates[i] for i in picked])


#: ``(dataset index, dataset, task index, task, graph)`` of one cell
Cell = tuple[int, str, int, str, Graph]


def build_cells(args) -> tuple[list[Cell], list[str]]:
    """One cell per (dataset, task); the instance of each run is drawn in ``job``."""
    cells: list[Cell] = []
    sources: list[str] = []
    if args.synthetic:
        rng = np.random.default_rng([args.seed, 7, args.nodes, args.edges])
        graph = synthetic_graph(args.nodes, args.edges, rng)
        sources.append(f"SYN(n={args.nodes},m={args.edges})")
        cells = [(0, "SYN", t_i, task, graph) for t_i, task in enumerate(args.tasks)]
        return cells, sources
    for ds_i, dataset in enumerate(args.datasets):
        graph = dataset_graph(args.data, dataset)
        sources.append(f"{dataset}(n={graph.n},m={graph.m})")
        cells += [(ds_i, dataset, t_i, task, graph) for t_i, task in enumerate(args.tasks)]
    return cells, sources


def instance_rng(args, ds_i: int, t_i: int, run: int) -> np.random.Generator:
    """Stream that picks the target node / edge of run ``run`` (0-based).

    Every run gets a fresh instance by default; ``--fixed-target`` keeps the
    same instance across the runs of a cell.
    """
    return np.random.default_rng([args.seed, 101 + ds_i, t_i, 0 if args.fixed_target else run])


# ---------------------------------------------------------------------------
# One Naive run
# ---------------------------------------------------------------------------


async def run_once(
    model, formatter, record: StructRecord, eps: float, rng: np.random.Generator, naive_prompt: str,
) -> tuple[float | str | None, float | str, list[dict], int, int, str]:
    """Return ``(llm answer, rule answer, errors, noisy edge count, retries, reply)``."""
    with collect_errors(dataset=record.dataset, task=record.task, method="Naive") as errors:
        split = naive_budget(eps)
        noisy = build_noisy_graph(record.graph(), split.eps1, rng)  # Algorithm 1
        prompt = struct_naive_prompt(record, noisy.edges, naive_prompt)
        system = None if naive_prompt in PAPER_NAIVE_PROMPTS else CURATOR_SYSTEM
        reply = await chat(model, formatter, system, prompt, agent="Naive")
        predicted = parse_answer(record.task, reply)
    rule = naive_answer_on_edges(record.task, record.n, noisy.edges, record.target)
    retries = count_errors(errors, *RETRY_KINDS)
    return predicted, rule, errors, noisy.m, retries, reply


async def run_all(args, cfg: ModelConfig, cells: list[Cell], out_dir: Path) -> list[dict]:
    model = create_model(cfg, "curator")  # Naive answers with the curator model only
    formatter = create_formatter(cfg)
    limiter = asyncio.Semaphore(max(1, cfg.parallel_runs))
    total = len(cells) * args.runs
    rows: list[dict] = []
    done = 0

    async def job(ds_i: int, dataset: str, t_i: int, task: str, graph, i: int) -> None:
        nonlocal done
        record = build_record(dataset, graph, task, instance_rng(args, ds_i, t_i, i))
        async with limiter:
            t0 = time.perf_counter()
            predicted, rule, errors, noisy_edges, retries, reply_text = await run_once(
                model, formatter, record, args.eps, run_rng(args.seed, i), args.naive_prompt,
            )
            truth = record.answer
            count_task = answer_kind(record.task) == "count"
            row = {
                "dataset": record.dataset,
                "task": record.task,
                "eps": args.eps,
                "run": i + 1,
                "seed": args.seed,
                "target": record.target,
                "truth": truth,
                "estimate": predicted,
                "rule_estimate": rule,
                "correct": is_correct(predicted, truth),
                "rule_correct": is_correct(rule, truth),
                "relative_error": (
                    relative_error(float(predicted), float(truth), record.n)
                    if count_task and predicted is not None else None
                ),
                "rule_relative_error": (
                    relative_error(float(rule), float(truth), record.n) if count_task else None
                ),
                "noisy_edges": noisy_edges,
                "api_retries": retries,
                "failed_calls": count_errors(errors, "call_failed"),
                "parse_failures": count_errors(errors, "parse_failure"),
                "errors": errors,
                "reply": reply_text,
                "elapsed": round(time.perf_counter() - t0, 2),
                "provider": cfg.provider,
                "node_model": cfg.node_model,
                "curator_model": cfg.curator_model,
                "naive_prompt": args.naive_prompt,
            }
            append_run(out_dir / "runs.jsonl", row)
            rows.append(row)
            done += 1
            if args.verbose:
                print(
                    f"[{done}/{total}] {record.dataset:>3} {record.task:<13} run {i + 1}/{args.runs} "
                    f"llm={predicted} rule={rule} truth={truth} "
                    f"ok={row['correct']} retries={retries} {row['elapsed']}s",
                    flush=True,
                )

    await asyncio.gather(*(job(*cell, i) for cell in cells for i in range(args.runs)))
    return rows


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------


def summarize(rows: list[dict]) -> list[dict]:
    out = []
    keys = list(dict.fromkeys((r["dataset"], r["task"]) for r in rows))
    for dataset, task in keys:
        cell = [r for r in rows if r["dataset"] == dataset and r["task"] == task]
        entry = {
            "dataset": dataset,
            "task": task,
            "eps": cell[0]["eps"],
            "runs": len(cell),
            "first_truth": cell[0]["truth"],
            "accuracy": float(np.mean([r["correct"] for r in cell])),
            "rule_accuracy": float(np.mean([r["rule_correct"] for r in cell])),
            "parse_failures": int(sum(r["parse_failures"] for r in cell)),
            "failed_calls": int(sum(r["failed_calls"] for r in cell)),
            "api_retries": int(sum(r["api_retries"] for r in cell)),
            "llm_calls_per_run": 1.0,
            "provider": cell[0]["provider"],
            "node_model": cell[0]["node_model"],
            "curator_model": cell[0]["curator_model"],
            "naive_prompt": cell[0]["naive_prompt"],
        }
        if answer_kind(task) == "count":
            errs = [r["relative_error"] for r in cell if r["relative_error"] is not None]
            entry["avg_relative_error"] = float(np.mean(errs)) if errs else None
            entry["rule_avg_relative_error"] = float(np.mean([r["rule_relative_error"] for r in cell]))
            entry["median_estimate"] = float(np.median([r["estimate"] for r in cell]))
        out.append(entry)
    return out


def markdown(summary: list[dict], sources: list[str], args) -> str:
    datasets = list(dict.fromkeys(r["dataset"] for r in summary))
    tasks = [t for t in args.tasks if any(r["task"] == t for r in summary)]
    idx = {(r["task"], r["dataset"]): r for r in summary}
    head = "| Task | Method | " + " | ".join(datasets) + " | Avg. |"
    lines = [head, "|" + "---|" * (len(datasets) + 3)]
    for task in tasks:
        for method, column in (("Naive (LLM)", "accuracy"), ("GT-Naive (same noisy graph)", "rule_accuracy")):
            values = [idx[(task, ds)][column] for ds in datasets if (task, ds) in idx]
            lines.append(
                f"| {task} | {method} | "
                + " | ".join(f"{idx[(task, ds)][column]:.4f}" for ds in datasets if (task, ds) in idx)
                + f" | {float(np.mean(values)):.4f} |",
            )
    lines += ["", f"Accuracy of the boolean tasks; {args.runs} runs per cell, eps = {args.eps:g}. "
                  f"Graphs: {', '.join(sources)}."]
    count_rows = [r for r in summary if "avg_relative_error" in r]
    if count_rows:
        lines += ["", "Relative error of the counting task (smaller is better):", "",
                  "| Task | Method | " + " | ".join(datasets) + " | Avg. |",
                  "|" + "---|" * (len(datasets) + 3)]
        for task in [t for t in tasks if t in COUNT_TASKS]:
            for method, column in (("Naive (LLM)", "avg_relative_error"),
                                   ("GT-Naive (same noisy graph)", "rule_avg_relative_error")):
                values = [idx[(task, ds)][column] for ds in datasets if idx.get((task, ds))]
                lines.append(
                    f"| {task} | {method} | "
                    + " | ".join(
                        "-" if idx[(task, ds)][column] is None else f"{idx[(task, ds)][column]:.4f}"
                        for ds in datasets if (task, ds) in idx
                    )
                    + f" | {float(np.mean([v for v in values if v is not None])):.4f} |",
                )
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tasks", default=",".join(STRUCT_TASKS), help=f"comma separated, from {STRUCT_TASKS}")
    ap.add_argument("--datasets", default="CU,Do", help=f"comma separated, from {DATASETS}")
    ap.add_argument("--data", default="data")
    ap.add_argument("--synthetic", action="store_true", help="use one random graph instead of the datasets")
    ap.add_argument("--nodes", type=int, default=12, help="synthetic graph: node count")
    ap.add_argument("--edges", type=int, default=20, help="synthetic graph: edge count")
    ap.add_argument("--runs", type=int, default=3, help="runs per (dataset, task); each draws new DP noise")
    ap.add_argument("--fixed-target", action="store_true",
                    help="keep the same target node/edge across the runs of a cell (default: a new instance per run)")
    ap.add_argument("--eps", type=float, default=2.0)
    ap.add_argument("--naive-prompt", choices=NAIVE_PROMPTS, default=DEFAULT_NAIVE_PROMPT,
                    help="'paper' (default): only (V(G), Q) + noisy edge list; 'cot': + step-by-step/JSON instruction")
    ap.add_argument("--provider", default="dashscope", choices=PROVIDERS)
    ap.add_argument("--node-model", default="qwen3-8b")
    ap.add_argument("--curator-model", default="qwen3-8b", help="Naive answers with this model")
    ap.add_argument("--config", default=None)
    ap.add_argument("--profile", default=None)
    ap.add_argument("--concurrency", type=int, default=None)
    ap.add_argument("--parallel-runs", type=int, default=None)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default="results")
    ap.add_argument("--tag", default=None)
    ap.add_argument("--dry-run", action="store_true", help="print the plan without calling a model")
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--no-save-transcripts", dest="save_transcripts", action="store_false", default=True)
    ap.add_argument("--log-level", default="WARNING")
    args = ap.parse_args()

    args.tasks = [t.strip() for t in args.tasks.split(",") if t.strip()]
    if set(args.tasks) - set(STRUCT_TASKS):
        ap.error(f"unknown task(s) {sorted(set(args.tasks) - set(STRUCT_TASKS))}; choose from {STRUCT_TASKS}")
    if not args.synthetic:
        args.datasets = [d.strip() for d in args.datasets.split(",") if d.strip()]
        if set(args.datasets) - set(DATASETS):
            ap.error(f"unknown dataset(s) {sorted(set(args.datasets) - set(DATASETS))}")
    if args.runs < 1:
        ap.error("--runs must be positive")

    cfg = ModelConfig.from_env(
        args.provider, config_path=args.config, profile=args.profile,
        node_model=args.node_model, curator_model=args.curator_model,
        max_concurrency=args.concurrency, parallel_runs=args.parallel_runs,
    )
    cells, sources = build_cells(args)
    total_runs = len(cells) * args.runs
    print(
        f"provider={cfg.provider} node_model={cfg.node_model} curator_model={cfg.curator_model} "
        f"temperature={cfg.temperature} parallel_runs={cfg.parallel_runs} "
        f"naive_prompt={args.naive_prompt} eps={args.eps:g}",
    )
    print(
        f"tasks={args.tasks} sources={sources} runs/cell={args.runs} "
        f"total runs={total_runs} expected LLM calls={total_runs}",
    )
    for ds_i, dataset, t_i, task, graph in cells:
        for i in range(1 if args.dry_run else 0):
            record = build_record(dataset, graph, task, instance_rng(args, ds_i, t_i, i))
            print(f"  {record.dataset:>3} {record.task:<13} run {i + 1} target={record.target} truth={record.answer}")
    if args.dry_run:
        return

    try:
        out_dir = new_run_directory(
            Path(args.out) / "naive_struct", args.tag,
            f"{default_tag(cfg)}_struct_eps{args.eps:g}_{args.naive_prompt}",
        )
    except (FileExistsError, ValueError) as exc:
        ap.error(f"{exc}; choose a new --tag to preserve previous runs")
    write_manifest(out_dir, DEFAULT_MECHANISM, args.data, [] if args.synthetic else args.datasets, {
        "script": "run_naive_struct_tasks.py",
        "tasks": args.tasks,
        "sources": sources,
        "runs": args.runs,
        "eps": args.eps,
        "seed": args.seed,
        "provider": cfg.provider,
        "profile": cfg.profile,
        "node_model": cfg.node_model,
        "curator_model": cfg.curator_model,
        "temperature": cfg.temperature,
        "naive_prompt": args.naive_prompt,
        "synthetic": args.synthetic,
        "fixed_target": args.fixed_target,
        "mechanism": "naive_rr_full_budget",
        "rng_recipe": "default_rng([seed, run-1]) for the DP noise of a run; the target node/edge "
                      "comes from default_rng([seed, 101+dataset, task, run])",
    })
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.WARNING))
    set_error_sink(out_dir / "errors.jsonl")
    if args.save_transcripts:
        set_transcript_sink(out_dir / "transcripts.jsonl")

    rows = asyncio.run(run_all(args, cfg, cells, out_dir))
    summary = summarize(rows)
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (out_dir / "runs.json").write_text(json.dumps(rows, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
    md = markdown(summary, sources, args)
    (out_dir / "table.md").write_text(md + "\n", encoding="utf-8")

    print("\n" + md)
    print(f"\nsaved summary.json, runs.json, runs.jsonl, manifest.json, table.md, errors.jsonl"
          + (", transcripts.jsonl" if args.save_transcripts else "") + f" in {out_dir}/")


if __name__ == "__main__":
    main()
