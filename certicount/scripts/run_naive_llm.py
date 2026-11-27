"""Naive (single LLM on the RR noisy graph) on the CertiCount tasks.

The table of :mod:`scripts.run_gt_select` holds only code methods (GT-Naive /
GT-Select / GT-DSL) plus the LLM-designed CertiCount. This runner fills the
missing ``Naive`` row: the paper's Section 2.4 baseline executed by a real
model.

Per run:

1. the whole budget goes to Algorithm 1 (randomized response), exactly as
   :func:`certicount.dsl.ground_truth.gt_naive`;
2. the curator model receives only ``(V(G), Q)`` with the noisy edge list
   pasted in (``psc.prompts.insert_edges_into_prompt``) and answers once;
3. the answer is parsed with :func:`psc.prompts.extract_number` and scored with
   ``|f_hat - f| / max(f, 0.001 n)``; the exact count on the same noisy graph
   (GT-Naive) is recorded as the paired code reference.

Tasks are the CertiCount ones (counts, not yes/no): ``open-wedge``,
``degree-ge3`` (nodes with degree >= 3), ``triangle-node`` (nodes on a
triangle), ``triangle-edge`` (edges on a triangle). Task prompts and truths come
from :func:`certicount.dsl.quality.task_record`, so they match the tables.

Examples::

    # local vLLM Qwen3-8B, CU/Do/ML/CS/EE, 20 runs per cell
    VLLM_CURATOR_BASE_URL=http://127.0.0.1:8000/v1 ../.venv/bin/python scripts/run_naive_llm.py \
        --provider vllm --config ../psc/config.vllm.toml \
        --node-model Qwen3-8B --curator-model Qwen3-8B --runs 20 --tag naive_qwen3-8b_r20

    # preview without calling a model
    ../.venv/bin/python scripts/run_naive_llm.py --dry-run
"""

from __future__ import annotations

import argparse
import asyncio
import math
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import certicount  # noqa: E402,F401  (puts ../psc on sys.path)
from psc.dp import build_noisy_graph, naive_budget  # noqa: E402
from psc.events import collect_errors, count_errors, record_error, set_error_sink  # noqa: E402
from psc.experiments import run_rng  # noqa: E402
from psc.graph import load_dataset  # noqa: E402
from psc.ground_truth import relative_error  # noqa: E402
from psc.models import PROVIDERS, ModelConfig, chat, create_formatter, create_model  # noqa: E402
from psc.prompts import extract_number, insert_edges_into_prompt  # noqa: E402
from certicount import DATA_DIR  # noqa: E402
from certicount.artifacts import append_jsonl, markdown_table, out_dir, write_json, write_manifest  # noqa: E402
from certicount.dsl.ground_truth import gt_naive  # noqa: E402
from certicount.dsl.quality import task_record  # noqa: E402

TASKS = ("open-wedge", "degree-ge3", "triangle-node", "triangle-edge")
DATASETS = ("CU", "Do", "ML", "CS", "EE", "PM")
RETRY_KINDS = ("api_error", "empty_reply")
ANSWER_ONLY = (
    "Answer with the final number only. Do not explain, do not show intermediate "
    "calculations, and do not list nodes or edges."
)
# Small models degenerate into counting sequences ("1234567891011...") when asked
# for the bare number; free reasoning plus an explicit final answer keeps the
# single-turn Naive setting while making the answer parseable.
BOXED = "Put the final number inside \\boxed{}."


def naive_prompt(record, noisy_edges, style: str) -> str:
    """RAW-style Naive prompt: ``(V(G), Q)`` with the noisy edge list pasted in."""
    prompt = insert_edges_into_prompt(record.input_prompt, noisy_edges)
    if style == "direct":
        prompt = f"{prompt}\n\n{ANSWER_ONLY}"
    elif style == "boxed":
        prompt = f"{prompt}\n\n{BOXED}"
    return prompt


#: Any graph statistic of these datasets is far below this; larger numbers are
#: degenerate replies (counting sequences, hallucinated combinatorics).
ABSURD_ANSWER = 1e11


def is_sane(estimate: float | None) -> bool:
    return estimate is not None and 0.0 <= estimate < ABSURD_ANSWER


async def run_cell(args, cfg: ModelConfig, dataset: str, task: str, out: Path, model, formatter,
                   limiter: asyncio.Semaphore) -> list[dict]:
    record = task_record(load_dataset(args.data, dataset), dataset, task)
    truth, n = float(record.answer), record.vertex_num
    rows: list[dict] = []

    async def job(i: int) -> None:
        async with limiter:
            rng = run_rng(args.seed, i)  # same noise stream as every other runner
            with collect_errors(dataset=dataset, task=task, method="Naive", run=i + 1) as errors:
                t0 = time.perf_counter()
                noisy = build_noisy_graph(record.graph(), naive_budget(args.eps).eps1, rng)
                prompt = naive_prompt(record, noisy.edges, args.naive_prompt)
                reply = await chat(model, formatter, None, prompt, agent="Naive")
                elapsed = time.perf_counter() - t0
                estimate = extract_number(reply) if reply else None
                # with the boxed instruction a reply without \boxed{} was cut off
                # (max_tokens) or never answered: its last number is a node id, not an answer
                missing_box = args.naive_prompt == "boxed" and "\\boxed" not in (reply or "")
                if missing_box or not is_sane(estimate):
                    record_error(
                        "parse_failure",
                        "Naive: no usable numeric answer (empty, truncated without \\boxed{}, or degenerate)",
                        reply=reply, agent="Naive", phase="answer", raw_estimate=estimate,
                    )
                    estimate = None
            rule = gt_naive(record.graph(), task, args.eps, run_rng(args.seed, i))
            row = {
                "dataset": dataset,
                "task": task,
                "n": n,
                "truth": truth,
                "run": i + 1,
                "seed": args.seed,
                "estimate": estimate,
                "relative_error": relative_error(estimate, truth, n) if estimate is not None else None,
                "gt_naive": rule,
                "gt_naive_relative_error": relative_error(rule, truth, n),
                "noisy_edges": noisy.m,
                "prompt_chars": len(prompt),
                "elapsed": round(elapsed, 2),
                "api_retries": count_errors(errors, *RETRY_KINDS),
                "failed_calls": count_errors(errors, "call_failed"),
                "errors": errors,
                "reply": reply,
                "provider": cfg.provider,
                "node_model": cfg.node_model,
                "curator_model": cfg.curator_model,
                "naive_prompt": args.naive_prompt,
            }
            append_jsonl(row, out / "runs.jsonl")
            rows.append(row)
            if args.verbose:
                re_ = "-" if row["relative_error"] is None else f"{row['relative_error']:.3f}"
                print(f"  {dataset:>3} {task:<14} run {i + 1:>3}/{args.runs} est={estimate} truth={truth:.1f} "
                      f"RE={re_} gt={rule:.1f} edges={noisy.m} {row['elapsed']}s", flush=True)

    await asyncio.gather(*(job(i) for i in range(args.runs)))
    return rows


def summarize(rows: list[dict]) -> list[dict]:
    out = []
    for key in dict.fromkeys((r["dataset"], r["task"]) for r in rows):
        cell = [r for r in rows if (r["dataset"], r["task"]) == key]
        ok = [r for r in cell if r["relative_error"] is not None]
        re_naive = [r["relative_error"] for r in ok]
        re_gt = [r["gt_naive_relative_error"] for r in ok]
        paired = [a - b for a, b in zip(re_naive, re_gt)]
        out.append({
            "dataset": key[0],
            "task": key[1],
            "n": cell[0]["n"],
            "truth": cell[0]["truth"],
            "runs": len(cell),
            "answered": len(ok),
            "Naive": float(np.mean(re_naive)) if re_naive else None,
            "se_naive": float(np.std(re_naive, ddof=1) / math.sqrt(len(re_naive))) if len(re_naive) > 1 else None,
            "GT-Naive": float(np.mean(re_gt)),
            "naive_minus_gt": float(np.mean(paired)) if paired else None,
            "parse_failures": sum(1 for r in cell if r["relative_error"] is None),
            "failed_calls": int(sum(r["failed_calls"] for r in cell)),
            "api_retries": int(sum(r["api_retries"] for r in cell)),
            "median_estimate": float(np.median([r["estimate"] for r in ok])) if ok else None,
            "noisy_edges": cell[0]["noisy_edges"],
            "provider": cell[0]["provider"],
            "curator_model": cell[0]["curator_model"],
            "naive_prompt": cell[0]["naive_prompt"],
        })
    return out


def build_table(summary: list[dict], datasets: list[str], tasks: list[str], methods: dict[str, str]) -> str:
    """``methods`` maps a display name to the summary column."""
    lines = ["| Task | Method | " + " | ".join(datasets) + " | Avg. |", "|" + "---|" * (len(datasets) + 3)]
    idx = {(r["task"], r["dataset"]): r for r in summary}
    for task in tasks:
        for label, column in methods.items():
            cells, vals = [], []
            for ds in datasets:
                row = idx.get((task, ds))
                value = None if row is None else row.get(column)
                if value is None:
                    cells.append("-")
                else:
                    cells.append(f"{value:.4f}")
                    if math.isfinite(value):
                        vals.append(value)
            if not vals:
                continue
            avg = f"{float(np.mean(vals)):.4f}"
            lines.append(f"| {task} | {label} | " + " | ".join(cells) + f" | {avg} |")
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--datasets", default="CU,Do,ML,CS,EE", help=f"comma separated, from {DATASETS} (PM needs >32k context)")
    ap.add_argument("--tasks", default=",".join(TASKS), help=f"comma separated, from {TASKS}")
    ap.add_argument("--data", default=str(DATA_DIR))
    ap.add_argument("--runs", type=int, default=20, help="runs per (dataset, task); run i uses noise [seed, i]")
    ap.add_argument("--eps", type=float, default=2.0)
    ap.add_argument("--naive-prompt", choices=("boxed", "paper", "direct"), default="boxed",
                    help="'boxed' (default): paper prompt + 'put the final number in \\\\boxed{}'; "
                         "'paper': (V(G), Q) + noisy edge list only; 'direct': + 'answer with the number only'")
    ap.add_argument("--provider", default="vllm", choices=PROVIDERS)
    ap.add_argument("--node-model", default="Qwen3-8B")
    ap.add_argument("--curator-model", default="Qwen3-8B", help="Naive answers with this model")
    ap.add_argument("--config", default=str(ROOT.parent / "psc" / "config.vllm.toml"))
    ap.add_argument("--profile", default=None)
    ap.add_argument("--parallel-runs", type=int, default=8)
    ap.add_argument("--concurrency", type=int, default=8)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--tag", default=None)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    args.datasets = [d.strip() for d in args.datasets.split(",") if d.strip()]
    args.tasks = [t.strip() for t in args.tasks.split(",") if t.strip()]
    if set(args.datasets) - set(DATASETS) or set(args.tasks) - set(TASKS):
        ap.error(f"datasets from {DATASETS}, tasks from {TASKS}")
    if args.runs < 1:
        ap.error("--runs must be positive")

    cfg = ModelConfig.from_env(
        args.provider, config_path=args.config, profile=args.profile,
        node_model=args.node_model, curator_model=args.curator_model,
        max_concurrency=args.concurrency, parallel_runs=args.parallel_runs,
    )
    cells = [(ds, task) for ds in args.datasets for task in args.tasks]
    print(f"provider={cfg.provider} curator_model={cfg.curator_model} temperature={cfg.temperature} "
          f"eps={args.eps:g} runs/cell={args.runs} cells={len(cells)} "
          f"total={len(cells) * args.runs} LLM calls (1 per run)")
    if args.dry_run:
        for ds, task in cells:
            record = task_record(load_dataset(args.data, ds), ds, task)
            noisy = build_noisy_graph(record.graph(), naive_budget(args.eps).eps1, run_rng(args.seed, 0))
            print(f"  {ds:>3} {task:<14} n={record.vertex_num:>4} truth={float(record.answer):>9.1f} "
                  f"noisy_edges={noisy.m:>5} prompt_chars~{len(naive_prompt(record, noisy.edges, args.naive_prompt))}")
        return

    out = out_dir("execution", args.tag, f"naive_{cfg.curator_model}_{args.eps:g}")
    write_manifest(out, {
        "script": "run_naive_llm.py", "datasets": args.datasets, "tasks": args.tasks, "runs": args.runs,
        "eps": args.eps, "seed": args.seed, "provider": cfg.provider, "curator_model": cfg.curator_model,
        "temperature": cfg.temperature, "naive_prompt": args.naive_prompt,
        "routing": "naive_budget(eps): the whole budget on the RR noisy graph",
        "rng": "run_rng(seed, i) for both the LLM's noisy graph and the paired GT-Naive",
    })
    set_error_sink(out / "errors.jsonl")

    async def run_all() -> list[dict]:
        model = create_model(cfg, "curator")
        formatter = create_formatter(cfg)
        limiter = asyncio.Semaphore(max(1, cfg.parallel_runs))
        collected: list[dict] = []
        for ds, task in cells:
            rows = await run_cell(args, cfg, ds, task, out, model, formatter, limiter)
            collected += rows
            ok = [r["relative_error"] for r in rows if r["relative_error"] is not None]
            print(f"[{ds:>3} {task:<14}] answered {len(ok)}/{len(rows)} "
                  f"Naive={np.mean(ok) if ok else float('nan'):.4f} "
                  f"GT-Naive={np.mean([r['gt_naive_relative_error'] for r in rows]):.4f}", flush=True)
        return collected

    rows = asyncio.run(run_all())
    summary = summarize(rows)
    write_json(summary, out / "summary.json")
    table = build_table(summary, args.datasets, args.tasks,
                        {"Naive (LLM)": "Naive", "GT-Naive (same runs)": "GT-Naive",
                         "Naive - GT-Naive": "naive_minus_gt"})
    (out / "table.md").write_text(
        f"Naive (LLM) on the CertiCount tasks: eps = {args.eps:g}, {args.runs} runs per cell, "
        f"model = {cfg.curator_model}, prompt = {args.naive_prompt}. Mean relative error, lower is better.\n\n"
        f"{table}\n\n"
        "Naive = the model answers from the RR noisy edge list only; GT-Naive = the exact count on the same "
        "noisy graph; Naive - GT-Naive > 0 means the model's execution is worse than perfect execution of the "
        "same mechanism.\n",
        encoding="utf-8",
    )
    print("\n" + table)
    print(f"\nsaved in {out}/")


if __name__ == "__main__":
    main()
